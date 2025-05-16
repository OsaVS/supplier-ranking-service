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
    
    # Increase cache timeout from 1 hour to 24 hours (86400 seconds)
    CACHE_TIMEOUT = 86400  # seconds
    
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
                # Use product data directly without making additional API calls
                products.append({
                    "supplier_id": data["supplier_id"],
                    "product_id": product["product_id"],
                    "supplier_name": data.get("supplier_name", "Unknown"),
                    "product_name": product.get("product_name", f"Product {product['product_id']}"),
                    "unit_price": product["supplier_price"],
                    "lead_time_days": product.get("lead_time_days", 0),
                    "minimum_order_quantity": product.get("minimum_order_quantity", 0),
                    "maximum_order_quantity": product.get("maximum_order_quantity", 0),
                    "is_preferred": product.get("is_preferred", False)
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
            # Use a shorter timeout for product requests since they should be quick
            timeout = min(5, self.timeout)  
            
            logger.info(f"API call: get_product for product_id={product_id}")
            # Get product details
            response = requests.get(
                f"{self.base_url}/api/product/products/{product_id}/",
                headers=self.headers,
                timeout=timeout
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
    
    def get_suppliers_products_batch(self, supplier_ids):
        """Get products for multiple suppliers in a single method call to reduce individual API calls
        
        Args:
            supplier_ids (list): List of supplier IDs
            
        Returns:
            dict: Dictionary mapping supplier_id to their products list
        """
        if not supplier_ids:
            return {}
            
        # Check if we're using dummy data
        if self.use_dummy_data:
            # For dummy data, we can just call individual methods
            result = {}
            for supplier_id in supplier_ids:
                result[supplier_id] = self.get_supplier_products(supplier_id)
            return result
        
        # First check cache for all suppliers
        result = {}
        missing_suppliers = []
        
        for supplier_id in supplier_ids:
            cache_key = f"supplier_products_{supplier_id}"
            cached_data = self._get_from_cache(cache_key)
            if cached_data:
                result[supplier_id] = cached_data
            else:
                missing_suppliers.append(supplier_id)
        
        # If all suppliers were in cache, return immediately
        if not missing_suppliers:
            return result
        
        # For remaining suppliers, use parallel API calls for better performance
        try:
            # Import the utility in the method to avoid circular imports
            from connectors.utils import parallel_execution
            
            # Create a worker function that processes one supplier
            def get_supplier_products_worker(supplier_id):
                return self.get_supplier_products(supplier_id)
            
            # Execute in parallel with reasonable limits
            max_parallel = min(5, len(missing_suppliers))
            missing_results = parallel_execution(
                items=missing_suppliers,
                worker_func=get_supplier_products_worker,
                max_workers=max_parallel,
                timeout=20,
                description="suppliers"
            )
            
            # Add the results to our return dictionary
            result.update(missing_results)
            
        except ImportError:
            # If utils module not available, fall back to sequential execution
            logger.warning("Parallel execution utilities not available, using sequential execution")
            for supplier_id in missing_suppliers:
                result[supplier_id] = self.get_supplier_products(supplier_id)
        except Exception as e:
            logger.error(f"Error in parallel supplier products fetch: {str(e)}")
            # If parallel execution fails, fall back to sequential execution
            for supplier_id in missing_suppliers:
                if supplier_id not in result:
                    result[supplier_id] = self.get_supplier_products(supplier_id)
                    
        return result
    
    def get_products_batch(self, product_ids):
        """
        Get details for multiple products in a single method call
        
        Args:
            product_ids (list): List of product IDs
            
        Returns:
            dict: Dictionary mapping product_id to product details
        """
        if not product_ids:
            return {}
            
        result = {}
        
        # Check if we're using dummy data
        if self.use_dummy_data:
            for product_id in product_ids:
                result[product_id] = self.get_product(product_id)
            return result
            
        # First check cache for all products
        missing_products = []
        for product_id in product_ids:
            cache_key = f"product_{product_id}"
            cached_data = self._get_from_cache(cache_key)
            if cached_data:
                result[product_id] = cached_data
            else:
                missing_products.append(product_id)
                
        # If all products were in cache, return immediately
        if not missing_products:
            return result
            
        # For remaining products, try to use batch endpoint first
        try:
            # Use a shorter timeout for product batch requests
            timeout = min(8, self.timeout)
            
            # If there's a batch endpoint, use it
            if len(missing_products) > 1:
                logger.info(f"API call: get_products_batch for {len(missing_products)} products")
                try:
                    # Try to use batch endpoint if it exists
                    response = requests.get(
                        f"{self.base_url}/api/product/products/batch/",
                        params={"ids": ",".join(str(pid) for pid in missing_products)},
                        headers=self.headers,
                        timeout=timeout
                    )
                    if response.status_code == 200:
                        products_data = response.json()
                        for product in products_data:
                            product_id = product.get("id")
                            if product_id:
                                # Cache individual products
                                self._set_in_cache(f"product_{product_id}", product)
                                result[product_id] = product
                        
                        # Check if all products were retrieved
                        still_missing = [pid for pid in missing_products if pid not in result]
                        if not still_missing:
                            return result
                        
                        # Update missing_products list with those still missing
                        missing_products = still_missing
                except Exception as e:
                    # If batch endpoint doesn't exist or fails, continue to parallel fetching
                    logger.warning(f"Batch product fetch failed, falling back to parallel: {str(e)}")
            
            # For remaining products, use parallel execution
            try:
                # Import utility here to avoid circular imports
                from connectors.utils import parallel_execution
                
                # Define worker function
                def get_product_worker(product_id):
                    return self.get_product(product_id)
                
                # Use parallel execution with reasonable limits
                max_parallel = min(8, len(missing_products))
                missing_results = parallel_execution(
                    items=missing_products,
                    worker_func=get_product_worker,
                    max_workers=max_parallel,
                    timeout=15,
                    description="products"
                )
                
                # Add results
                result.update(missing_results)
                
            except ImportError:
                # If utils not available, use sequential
                logger.warning("Parallel execution utilities not available, using sequential execution")
                for product_id in missing_products:
                    product_data = self.get_product(product_id)
                    if product_data:
                        result[product_id] = product_data
            except Exception as e:
                logger.error(f"Error in parallel product fetch: {str(e)}")
                # Fall back to sequential if parallel fails
                for product_id in missing_products:
                    if product_id not in result:
                        product_data = self.get_product(product_id)
                        if product_data:
                            result[product_id] = product_data
                    
        except Exception as e:
            logger.error(f"Error in batch product fetch: {str(e)}")
            # Attempt sequential fetch as a last resort
            for product_id in missing_products:
                if product_id not in result:
                    product_data = self.get_product(product_id)
                    if product_data:
                        result[product_id] = product_data
            
        return result
    
    def pre_warm_cache(self, max_suppliers=50, max_products=100):
        """
        Pre-warm the cache with commonly accessed data to improve response times
        
        Args:
            max_suppliers (int): Maximum number of suppliers to pre-cache
            max_products (int): Maximum number of products to pre-cache
            
        Returns:
            dict: Cache statistics after pre-warming
        """
        logger.info(f"Pre-warming cache with up to {max_suppliers} suppliers and {max_products} products")
        
        # We'll use dummy data if that setting is enabled
        if self.use_dummy_data:
            logger.info("Using dummy data for cache pre-warming")
            # Warm dummy suppliers
            for i in range(1, max_suppliers + 1):
                self.get_supplier_products(i)
                
            # Warm dummy products
            for i in range(1, max_products + 1):
                self.get_product(i)
                
            return self.get_cache_stats()
        
        try:
            # Get list of active suppliers (limit by max_suppliers)
            try:
                response = requests.get(
                    f"{self.base_url}/api/product/suppliers/",
                    headers=self.headers,
                    params={"limit": max_suppliers, "active": True},
                    timeout=15
                )
                
                if response.status_code == 200:
                    suppliers_data = response.json()
                    suppliers = []
                    
                    # Handle different response formats
                    if isinstance(suppliers_data, list):
                        suppliers = [s.get('id') for s in suppliers_data if s.get('id')]
                    elif isinstance(suppliers_data, dict) and 'suppliers' in suppliers_data:
                        suppliers = [s.get('id') for s in suppliers_data['suppliers'] if s.get('id')]
                    
                    # Pre-warm supplier products
                    for supplier_id in suppliers[:max_suppliers]:
                        self.get_supplier_products(supplier_id)
                
            except Exception as e:
                logger.warning(f"Error pre-warming supplier cache: {str(e)}")
            
            # Get list of popular products
            try:
                response = requests.get(
                    f"{self.base_url}/api/product/products/",
                    headers=self.headers,
                    params={"limit": max_products, "sort": "popularity"},
                    timeout=15
                )
                
                if response.status_code == 200:
                    products_data = response.json()
                    product_ids = []
                    
                    # Handle different response formats
                    if isinstance(products_data, list):
                        product_ids = [p.get('id') for p in products_data if p.get('id')]
                    elif isinstance(products_data, dict) and 'products' in products_data:
                        product_ids = [p.get('id') for p in products_data['products'] if p.get('id')]
                    
                    # Use batch method if available
                    self.get_products_batch(product_ids)
                    
            except Exception as e:
                logger.warning(f"Error pre-warming product cache: {str(e)}")
            
            # Use any other endpoints you need to warm up
            
        except Exception as e:
            logger.error(f"Error during cache pre-warming: {str(e)}")
            
        return self.get_cache_stats()