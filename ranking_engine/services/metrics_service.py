"""
Metrics Service - Calculates and aggregates supplier performance metrics

This service handles the calculation of all metrics used to evaluate
supplier performance, which will feed into the Q-Learning ranking system.
"""

from django.db.models import Avg, Count, F, Sum, Max, Min, Q, Value, ExpressionWrapper, FloatField
from django.utils import timezone
from datetime import date, timedelta
import numpy as np

from api.models import (
    Supplier,
    SupplierProduct,
    SupplierPerformance,
    Transaction,
    SupplierRanking,
    RankingConfiguration
)


class MetricsService:
    """Service for calculating supplier performance metrics"""
    
    @staticmethod
    def get_active_configuration():
        """
        Returns the active ranking configuration
        """
        try:
            return RankingConfiguration.objects.get(is_active=True)
        except RankingConfiguration.DoesNotExist:
            # Return default configuration if none exists
            return RankingConfiguration(
                name="Default Configuration",
                learning_rate=0.1,
                discount_factor=0.9,
                exploration_rate=0.3,
                quality_weight=0.25,
                delivery_weight=0.25,
                price_weight=0.25,
                service_weight=0.25,
                is_active=True
            )
    
    @staticmethod
    def calculate_quality_metrics(supplier_id, days=90):
        """
        Calculates quality-related metrics for a supplier
        
        Returns:
            dict: Dictionary containing quality metrics
        """
        start_date = timezone.now() - timedelta(days=days)
        
        transactions = Transaction.objects.filter(
            supplier_id=supplier_id,
            order_date__gte=start_date
        )
        
        # Combine explicit performance records with transaction data
        performance_records = SupplierPerformance.objects.filter(
            supplier_id=supplier_id,
            date__gte=start_date
        )
        
        # Calculate quality metrics from transactions
        total_orders = transactions.count()
        total_quantity = transactions.aggregate(Sum('quantity'))['quantity__sum'] or 0
        total_defects = transactions.aggregate(Sum('defect_count'))['defect_count__sum'] or 0
        
        # Calculate defect rate
        defect_rate = (total_defects / total_quantity * 100) if total_quantity > 0 else 0
        
        # Calculate return rate (transactions marked as RETURNED)
        returned_transactions = transactions.filter(status='RETURNED')
        return_rate = (returned_transactions.count() / total_orders * 100) if total_orders > 0 else 0
        
        # Average quality scores from performance records
        avg_quality_score = performance_records.aggregate(Avg('quality_score'))['quality_score__avg'] or 0
        avg_recorded_defect_rate = performance_records.aggregate(Avg('defect_rate'))['defect_rate__avg'] or 0
        avg_recorded_return_rate = performance_records.aggregate(Avg('return_rate'))['return_rate__avg'] or 0
        
        # Combine transaction-based metrics with recorded metrics
        # using weightings that favor recent transaction data
        combined_defect_rate = defect_rate * 0.7 + avg_recorded_defect_rate * 0.3
        combined_return_rate = return_rate * 0.7 + avg_recorded_return_rate * 0.3
        
        # Convert to a 0-10 scale for consistency
        defect_rate_score = max(0, 10 - (combined_defect_rate / 2))
        return_rate_score = max(0, 10 - (combined_return_rate / 2))
        
        # Weighted quality score (can be adjusted based on business needs)
        quality_score = (
            avg_quality_score * 0.4 +
            defect_rate_score * 0.4 +
            return_rate_score * 0.2
        )
        
        return {
            'quality_score': quality_score,
            'defect_rate': combined_defect_rate,
            'return_rate': combined_return_rate,
            'raw_quality_score': avg_quality_score,
            'transactions_analyzed': total_orders,
            'quantity_analyzed': total_quantity
        }
    
    @staticmethod
    def calculate_delivery_metrics(supplier_id, days=90):
        """
        Calculates delivery-related metrics for a supplier
        
        Returns:
            dict: Dictionary containing delivery metrics
        """
        start_date = timezone.now() - timedelta(days=days)
        
        # Get completed transactions
        completed_transactions = Transaction.objects.filter(
            supplier_id=supplier_id,
            order_date__gte=start_date,
            actual_delivery_date__isnull=False  # Only consider delivered orders
        ).exclude(
            status__in=['CANCELLED', 'ORDERED']  # Exclude non-completed orders
        )
        
        # Get performance records
        performance_records = SupplierPerformance.objects.filter(
            supplier_id=supplier_id,
            date__gte=start_date
        )
        
        # Calculate on-time delivery rate from transactions
        total_delivered = completed_transactions.count()
        on_time_delivered = completed_transactions.filter(
            actual_delivery_date__lte=F('expected_delivery_date')
        ).count()
        
        on_time_rate = (on_time_delivered / total_delivered * 100) if total_delivered > 0 else 0
        
        # Calculate average delay in days for delayed transactions
        delayed_transactions = completed_transactions.filter(
            actual_delivery_date__gt=F('expected_delivery_date')
        )
        
        # Instead of using ExpressionWrapper directly, use the delay_days property
        # This ensures we're working with numerical days, not timedelta objects
        if delayed_transactions.exists():
            total_delay_days = 0
            for transaction in delayed_transactions:
                total_delay_days += transaction.delay_days
            avg_delay = total_delay_days / delayed_transactions.count()
        else:
            avg_delay = 0
        
        # Get averages from performance records
        avg_recorded_on_time_rate = performance_records.aggregate(
            Avg('on_time_delivery_rate')
        )['on_time_delivery_rate__avg'] or 0
        
        avg_recorded_delay = performance_records.aggregate(
            Avg('average_delay_days')
        )['average_delay_days__avg'] or 0
        
        # Combine transaction-based metrics with recorded metrics
        combined_on_time_rate = on_time_rate * 0.7 + avg_recorded_on_time_rate * 0.3
        combined_avg_delay = avg_delay * 0.7 + avg_recorded_delay * 0.3
        
        # Convert to a 0-10 scale score
        on_time_score = combined_on_time_rate / 10
        delay_score = max(0, 10 - min(10, combined_avg_delay * 2))
        
        # Average lead time across products
        avg_lead_time = SupplierProduct.objects.filter(
            supplier_id=supplier_id
        ).aggregate(Avg('lead_time_days'))['lead_time_days__avg'] or 0
        
        # Weighted delivery score
        delivery_score = (
            on_time_score * 0.6 +
            delay_score * 0.4
        )
        
        return {
            'delivery_score': delivery_score,
            'on_time_delivery_rate': combined_on_time_rate,
            'average_delay_days': combined_avg_delay,
            'average_lead_time': avg_lead_time,
            'transactions_analyzed': total_delivered
        }
    
    @staticmethod
    def calculate_price_metrics(supplier_id, days=90):
        """
        Calculates price-related metrics for a supplier
        
        Returns:
            dict: Dictionary containing price metrics
        """
        # Get performance records
        performance_records = SupplierPerformance.objects.filter(
            supplier_id=supplier_id,
            date__gte=date.today() - timedelta(days=days)
        )
        
        # Get average price competitiveness from performance records
        avg_price_comp = performance_records.aggregate(
            Avg('price_competitiveness')
        )['price_competitiveness__avg'] or 5.0  # Default to average if no data
        
        # Get all supplier products
        supplier_products = SupplierProduct.objects.filter(
            supplier_id=supplier_id
        )
        
        # Calculate price competitiveness for each product by comparing with other suppliers
        product_price_scores = []
        
        for sp in supplier_products:
            # Get all suppliers for this product
            all_supplier_prices = SupplierProduct.objects.filter(
                product_id=sp.product_id
            ).values_list('unit_price', flat=True)
            
            if all_supplier_prices:
                # Convert to list for numpy functions
                prices_list = list(all_supplier_prices)
                
                # Calculate percentile rank (lower is better for price)
                if len(prices_list) > 1:
                    sorted_prices = sorted(prices_list)
                    
                    # Fix: Use a more robust approach to find the closest price or position
                    # Instead of exact matching, find the position where this price would be inserted
                    current_price = float(sp.unit_price)
                    
                    # Find the position where this value would be inserted in the sorted list
                    import bisect
                    position = bisect.bisect_left(sorted_prices, current_price)
                    
                    # Calculate percentile based on position
                    percentile = position / (len(sorted_prices) - 1) if len(sorted_prices) > 1 else 0.5
                    
                    # Convert to a 0-10 score (10 being the cheapest)
                    price_score = 10 * (1 - percentile)
                else:
                    price_score = 5.0  # Default if this is the only supplier
                
                product_price_scores.append(price_score)
        
        # Calculate overall price score
        calculated_price_score = (
            np.mean(product_price_scores) if product_price_scores else 5.0
        )
        
        # Combine calculated score with recorded competitiveness
        price_score = calculated_price_score * 0.7 + avg_price_comp * 0.3
        
        return {
            'price_score': price_score,
            'price_competitiveness': avg_price_comp,
            'calculated_price_competitiveness': calculated_price_score,
            'products_analyzed': len(product_price_scores)
        }
    
    @staticmethod
    def calculate_service_metrics(supplier_id, days=90):
        """
        Calculates service-related metrics for a supplier
        
        Returns:
            dict: Dictionary containing service metrics
        """
        # Get performance records
        performance_records = SupplierPerformance.objects.filter(
            supplier_id=supplier_id,
            date__gte=date.today() - timedelta(days=days)
        )
        
        # Get service metrics from performance records
        avg_responsiveness = performance_records.aggregate(
            Avg('responsiveness')
        )['responsiveness__avg'] or 5.0
        
        avg_issue_resolution = performance_records.aggregate(
            Avg('issue_resolution_time')
        )['issue_resolution_time__avg']
        
        avg_fill_rate = performance_records.aggregate(
            Avg('fill_rate')
        )['fill_rate__avg'] or 90.0  # Default to 90% if no data
        
        avg_order_accuracy = performance_records.aggregate(
            Avg('order_accuracy')
        )['order_accuracy__avg'] or 95.0  # Default to 95% if no data
        
        # Convert to 0-10 scales where needed
        fill_rate_score = avg_fill_rate / 10
        order_accuracy_score = avg_order_accuracy / 10
        
        # Convert issue resolution time to a score (lower is better)
        if avg_issue_resolution is not None:
            # Assuming 72 hours as a reference point (3 days to resolve an issue)
            issue_resolution_score = max(0, 10 - (avg_issue_resolution / 7.2))
        else:
            issue_resolution_score = 5.0  # Default if no data
        
        # Weighted service score
        service_score = (
            avg_responsiveness * 0.3 +
            issue_resolution_score * 0.2 +
            fill_rate_score * 0.25 +
            order_accuracy_score * 0.25
        )
        
        return {
            'service_score': service_score,
            'responsiveness': avg_responsiveness,
            'issue_resolution_time': avg_issue_resolution,
            'fill_rate': avg_fill_rate,
            'order_accuracy': avg_order_accuracy
        }
    
    @staticmethod
    def calculate_combined_metrics(supplier_id, days=90):
        """
        Calculates all metrics for a supplier and returns a combined result
        
        Returns:
            dict: Dictionary containing all metrics
        """
        # Get active configuration for weights
        config = MetricsService.get_active_configuration()
        
        # Calculate individual metric categories
        quality_metrics = MetricsService.calculate_quality_metrics(supplier_id, days)
        delivery_metrics = MetricsService.calculate_delivery_metrics(supplier_id, days)
        price_metrics = MetricsService.calculate_price_metrics(supplier_id, days)
        service_metrics = MetricsService.calculate_service_metrics(supplier_id, days)
        
        # Calculate overall score based on configuration weights
        overall_score = (
            quality_metrics['quality_score'] * config.quality_weight +
            delivery_metrics['delivery_score'] * config.delivery_weight +
            price_metrics['price_score'] * config.price_weight +
            service_metrics['service_score'] * config.service_weight
        )
        
        # Build combined metrics dictionary
        combined_metrics = {
            'supplier_id': supplier_id,
            'overall_score': overall_score,
            'quality_score': quality_metrics['quality_score'],
            'delivery_score': delivery_metrics['delivery_score'],
            'price_score': price_metrics['price_score'],
            'service_score': service_metrics['service_score'],
            'quality_metrics': quality_metrics,
            'delivery_metrics': delivery_metrics,
            'price_metrics': price_metrics,
            'service_metrics': service_metrics,
            'calculation_date': date.today()
        }
        
        return combined_metrics
    
    @staticmethod
    def calculate_metrics_for_all_suppliers(days=90):
        """
        Calculates metrics for all active suppliers
        
        Returns:
            list: List of dictionaries with supplier metrics
        """
        suppliers = Supplier.objects.filter(is_active=True)
        all_metrics = []
        
        for supplier in suppliers:
            metrics = MetricsService.calculate_combined_metrics(supplier.id, days)
            metrics['supplier_name'] = supplier.name
            metrics['supplier_code'] = supplier.code
            all_metrics.append(metrics)
        
        # Sort by overall score
        all_metrics.sort(key=lambda x: x['overall_score'], reverse=True)
        
        # Add rank
        for i, metrics in enumerate(all_metrics):
            metrics['rank'] = i + 1
        
        return all_metrics