"""
Connector for the User Service that handles supplier and user data.
"""

import requests
import logging
import os
import hashlib
import random
from django.conf import settings
from datetime import datetime, date, timedelta
from django.utils import timezone

logger = logging.getLogger(__name__)

class UserServiceConnector:
    """Connector to fetch user and supplier data from the User Service"""
    
    def __init__(self, use_dummy_data=True):
        """Initialize connector with base URL and auth credentials from settings"""
        # Use environment variable first, then settings
        self.base_url = os.environ.get('AUTH_SERVICE_URL', 'http://localhost:8000')
        
        # Get authentication credentials from settings or environment
        self.api_key = os.environ.get('AUTH_SERVICE_API_KEY', 'dev-api-key')
        
        # Headers for API requests
        self.headers = {
            "Authorization": f"ApiKey {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Connection timeout settings
        self.timeout = 10  # seconds
        
        # Flag to use dummy data for testing
        self.use_dummy_data = use_dummy_data
        
        # Create dummy supplier data
        self._create_dummy_suppliers()
        
        logger.info(f"Initialized UserServiceConnector with base URL: {self.base_url}")
    
    def _create_dummy_suppliers(self):
        """Create dummy supplier data for testing"""
        # List of supplier company names
        company_names = [
            "Alpha Supplies Ltd", "Beta Components Inc", "Gamma Electronics Co",
            "Delta Materials", "Epsilon Industrial", "Zeta Manufacturing",
            "Eta Distribution", "Theta Products", "Iota Technologies",
            "Kappa Systems", "Lambda Solutions", "Mu Logistics"
        ]
        
        cities = ["Colombo", "Galle", "Kandy", "Jaffna", "Negombo", "Batticaloa"]
        business_types = ["Manufacturing", "Distribution", "Retail", "Wholesale"]
        
        # Generate suppliers with IDs 1-12
        self.dummy_suppliers = {}
        for i in range(1, 13):
            # Use deterministic random based on supplier ID
            random.seed(i)
            
            # Create a random but consistent compliance score for this supplier
            compliance_score = round(5.0 + random.random() * 4.0, 1)
            
            self.dummy_suppliers[i] = {
                "user": {
                    "id": i,
                    "username": f"supplier{i}",
                    "email": f"supplier{i}@example.com",
                    "first_name": f"Supplier",
                    "last_name": f"{i}",
                    "is_active": True,
                    "city": random.choice(cities)
                },
                "company_name": company_names[i-1] if i <= len(company_names) else f"Supplier {i}",
                "code": f"SUP-{i*100 + random.randint(10, 99)}",
                "business_type": random.choice(business_types),
                "tax_id": f"TAX{i*1000 + random.randint(100, 999)}",
                "compliance_score": compliance_score,
                "active": True,
                "city": random.choice(cities),
                "created_at": (date.today() - timedelta(days=random.randint(30, 365))).isoformat(),
                "updated_at": (date.today() - timedelta(days=random.randint(1, 30))).isoformat()
            }
    
    def get_supplier(self, supplier_id):
        """
        Get a specific supplier by ID
        
        Args:
            supplier_id (int): ID of the supplier
            
        Returns:
            dict: Supplier information dictionary
        """
        if self.use_dummy_data:
            # Convert to int if it's a string
            if isinstance(supplier_id, str) and supplier_id.isdigit():
                supplier_id = int(supplier_id)
                
            return self.dummy_suppliers.get(supplier_id, None)
        
        try:
            response = requests.get(
                f"{self.base_url}/api/v1/suppliers/{supplier_id}/",
                headers=self.headers,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching supplier {supplier_id}: {str(e)}")
            return None
    
    def get_supplier_by_id(self, supplier_id):
        """Alias for get_supplier"""
        return self.get_supplier(supplier_id)
    
    def get_all_suppliers(self):
        """
        Get all suppliers
        
        Returns:
            list: List of supplier dictionaries
        """
        if self.use_dummy_data:
            return list(self.dummy_suppliers.values())
        
        try:
            response = requests.get(
                f"{self.base_url}/api/v1/suppliers/",
                headers=self.headers,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching all suppliers: {str(e)}")
            return []
    
    def get_active_suppliers(self):
        """
        Get all active suppliers
        
        Returns:
            list: List of active supplier dictionaries
        """
        if self.use_dummy_data:
            return [s for s in self.dummy_suppliers.values() if s.get('active', True)]
        
        try:
            response = requests.get(
                f"{self.base_url}/api/v1/suppliers/active/",
                headers=self.headers,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching active suppliers: {str(e)}")
            return []
    
    def get_supplier_compliance_data(self, supplier_id):
        """
        Get compliance data for a specific supplier
        
        Args:
            supplier_id (int): ID of the supplier
            
        Returns:
            dict: Supplier compliance data
        """
        if self.use_dummy_data:
            supplier = self.get_supplier(supplier_id)
            if not supplier:
                return {"compliance_score": 5.0}
                
            # Return the compliance score
            return {"compliance_score": supplier.get('compliance_score', 5.0)}
            
        try:
            response = requests.get(
                f"{self.base_url}/api/v1/suppliers/{supplier_id}/compliance/",
                headers=self.headers,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching compliance data for supplier {supplier_id}: {str(e)}")
            return {"compliance_score": 5.0}
    
    def test_connection(self):
        """
        Test connection to the User Service
        Returns True if connection is successful, False otherwise
        """
        if self.use_dummy_data:
            # Always return success when using dummy data
            return True
            
        try:
            # Try to connect to the health check endpoint
            response = requests.get(
                f"{self.base_url}/api/health-check/",
                headers=self.headers,
                timeout=5  # Short timeout for health check
            )
            
            return response.status_code == 200
        except requests.exceptions.RequestException as e:
            logger.error(f"Connection test failed: {str(e)}")
            return False