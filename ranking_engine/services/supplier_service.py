"""
Supplier Service - Handles all supplier-related operations

This service acts as an abstraction layer for all supplier-related operations,
including CRUD operations and data retrieval for the ranking system.
"""

from django.db.models import Avg, Count, F, Max, Min, Q, Sum
from django.utils import timezone
from datetime import date, timedelta
from api.models import (
    Supplier, 
    SupplierProduct, 
    SupplierPerformance, 
    Transaction,
    SupplierRanking
)


class SupplierService:
    """Service for managing supplier operations"""
    
    @staticmethod
    def get_active_suppliers():
        """
        Returns all active suppliers
        """
        return Supplier.objects.filter(is_active=True)
    
    @staticmethod
    def get_supplier_by_id(supplier_id):
        """
        Returns a specific supplier by ID
        """
        try:
            return Supplier.objects.get(id=supplier_id)
        except Supplier.DoesNotExist:
            return None
    
    @staticmethod
    def get_supplier_products(supplier_id):
        """
        Returns all products offered by a supplier
        """
        return SupplierProduct.objects.filter(supplier_id=supplier_id)
    
    @staticmethod
    def get_supplier_performance_history(supplier_id, days=90):
        """
        Returns performance history for a supplier for the given time period
        """
        start_date = date.today() - timedelta(days=days)
        return SupplierPerformance.objects.filter(
            supplier_id=supplier_id,
            date__gte=start_date
        ).order_by('date')
    
    @staticmethod
    def get_supplier_transactions(supplier_id, days=90):
        """
        Returns transaction history for a supplier for the given time period
        """
        start_date = timezone.now() - timedelta(days=days)
        return Transaction.objects.filter(
            supplier_id=supplier_id,
            order_date__gte=start_date
        ).order_by('-order_date')
    
    @staticmethod
    def get_supplier_ranking_history(supplier_id, days=90):
        """
        Returns ranking history for a supplier
        """
        start_date = date.today() - timedelta(days=days)
        return SupplierRanking.objects.filter(
            supplier_id=supplier_id,
            date__gte=start_date
        ).order_by('date')
    
    @staticmethod
    def get_latest_supplier_rankings():
        """
        Returns the most recent ranking for each supplier
        """
        latest_date = SupplierRanking.objects.aggregate(Max('date'))['date__max']
        if not latest_date:
            return []
            
        return SupplierRanking.objects.filter(date=latest_date).order_by('rank')
    
    @staticmethod
    def get_top_ranked_suppliers(count=10, category=None):
        """
        Returns the top ranked suppliers, optionally filtered by product category
        """
        latest_date = SupplierRanking.objects.aggregate(Max('date'))['date__max']
        if not latest_date:
            return []
            
        rankings = SupplierRanking.objects.filter(date=latest_date).order_by('rank')
        
        if category:
            # Filter by suppliers who offer products in the specified category
            supplier_ids = SupplierProduct.objects.filter(
                product__category=category
            ).values_list('supplier_id', flat=True).distinct()
            
            rankings = rankings.filter(supplier_id__in=supplier_ids)
            
        return rankings[:count]
    
    @staticmethod
    def get_supplier_category_performance(supplier_id):
        """
        Returns supplier performance grouped by product category
        """
        # Get all product categories this supplier provides
        categories = SupplierProduct.objects.filter(
            supplier_id=supplier_id
        ).values_list(
            'product__category', flat=True
        ).distinct()
        
        result = {}
        for category in categories:
            # Get products in this category
            product_ids = SupplierProduct.objects.filter(
                supplier_id=supplier_id,
                product__category=category
            ).values_list('product_id', flat=True)
            
            # Get transactions for these products
            transactions = Transaction.objects.filter(
                supplier_id=supplier_id,
                product_id__in=product_ids
            )
            
            # Calculate metrics
            metrics = {
                'total_orders': transactions.count(),
                'on_time_delivery_rate': transactions.filter(
                    actual_delivery_date__lte=F('expected_delivery_date')
                ).count() / max(transactions.count(), 1) * 100,
                'average_delay': transactions.filter(
                    actual_delivery_date__gt=F('expected_delivery_date')
                ).aggregate(
                    avg_delay=Avg(F('actual_delivery_date') - F('expected_delivery_date'))
                )['avg_delay'] or 0,
                'defect_rate': transactions.aggregate(
                    defect_sum=Sum('defect_count'),
                    qty_sum=Sum('quantity')
                )
            }
            
            if metrics['defect_rate']['qty_sum']:
                metrics['defect_rate'] = (
                    metrics['defect_rate']['defect_sum'] / metrics['defect_rate']['qty_sum'] * 100
                )
            else:
                metrics['defect_rate'] = 0
                
            result[category] = metrics
            
        return result
    
    @staticmethod
    def update_supplier_preferences(supplier_id, preferences_data):
        """
        Updates preference flags for a supplier's products
        """
        for product_id, is_preferred in preferences_data.items():
            try:
                supplier_product = SupplierProduct.objects.get(
                    supplier_id=supplier_id,
                    product_id=product_id
                )
                supplier_product.is_preferred = is_preferred
                supplier_product.save()
            except SupplierProduct.DoesNotExist:
                pass
                
        return True