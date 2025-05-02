"""
Utility functions for preprocessing supplier data for the Q-Learning algorithm.
This module handles data normalization, feature extraction, and preparation
of supplier performance metrics for use in the ranking system.
"""
import pandas as pd
import numpy as np
from django.db.models import Avg, Count, F, Sum, Max, Min
from django.utils import timezone
from datetime import timedelta
from api.models import (
    Supplier, SupplierPerformance, Transaction, SupplierProduct,
    QLearningState, QLearningAction, QTableEntry
)


def normalize_metric(value, min_val, max_val, reverse=False):
    """
    Normalize a metric to a value between 0 and 1.
    
    Args:
        value: The value to normalize
        min_val: The minimum value in the dataset
        max_val: The maximum value in the dataset
        reverse: If True, smaller values are better (e.g., defect rate)
        
    Returns:
        Normalized value between 0 and 1
    """
    if min_val == max_val:
        return 0.5  # Default when there's no variation
    
    if reverse:
        # For metrics where lower is better
        return 1 - ((value - min_val) / (max_val - min_val)) if max_val > min_val else 0.5
    else:
        # For metrics where higher is better
        return (value - min_val) / (max_val - min_val) if max_val > min_val else 0.5


def calculate_supplier_metrics(supplier_id, start_date=None, end_date=None):
    """
    Calculate comprehensive metrics for a specific supplier within a date range.
    
    Args:
        supplier_id: ID of the supplier
        start_date: Beginning of the date range (default: 90 days ago)
        end_date: End of the date range (default: today)
        
    Returns:
        Dictionary containing calculated metrics
    """
    if not start_date:
        start_date = timezone.now().date() - timedelta(days=90)
    if not end_date:
        end_date = timezone.now().date()
        
    # Get supplier
    try:
        supplier = Supplier.objects.get(id=supplier_id)
    except Supplier.DoesNotExist:
        return None
    
    # Get performance records in date range
    performance_records = SupplierPerformance.objects.filter(
        supplier_id=supplier_id,
        date__gte=start_date,
        date__lte=end_date
    )
    
    # Get transactions in date range
    transactions = Transaction.objects.filter(
        supplier_id=supplier_id,
        order_date__date__gte=start_date,
        order_date__date__lte=end_date
    )
    
    # If no data, return empty metrics
    if not performance_records.exists() and not transactions.exists():
        return {
            'supplier_id': supplier_id,
            'supplier_name': supplier.name,
            'data_available': False,
            'message': 'No data available for this supplier in the specified date range'
        }
    
    # Calculate average performance metrics if records exist
    performance_metrics = {}
    if performance_records.exists():
        performance_agg = performance_records.aggregate(
            avg_quality_score=Avg('quality_score'),
            avg_defect_rate=Avg('defect_rate'),
            avg_return_rate=Avg('return_rate'),
            avg_on_time_delivery_rate=Avg('on_time_delivery_rate'),
            avg_delay_days=Avg('average_delay_days'),
            avg_price_competitiveness=Avg('price_competitiveness'),
            avg_responsiveness=Avg('responsiveness'),
            avg_issue_resolution_time=Avg('issue_resolution_time'),
            avg_fill_rate=Avg('fill_rate'),
            avg_order_accuracy=Avg('order_accuracy'),
            avg_compliance_score=Avg('compliance_score')
        )
        performance_metrics = performance_agg
    
    # Calculate transaction-based metrics if transactions exist
    transaction_metrics = {}
    if transactions.exists():
        delivered_transactions = transactions.filter(
            status='DELIVERED',
            actual_delivery_date__isnull=False
        )
        
        # Calculate delivery metrics
        if delivered_transactions.exists():
            on_time_count = delivered_transactions.filter(
                actual_delivery_date__lte=F('expected_delivery_date')
            ).count()
            
            total_delivered = delivered_transactions.count()
            on_time_percentage = (on_time_count / total_delivered * 100) if total_delivered > 0 else 0
            
            avg_delay = delivered_transactions.filter(
                actual_delivery_date__gt=F('expected_delivery_date')
            ).aggregate(
                avg_delay=Avg(F('actual_delivery_date') - F('expected_delivery_date'))
            )['avg_delay']
            
            avg_delay_days = avg_delay.days if avg_delay else 0
            
            transaction_metrics['transaction_on_time_rate'] = on_time_percentage
            transaction_metrics['transaction_avg_delay_days'] = avg_delay_days
        
        # Calculate quality metrics
        total_quantity = transactions.aggregate(total=Sum('quantity'))['total'] or 0
        total_defects = transactions.aggregate(total=Sum('defect_count'))['total'] or 0
        
        if total_quantity > 0:
            defect_rate = (total_defects / total_quantity * 100)
            transaction_metrics['transaction_defect_rate'] = defect_rate
        
        # Calculate cancellation rate
        cancelled_count = transactions.filter(status='CANCELLED').count()
        total_transactions = transactions.count()
        
        if total_transactions > 0:
            cancellation_rate = (cancelled_count / total_transactions * 100)
            transaction_metrics['cancellation_rate'] = cancellation_rate
    
    # Combine all metrics
    result = {
        'supplier_id': supplier_id,
        'supplier_name': supplier.name,
        'data_available': True,
        'metrics_period': {
            'start_date': start_date,
            'end_date': end_date
        }
    }
    
    # Add supplier basic info
    result.update({
        'credit_score': supplier.credit_score,
        'average_lead_time': supplier.average_lead_time,
        'supplier_size': supplier.supplier_size,
        'is_active': supplier.is_active,
    })
    
    # Add performance metrics if available
    if performance_metrics:
        result.update(performance_metrics)
    
    # Add transaction metrics if available
    if transaction_metrics:
        result.update(transaction_metrics)
    
    return result


def extract_features_for_q_learning(supplier_id, metrics=None):
    """
    Extract and transform supplier metrics into features for Q-Learning.
    
    Args:
        supplier_id: ID of the supplier
        metrics: Pre-calculated metrics (optional, will be calculated if not provided)
        
    Returns:
        Dictionary of features suitable for Q-Learning state mapping
    """
    if not metrics:
        metrics = calculate_supplier_metrics(supplier_id)
    
    if not metrics or not metrics.get('data_available', False):
        return None
    
    # Get all suppliers for normalization context
    all_suppliers = Supplier.objects.filter(is_active=True)
    supplier_ids = list(all_suppliers.values_list('id', flat=True))
    
    # If there's only one supplier, we can't normalize properly
    if len(supplier_ids) <= 1:
        return {
            'supplier_id': supplier_id,
            'quality_score': 0.5,
            'delivery_score': 0.5,
            'price_score': 0.5,
            'responsiveness_score': 0.5,
            'risk_score': 0.5
        }
    
    # Get min/max values for normalization
    # For quality metrics
    quality_bounds = SupplierPerformance.objects.filter(
        supplier_id__in=supplier_ids
    ).aggregate(
        min_quality=Min('quality_score'),
        max_quality=Max('quality_score'),
        min_defect=Min('defect_rate'),
        max_defect=Max('defect_rate')
    )
    
    # For delivery metrics
    delivery_bounds = SupplierPerformance.objects.filter(
        supplier_id__in=supplier_ids
    ).aggregate(
        min_otd=Min('on_time_delivery_rate'),
        max_otd=Max('on_time_delivery_rate'),
        min_delay=Min('average_delay_days'),
        max_delay=Max('average_delay_days')
    )
    
    # For price metrics
    price_bounds = SupplierPerformance.objects.filter(
        supplier_id__in=supplier_ids
    ).aggregate(
        min_price=Min('price_competitiveness'),
        max_price=Max('price_competitiveness')
    )
    
    # Extract and normalize features
    features = {
        'supplier_id': supplier_id,
    }
    
    # Quality feature
    quality_score = metrics.get('avg_quality_score', 5.0)
    defect_rate = metrics.get('avg_defect_rate', 2.0)
    
    norm_quality = normalize_metric(
        quality_score,
        quality_bounds.get('min_quality', 0),
        quality_bounds.get('max_quality', 10)
    )
    
    norm_defect = normalize_metric(
        defect_rate,
        quality_bounds.get('min_defect', 0),
        quality_bounds.get('max_defect', 100),
        reverse=True  # Lower defect rate is better
    )
    
    features['quality_score'] = (norm_quality + norm_defect) / 2
    
    # Delivery feature
    on_time_rate = metrics.get('avg_on_time_delivery_rate', 50.0)
    delay_days = metrics.get('avg_delay_days', 2.0)
    
    norm_otd = normalize_metric(
        on_time_rate,
        delivery_bounds.get('min_otd', 0),
        delivery_bounds.get('max_otd', 100)
    )
    
    norm_delay = normalize_metric(
        delay_days,
        delivery_bounds.get('min_delay', 0),
        delivery_bounds.get('max_delay', 10),
        reverse=True  # Lower delay is better
    )
    
    features['delivery_score'] = (norm_otd + norm_delay) / 2
    
    # Price feature
    price_comp = metrics.get('avg_price_competitiveness', 5.0)
    
    features['price_score'] = normalize_metric(
        price_comp,
        price_bounds.get('min_price', 0),
        price_bounds.get('max_price', 10)
    )
    
    # Responsiveness feature (service)
    resp_score = metrics.get('avg_responsiveness', 5.0)
    features['responsiveness_score'] = resp_score / 10.0  # Assuming 0-10 scale
    
    # Risk score (based on credit score, cancellation rate, etc.)
    credit_score = metrics.get('credit_score', 50.0)
    cancellation_rate = metrics.get('cancellation_rate', 5.0)
    
    # Normalize and combine for risk (lower is better for risk)
    norm_credit = credit_score / 100.0 if credit_score else 0.5
    norm_cancel = 1.0 - (cancellation_rate / 100.0) if cancellation_rate else 0.5
    
    features['risk_score'] = (norm_credit + norm_cancel) / 2
    
    return features


def discretize_features(features, num_buckets=5):
    """
    Convert continuous feature values to discrete buckets for Q-Learning states.
    
    Args:
        features: Dictionary of normalized features
        num_buckets: Number of buckets to divide the feature range into
        
    Returns:
        Dictionary of discretized features
    """
    discretized = {}
    
    for key, value in features.items():
        if key == 'supplier_id':
            discretized[key] = value
            continue
            
        if value is None:
            discretized[key] = 'medium'  # Default for missing values
            continue
            
        # Divide 0-1 range into buckets
        bucket_size = 1.0 / num_buckets
        bucket = min(int(value / bucket_size), num_buckets - 1)
        
        # Convert bucket to text label
        if num_buckets == 3:
            labels = ['low', 'medium', 'high']
        elif num_buckets == 5:
            labels = ['very_low', 'low', 'medium', 'high', 'very_high']
        else:
            labels = [str(i) for i in range(num_buckets)]
            
        discretized[key] = labels[bucket]
    
    return discretized


def create_state_key(discretized_features):
    """
    Create a state key string from discretized features for Q-Learning.
    
    Args:
        discretized_features: Dictionary of discretized features
        
    Returns:
        String representing the state
    """
    # Order of features in state key
    feature_order = [
        'quality_score', 'delivery_score', 'price_score', 
        'responsiveness_score', 'risk_score'
    ]
    
    # Create state key
    state_parts = []
    for feature in feature_order:
        if feature in discretized_features:
            state_parts.append(f"{feature}_{discretized_features[feature]}")
    
    return "_".join(state_parts)


def prepare_supplier_data_for_ranking(supplier_ids=None, days=90):
    """
    Prepare data for all suppliers (or specified suppliers) for ranking.
    
    Args:
        supplier_ids: List of supplier IDs (default: all active suppliers)
        days: Number of days to look back for data
        
    Returns:
        List of dictionaries with supplier features
    """
    if not supplier_ids:
        supplier_ids = Supplier.objects.filter(is_active=True).values_list('id', flat=True)
    
    start_date = timezone.now().date() - timedelta(days=days)
    end_date = timezone.now().date()
    
    result = []
    for supplier_id in supplier_ids:
        # Calculate metrics
        metrics = calculate_supplier_metrics(supplier_id, start_date, end_date)
        
        if not metrics or not metrics.get('data_available', False):
            continue
        
        # Extract features
        features = extract_features_for_q_learning(supplier_id, metrics)
        
        if features:
            # Add original metrics for reference
            features['raw_metrics'] = metrics
            result.append(features)
    
    return result


def get_data_from_other_groups():
    """
    Placeholder for getting data from other groups.
    This would be implemented to fetch data from Group 29, 30, and 32.
    
    Returns:
        Dictionary with data from other groups
    """
    # This would be implemented to integrate with other groups
    # For now, return a placeholder
    return {
        'group29_data': {
            'demand_forecast': {}  # Will contain demand forecasting data
        },
        'group30_data': {
            'blockchain_records': {}  # Will contain blockchain tracking data
        },
        'group32_data': {
            'logistics_data': {}  # Will contain logistics optimization data
        }
    }