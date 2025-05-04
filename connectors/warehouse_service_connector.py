"""
Connector for the Warehouse Service that handles product data.
"""

import requests
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

class WarehouseServiceConnector:
    """Connector to fetch product data from the Warehouse Service"""
    
    def __init__(self):
        """Initialize connector with base URL from settings"""
        self.base_url = settings.WAREHOUSE_SERVICE_URL
        
    def get_supplier_products(self, supplier_id):
        """
        Get products for a supplier
        
        Args:
            supplier_id: ID of the supplier
            
        Returns:
            list: List of product dictionaries
        """
        # Mock implementation for testing
        products = []
        
        # Sample data for supplier 1
        if supplier_id == 1:
            products = [
                {
                    "id": 101,
                    "name": "Product A",
                    "supplier_id": 1,
                    "lead_time_days": 5,
                    "stock_level": 250
                },
                {
                    "id": 102,
                    "name": "Product B",
                    "supplier_id": 1,
                    "lead_time_days": 7,
                    "stock_level": 150
                }
            ]
        
        # Sample data for supplier 2
        elif supplier_id == 2:
            products = [
                {
                    "id": 103,
                    "name": "Product C",
                    "supplier_id": 2,
                    "lead_time_days": 3,
                    "stock_level": 300
                },
                {
                    "id": 101,
                    "name": "Product A",
                    "supplier_id": 2,
                    "lead_time_days": 4,
                    "stock_level": 200
                }
            ]
        
        # Sample data for supplier 3
        elif supplier_id == 3:
            products = [
                {
                    "id": 102,
                    "name": "Product B",
                    "supplier_id": 3,
                    "lead_time_days": 2,
                    "stock_level": 400
                },
                {
                    "id": 103,
                    "name": "Product C",
                    "supplier_id": 3,
                    "lead_time_days": 3,
                    "stock_level": 350
                }
            ]
            
        return products
    
    def get_suppliers_by_category(self, category):
        """Fetch supplier IDs that offer products in a specific category"""
        # try:
        #     response = requests.get(f"{self.base_url}/api/suppliers-by-category?category={category}")
        #     response.raise_for_status()
        #     return response.json().get('supplier_ids', [])
        # except requests.exceptions.RequestException as e:
        #     logger.error(f"Error fetching suppliers for category {category}: {str(e)}")
        #     return []
        
        # Simulated response
        category_supplier_map = {
            "Furniture": [1, 2, 3],
            "Office Supplies": [1, 3],
            "Electronics": [2, 3],
            "Stationery": [1, 2],
            "Kitchen Supplies": [3]
        }
        
        return category_supplier_map.get(category, [])
    
    def update_supplier_preferences(self, supplier_id, preferences_data):
        """Update preference flags for supplier products"""
        # try:
        #     response = requests.post(
        #         f"{self.base_url}/api/supplier-products/preferences",
        #         json={
        #             'supplier_id': supplier_id,
        #             'preferences': preferences_data
        #         }
        #     )
        #     response.raise_for_status()
        #     return True
        # except requests.exceptions.RequestException as e:
        #     logger.error(f"Error updating preferences for supplier {supplier_id}: {str(e)}")
        #     return False
        
        # Simulated response - always return success for test data
        logger.info(f"Simulated update of preferences for supplier {supplier_id}: {preferences_data}")
        return True
        
    def get_product_suppliers(self, product_id):
        """
        Get all suppliers offering a specific product
        
        Args:
            product_id (int): ID of the product
            
        Returns:
            list: List of supplier product dictionaries
        """
        # In a real implementation, this would make an API call to Warehouse Service
        # Example:
        # response = requests.get(f"{self.base_url}/supplier-products/?product_id={product_id}")
        # return response.json()
        
        # Simulated response
        products = {
            101: [
                {"supplier_id": 1, "unit_price": 10.50, "lead_time_days": 3},
                {"supplier_id": 2, "unit_price": 11.00, "lead_time_days": 2}
            ],
            102: [
                {"supplier_id": 1, "unit_price": 25.75, "lead_time_days": 5},
                {"supplier_id": 3, "unit_price": 24.50, "lead_time_days": 6}
            ],
            103: [
                {"supplier_id": 2, "unit_price": 30.25, "lead_time_days": 4},
                {"supplier_id": 3, "unit_price": 29.75, "lead_time_days": 3}
            ]
        }
        return products.get(product_id, [])