"""
Development settings for Comuniza.
"""

from .base import *

# Skip static file collection in development for speed
COLLECTSTATIC_ON_DEPLOY = os.environ.get('COLLECTSTATIC_ON_DEPLOY', 'False').lower() == 'true'

DEBUG = True

# Allow access from local network (including mobile devices)
ALLOWED_HOSTS = [
    "localhost",
    "127.0.0.1",
    "0.0.0.0",
    "testserver",
]

# django-watchfiles: Add to INSTALLED_APPS so Django uses WatchfilesReloader
# This is REQUIRED - without it, Django falls back to StatReloader which is slower
try:
    import django_watchfiles
    if 'django_watchfiles' not in INSTALLED_APPS:
        INSTALLED_APPS.append('django_watchfiles')
except ImportError:
    pass


# django-browser-reload: Add for automatic browser refresh on file changes
try:
    import django_browser_reload
    if 'django_browser_reload' not in INSTALLED_APPS:
        INSTALLED_APPS.append('django_browser_reload')
    if 'django_browser_reload.middleware.BrowserReloadMiddleware' not in MIDDLEWARE:
        MIDDLEWARE.append('django_browser_reload.middleware.BrowserReloadMiddleware')
except ImportError:
    pass

# Conditionally add debug_toolbar
if 'debug_toolbar' not in INSTALLED_APPS:
    try:
        import debug_toolbar
        INSTALLED_APPS.append("debug_toolbar")
        MIDDLEWARE.insert(0, "debug_toolbar.middleware.DebugToolbarMiddleware")
        INTERNAL_IPS = ["127.0.0.1", "localhost", "192.168.178.36"]
    except ImportError:
        pass

# CORS settings for development
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True

# Email settings for development (use console to avoid SMTP issues)
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
EMAIL_HOST = "mailcatcher"
EMAIL_PORT = 1025
EMAIL_USE_TLS = False
DEFAULT_FROM_EMAIL = "no-reply@comuniza.org"
SERVER_EMAIL = "no-reply@comuniza.org"
ACCOUNT_EMAIL_VERIFICATION = "none"

# File upload settings
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB

# Template debugging for better development experience
if 'TEMPLATES' in locals() and TEMPLATES:
    TEMPLATES[0]['OPTIONS']['debug'] = True

# PostgreSQL database for development (to test migration)
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("DB_NAME", default="comuniza123"),
        "USER": env("DB_USER", default="comuniza123"),
        "PASSWORD": env("DB_PASSWORD"),
        "HOST": env("DB_HOST", default="postgres"),
        "PORT": env("DB_PORT", default="5432"),
        "OPTIONS": {
            "sslmode": "disable",  # Disable SSL for development
        },
        "CONN_MAX_AGE": 300,
    }
}

# Enhanced logging for development
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
        "simple": {
            "format": "{levelname} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "django.request": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": False,
        },
        "django.db.backends": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": False,
        },
    },
}
# Fix for template watching - Django uses **/* which doesn't match root files
from django.utils.autoreload import autoreload_started
from django.template.autoreload import get_template_directories

def fix_template_watching(sender, **kwargs):
    for directory in get_template_directories():
        sender.watch_dir(directory, "*")  # Watch root files too

autoreload_started.connect(fix_template_watching)
