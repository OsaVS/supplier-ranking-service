"""
Connector for the User Service that handles supplier data.
"""

import requests
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

class UserServiceConnector:
    """Connector to fetch supplier data from the User Service"""
    
    def __init__(self):
        """Initialize connector with base URL from settings"""
        self.base_url = settings.USER_SERVICE_URL
        
    def get_active_suppliers(self):
        """Fetch all active suppliers from User Service"""
        # try:
        #     response = requests.get(f"{self.base_url}/api/suppliers?active=true")
        #     response.raise_for_status()
        #     return response.json()
        # except requests.exceptions.RequestException as e:
        #     logger.error(f"Error fetching active suppliers: {str(e)}")
        #     return []
        
        # Simulated response
        return [
            {"id": 1, "name": "Supplier A", "code": "SA001", "active": True},
            {"id": 2, "name": "Supplier B", "code": "SB002", "active": True},
            {"id": 3, "name": "Supplier C", "code": "SC003", "active": True},
            {"id": 5, "name": "Supplier E", "code": "SE005", "active": True}
        ]
    
    def get_active_supplier_count(self):
        """Get the count of active suppliers"""
        # try:
        #     response = requests.get(f"{self.base_url}/api/suppliers/count?active=true")
        #     response.raise_for_status()
        #     return response.json().get('count', 0)
        # except requests.exceptions.RequestException as e:
        #     logger.error(f"Error fetching supplier count: {str(e)}")
        #     return 0
        
        # Simulated response
        return 4  # Matching the number of suppliers in get_active_suppliers
            
    def get_supplier_by_id(self, supplier_id):
        """Fetch a specific supplier by ID"""
        # try:
        #     response = requests.get(f"{self.base_url}/api/suppliers/{supplier_id}")
        #     response.raise_for_status()
        #     return response.json()
        # except requests.exceptions.RequestException as e:
        #     logger.error(f"Error fetching supplier {supplier_id}: {str(e)}")
        #     return None
        
        try:
        # Simulated response
            suppliers = {
                1: {"id": 1, "name": "Supplier A", "code": "SA001", "active": True},
                2: {"id": 2, "name": "Supplier B", "code": "SB002", "active": True},
                3: {"id": 3, "name": "Supplier C", "code": "SC003", "active": True},
                4: {"id": 4, "name": "Supplier D", "code": "SD004", "active": False},
                5: {"id": 5, "name": "Supplier E", "code": "SE005", "active": True}
            }
            return suppliers.get(supplier_id)
        
        except:
            return None
        
    def get_supplier_info(self, supplier_id):
        """
        Get detailed information about a specific supplier
        
        Args:
            supplier_id (int): ID of the supplier
            
        Returns:
            dict: Supplier details including compliance score
        """
        # In a real implementation, this would make an API call to User Service
        # Example:
        # response = requests.get(f"{self.base_url}/suppliers/{supplier_id}/")
        # return response.json()
        
        try:
            # Simulated response
            suppliers = {
                1: {"id": 1, "name": "Supplier A", "code": "SA001", "compliance_score": 8.5},
                2: {"id": 2, "name": "Supplier B", "code": "SB002", "compliance_score": 7.2},
                3: {"id": 3, "name": "Supplier C", "code": "SC003", "compliance_score": 9.1}
            }

            return suppliers.get(supplier_id)

        except Exception:
            # Log the exception here if needed
            return None