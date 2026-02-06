"""
Production settings for Comuniza.
"""

from .base import *
import os

# Production settings
DEBUG = False

# Allow access from production domain and server IP
ALLOWED_HOSTS = [
    "comuniza.org",
    "www.comuniza.org",
    "localhost",
    "127.0.0.1",
    "0.0.0.0",
    "testserver",
]

# Security settings for production
SECURE_SSL_REDIRECT = False  # Set to True when SSL is configured
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'

# Email settings for production (using Mailcow SMTP with TLS)
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = env('EMAIL_HOST', default='smtp.server.org')  # Use host IP for Docker networking
EMAIL_PORT = env('EMAIL_PORT', default='587')  # STARTTLS port
EMAIL_USE_TLS = env.bool('EMAIL_USE_TLS', default=True)  # Enable STARTTLS
EMAIL_USE_SSL = env.bool('EMAIL_USE_SSL', default=False)  # Disable SSL for port 587
EMAIL_HOST_USER = env('EMAIL_HOST_USER', default='no-reply@comuniza.org')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', default='Comuniza <no-reply@comuniza.org>')
SERVER_EMAIL = env('SERVER_EMAIL', default='Comuniza <no-reply@comuniza.org>')
EMAIL_TIMEOUT = env.int('EMAIL_TIMEOUT', default=30)

# Fallback to console if email not configured
if not EMAIL_HOST_PASSWORD:
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
    print("⚠️  EMAIL_BACKEND: Using console backend (EMAIL_HOST_PASSWORD not set)")

# Enable mandatory email verification for production
ACCOUNT_EMAIL_VERIFICATION = "mandatory"

# Site configuration from environment (fallback if Site model fails)
SITE_NAME = env('SITE_NAME', default='Comuniza')
SITE_DOMAIN = env('SITE_DOMAIN', default='comuniza.org')

# Ensure log directory exists (with permission handling)
LOG_DIR = '/app/logs'
LOG_DIR_AVAILABLE = False

try:
    os.makedirs(LOG_DIR, exist_ok=True)
    LOG_DIR_AVAILABLE = True
except PermissionError:
    # If we can't create the directory, fall back to console logging only
    print(f"⚠️  Warning: Cannot create log directory {LOG_DIR}, using console logging only")
    LOG_DIR_AVAILABLE = False
except Exception as e:
    print(f"⚠️  Warning: Error creating log directory {LOG_DIR}: {e}")
    LOG_DIR_AVAILABLE = False

# Production logging with graceful fallback for missing directories
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True,
        },
        'apps': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True,
        },
        'celery': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True,
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}

# Add file handlers only if directory is accessible
if LOG_DIR_AVAILABLE:
    try:
        if os.path.exists(LOG_DIR) and os.access(LOG_DIR, os.W_OK):
            LOGGING['handlers'].update({
                'file': {
                    'level': 'INFO',
                    'class': 'logging.FileHandler',
                    'filename': os.path.join(LOG_DIR, 'django.log'),
                    'formatter': 'verbose',
                },
                'error_file': {
                    'level': 'ERROR',
                    'class': 'logging.FileHandler',
                    'filename': os.path.join(LOG_DIR, 'django_error.log'),
                    'formatter': 'verbose',
                },
            })

            # Update loggers to use file handlers
            for logger_name in ['django', 'apps', 'celery']:
                if logger_name in LOGGING['loggers']:
                    LOGGING['loggers'][logger_name]['handlers'].extend(['file'])

            # Add error_file to django and apps loggers
            for logger_name in ['django', 'apps']:
                if logger_name in LOGGING['loggers']:
                    LOGGING['loggers'][logger_name]['handlers'].append('error_file')

            # Update root logger
            LOGGING['root']['handlers'].append('file')
    except Exception as e:
        print(f"⚠️  Warning: Cannot configure file logging: {e}")
else:
    print(f"⚠️  Warning: Log directory not available, using console logging only")

# File upload settings for production
FILE_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024  # 5MB

# CORS settings for production (restrict as needed)
CORS_ALLOWED_ORIGINS = [
    "http://comuniza.org",
    "https://comuniza.org",
    "http://www.comuniza.org",
    "https://www.comuniza.org",
]
CORS_ALLOW_CREDENTIALS = True

CSRF_TRUSTED_ORIGINS = [
    "https://comuniza.org",
    "https://www.comuniza.org",
    "http://comuniza.org",
    "http://www.comuniza.org",
]

# Cookie settings for production
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = True


# Static files settings (ensure they're properly collected)
STATIC_URL = '/static/'
STATIC_ROOT = '/app/staticfiles'
MEDIA_ROOT = '/app/media'
MEDIA_URL = '/media/'

# WhiteNoise configuration for production
WHITENOISE_ROOT = '/app/staticfiles'
WHITENOISE_USE_FINDERS = True
WHITENOISE_AUTOREFRESH = False

# Caching configuration for production - use Redis like development
# Note: Production inherits Redis cache configuration from base.py

# Static file caching
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

print("✅ Production settings loaded")
