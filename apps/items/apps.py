"""
Django app configuration for Items app.
"""

from django.apps import AppConfig


class ItemsConfig(AppConfig):
    """
    Configuration class for Items application.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.items'
    verbose_name = 'Items'
    
    def ready(self):
        """
        Import signals when app is ready.
        This ensures signals are registered when Django starts.
        """
        import apps.items.signals
