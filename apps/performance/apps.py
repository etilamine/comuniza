"""
Performance app configuration for Comuniza.
"""

from django.apps import AppConfig


class PerformanceConfig(AppConfig):
    """Performance monitoring app configuration."""
    
    default_auto_field = 'id'
    name = 'performance'
    verbose_name = 'Performance Monitoring'
    
    def ready(self):
        """Import signals when app is ready."""
        try:
            from . import signals
        except ImportError:
            pass