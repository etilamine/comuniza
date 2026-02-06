"""
Django app configuration for Groups app.
"""

from django.apps import AppConfig


class GroupsConfig(AppConfig):
    """
    Configuration class for Groups application.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.groups'
    verbose_name = 'Groups'

    def ready(self):
        """
        Import signals when app is ready.
        This ensures signals are registered when Django starts.
        """
        import apps.groups.signals
