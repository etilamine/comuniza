import os
from celery import Celery

# Set the default Django settings module based on environment
django_env = os.environ.get('DJANGO_ENV', 'development')
settings_module = f'core.settings.{django_env}'
os.environ.setdefault('DJANGO_SETTINGS_MODULE', settings_module)

app = Celery('comuniza')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
