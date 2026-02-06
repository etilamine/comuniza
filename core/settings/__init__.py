import os
from .base import *

# Load environment-specific settings
DJANGO_ENV = os.environ.get('DJANGO_ENV', 'development')

if DJANGO_ENV == 'production':
    from .production import *
elif DJANGO_ENV == 'development':
    from .development import *
else:
    # Fallback to development for safety
    from .development import *