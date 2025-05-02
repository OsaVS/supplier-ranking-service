"""
State mapper module for Q-Learning implementation.

This module is responsible for mapping supplier data to states that can be used by the Q-Learning algorithm.
It categorizes supplier performance metrics into discrete states that the Q-Learning agent can work with.
"""

from api.models import Supplier, SupplierPerformance, Transaction, QLearningState
from django.db.models import Avg, Count, Sum, F, ExpressionWrapper, FloatField
from django.db.models.functions import Coalesce
from datetime import datetime, timedelta
import numpy as np


class StateMapper:
    """
    Maps supplier data to states for Q-Learning algorithm.
    
    This class contains methods for converting supplier performance metrics into 
    discrete states that can be used by the Q-Learning algorithm. 
    """
    
    # Define thresholds for different metrics
    QUALITY_THRESHOLDS = [3.0, 5.0, 7.0, 9.0]  # Poor, Average, Good, Excellent
    DELIVERY_THRESHOLDS = [70, 80, 90, 95]     # % on-time delivery
    PRICE_THRESHOLDS = [3.0, 5.0, 7.0, 9.0]    # Price competitiveness score
    SERVICE_THRESHOLDS = [3.0, 5.0, 7.0, 9.0]  # Service quality score
    
    def __init__(self, time_window=90):
        """
        Initialize the StateMapper.
        
        Args:
            time_window (int): Number of days to look back for metrics calculation
        """
        self.time_window = time_window
    
    def get_supplier_state(self, supplier_id):
        """
        Get the current state for a specific supplier based on their recent performance.
        
        Args:
            supplier_id (int): ID of the supplier
            
        Returns:
            QLearningState: The state object representing the supplier's current state
        """
        # Calculate recent metrics
        metrics = self._calculate_supplier_metrics(supplier_id)
        
        # Map metrics to state category
        quality_category = self._categorize_metric(metrics['quality_score'], self.QUALITY_THRESHOLDS)
        delivery_category = self._categorize_metric(metrics['on_time_delivery_rate'], self.DELIVERY_THRESHOLDS)
        price_category = self._categorize_metric(metrics['price_competitiveness'], self.PRICE_THRESHOLDS)
        service_category = self._categorize_metric(metrics['service_score'], self.SERVICE_THRESHOLDS)
        
        # Create a state name based on the categories
        state_name = f"Q{quality_category}_D{delivery_category}_P{price_category}_S{service_category}"
        
        # Get or create the state in the database
        state, created = QLearningState.objects.get_or_create(
            name=state_name,
            defaults={'description': f"Quality: {quality_category}/5, Delivery: {delivery_category}/5, "
                                    f"Price: {price_category}/5, Service: {service_category}/5"}
        )
        
        return state
    
    def _calculate_supplier_metrics(self, supplier_id):
        """
        Calculate recent performance metrics for a supplier.
        
        Args:
            supplier_id (int): ID of the supplier
            
        Returns:
            dict: Dictionary containing performance metrics
        """
        # Define the date range for recent performance
        cutoff_date = datetime.now().date() - timedelta(days=self.time_window)
        
        # Get recent performance records
        recent_performance = SupplierPerformance.objects.filter(
            supplier_id=supplier_id,
            date__gte=cutoff_date
        )
        
        # Get recent transactions
        recent_transactions = Transaction.objects.filter(
            supplier_id=supplier_id,
            order_date__gte=cutoff_date
        )
        
        # Calculate average performance metrics
        metrics = {}
        
        if recent_performance.exists():
            # Quality metrics
            metrics['quality_score'] = recent_performance.aggregate(
                avg=Avg('quality_score')
            )['avg'] or 5.0
            
            metrics['defect_rate'] = recent_performance.aggregate(
                avg=Avg('defect_rate')
            )['avg'] or 0.0
            
            # Delivery metrics
            metrics['on_time_delivery_rate'] = recent_performance.aggregate(
                avg=Avg('on_time_delivery_rate')
            )['avg'] or 80.0
            
            # Price metrics
            metrics['price_competitiveness'] = recent_performance.aggregate(
                avg=Avg('price_competitiveness')
            )['avg'] or 5.0
            
            # Service metrics
            metrics['responsiveness'] = recent_performance.aggregate(
                avg=Avg('responsiveness')
            )['avg'] or 5.0
            
            metrics['service_score'] = (metrics['responsiveness'] + 
                                     recent_performance.aggregate(avg=Coalesce(Avg('compliance_score'), 5.0))['avg']) / 2
            
        else:
            # Default values if no recent performance data
            metrics['quality_score'] = 5.0
            metrics['defect_rate'] = 0.0
            metrics['on_time_delivery_rate'] = 80.0
            metrics['price_competitiveness'] = 5.0
            metrics['responsiveness'] = 5.0
            metrics['service_score'] = 5.0
        
        # Supplement with transaction data if available
        if recent_transactions.exists():
            # Calculate actual delivery performance from transactions
            delivered = recent_transactions.filter(actual_delivery_date__isnull=False)
            if delivered.exists():
                # Update on-time delivery rate using actual transaction data
                on_time_count = delivered.filter(actual_delivery_date__lte=F('expected_delivery_date')).count()
                actual_on_time_rate = (on_time_count / delivered.count()) * 100
                # Blend model data with actual transaction data (with more weight to actual data)
                metrics['on_time_delivery_rate'] = 0.3 * metrics['on_time_delivery_rate'] + 0.7 * actual_on_time_rate
                
                # Calculate average delay
                delay_expr = ExpressionWrapper(
                    F('actual_delivery_date') - F('expected_delivery_date'),
                    output_field=FloatField()
                )
                avg_delay = delivered.annotate(delay=delay_expr).aggregate(avg=Avg('delay'))['avg'] or 0
                metrics['avg_delay_days'] = max(0, avg_delay)
                
                # Calculate defect rate from transactions
                actual_defect_rate = (delivered.aggregate(total_defects=Sum('defect_count'))['total_defects'] or 0) / \
                                    (delivered.aggregate(total_qty=Sum('quantity'))['total_qty'] or 1) * 100
                metrics['defect_rate'] = 0.3 * metrics['defect_rate'] + 0.7 * actual_defect_rate
        
        return metrics
    
    def _categorize_metric(self, value, thresholds):
        """
        Categorize a metric value based on thresholds.
        
        Args:
            value (float): The metric value to categorize
            thresholds (list): List of threshold values in ascending order
            
        Returns:
            int: Category value from 1 to 5
        """
        # Default to lowest category
        category = 1
        
        # Increment category based on thresholds
        for i, threshold in enumerate(thresholds):
            if value >= threshold:
                category = i + 2
            else:
                break
                
        return category
    
    def get_all_possible_states(self):
        """
        Generate all possible state combinations.
        
        Returns:
            list: List of all possible state objects
        """
        states = []
        
        # Create all combinations of categories
        for q in range(1, 6):
            for d in range(1, 6):
                for p in range(1, 6):
                    for s in range(1, 6):
                        state_name = f"Q{q}_D{d}_P{p}_S{s}"
                        state, created = QLearningState.objects.get_or_create(
                            name=state_name,
                            defaults={'description': f"Quality: {q}/5, Delivery: {d}/5, "
                                                   f"Price: {p}/5, Service: {s}/5"}
                        )
                        states.append(state)
        
        return states
    
    def get_state_from_metrics(self, metrics):
        """
        Map metrics dictionary directly to a state.
        
        Args:
            metrics (dict): Dictionary containing performance metrics
                
        Returns:
            QLearningState: The state object representing the supplier's state
        """
        # Get metrics with default values if keys are missing
        quality_score = metrics.get('quality_score', 5.0)
        on_time_delivery_rate = metrics.get('on_time_delivery_rate', 80.0)
        price_competitiveness = metrics.get('price_competitiveness', 5.0)
        service_score = metrics.get('service_score', 5.0)
        
        # Map metrics to state category
        quality_category = self._categorize_metric(quality_score, self.QUALITY_THRESHOLDS)
        delivery_category = self._categorize_metric(on_time_delivery_rate, self.DELIVERY_THRESHOLDS)
        price_category = self._categorize_metric(price_competitiveness, self.PRICE_THRESHOLDS)
        service_category = self._categorize_metric(service_score, self.SERVICE_THRESHOLDS)
        
        # Create a state name based on the categories
        state_name = f"Q{quality_category}_D{delivery_category}_P{price_category}_S{service_category}"
        
        # Get or create the state in the database
        state, created = QLearningState.objects.get_or_create(
            name=state_name,
            defaults={'description': f"Quality: {quality_category}/5, Delivery: {delivery_category}/5, "
                                    f"Price: {price_category}/5, Service: {service_category}/5"}
        )
        
        return state