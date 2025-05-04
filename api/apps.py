from django.apps import AppConfig


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
        
        # Initialize any services that should start with the application
        pass