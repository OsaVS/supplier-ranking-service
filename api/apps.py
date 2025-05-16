from django.apps import AppConfig
import logging
import threading
import time

logger = logging.getLogger(__name__)

class ApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api'
    
    def ready(self):
        """
        Initialize any application-specific setup when the Django app is ready.
        This is a good place to set up signal handlers or initialize services.
        """
        # Import signals to register them (if you create signals later)
        # from . import signals
        
        # Avoid running twice in development (Django's autoreloader launches it twice)
        import sys
        if not any(arg.endswith('manage.py') for arg in sys.argv) or 'runserver' not in sys.argv:
            # Start cache warming in a background thread to avoid blocking startup
            self._start_cache_warming()
        
    def _start_cache_warming(self):
        """Start cache warming in a background thread"""
        def warm_cache():
            # Delay a bit to ensure the application is fully loaded
            time.sleep(5)
            
            try:
                logger.info("Starting cache pre-warming...")
                
                # Import here to avoid circular imports
                from connectors.warehouse_service_connector import WarehouseServiceConnector
                from connectors.user_service_connector import UserServiceConnector
                from connectors.order_service_connector import OrderServiceConnector
                
                # Pre-warm warehouse service cache
                warehouse_connector = WarehouseServiceConnector()
                cache_stats = warehouse_connector.pre_warm_cache(max_suppliers=30, max_products=50)
                logger.info(f"Warehouse service cache warmed: {cache_stats}")
                
                # Pre-warm other service caches if needed
                # user_connector = UserServiceConnector()
                # order_connector = OrderServiceConnector()
                
                logger.info("Cache pre-warming completed successfully")
            except Exception as e:
                logger.error(f"Error during cache pre-warming: {str(e)}")
        
        # Start the cache warming in a separate thread
        thread = threading.Thread(target=warm_cache, daemon=True)
        thread.start()
        logger.info("Cache warming thread started")