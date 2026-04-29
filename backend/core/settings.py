"""
Django settings for core project.
"""

from pathlib import Path
from datetime import timedelta
import os
import sys

from django.core.exceptions import ImproperlyConfigured
from django.core.management.utils import get_random_secret_key
from dotenv import load_dotenv

load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent
RUNNING_TESTS = "test" in sys.argv


def get_bool_env(name, default=False):
    return os.getenv(name, str(default)).strip().lower() in {"1", "true", "yes", "on"}


def get_list_env(name, default=""):
    value = os.getenv(name, default)
    return [item.strip() for item in value.split(",") if item.strip()]


# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv("SECRET_KEY")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = get_bool_env("DEBUG", False)

if not SECRET_KEY:
    if DEBUG or RUNNING_TESTS:
        SECRET_KEY = get_random_secret_key()
    else:
        raise ImproperlyConfigured("SECRET_KEY must be set when DEBUG is False.")

ALLOWED_HOSTS = get_list_env("ALLOWED_HOSTS", "localhost,127.0.0.1")


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'django_filters',
    'tickets',
    'users',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / "core" / "templates"],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'core.wsgi.application'


# Database
db_name = os.getenv('DB_NAME', 'smart_support')
test_db_name = os.getenv(
    'TEST_DB_NAME',
    'test_smart_support' if db_name == 'postgres' else f'test_{db_name}',
)

DATABASES = {
    'default': {
        'ENGINE': os.getenv('DB_ENGINE', 'django.db.backends.postgresql'),
        'NAME': db_name,
        'USER': os.getenv('DB_USER', 'postgres'),
        'PASSWORD': os.getenv('DB_PASSWORD_LOCAL'),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '5432'),
        'TEST': {
            'NAME': test_db_name,
        },
    }
}


# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True


# Static files
STATIC_URL = 'static/'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# Custom user model
AUTH_USER_MODEL = 'users.User'


# Django REST Framework
REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 3,
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
}


# Simple JWT
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
}

local_frontend_origins = "http://localhost:3000,http://127.0.0.1:3000"

CSRF_TRUSTED_ORIGINS = get_list_env("CSRF_TRUSTED_ORIGINS", local_frontend_origins)

# CORS
CORS_ALLOWED_ORIGINS = get_list_env("CORS_ALLOWED_ORIGINS", local_frontend_origins)

production_like = not DEBUG and not RUNNING_TESTS

SECURE_SSL_REDIRECT = get_bool_env("SECURE_SSL_REDIRECT", production_like)
SESSION_COOKIE_SECURE = get_bool_env("SESSION_COOKIE_SECURE", production_like)
CSRF_COOKIE_SECURE = get_bool_env("CSRF_COOKIE_SECURE", production_like)
SECURE_HSTS_SECONDS = int(os.getenv("SECURE_HSTS_SECONDS", "3600" if production_like else "0"))
SECURE_HSTS_INCLUDE_SUBDOMAINS = get_bool_env("SECURE_HSTS_INCLUDE_SUBDOMAINS", production_like)
SECURE_HSTS_PRELOAD = get_bool_env("SECURE_HSTS_PRELOAD", production_like)
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https") if get_bool_env("USE_X_FORWARDED_PROTO", False) else None


# Groq
GROQ_API_KEY = os.getenv('GROQ_API_KEY')


EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp-relay.brevo.com'
EMAIL_PORT = 465
EMAIL_USE_SSL = True
EMAIL_USE_TLS = False

EMAIL_HOST_USER = os.getenv('BREVO_SMTP_USER')     # from Brevo
EMAIL_HOST_PASSWORD =os.getenv('BREVO_SMTP_PASS')        # SMTP key (NOT API key)
BREVO_API_KEY=os.getenv('BREVO_API_KEY')
DEFAULT_FROM_EMAIL = os.getenv('BREVO_SENDER_EMAIL')
FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:3000')

CELERY_BROKER_URL = 'redis://127.0.0.1:6379/0'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60
# settings.py
CELERY_WORKER_POOL = 'solo'

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "%(asctime)s %(levelname)s %(name)s %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "standard",
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
        "tickets": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "users": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}
