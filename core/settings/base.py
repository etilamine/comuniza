"""
Django base settings for Comuniza.
"""

import os
from datetime import timedelta
from pathlib import Path

import environ  # type: ignore

# Build paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Initialize environment FIRST - before any usage
env = environ.Env()

# Load environment-specific .env file from home directory
DJANGO_ENV = os.environ.get('DJANGO_ENV', 'development')
env_file = os.path.expanduser(f"~/.env.{DJANGO_ENV}")
if os.path.exists(env_file):
    environ.Env.read_env(env_file)
else:
    # Fallback to .env in project directory for backward compatibility
    environ.Env.read_env(os.path.join(BASE_DIR, ".env"))

# Secret key
SECRET_KEY = env("SECRET_KEY", default="django-insecure-dev-key")

# Application definition
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
    "django.contrib.sites",
    # Third-party
    "django_extensions",
    "django_filters",
    "widget_tweaks",
    "rest_framework",
    "rest_framework_simplejwt",
    "drf_spectacular",  # OpenAPI/Swagger documentation
    "corsheaders",
    "django_ratelimit",
    "easy_thumbnails",
    # Allauth
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.google",
    "allauth.socialaccount.providers.github",
    "allauth.mfa",
    # Local apps
    "apps.users",
    "apps.groups",
    "apps.items",
    "apps.loans",
    "apps.notifications",
    "apps.messaging",
    "apps.search",
    "apps.badges",
    "apps.api",
    "apps.core",
]

MIDDLEWARE = [
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "allauth.account.middleware.AccountMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    # Audit logging middleware
    "apps.core.middleware.AuditMiddleware",
]

ROOT_URLCONF = "core.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "apps.core.context_processors.site_settings",
                "apps.core.context_processors.notification_counts",
            ],
        },
    },
]

WSGI_APPLICATION = "core.wsgi.application"

# Database
# Temporarily modify core/settings/base.py for export
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("DB_NAME", default="comuniza123"),
        "USER": env("DB_USER", default="comuniza123"),
        "PASSWORD": env("DB_PASSWORD"),
        "HOST": env("DB_HOST", default="postgres"),
        "PORT": env("DB_PORT", default="5432"),
        "OPTIONS": {
            "sslmode": "prefer",
        },
        "CONN_MAX_AGE": 300,
    }
}


# Caching Configuration
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": "redis://redis:6379/1",
    },
    "ratelimit": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": "redis://redis:6379/2",
    }
}



# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# Internationalization
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_L10N = True
USE_TZ = True

# Supported languages
LANGUAGES = [
    ('en', 'English'),
    ('de', 'Deutsch'),
    ('es', 'Español'),
]

# Locale paths
LOCALE_PATHS = [
    BASE_DIR / "locale",
]

# Static files
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]

# Media files
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# Default primary key
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Custom user model
AUTH_USER_MODEL = "users.User"

# Login/Logout
LOGIN_URL = "account_login"
LOGIN_REDIRECT_URL = "users:profile"
LOGOUT_REDIRECT_URL = "/"

# Celery
CELERY_BROKER_URL = env("REDIS_URL", default="redis://redis:6379/0")
CELERY_RESULT_BACKEND = env("REDIS_URL", default="redis://redis:6379/0")
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = TIME_ZONE

# Django Allauth
SITE_ID = 1

AUTHENTICATION_BACKENDS = [
    # Custom backend for GDPR-compliant email authentication
    "apps.users.auth_backend.EmailAuthenticationBackend",
    # Needed to login by username in Django admin, regardless of `allauth`
    "django.contrib.auth.backends.ModelBackend",
    # `allauth` specific authentication methods, such as login by e-mail
    "allauth.account.auth_backends.AuthenticationBackend",
]

# Allauth settings
ACCOUNT_LOGIN_METHODS = {'email'}
ACCOUNT_SIGNUP_FIELDS = ['email*', 'password1*', 'password2*']
ACCOUNT_UNIQUE_EMAIL = True
ACCOUNT_USER_MODEL_USERNAME_FIELD = None
ACCOUNT_EMAIL_VERIFICATION = env('ACCOUNT_EMAIL_VERIFICATION', default='optional')  # Default: optional (can be overridden)
ACCOUNT_LOGIN_ON_EMAIL_CONFIRMATION = True
ACCOUNT_SESSION_REMEMBER = True
ACCOUNT_LOGOUT_ON_GET = False
ACCOUNT_EMAIL_CONFIRMATION_EXPIRE_DAYS = 7  # Links expire in 7 days
ACCOUNT_EMAIL_VERIFICATION_REDIRECT_URL = "/users/profile/"
ACCOUNT_EMAIL_SUBJECT_PREFIX=""

# Custom forms
ACCOUNT_FORMS = {
    'signup': 'apps.users.forms.CustomUserCreationForm',
    'login': 'allauth.account.forms.LoginForm',
    'change_password': 'allauth.account.forms.ChangePasswordForm',
}

# Custom adapter
ACCOUNT_ADAPTER = 'apps.users.adapter.ComunizaAccountAdapter'

# Social account adapter for OAuth users
SOCIALACCOUNT_ADAPTER = 'apps.users.adapter.ComunizaSocialAccountAdapter'

# Error handlers
handler404 = 'core.views.handler404'
handler500 = 'core.views.handler500'
handler405 = 'core.views.handler405'

# Social account settings
SOCIALACCOUNT_AUTO_SIGNUP = True
SOCIALACCOUNT_EMAIL_VERIFICATION = "optional"
SOCIALACCOUNT_QUERY_EMAIL = True

# Redirect URLs
ACCOUNT_LOGOUT_REDIRECT_URL = "/"

# REST Framework Configuration
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',  # Allow public access by default
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
    ],
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

# DRF Spectacular Configuration for API Documentation
SPECTACULAR_SETTINGS = {
    'TITLE': 'Comuniza API',
    'DESCRIPTION': 'API for the Comuniza sharing platform',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'COMPONENT_SPLIT_REQUEST': True,
    'SWAGGER_UI_SETTINGS': {
        'deepLinking': True,
        'persistAuthorization': True,
        'displayOperationId': True,
    },
    'REDOC_UI_SETTINGS': {
        'hideDownloadButton': True,
        'hideHostname': True,
    },
}

# Rate Limiting Configuration
RATELIMIT_ENABLE = True
RATELIMIT_USE_CACHE = 'ratelimit'  # Use dedicated rate limit cache
RATELIMIT_SKIP_CACHE_SUCCESS = True  # Don't cache successful requests

# File Upload Security Configuration
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB in memory
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB for request data
FILE_UPLOAD_PERMISSIONS = 0o644  # Secure file permissions
FILE_UPLOAD_DIRECTORY_PERMISSIONS = 0o755  # Secure directory permissions

# Image Upload Restrictions
IMAGE_UPLOAD_MAX_SIZE = 5 * 1024 * 1024  # 5MB max for images
AVATAR_UPLOAD_MAX_SIZE = 5 * 1024 * 1024  # 5MB max for avatars
GROUP_IMAGE_UPLOAD_MAX_SIZE = 5 * 1024 * 1024  # 5MB max for group images

# Allowed image file extensions
ALLOWED_IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.webp', '.gif']

# Content Security Settings
CONTENT_SECURITY_POLICY = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; font-src 'self'; connect-src 'self'; frame-ancestors 'none';"

# XSS Protection
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# Social providers (configure in admin or .env)
SOCIALACCOUNT_PROVIDERS = {
    "google": {
        "SCOPE": [
            "profile",
            "email",
        ],
        "AUTH_PARAMS": {
            "access_type": "online",
        },
        "APP": {
            "client_id": env("GOOGLE_CLIENT_ID", default=""),
            "secret": env("GOOGLE_CLIENT_SECRET", default=""),
        },
    },
}

# Easy-Thumbnails Configuration
THUMBNAIL_ALIASES = {
    '': {
        # Item thumbnails for different views
        'item_list': {'size': (150, 150), 'crop': False, 'upscale': True, 'quality': 85},
        'item_detail': {'size': (400, 400), 'crop': False, 'upscale': True, 'quality': 85},
        'item_large': {'size': (800, 600), 'crop': False, 'upscale': True, 'quality': 90},
        'item_gallery': {'size': (600, 600), 'crop': False, 'upscale': True, 'quality': 85},
        'item_xlarge': {'size': (1200, 1200), 'crop': False, 'upscale': True, 'quality': 90},

        # User avatar thumbnails
        'avatar_small': {'size': (50, 50), 'crop': '(0,0)', 'upscale': True, 'quality': 85},
        'avatar_medium': {'size': (100, 100), 'crop': '(0,0)', 'upscale': True, 'quality': 85},
        'avatar_large': {'size': (300, 300), 'crop': '(0,0)', 'upscale': True, 'quality': 90},

        # Group image thumbnails
        'group_list': {'size': (300, 100), 'crop': '(0,0)', 'upscale': True, 'quality': 85},
        'group_detail': {'size': (350, 105), 'crop': '(0,0)', 'upscale': True, 'quality': 85},
        'group_large': {'size': (1000, 300), 'crop': '(0,0)', 'upscale': True, 'quality': 90},
        'group_xlarge': {'size': (1500, 1500), 'crop': False, 'upscale': True, 'quality': 90},
    }
}

# Thumbnail optimization settings (optional - requires jpegoptim/optipng)
THUMBNAIL_OPTIMIZE_COMMAND = {
    'png': '/usr/bin/optipng {filename}',
    'gif': '/usr/bin/gifsicle --optimize {filename}',
    'jpeg': '/usr/bin/jpegoptim --strip-all {filename}',
}

# Thumbnail storage settings
THUMBNAIL_DEFAULT_STORAGE = 'django.core.files.storage.FileSystemStorage'
THUMBNAIL_MEDIA_ROOT = MEDIA_ROOT / 'thumbnails'
THUMBNAIL_MEDIA_URL = MEDIA_URL + 'thumbnails/'

# Thumbnail quality and processing settings
THUMBNAIL_PRESERVE_EXTENSIONS = ('svg',)
THUMBNAIL_PROCESSORS = (
    'easy_thumbnails.processors.colorspace',
    'easy_thumbnails.processors.autocrop',
    'easy_thumbnails.processors.scale_and_crop',
    'easy_thumbnails.processors.filters',
    'easy_thumbnails.processors.background',
)
