# Import the Celery app from config
from config.celery import app

# This makes the app available as 'core.celery.app'
__all__ = ['app']
