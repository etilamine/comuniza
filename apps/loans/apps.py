"""
Django app configuration for Loans app.
"""

from django.apps import AppConfig


class LoansConfig(AppConfig):
    """
    Configuration class for the Loans application.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.loans'
    verbose_name = 'Loans'

    def ready(self):
        """
        Import signals when app is ready.
        This ensures signals are registered when Django starts.
        """
        import apps.loans.signals
