"""
Test settings for pytest.
"""

import os
from pathlib import Path

# Build paths
BASE_DIR = Path(__file__).resolve().parent.parent

# Security
SECRET_KEY = 'test-secret-key-for-pytest-only'

# Database for testing
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

# Installed apps for testing
INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    # Third-party
    'rest_framework',
    'rest_framework_simplejwt',
    'drf_spectacular',
    'django_filters',
    # Local apps
    'apps.users',
    'apps.groups',
    'apps.items',
    'apps.loans',
    'apps.notifications',
    'apps.messaging',
    'apps.search',
    'apps.badges',
    'apps.api',
    'apps.core',
]

# Django settings
DEBUG = True
USE_TZ = True

# URL configuration for tests
ROOT_URLCONF = 'core.urls'

# REST Framework for testing
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',  # Allow all for testing
    ],
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

# User model
AUTH_USER_MODEL = 'users.User'

# Site ID
SITE_ID = 1

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'test_media'

# Static files
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'test_static'

# Password validation (minimal for testing)
AUTH_PASSWORD_VALIDATORS = []

# No email required for testing
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Celery for testing (synchronous)
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True