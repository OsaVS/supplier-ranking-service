"""
Connector for the Warehouse Service that handles product data.
"""

import requests
import logging
import os
from django.conf import settings
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Class-level static cache to be shared across all instances
_GLOBAL_CACHE = {}
_GLOBAL_CACHE_STATS = {
    "hits": 0,
    "misses": 0,
    "last_cleared": datetime.now()
}

class WarehouseServiceConnector:
    """Connector to fetch warehouse and product data from the Warehouse Service"""
    
    # Set a reasonable cache timeout (1 hour)
    CACHE_TIMEOUT = 3600  # seconds
    
    def __init__(self, use_dummy_data=False):
        """Initialize connector with base URL and auth credentials from settings"""
        # Use environment variable first, then settings
        self.base_url = os.environ.get('WAREHOUSE_SERVICE_URL', 'http://localhost:8002')
        
        # Fix URL if running in Docker but using localhost
        if 'localhost' in self.base_url and os.environ.get('DOCKER_ENV', 'False') == 'True':
            self.base_url = os.environ.get('WAREHOUSE_SERVICE_URL', 'http://localhost:8002')
            
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
        self._create_dummy_data()
        
        logger.info(f"Initialized WarehouseServiceConnector with base URL: {self.base_url}, dummy data: {use_dummy_data}")
    
    def _create_dummy_data(self):
        """Create dummy data for testing"""
        # Dummy data implementation remains the same
        # ...existing dummy data code...
        
        # Dummy products
        self.dummy_products = {
            1: {
                "id": 1,
                "name": "Widget A",
                "sku": "WIDGET-A",
                "description": "Standard widget for industrial use",
                "category": "Widgets",
                "unit_cost": 10.50,
                "stock_quantity": 500,
                "min_stock_level": 100
            },
            2: {
                "id": 2,
                "name": "Widget B",
                "sku": "WIDGET-B",
                "description": "Premium widget for specialized use",
                "category": "Widgets",
                "unit_cost": 15.75,
                "stock_quantity": 250,
                "min_stock_level": 50
            },
            3: {
                "id": 3,
                "name": "Component X",
                "sku": "COMP-X",
                "description": "Essential component for assembly",
                "category": "Components",
                "unit_cost": 5.25,
                "stock_quantity": 1000,
                "min_stock_level": 200
            }
        }
        
        # Dummy supplier-product relationships
        self.dummy_supplier_products = [
            {
                "supplier_id": 3,
                "product_id": 1,
                "supplier_name": "A Supplies Inc.",
                "product_name": "Widget A",
                "unit_price": 1.50,
                "lead_time_days": 2,
                "minimum_order_quantity": 50,
                "maximum_order_quantity": 1000,
                "is_preferred": True
            },
            {
                "supplier_id": 3,
                "product_id": 2,
                "supplier_name": "A Supplies Inc.",
                "product_name": "Widget B",
                "unit_price": 14.75,
                "lead_time_days": 7,
                "minimum_order_quantity": 25,
                "maximum_order_quantity": 500,
                "is_preferred": True
            },
            {
                "supplier_id": 4,
                "product_id": 1,
                "supplier_name": "B Supplies Inc.",
                "product_name": "Widget A",
                "unit_price": 9.80,
                "lead_time_days": 4,
                "minimum_order_quantity": 50,
                "maximum_order_quantity": 1000,
                "is_preferred": False
            },
            {
                "supplier_id": 5,
                "product_id": 2,
                "supplier_name": "C Supplies Inc.",
                "product_name": "Widget B",
                "unit_price": 14.50,
                "lead_time_days": 6,
                "minimum_order_quantity": 20,
                "maximum_order_quantity": 600,
                "is_preferred": False
            },
            {
                "supplier_id": 5,
                "product_id": 3,
                "supplier_name": "C Supplies Inc.",
                "product_name": "Component X",
                "unit_price": 4.90,
                "lead_time_days": 3,
                "minimum_order_quantity": 100,
                "maximum_order_quantity": 2000,
                "is_preferred": True
            }
        ]
        
        # Dummy categories
        self.dummy_categories = [
            {"id": 1, "name": "Widgets", "description": "Standard industrial widgets"},
            {"id": 2, "name": "Components", "description": "Assembly components"},
            {"id": 3, "name": "Raw Materials", "description": "Basic raw materials"}
        ]
        
        # Dummy supplier categories (which suppliers provide products in which categories)
        self.dummy_supplier_categories = {
            3: [1, 2],  # A Supplies Inc. provides Widgets and Components
            4: [1],     # B Supplies Inc. provides Widgets only
            5: [2, 3]   # C Supplies Inc. provides Components and Raw Materials
        }
    
    def _get_from_cache(self, cache_key):
        """Get data from cache if available and not expired"""
        global _GLOBAL_CACHE, _GLOBAL_CACHE_STATS
        
        if cache_key in _GLOBAL_CACHE:
            timestamp, data = _GLOBAL_CACHE[cache_key]
            if datetime.now() - timestamp < timedelta(seconds=self.CACHE_TIMEOUT):
                _GLOBAL_CACHE_STATS["hits"] += 1
                logger.debug(f"Cache HIT for {cache_key} ({len(_GLOBAL_CACHE)} items in cache)")
                return data
        
        _GLOBAL_CACHE_STATS["misses"] += 1
        logger.debug(f"Cache MISS for {cache_key}")
        return None
    
    def _set_in_cache(self, cache_key, data):
        """Store data in cache with current timestamp"""
        global _GLOBAL_CACHE
        
        _GLOBAL_CACHE[cache_key] = (datetime.now(), data)
        logger.debug(f"Stored in cache: {cache_key} (total: {len(_GLOBAL_CACHE)} items)")
        
        # Auto-clean cache if it gets too large
        if len(_GLOBAL_CACHE) > 1000:
            self._clean_cache()
    
    def _clean_cache(self):
        """Remove expired items from cache"""
        global _GLOBAL_CACHE
        
        now = datetime.now()
        expired_keys = [
            key for key, (timestamp, _) in _GLOBAL_CACHE.items()
            if now - timestamp > timedelta(seconds=self.CACHE_TIMEOUT)
        ]
        
        for key in expired_keys:
            del _GLOBAL_CACHE[key]
        
        logger.info(f"Cleaned cache: removed {len(expired_keys)} expired items, {len(_GLOBAL_CACHE)} remain")
    
    @classmethod
    def clear_cache(cls):
        """Clear the entire cache"""
        global _GLOBAL_CACHE, _GLOBAL_CACHE_STATS
        
        cache_size = len(_GLOBAL_CACHE)
        _GLOBAL_CACHE = {}
        _GLOBAL_CACHE_STATS["hits"] = 0
        _GLOBAL_CACHE_STATS["misses"] = 0
        _GLOBAL_CACHE_STATS["last_cleared"] = datetime.now()
        
        logger.info(f"Cache cleared ({cache_size} items removed)")
    
    @classmethod
    def get_cache_stats(cls):
        """Return statistics about the cache usage"""
        global _GLOBAL_CACHE, _GLOBAL_CACHE_STATS
        
        total = _GLOBAL_CACHE_STATS["hits"] + _GLOBAL_CACHE_STATS["misses"]
        hit_ratio = _GLOBAL_CACHE_STATS["hits"] / total if total > 0 else 0
        
        return {
            "cache_size": len(_GLOBAL_CACHE),
            "cache_hits": _GLOBAL_CACHE_STATS["hits"],
            "cache_misses": _GLOBAL_CACHE_STATS["misses"],
            "hit_ratio": hit_ratio,
            "last_cleared": _GLOBAL_CACHE_STATS["last_cleared"].isoformat()
        }
    
    def get_supplier_products(self, supplier_id):
        """Get all products offered by a supplier"""
        # Check cache first
        cache_key = f"supplier_products_{supplier_id}"
        cached_data = self._get_from_cache(cache_key)
        if cached_data:
            return cached_data
            
        if self.use_dummy_data:
            # Filter supplier products by supplier_id
            result = [sp for sp in self.dummy_supplier_products if sp['supplier_id'] == supplier_id]
            self._set_in_cache(cache_key, result)
            return result
        
        try:
            logger.info(f"API call: get_supplier_products for supplier_id={supplier_id}")
            # Updated to match actual API endpoint
            response = requests.get(
                f"{self.base_url}/api/product/products-by-supplier/",
                params={"supplier_id": supplier_id},
                headers=self.headers,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            # Transform the response to match expected format
            data = response.json()
            products = []
            
            for product in data.get("products", []):
                # Get product details from cache if possible to avoid additional API calls
                product_detail = self.get_product(product["product_id"])
                if product_detail:
                    products.append({
                        "supplier_id": data["supplier_id"],
                        "product_id": product["product_id"],
                        "supplier_name": "Unknown",  # Not provided by API
                        "product_name": product_detail.get("product_name", "Unknown"),
                        "unit_price": product["supplier_price"],
                        "lead_time_days": 0,  # Not provided by API
                        "minimum_order_quantity": 0,  # Not provided by API
                        "maximum_order_quantity": 0,  # Not provided by API
                        "is_preferred": False  # Not provided by API
                    })
            
            # Cache the result
            self._set_in_cache(cache_key, products)
            return products
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching supplier products for {supplier_id}: {str(e)}")
            return []
    
    def get_product_suppliers(self, product_id):
        """Get all suppliers that offer a specific product"""
        # Check cache first
        cache_key = f"product_suppliers_{product_id}"
        cached_data = self._get_from_cache(cache_key)
        if cached_data:
            return cached_data
            
        if self.use_dummy_data:
            # Filter supplier products by product_id
            result = [sp for sp in self.dummy_supplier_products if sp['product_id'] == product_id]
            self._set_in_cache(cache_key, result)
            return result
        
        try:
            logger.info(f"API call: get_product_suppliers for product_id={product_id}")
            # Direct API call instead of making nested calls
            response = requests.get(
                f"{self.base_url}/api/product/suppliers-by-product/",
                params={"product_id": product_id},
                headers=self.headers,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            data = response.json()
            supplier_ids = data.get("supplier_ids", [])
            
            # Format the response without additional API calls
            suppliers = []
            for supplier_id in supplier_ids:
                suppliers.append({
                    "supplier_id": supplier_id,
                    "product_id": product_id,
                    "supplier_name": f"Supplier {supplier_id}",  # Use a placeholder
                    "product_name": f"Product {product_id}",  # Use a placeholder
                    "unit_price": 0.0,  # Use a default
                    "lead_time_days": 0,  # Use a default
                    "minimum_order_quantity": 0,  # Use a default
                    "maximum_order_quantity": 0,  # Use a default
                    "is_preferred": False  # Use a default
                })
            
            # Cache the result
            self._set_in_cache(cache_key, suppliers)
            return suppliers
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching suppliers for product {product_id}: {str(e)}")
            return []
    
    def get_suppliers_by_product(self, product_id):
        """
        Get suppliers that offer a specific product
        
        Args:
            product_id (int or str): ID of the product
            
        Returns:
            list: List of supplier IDs
        """
        # Check cache first
        cache_key = f"suppliers_by_product_{product_id}"
        cached_data = self._get_from_cache(cache_key)
        if cached_data:
            return cached_data
            
        if self.use_dummy_data:
            # Make sure product_id is treated as integer
            if isinstance(product_id, str) and product_id.isdigit():
                product_id = int(product_id)
            else:
                try:
                    product_id = int(product_id)
                except:
                    product_id = 1  # Default to product 1 if invalid
                    
            # Generate a deterministic but varied set of supplier IDs for each product
            import hashlib
            import random
            
            # Seed with product_id to get consistent results
            random.seed(product_id)
            
            # Determine how many suppliers offer this product (2-5)
            supplier_count = (product_id % 3) + 2  # 2-4 suppliers per product
            
            # Generate a list of potential supplier IDs (1-12)
            supplier_ids = random.sample(range(1, 100), supplier_count)
            
            # Cache the result
            self._set_in_cache(cache_key, supplier_ids)
            return supplier_ids
        
        try:
            logger.info(f"API call: get_suppliers_by_product for product_id={product_id}")
            # Get suppliers that offer this product
            response = requests.get(
                f"{self.base_url}/api/product/suppliers-by-product/",
                params={"product_id": product_id},
                headers=self.headers,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            data = response.json()
            supplier_ids = data.get("supplier_ids", [])
            
            # Cache the result
            self._set_in_cache(cache_key, supplier_ids)
            return supplier_ids
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching suppliers for product {product_id}: {str(e)}")
            return []
    
    def get_product(self, product_id):
        """
        Get product details by ID
        
        Args:
            product_id (int or str): ID of the product
            
        Returns:
            dict: Product details
        """
        # Check cache first
        cache_key = f"product_{product_id}"
        cached_data = self._get_from_cache(cache_key)
        if cached_data:
            return cached_data
            
        if self.use_dummy_data:
            # Convert to int if string
            if isinstance(product_id, str) and product_id.isdigit():
                product_id = int(product_id)
            else:
                try:
                    product_id = int(product_id)
                except:
                    product_id = 1  # Default to product 1 if invalid
            
            # Return dummy product if it exists
            product = self.dummy_products.get(product_id, {
                "id": product_id,
                "name": f"Product {product_id}",
                "sku": f"SKU-{product_id}",
                "description": "Generic product",
                "category": "Miscellaneous"
            })
            
            # Cache the result
            self._set_in_cache(cache_key, product)
            return product
            
        try:
            logger.info(f"API call: get_product for product_id={product_id}")
            # Get product details
            response = requests.get(
                f"{self.base_url}/api/product/products/{product_id}/",
                headers=self.headers,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            product = response.json()
            
            # Cache the result
            self._set_in_cache(cache_key, product)
            return product
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching product {product_id}: {str(e)}")
            return None
    
    def get_suppliers_by_category(self, category_id):
        """Get all suppliers that offer products in a specific category"""
        # Check cache first
        cache_key = f"suppliers_by_category_{category_id}"
        cached_data = self._get_from_cache(cache_key)
        if cached_data:
            return cached_data
            
        if self.use_dummy_data:
            # Find suppliers that provide products in this category
            suppliers = []
            for supplier_id, categories in self.dummy_supplier_categories.items():
                if category_id in categories:
                    suppliers.append(supplier_id)
            
            # Cache the result
            self._set_in_cache(cache_key, suppliers)
            return suppliers
        
        # This endpoint doesn't exist in the actual API
        # We need to implement a workaround
        try:
            logger.info(f"API call sequence: get_suppliers_by_category for category_id={category_id}")
            # Get all products in this category
            response = requests.get(
                f"{self.base_url}/api/product/categories/{category_id}/",
                headers=self.headers,
                timeout=self.timeout
            )
            response.raise_for_status()
            category_data = response.json()
            
            # Get all products (to filter by category)
            response = requests.get(
                f"{self.base_url}/api/product/products/",
                headers=self.headers,
                timeout=self.timeout
            )
            response.raise_for_status()
            products = response.json()
            
            # Filter products by category
            category_products = [p for p in products if p.get("category") == category_data.get("name")]
            
            # Get suppliers for each product (use cache where possible)
            all_suppliers = set()
            for product in category_products:
                suppliers = self.get_suppliers_by_product(product["id"])
                all_suppliers.update(suppliers)
            
            suppliers_list = list(all_suppliers)
            
            # Cache the result
            self._set_in_cache(cache_key, suppliers_list)
            return suppliers_list
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching suppliers for category {category_id}: {str(e)}")
            return []
    
    def test_connection(self):
        """
        Test connection to the Warehouse Service
        Returns True if connection is successful, False otherwise
        """
        if self.use_dummy_data:
            # Always return success when using dummy data
            return True
            
        try:
            logger.info(f"Testing connection to {self.base_url}")
            # Try to connect to the root URL instead of a health check endpoint
            response = requests.get(
                f"{self.base_url}/api/product/",
                headers=self.headers,
                timeout=5  # Short timeout for health check
            )
            
            success = response.status_code == 200
            logger.info(f"Connection test {'successful' if success else 'failed'}: {response.status_code}")
            return success
        except requests.exceptions.RequestException as e:
            logger.error(f"Connection test failed: {str(e)}")
            return False