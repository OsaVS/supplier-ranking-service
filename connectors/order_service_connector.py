"""
Connector for the Order Service that handles transaction data.
"""

import requests
import logging
import os
from django.conf import settings
from datetime import datetime, date, timedelta
from django.utils import timezone
import json

logger = logging.getLogger(__name__)

class OrderServiceConnector:
    """Connector to fetch order and transaction data from the Order Service"""
    
    def __init__(self, use_dummy_data=False):
        """Initialize connector with base URL and auth credentials from settings"""
        # Use environment variable first, then settings
        self.base_url = os.environ.get('ORDER_SERVICE_URL', 'http://127.0.0.1:8003/')
        
        # Fix URL if running in Docker but using localhost
        if 'localhost' in self.base_url and os.environ.get('DOCKER_ENV', 'False') == 'True':
            self.base_url = os.environ.get('ORDER_SERVICE_URL', 'http://127.0.0.1:8003/')
            
        # Get authentication credentials from settings or environment
        self.auth_token = ''
        
        # Headers for API requests
        self.headers = {
            "Authorization": f"Bearer {self.auth_token}",
            "Content-Type": "application/json"
        }
        
        # Connection timeout settings
        self.timeout = 10  # seconds
        
        # Flag to use dummy data for testing
        self.use_dummy_data = use_dummy_data
        
        # Create dummy data for testing
        if self.use_dummy_data:
            self._create_dummy_data()
        
        logger.info(f"Initialized OrderServiceConnector with base URL: {self.base_url}")
    
    def _create_dummy_data(self):
        """Create dummy data for testing"""
        today = date.today()
        
        # Generate transaction history for suppliers
        self.dummy_transactions = {
            3: [  # Supplier A transactions
                {
                    "id": 101,
                    "supplier_id": 3,
                    "product_id": 1,
                    "order_id": "ORD-1001",
                    "quantity": 100,
                    "unit_price": 9.50,
                    "total_price": 950.00,
                    "status": "DELIVERED",
                    "expected_delivery_date": (today - timedelta(days=30)).isoformat(),
                    "actual_delivery_date": (today - timedelta(days=29)).isoformat(),
                    "defect_count": 3,
                    "created_at": (today - timedelta(days=45)).isoformat()
                },
                {
                    "id": 102,
                    "supplier_id": 3,
                    "product_id": 2,
                    "order_id": "ORD-1002",
                    "quantity": 50,
                    "unit_price": 14.75,
                    "total_price": 737.50,
                    "status": "DELIVERED",
                    "expected_delivery_date": (today - timedelta(days=20)).isoformat(),
                    "actual_delivery_date": (today - timedelta(days=21)).isoformat(),
                    "defect_count": 0,
                    "created_at": (today - timedelta(days=30)).isoformat()
                },
                {
                    "id": 103,
                    "supplier_id": 3,
                    "product_id": 1,
                    "order_id": "ORD-1003",
                    "quantity": 75,
                    "unit_price": 9.50,
                    "total_price": 712.50,
                    "status": "RETURNED",
                    "expected_delivery_date": (today - timedelta(days=15)).isoformat(),
                    "actual_delivery_date": (today - timedelta(days=16)).isoformat(),
                    "defect_count": 20,
                    "created_at": (today - timedelta(days=25)).isoformat()
                }
            ],
            4: [  # Supplier B transactions
                {
                    "id": 201,
                    "supplier_id": 4,
                    "product_id": 1,
                    "order_id": "ORD-2001",
                    "quantity": 80,
                    "unit_price": 9.80,
                    "total_price": 784.00,
                    "status": "DELIVERED",
                    "expected_delivery_date": (today - timedelta(days=25)).isoformat(),
                    "actual_delivery_date": (today - timedelta(days=22)).isoformat(),
                    "defect_count": 1,
                    "created_at": (today - timedelta(days=35)).isoformat()
                },
                {
                    "id": 202,
                    "supplier_id": 4,
                    "product_id": 1,
                    "order_id": "ORD-2002",
                    "quantity": 60,
                    "unit_price": 9.80,
                    "total_price": 588.00,
                    "status": "DELIVERED",
                    "expected_delivery_date": (today - timedelta(days=10)).isoformat(),
                    "actual_delivery_date": (today - timedelta(days=10)).isoformat(),
                    "defect_count": 0,
                    "created_at": (today - timedelta(days=20)).isoformat()
                }
            ],
            5: [  # Supplier C transactions
                {
                    "id": 301,
                    "supplier_id": 5,
                    "product_id": 2,
                    "order_id": "ORD-3001",
                    "quantity": 40,
                    "unit_price": 14.50,
                    "total_price": 580.00,
                    "status": "DELIVERED",
                    "expected_delivery_date": (today - timedelta(days=15)).isoformat(),
                    "actual_delivery_date": (today - timedelta(days=16)).isoformat(),
                    "defect_count": 2,
                    "created_at": (today - timedelta(days=25)).isoformat()
                },
                {
                    "id": 302,
                    "supplier_id": 5,
                    "product_id": 3,
                    "order_id": "ORD-3002",
                    "quantity": 200,
                    "unit_price": 4.90,
                    "total_price": 980.00,
                    "status": "DELIVERED",
                    "expected_delivery_date": (today - timedelta(days=7)).isoformat(),
                    "actual_delivery_date": (today - timedelta(days=5)).isoformat(),
                    "defect_count": 0,
                    "created_at": (today - timedelta(days=15)).isoformat()
                }
            ]
        }
        
        # Generate performance records
        self.dummy_performance_records = {
            3: [  # Supplier A performance
                {
                    "supplier_id": 3,
                    "date": (today - timedelta(days=30)).isoformat(),
                    "quality_score": 8.5,
                    "defect_rate": 3.0,
                    "return_rate": 1.0,
                    "on_time_delivery_rate": 95.0,
                    "price_competitiveness": 8.0,
                    "responsiveness": 9.0,
                    "fill_rate": 98.0,
                    "order_accuracy": 97.0
                },
                {
                    "supplier_id": 3,
                    "date": (today - timedelta(days=15)).isoformat(),
                    "quality_score": 7.8,
                    "defect_rate": 5.0,
                    "return_rate": 5.0,
                    "on_time_delivery_rate": 90.0,
                    "price_competitiveness": 8.0,
                    "responsiveness": 8.5,
                    "fill_rate": 96.0,
                    "order_accuracy": 95.0
                }
            ],
            4: [  # Supplier B performance
                {
                    "supplier_id": 4,
                    "date": (today - timedelta(days=30)).isoformat(),
                    "quality_score": 9.0,
                    "defect_rate": 1.5,
                    "return_rate": 0.5,
                    "on_time_delivery_rate": 97.0,
                    "price_competitiveness": 7.5,
                    "responsiveness": 8.0,
                    "fill_rate": 99.0,
                    "order_accuracy": 98.0
                },
                {
                    "supplier_id": 4,
                    "date": (today - timedelta(days=15)).isoformat(),
                    "quality_score": 9.2,
                    "defect_rate": 1.0,
                    "return_rate": 0.0,
                    "on_time_delivery_rate": 98.0,
                    "price_competitiveness": 7.5,
                    "responsiveness": 8.0,
                    "fill_rate": 99.0,
                    "order_accuracy": 99.0
                }
            ],
            5: [  # Supplier C performance
                {
                    "supplier_id": 5,
                    "date": (today - timedelta(days=30)).isoformat(),
                    "quality_score": 9.5,
                    "defect_rate": 1.0,
                    "return_rate": 0.0,
                    "on_time_delivery_rate": 98.0,
                    "price_competitiveness": 8.5,
                    "responsiveness": 9.0,
                    "fill_rate": 99.5,
                    "order_accuracy": 99.0
                },
                {
                    "supplier_id": 5,
                    "date": (today - timedelta(days=15)).isoformat(),
                    "quality_score": 9.6,
                    "defect_rate": 0.5,
                    "return_rate": 0.0,
                    "on_time_delivery_rate": 99.0,
                    "price_competitiveness": 8.5,
                    "responsiveness": 9.0,
                    "fill_rate": 99.5,
                    "order_accuracy": 99.5
                }
            ]
        }
        
        # Generate category performance data
        self.dummy_category_performance = {
            3: {  # Supplier A
                "Widgets": {
                    "quality_score": 8.2,
                    "on_time_delivery_rate": 92.5,
                    "price_competitiveness": 8.0
                },
                "Components": {
                    "quality_score": 8.5,
                    "on_time_delivery_rate": 95.0,
                    "price_competitiveness": 7.8
                }
            },
            4: {  # Supplier B
                "Widgets": {
                    "quality_score": 9.1,
                    "on_time_delivery_rate": 97.5,
                    "price_competitiveness": 7.5
                }
            },
            5: {  # Supplier C
                "Components": {
                    "quality_score": 9.6,
                    "on_time_delivery_rate": 98.5,
                    "price_competitiveness": 8.5
                },
                "Raw Materials": {
                    "quality_score": 9.4,
                    "on_time_delivery_rate": 97.0,
                    "price_competitiveness": 8.6
                }
            }
        }
    
    def _fetch_supplier_metrics(self, supplier_id, start_date=None):
        """
        Fetch metrics data from the API for a specific supplier
        
        Args:
            supplier_id (int): ID of the supplier
            start_date (date or datetime, optional): Start date for filtering data
            
        Returns:
            list: Raw metrics data from the API
        """
        try:
            url = f"{self.base_url}/api/v0/supplier-request/metrics/{supplier_id}/"
            params = {}
            
            if start_date:
                if isinstance(start_date, datetime):
                    start_date = start_date.date()
                params['start_date'] = start_date.isoformat()
            
            response = requests.get(
                url,
                params=params,
                headers=self.headers,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Error fetching supplier metrics - Status {response.status_code}: {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching supplier metrics for supplier {supplier_id}: {str(e)}")
            return None
    
    def _convert_api_data_to_transactions(self, metrics_data, supplier_id):
        """
        Convert API metrics data to transaction format matching dummy data structure
        
        Args:
            metrics_data (list): Raw metrics data from the API
            supplier_id (int): ID of the supplier
            
        Returns:
            list: List of transaction dictionaries
        """
        transactions = []
        transaction_id = 1000  # Starting ID for generated transactions
        
        if not metrics_data:
            return []
        
        for product_metrics in metrics_data:
            product_id = product_metrics.get('product_id')
            
            # Process each transaction in the data array
            for item in product_metrics.get('data', []):
                # Map status values from API to expected format
                status_mapping = {
                    'pending': 'PENDING',
                    'accepted': 'ACCEPTED',
                    'received': 'DELIVERED',
                    'returned': 'RETURNED'
                }
                
                status = status_mapping.get(item.get('status', '').lower(), 'UNKNOWN')
                
                # Calculate total price if both unit price and count are available
                unit_price = item.get('unit_price')
                quantity = item.get('count')
                total_price = None
                if unit_price is not None and quantity is not None:
                    # Make sure unit_price and quantity are numeric before multiplication
                    try:
                        unit_price = float(unit_price)
                        quantity = float(quantity)
                        total_price = unit_price * quantity
                    except (ValueError, TypeError):
                        # Log the error and continue with None value
                        logger.warning(f"Could not calculate total_price for item: {item}")
                        unit_price = 0.0 if unit_price is None else float(unit_price)
                        quantity = 0 if quantity is None else int(quantity)
                        total_price = 0.0
                
                # Determine defect count based on is_defective flag
                defect_count = 0
                if item.get('is_defective') is True:
                    # If marked defective but no specific count, assume all are defective
                    defect_count = quantity if quantity else 0
                
                # Generate order_id based on transaction_id
                order_id = f"ORD-{transaction_id}"
                
                # Convert string dates to ISO format if not already
                expected_delivery_date = item.get('expected_delivery_date')
                actual_delivery_date = item.get('received_at')
                created_at = item.get('created_at')
                
                transaction = {
                    "id": transaction_id,
                    "supplier_id": supplier_id,
                    "product_id": product_id,
                    "order_id": order_id,
                    "quantity": quantity,
                    "unit_price": unit_price,
                    "total_price": total_price,
                    "status": status,
                    "expected_delivery_date": expected_delivery_date,
                    "actual_delivery_date": actual_delivery_date,
                    "defect_count": defect_count,
                    "created_at": created_at
                }
                
                transactions.append(transaction)
                transaction_id += 1
        
        return transactions
    
    def _create_performance_record_from_metrics(self, metrics_data, supplier_id):
        """
        Create performance records from metrics data
        
        Args:
            metrics_data (list): Raw metrics data from the API
            supplier_id (int): ID of the supplier
            
        Returns:
            list: List of performance record dictionaries
        """
        if not metrics_data:
            return []
        
        # Initialize overall metrics
        total_requests = 0
        total_defective = 0
        total_returned = 0
        quality_score_sum = 0
        quality_score_count = 0
        on_time_delivery_count = 0
        fill_rate_count = 0
        responsiveness_sum = 0
        responsiveness_count = 0
        order_accuracy_count = 0
        
        # Collect all dates to create one record per date
        date_transactions = {}
        
        # Process each product's metrics
        for product_metrics in metrics_data:
            # Safely get values with default of 0 if None
            total_requests += product_metrics.get('total_requests', 0) or 0
            total_defective += product_metrics.get('defective_count', 0) or 0
            total_returned += product_metrics.get('return_count', 0) or 0
            
            # Add quality score if available
            if product_metrics.get('quality_score') is not None:
                try:
                    quality_score = float(product_metrics.get('quality_score', 0))
                    quality_score_sum += quality_score
                    quality_score_count += 1
                except (ValueError, TypeError):
                    logger.warning(f"Invalid quality_score value: {product_metrics.get('quality_score')}")
            
            # Safely process other metrics
            if product_metrics.get('on_time_delivery_rate') is not None:
                on_time_delivery_count += 1
            
            if product_metrics.get('fill_rate') is not None:
                fill_rate_count += 1
            
            if product_metrics.get('avg_responsiveness') is not None:
                try:
                    responsiveness = float(product_metrics.get('avg_responsiveness', 0))
                    responsiveness_sum += responsiveness
                    responsiveness_count += 1
                except (ValueError, TypeError):
                    logger.warning(f"Invalid avg_responsiveness value: {product_metrics.get('avg_responsiveness')}")
            
            if product_metrics.get('order_accuracy_rate') is not None:
                order_accuracy_count += 1
                
            # Process each transaction date
            for item in product_metrics.get('data', []):
                created_date = item.get('created_at')
                if created_date:
                    try:
                        # Extract just the date part
                        date_obj = datetime.fromisoformat(created_date.replace('Z', '+00:00'))
                        date_str = date_obj.date().isoformat()
                        
                        if date_str not in date_transactions:
                            date_transactions[date_str] = {
                                'supplier_id': supplier_id,
                                'date': date_str,
                                'items': []
                            }
                        
                        date_transactions[date_str]['items'].append(item)
                    except (ValueError, TypeError):
                        logger.warning(f"Invalid date format: {created_date}")
        
        # Create performance records for each date
        performance_records = []
        
        for date_str, date_data in date_transactions.items():
            items = date_data['items']
            
            # Safely handle possible None values in quality scores
            date_quality_scores = []
            for item in items:
                quality = item.get('quality')
                if quality is not None:
                    try:
                        quality = float(quality)
                        date_quality_scores.append(quality)
                    except (ValueError, TypeError):
                        logger.warning(f"Invalid quality value: {quality}")
            
            # Calculate metrics for this date with safe default values
            quality_score = 0.0
            if date_quality_scores:
                quality_score = sum(date_quality_scores) / len(date_quality_scores)
            
            # Count defective and returned items for this date
            defective_count = sum(1 for item in items if item.get('is_defective') is True)
            returned_count = sum(1 for item in items if item.get('status', '').lower() == 'returned')
            
            # Calculate rates with safe division
            defect_rate = (defective_count / len(items)) * 100 if items else 0
            return_rate = (returned_count / len(items)) * 100 if items else 0
            
            # Count on-time deliveries with safe date parsing
            on_time_deliveries = 0
            for item in items:
                expected = item.get('expected_delivery_date')
                actual = item.get('received_at')
                if expected and actual:
                    try:
                        expected_dt = datetime.fromisoformat(expected.replace('Z', '+00:00'))
                        actual_dt = datetime.fromisoformat(actual.replace('Z', '+00:00'))
                        if actual_dt <= expected_dt:
                            on_time_deliveries += 1
                    except (ValueError, TypeError):
                        logger.warning(f"Invalid date format - expected: {expected}, actual: {actual}")
            
            on_time_delivery_rate = (on_time_deliveries / len(items)) * 100 if items else 0
            
            # Safely handle price competitiveness
            price_comp_values = []
            for item in items:
                price_comp = item.get('price_competitiveness')
                if price_comp is not None:
                    try:
                        price_comp = float(price_comp)
                        price_comp_values.append(price_comp)
                    except (ValueError, TypeError):
                        logger.warning(f"Invalid price_competitiveness value: {price_comp}")
            
            price_competitiveness = 0.0
            if price_comp_values:
                price_competitiveness = sum(price_comp_values) / len(price_comp_values)
            
            # Use global averages for other metrics with safe defaults
            fill_rate = 0.0
            order_accuracy = 0.0
            responsiveness = 0.0
            
            if metrics_data:
                # Safely process fill_rate
                fill_rates = [product.get('fill_rate', 0) for product in metrics_data]
                fill_rates = [float(rate) * 100 if rate is not None else 0.0 for rate in fill_rates]
                fill_rate = sum(fill_rates) / len(fill_rates) if fill_rates else 0.0
                
                # Safely process order_accuracy_rate
                accuracy_rates = [product.get('order_accuracy_rate', 0) for product in metrics_data]
                accuracy_rates = [float(rate) * 100 if rate is not None else 0.0 for rate in accuracy_rates]
                order_accuracy = sum(accuracy_rates) / len(accuracy_rates) if accuracy_rates else 0.0
                
                # Safely process avg_responsiveness
                responsiveness_values = [product.get('avg_responsiveness', 0) for product in metrics_data]
                responsiveness_values = [float(val) if val is not None else 0.0 for val in responsiveness_values]
                responsiveness = sum(responsiveness_values) / len(responsiveness_values) if responsiveness_values else 0.0
            
            # Create performance record
            record = {
                "supplier_id": supplier_id,
                "date": date_str,
                "quality_score": quality_score,
                "defect_rate": defect_rate,
                "return_rate": return_rate,
                "on_time_delivery_rate": on_time_delivery_rate,
                "price_competitiveness": price_competitiveness,
                "responsiveness": responsiveness,
                "fill_rate": fill_rate,
                "order_accuracy": order_accuracy
            }
            
            performance_records.append(record)
        
        return performance_records
    
    def _create_category_performance_from_metrics(self, metrics_data, supplier_id):
        """
        Create category performance data from metrics data
        
        Args:
            metrics_data (list): Raw metrics data from the API
            supplier_id (int): ID of the supplier
            
        Returns:
            dict: Dictionary containing performance metrics by category
        """
        # Since the API doesn't provide category information directly,
        # we'll create a simple mapping based on product IDs
        # In a real implementation, you might want to fetch this from a product catalog service
        product_category_mapping = {
            1: "Widgets",
            2: "Components",
            3: "Raw Materials"
        }
        
        category_performance = {}
        
        for product_metrics in metrics_data:
            product_id = product_metrics.get('product_id')
            category = product_category_mapping.get(product_id, f"Category-{product_id}")
            
            # Safely get metrics with defaults if None
            quality_score = 0.0
            if product_metrics.get('quality_score') is not None:
                try:
                    quality_score = float(product_metrics.get('quality_score', 0))
                except (ValueError, TypeError):
                    logger.warning(f"Invalid quality_score: {product_metrics.get('quality_score')}")
            
            on_time_delivery_rate = 0.0
            if product_metrics.get('on_time_delivery_rate') is not None:
                try:
                    on_time_delivery_rate = float(product_metrics.get('on_time_delivery_rate', 0)) * 100
                except (ValueError, TypeError):
                    logger.warning(f"Invalid on_time_delivery_rate: {product_metrics.get('on_time_delivery_rate')}")
            
            # Calculate average price competitiveness safely
            price_comp_values = []
            for item in product_metrics.get('data', []):
                price_comp = item.get('price_competitiveness')
                if price_comp is not None:
                    try:
                        price_comp = float(price_comp)
                        price_comp_values.append(price_comp)
                    except (ValueError, TypeError):
                        logger.warning(f"Invalid price_competitiveness: {price_comp}")
            
            price_competitiveness = 0.0
            if price_comp_values:
                price_competitiveness = sum(price_comp_values) / len(price_comp_values)
            
            # Add to category performance
            if category not in category_performance:
                category_performance[category] = {
                    "quality_score": quality_score,
                    "on_time_delivery_rate": on_time_delivery_rate,
                    "price_competitiveness": price_competitiveness
                }
        
        return category_performance
            
    def get_supplier_transactions(self, supplier_id, start_date=None, status=None, has_delivery_date=False):
        """
        Get transactions for a specific supplier
        
        Args:
            supplier_id (int): ID of the supplier
            start_date (date or datetime, optional): Start date for filtering transactions
            status (list, optional): List of status values to filter by
            has_delivery_date (bool, optional): If True, only return transactions with delivery dates
            
        Returns:
            list: List of transaction dictionaries
        """
        if self.use_dummy_data:
            # Get transactions for this supplier from dummy data
            supplier_transactions = self.dummy_transactions.get(supplier_id, [])
            
            # Apply filters
            filtered_transactions = []
            for tx in supplier_transactions:
                # Filter by start date
                if start_date:
                    # Make sure we convert to a datetime for comparison
                    tx_date = datetime.fromisoformat(tx['created_at'].replace('Z', '+00:00'))
                    
                    # Convert start_date to datetime if it's a date object
                    if isinstance(start_date, date) and not isinstance(start_date, datetime):
                        start_date_dt = datetime.combine(start_date, datetime.min.time())
                    else:
                        start_date_dt = start_date
                    
                    # Now handle timezone awareness
                    if hasattr(start_date_dt, 'tzinfo') and start_date_dt.tzinfo is not None and tx_date.tzinfo is None:
                        # Make tx_date timezone-aware if it isn't already
                        tx_date = timezone.make_aware(tx_date)
                    elif hasattr(start_date_dt, 'tzinfo') and start_date_dt.tzinfo is None and tx_date.tzinfo is not None:
                        # Make start_date timezone-aware if it isn't already
                        start_date_dt = timezone.make_aware(start_date_dt)
                    
                    if tx_date < start_date_dt:
                        continue
                
                # Filter by status
                if status and tx['status'] not in status:
                    continue
                
                # Filter by has_delivery_date
                if has_delivery_date and (not tx.get('expected_delivery_date') or not tx.get('actual_delivery_date')):
                    continue
                
                filtered_transactions.append(tx)
            
            return filtered_transactions
        
        # Fetch metrics data from the API
        metrics_data = self._fetch_supplier_metrics(supplier_id, start_date)
        
        if metrics_data is None:
            logger.warning(f"Failed to fetch metrics data for supplier {supplier_id}, returning empty list")
            return []
        
        # Convert API data to transaction format
        transactions = self._convert_api_data_to_transactions(metrics_data, supplier_id)
        
        # Apply filters
        filtered_transactions = []
        for tx in transactions:
            # Filter by status
            if status and tx['status'] not in status:
                continue
            
            # Filter by has_delivery_date
            if has_delivery_date and (not tx.get('expected_delivery_date') or not tx.get('actual_delivery_date')):
                continue
            
            filtered_transactions.append(tx)
        
        return filtered_transactions
    
    def get_supplier_performance_records(self, supplier_id, start_date=None):
        """
        Get performance records for a specific supplier
        
        Args:
            supplier_id (int): ID of the supplier
            start_date (date or datetime, optional): Start date for filtering records
            
        Returns:
            list: List of performance record dictionaries
        """
        if self.use_dummy_data:
            # Get performance records for this supplier from dummy data
            supplier_records = self.dummy_performance_records.get(supplier_id, [])
            
            # Apply start_date filter if provided
            if start_date:
                filtered_records = []
                for record in supplier_records:
                    # Make sure we convert to a datetime for comparison
                    record_date = datetime.fromisoformat(record['date'].replace('Z', '+00:00'))
                    
                    # Convert start_date to datetime if it's a date object
                    if isinstance(start_date, date) and not isinstance(start_date, datetime):
                        start_date_dt = datetime.combine(start_date, datetime.min.time())
                    else:
                        start_date_dt = start_date
                    
                    # Handle timezone awareness for comparison
                    if hasattr(start_date_dt, 'tzinfo') and start_date_dt.tzinfo is not None and record_date.tzinfo is None:
                        # Make record_date timezone-aware
                        record_date = timezone.make_aware(record_date)
                    elif hasattr(start_date_dt, 'tzinfo') and start_date_dt.tzinfo is None and record_date.tzinfo is not None:
                        # Make start_date timezone-aware
                        start_date_dt = timezone.make_aware(start_date_dt)
                        
                    if record_date >= start_date_dt:
                        filtered_records.append(record)
                return filtered_records
            
            return supplier_records
        
        # Fetch metrics data from the API
        metrics_data = self._fetch_supplier_metrics(supplier_id, start_date)
        
        if metrics_data is None:
            logger.warning(f"Failed to fetch metrics data for supplier {supplier_id}, returning empty list")
            return []
        
        # Create performance records from metrics data
        performance_records = self._create_performance_record_from_metrics(metrics_data, supplier_id)
        
        return performance_records
    
    def get_supplier_performance(self, supplier_id, start_date=None):
        """
        Get aggregated performance data for a specific supplier
        
        Args:
            supplier_id (int): ID of the supplier
            start_date (datetime, optional): Start date for filtering data
            
        Returns:
            dict: Dictionary containing aggregated performance metrics
        """
        if self.use_dummy_data:
            records = self.get_supplier_performance_records(supplier_id, start_date)
            
            if not records:
                return {
                    'quality_score': 8.0,
                    'defect_rate': 2.0,
                    'return_rate': 1.0,
                    'on_time_delivery_rate': 95.0,
                    'price_competitiveness': 7.5,
                    'responsiveness': 8.0,
                    'fill_rate': 97.0,
                    'order_accuracy': 98.0
                }
            
            # Sort by date (most recent first) and return the first one
            sorted_records = sorted(records, key=lambda r: r['date'], reverse=True)
            return sorted_records[0]
        
        # Fetch metrics data from the API
        metrics_data = self._fetch_supplier_metrics(supplier_id, start_date)
        
        if metrics_data is None or len(metrics_data) == 0:
            logger.warning(f"Failed to fetch metrics data for supplier {supplier_id}, returning default values")
            return {
                'quality_score': 8.0,
                'defect_rate': 2.0,
                'return_rate': 1.0,
                'on_time_delivery_rate': 95.0,
                'price_competitiveness': 7.5,
                'responsiveness': 8.0,
                'fill_rate': 97.0,
                'order_accuracy': 98.0
            }
        
        # Calculate aggregated metrics from all product metrics
        total_quality_score = 0
        total_defect_rate = 0
        total_return_rate = 0
        total_on_time_delivery_rate = 0
        total_price_competitiveness = 0
        total_responsiveness = 0
        total_fill_rate = 0
        total_order_accuracy = 0
        count = len(metrics_data)
        
        for product_metrics in metrics_data:
            total_quality_score += product_metrics.get('quality_score', 0)
            total_defect_rate += product_metrics.get('defective_rate', 0) * 100  # Convert to percentage
            total_return_rate += product_metrics.get('returned_rate', 0) * 100  # Convert to percentage
            total_on_time_delivery_rate += product_metrics.get('on_time_delivery_rate', 0) * 100  # Convert to percentage
            total_fill_rate += product_metrics.get('fill_rate', 0) * 100  # Convert to percentage
            total_responsiveness += product_metrics.get('avg_responsiveness', 0)
            total_order_accuracy += product_metrics.get('order_accuracy_rate', 0) * 100  # Convert to percentage
            
            # Calculate price competitiveness (average from transactions data)
            price_comp_values = []
            for item in product_metrics.get('data', []):
                if item.get('price_competitiveness') is not None:
                    price_comp_values.append(item.get('price_competitiveness'))
            
            if price_comp_values:
                total_price_competitiveness += sum(price_comp_values) / len(price_comp_values)
        
        # Calculate averages
        avg_quality_score = total_quality_score / count if count > 0 else 0
        avg_defect_rate = total_defect_rate / count if count > 0 else 0
        avg_return_rate = total_return_rate / count if count > 0 else 0
        avg_on_time_delivery_rate = total_on_time_delivery_rate / count if count > 0 else 0
        avg_price_competitiveness = total_price_competitiveness / count if count > 0 else 0
        avg_responsiveness = total_responsiveness / count if count > 0 else 0
        avg_fill_rate = total_fill_rate / count if count > 0 else 0
        avg_order_accuracy = total_order_accuracy / count if count > 0 else 0
        
        return {
            'quality_score': avg_quality_score,
            'defect_rate': avg_defect_rate,
            'return_rate': avg_return_rate,
            'on_time_delivery_rate': avg_on_time_delivery_rate,
            'price_competitiveness': avg_price_competitiveness,
            'responsiveness': avg_responsiveness,
            'fill_rate': avg_fill_rate,
            'order_accuracy': avg_order_accuracy
        }