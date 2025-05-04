"""
Connector for the Order Service that handles transaction data.
"""

import requests
import logging
from django.conf import settings
from datetime import datetime, date, timedelta

logger = logging.getLogger(__name__)

class OrderServiceConnector:
    """Connector to fetch transaction data from the Order Service"""
    
    def __init__(self):
        """Initialize connector with base URL from settings"""
        self.base_url = settings.ORDER_SERVICE_URL
        
    def get_supplier_transactions(self, supplier_id, start_date, status=None, has_delivery_date=None):
        """
        Fetch supplier transactions from the order service
        
        Args:
            supplier_id: ID of the supplier
            start_date: Earliest date to include transactions from
            status (list, optional): Filter by transaction status
            has_delivery_date (bool, optional): Filter transactions that have delivery dates
            
        Returns:
            list: List of transaction dictionaries
        """
        # This is a mock implementation that would be replaced
        # with actual API calls in production
        
        # For testing purposes, generate some sample transactions
        transactions = []
        
        # Sample data for supplier 1
        if supplier_id == 1:
            transactions = [
                {
                    "id": 101,
                    "supplier_id": 1,
                    "date": datetime(2025, 5, 1),
                    "product_id": 101,
                    "quantity": 100,
                    "unit_price": 10.50,
                    "on_time": True,
                    "quality_issues": 5,
                    "delivery_days": 3,
                    "status": "DELIVERED",
                    "expected_delivery_date": datetime(2025, 5, 3),
                    "actual_delivery_date": datetime(2025, 5, 2)
                },
                {
                    "id": 102,
                    "supplier_id": 1,
                    "date": datetime(2025, 4, 15),
                    "product_id": 102,
                    "quantity": 200,
                    "unit_price": 5.25,
                    "on_time": False,
                    "quality_issues": 10,
                    "delivery_days": 5,
                    "status": "DELIVERED",
                    "expected_delivery_date": datetime(2025, 4, 20),
                    "actual_delivery_date": datetime(2025, 4, 22)
                }
            ]
        
        # Sample data for supplier 2
        elif supplier_id == 2:
            transactions = [
                {
                    "id": 201,
                    "supplier_id": 2,
                    "date": datetime(2025, 5, 2),
                    "product_id": 101,
                    "quantity": 150,
                    "unit_price": 10.75,
                    "on_time": True,
                    "quality_issues": 2,
                    "delivery_days": 2,
                    "status": "DELIVERED",
                    "expected_delivery_date": datetime(2025, 5, 5),
                    "actual_delivery_date": datetime(2025, 5, 4)
                },
                {
                    "id": 202,
                    "supplier_id": 2, 
                    "date": datetime(2025, 4, 20),
                    "product_id": 103,
                    "quantity": 300,
                    "unit_price": 7.50,
                    "on_time": True, 
                    "quality_issues": 3,
                    "delivery_days": 3,
                    "status": "COMPLETED",
                    "expected_delivery_date": datetime(2025, 4, 23),
                    "actual_delivery_date": datetime(2025, 4, 23)
                }
            ]
        
        # Sample data for supplier 3
        elif supplier_id == 3:
            transactions = [
                {
                    "id": 301,
                    "supplier_id": 3,
                    "date": datetime(2025, 5, 3),
                    "product_id": 102,
                    "quantity": 120,
                    "unit_price": 5.00,
                    "on_time": True,
                    "quality_issues": 1,
                    "delivery_days": 2,
                    "status": "DELIVERED",
                    "expected_delivery_date": datetime(2025, 5, 6),
                    "actual_delivery_date": datetime(2025, 5, 5)
                },
                {
                    "id": 302,
                    "supplier_id": 3,
                    "date": datetime(2025, 4, 25),
                    "product_id": 103,
                    "quantity": 250,
                    "unit_price": 7.25,
                    "on_time": False,
                    "quality_issues": 8,
                    "delivery_days": 6,
                    "status": "DELIVERED",
                    "expected_delivery_date": datetime(2025, 4, 29),
                    "actual_delivery_date": datetime(2025, 5, 2)
                }
            ]
            
        # Convert start_date to datetime for comparison if it's a date object
        if isinstance(start_date, date) and not isinstance(start_date, datetime):
            start_date = datetime.combine(start_date, datetime.min.time())
        
        # FIX: Ensure we're comparing naive datetimes consistently
        # If start_date has tzinfo but transaction dates don't, make start_date naive too
        if hasattr(start_date, 'tzinfo') and start_date.tzinfo is not None:
            start_date = start_date.replace(tzinfo=None)
            
        # Apply filters
        filtered_transactions = transactions
        
        # Filter by date
        filtered_transactions = [t for t in filtered_transactions if t["date"] >= start_date]
        
        # Filter by status if specified
        if status:
            filtered_transactions = [t for t in filtered_transactions if t.get("status") in status]
            
        # Filter by delivery_date if specified
        if has_delivery_date:
            filtered_transactions = [t for t in filtered_transactions if t.get("expected_delivery_date") and t.get("actual_delivery_date")]
        
        transactions = filtered_transactions
        
        return transactions
    
    def get_supplier_performance(self, supplier_id, start_date=None):
        """Fetch performance metrics for a specific supplier"""
        # Simulated response
        performance_data = {
            "supplier_id": supplier_id,
            "overall_score": 8.5,
            "metrics": {
                "quality_score": 8.2,
                "delivery_score": 9.0,
                "price_score": 7.8,
                "communication_score": 8.7
            },
            "trends": {
                "last_30_days": "+0.3",
                "last_90_days": "+0.5",
                "last_year": "+1.2"
            },
            "total_orders": 145,
            "total_value": 587650.25,
            "average_order_value": 4052.76
        }
        
        return performance_data
    
    def get_supplier_category_performance(self, supplier_id):
        """Fetch performance metrics grouped by product category"""
        # Simulated response
        category_performance = {
            "Electronics": {
                "order_count": 42,
                "total_value": 185300.50,
                "defect_rate": 1.8,
                "on_time_delivery": 96.5,
                "score": 8.7
            },
            "Furniture": {
                "order_count": 28,
                "total_value": 120750.25,
                "defect_rate": 2.3,
                "on_time_delivery": 94.2,
                "score": 8.1
            },
            "Office Supplies": {
                "order_count": 75,
                "total_value": 281600.00,
                "defect_rate": 1.5,
                "on_time_delivery": 97.8,
                "score": 9.0
            }
        }
        
        return category_performance
        
    def get_supplier_performance_records(self, supplier_id, start_date=None):
        """
        Get performance records for a supplier
        
        Args:
            supplier_id (int): ID of the supplier
            start_date (datetime, optional): Filter records after this date
            
        Returns:
            list: List of performance record dictionaries
        """
        # Simulated response
        records = [
            {
                "id": 501,
                "supplier_id": supplier_id,
                # Using datetime instead of date to ensure type consistency
                "date": datetime.combine(date.today() - timedelta(days=30), datetime.min.time()),
                "quality_score": 8.2,
                "defect_rate": 2.5,
                "return_rate": 3.0,
                "on_time_delivery_rate": 95.0,
                "average_delay_days": 0.5,
                "price_competitiveness": 7.5,
                "responsiveness": 8.0,
                "issue_resolution_time": 24.0,
                "fill_rate": 98.0,
                "order_accuracy": 99.0
            },
            {
                "id": 502,
                "supplier_id": supplier_id,
                # Using datetime instead of date to ensure type consistency
                "date": datetime.combine(date.today() - timedelta(days=60), datetime.min.time()),
                "quality_score": 7.8,
                "defect_rate": 3.0,
                "return_rate": 4.5,
                "on_time_delivery_rate": 92.0,
                "average_delay_days": 0.8,
                "price_competitiveness": 8.0,
                "responsiveness": 7.5,
                "issue_resolution_time": 36.0,
                "fill_rate": 95.0,
                "order_accuracy": 97.0
            }
        ]
        
        if start_date:
            # FIX: Ensure start_date is datetime for consistent comparison
            if isinstance(start_date, date) and not isinstance(start_date, datetime):
                start_date = datetime.combine(start_date, datetime.min.time())
                
            # Handle timezone-aware datetime comparison
            if hasattr(start_date, 'tzinfo') and start_date.tzinfo is not None:
                # Make start_date naive for consistent comparison
                start_date = start_date.replace(tzinfo=None)
                
            records = [r for r in records if r["date"] >= start_date]
            
        return records