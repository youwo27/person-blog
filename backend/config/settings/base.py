"""
Django base settings for person-blog project.

All environment-specific settings (development, staging, production)
inherit from this module via `from .base import *`.

Reads configuration from environment variables using django-environ.
"""
import os
import re
import sys
from datetime import timedelta
from pathlib import Path

import environ

# ═══════════════════════════════════════════════════
# Paths
# ═══════════════════════════════════════════════════

# backend/
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# person-blog/ (repository root)
ROOT_DIR = BASE_DIR.parent

# Add apps/ and project root to Python path for clean imports
sys.path.insert(0, str(BASE_DIR / "apps"))
sys.path.insert(0, str(BASE_DIR))

# ═══════════════════════════════════════════════════
# Environment Variables
# ═══════════════════════════════════════════════════

env = environ.Env()

# Read .env file from project root if it exists
env_file = ROOT_DIR / ".env"
if env_file.exists():
    env.read_env(str(env_file))

# ═══════════════════════════════════════════════════
# Core Django Settings
# ═══════════════════════════════════════════════════

SECRET_KEY = env("SECRET_KEY")
DEBUG = env.bool("DEBUG", default=False)
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])

# Application definition
INSTALLED_APPS = [
    # ── Django built-ins ─────────────────────────
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.postgres",
    # ── Third-party packages ──────────────────────
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "corsheaders",
    "django_filters",
    "drf_spectacular",
    "django_celery_results",
    "django_celery_beat",
    "storages",
    # ── Local applications ────────────────────────
    "apps.accounts",
    "apps.blog",
    "apps.comments",
    "apps.media_library",
    "apps.search_index",
    "apps.notifications",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",       # 1st: security headers
    "corsheaders.middleware.CorsMiddleware",                # 2nd: CORS (as high as possible)
    "whitenoise.middleware.WhiteNoiseMiddleware",           # 3rd: static files (above session)
    "django.contrib.sessions.middleware.SessionMiddleware",  # 4th: sessions
    "django.middleware.locale.LocaleMiddleware",            # 5th: locale (after session)
    "django.middleware.common.CommonMiddleware",            # 6th: common
    "django.middleware.csrf.CsrfViewMiddleware",            # 7th: CSRF protection
    "django.contrib.auth.middleware.AuthenticationMiddleware",  # 8th: auth
    "django.contrib.messages.middleware.MessageMiddleware",  # 9th: messages
    "django.middleware.clickjacking.XFrameOptionsMiddleware",  # 10th: clickjacking
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Custom User model
AUTH_USER_MODEL = "accounts.User"

# Password reset token lifetime (seconds)
PASSWORD_RESET_TIMEOUT = 3600  # 1 hour

# ═══════════════════════════════════════════════════
# Database
# ═══════════════════════════════════════════════════

DATABASE_URL = env.str("DATABASE_URL", default="")

if DATABASE_URL:
    # Parse PostgreSQL URL: psql://USER:PASSWORD@HOST:PORT/DBNAME
    match = re.match(r"psql://(.+):(.+)@(.+):(\d+)/(.+)", DATABASE_URL)
    if match:
        user, password, host, port, dbname = match.groups()
        DATABASES = {
            "default": {
                "ENGINE": "django.db.backends.postgresql",
                "NAME": dbname,
                "USER": user,
                "PASSWORD": password,
                "HOST": host,
                "PORT": port,
                "CONN_MAX_AGE": env.int("DB_CONN_MAX_AGE", default=60),
                "OPTIONS": {
                    "pool": {
                        "min_size": env.int("DB_POOL_MIN_SIZE", default=2),
                        "max_size": env.int("DB_POOL_MAX_SIZE", default=5),
                    },
                },
            }
        }
    else:
        raise ValueError(f"Invalid DATABASE_URL format: {DATABASE_URL}")
else:
    # SQLite fallback for local development
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

# ═══════════════════════════════════════════════════
# Redis & Cache
# ═══════════════════════════════════════════════════

REDIS_URL = env.str("REDIS_URL", default="redis://localhost:6379/0")

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": REDIS_URL,
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "PARSER_CLASS": "redis.connection.HiredisParser",
            "CONNECTION_POOL_CLASS": "redis.ConnectionPool",
            "CONNECTION_POOL_KWARGS": {
                "max_connections": 50,
                "retry_on_timeout": True,
            },
            "SOCKET_CONNECT_TIMEOUT": 5,
            "SOCKET_TIMEOUT": 5,
        },
        "KEY_PREFIX": "blog",
    }
}

# Session cache backend
SESSION_ENGINE = "django.contrib.sessions.backends.cached_db"
SESSION_CACHE_ALIAS = "default"

# ═══════════════════════════════════════════════════
# Celery Configuration
# ═══════════════════════════════════════════════════

CELERY_BROKER_URL = env.str("CELERY_BROKER_URL", default="redis://localhost:6379/1")
CELERY_RESULT_BACKEND = env.str("CELERY_RESULT_BACKEND", default="redis://localhost:6379/2")
CELERY_ACCEPT_CONTENT = ["application/json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = "Asia/Shanghai"
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60  # 30 minutes hard limit
CELERY_TASK_SOFT_TIME_LIMIT = 25 * 60  # 25 minutes soft limit
CELERY_RESULT_EXPIRES = 3600  # Results expire after 1 hour
CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"

# ═══════════════════════════════════════════════════
# Django REST Framework
# ═══════════════════════════════════════════════════

REST_FRAMEWORK = {
    # ── Authentication ────────────────────────────
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ],
    # ── Permissions ───────────────────────────────
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticatedOrReadOnly",
    ],
    # ── Renderers ─────────────────────────────────
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
        "rest_framework.renderers.BrowsableAPIRenderer",
    ],
    # ── Parsers ───────────────────────────────────
    "DEFAULT_PARSER_CLASSES": [
        "rest_framework.parsers.JSONParser",
        "rest_framework.parsers.MultiPartParser",
        "rest_framework.parsers.FormParser",
    ],
    # ── Throttling ────────────────────────────────
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "100/hour",
        "user": "1000/hour",
        "login": "5/minute",
        "register": "3/hour",
        "comment": "20/minute",
        "upload": "50/day",
    },
    # ── Pagination ────────────────────────────────
    "DEFAULT_PAGINATION_CLASS": "common.pagination.StandardPageNumberPagination",
    "PAGE_SIZE": 20,
    # ── Filtering ─────────────────────────────────
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    # ── API Documentation ─────────────────────────
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    # ── Exception Handling ────────────────────────
    "EXCEPTION_HANDLER": "common.exceptions.custom_exception_handler",
    # ── Versioning ────────────────────────────────
    "DEFAULT_VERSIONING_CLASS": "rest_framework.versioning.AcceptHeaderVersioning",
    "DEFAULT_VERSION": "1.0",
    "ALLOWED_VERSIONS": ["1.0"],
    "VERSION_PARAM": "version",
}

# ═══════════════════════════════════════════════════
# JWT (SimpleJWT)
# ═══════════════════════════════════════════════════

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=30),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,
    "ALGORITHM": "HS256",
    "SIGNING_KEY": SECRET_KEY,
    "VERIFYING_KEY": "",
    "AUDIENCE": None,
    "ISSUER": None,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "AUTH_HEADER_NAME": "HTTP_AUTHORIZATION",
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
    "USER_AUTHENTICATION_RULE": "rest_framework_simplejwt.authentication.default_user_authentication_rule",
    "AUTH_TOKEN_CLASSES": ("rest_framework_simplejwt.tokens.AccessToken",),
    "TOKEN_TYPE_CLAIM": "token_type",
    "JTI_CLAIM": "jti",
}

# ═══════════════════════════════════════════════════
# drf-spectacular (OpenAPI 3.0)
# ═══════════════════════════════════════════════════

SPECTACULAR_SETTINGS = {
    "TITLE": "Person Blog API",
    "DESCRIPTION": (
        "Enterprise personal blog REST API.\n\n"
        "## Authentication\n"
        "- Obtain a JWT token via `/api/auth/login/`\n"
        "- Include it in requests: `Authorization: Bearer <token>`\n\n"
        "## Response Format\n"
        "All responses follow the uniform envelope:\n"
        "- Success: `{\"success\": true, ...}`\n"
        "- Error: `{\"success\": false, \"error\": {\"code\": \"...\", \"message\": \"...\"}}`"
    ),
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
    "SCHEMA_PATH_PREFIX": r"/api/",
    "TAGS": [
        {"name": "auth", "description": "Authentication & user management"},
        {"name": "posts", "description": "Blog post CRUD operations"},
        {"name": "categories", "description": "Category management"},
        {"name": "tags", "description": "Tag management"},
        {"name": "comments", "description": "Comment system"},
        {"name": "media", "description": "Media library & file uploads"},
        {"name": "search", "description": "Search & discovery"},
        {"name": "notifications", "description": "User notifications"},
    ],
}

# ═══════════════════════════════════════════════════
# CORS
# ═══════════════════════════════════════════════════

CORS_ALLOWED_ORIGINS = env.list(
    "CORS_ALLOWED_ORIGINS",
    default=["http://localhost:5173", "http://localhost:3000"],
)
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_METHODS = [
    "DELETE",
    "GET",
    "OPTIONS",
    "PATCH",
    "POST",
    "PUT",
]
CORS_ALLOW_HEADERS = [
    "accept",
    "accept-encoding",
    "authorization",
    "content-type",
    "dnt",
    "origin",
    "user-agent",
    "x-csrftoken",
    "x-requested-with",
]

# ═══════════════════════════════════════════════════
# Internationalization (i18n)
# ═══════════════════════════════════════════════════

LANGUAGE_CODE = "zh-hans"
TIME_ZONE = "Asia/Shanghai"
USE_I18N = True
USE_L10N = True
USE_TZ = True

LOCALE_PATHS = [BASE_DIR / "locales"]

LANGUAGES = [
    ("zh-hans", "Simplified Chinese"),
    ("en", "English"),
]

# ═══════════════════════════════════════════════════
# Static Files
# ═══════════════════════════════════════════════════

STATIC_URL = "/static/"
STATIC_ROOT = env.str("STATIC_ROOT", default=str(BASE_DIR / "staticfiles"))
STATICFILES_DIRS: list = []
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# ═══════════════════════════════════════════════════
# Media Files
# ═══════════════════════════════════════════════════

MEDIA_URL = "/media/"
MEDIA_ROOT = env.str("MEDIA_ROOT", default=str(BASE_DIR / "media"))

# In base, use filesystem storage. Override in production for S3.
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

# ═══════════════════════════════════════════════════
# Templates
# ═══════════════════════════════════════════════════

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
            ],
        },
    },
]

# ═══════════════════════════════════════════════════
# Password Validation
# ═══════════════════════════════════════════════════

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 8},
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# ═══════════════════════════════════════════════════
# Security (base defaults — tightened in production)
# ═══════════════════════════════════════════════════

CSRF_COOKIE_HTTPONLY = True
SESSION_COOKIE_HTTPONLY = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"

# ═══════════════════════════════════════════════════
# Sentry
# ═══════════════════════════════════════════════════

SENTRY_DSN = env.str("SENTRY_DSN", default="")

if SENTRY_DSN:
    import sentry_sdk
    from sentry_sdk.integrations.celery import CeleryIntegration
    from sentry_sdk.integrations.django import DjangoIntegration
    from sentry_sdk.integrations.redis import RedisIntegration

    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[
            DjangoIntegration(),
            CeleryIntegration(),
            RedisIntegration(),
        ],
        environment=env.str("SENTRY_ENVIRONMENT", default="development"),
        traces_sample_rate=env.float("SENTRY_TRACES_SAMPLE_RATE", default=0.1),
        send_default_pii=False,
    )

# ═══════════════════════════════════════════════════
# Logging (dictConfig)
# ═══════════════════════════════════════════════════

# Ensure logs directory exists
LOGS_DIR = BASE_DIR / "logs"
LOGS_DIR.mkdir(exist_ok=True)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
        "json": {
            "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
            "fmt": "%(levelname)s %(asctime)s %(name)s %(module)s %(message)s",
        },
        "simple": {
            "format": "{levelname} {asctime} {message}",
            "style": "{",
        },
    },
    "filters": {
        "require_debug_false": {
            "()": "django.utils.log.RequireDebugFalse",
        },
        "require_debug_true": {
            "()": "django.utils.log.RequireDebugTrue",
        },
    },
    "handlers": {
        # Console output (development)
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "simple",
            "filters": ["require_debug_true"],
        },
        # Info-level rotating file
        "file_info": {
            "level": "INFO",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": LOGS_DIR / "info.log",
            "maxBytes": 10 * 1024 * 1024,  # 10 MB
            "backupCount": 7,
            "formatter": "verbose",
        },
        # Error-level rotating file
        "file_error": {
            "level": "ERROR",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": LOGS_DIR / "error.log",
            "maxBytes": 10 * 1024 * 1024,  # 10 MB
            "backupCount": 14,
            "formatter": "verbose",
        },
        # Structured JSON log (for log aggregation)
        "file_json": {
            "level": "INFO",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": LOGS_DIR / "app.jsonl",
            "maxBytes": 50 * 1024 * 1024,  # 50 MB
            "backupCount": 3,
            "formatter": "json",
        },
        # Email admins on errors (production)
        "mail_admins": {
            "level": "ERROR",
            "class": "django.utils.log.AdminEmailHandler",
            "filters": ["require_debug_false"],
        },
    },
    "loggers": {
        # Django internals
        "django": {
            "handlers": ["console", "file_info"],
            "level": "INFO",
            "propagate": False,
        },
        "django.request": {
            "handlers": ["file_error", "mail_admins"],
            "level": "ERROR",
            "propagate": False,
        },
        "django.security": {
            "handlers": ["file_error", "mail_admins"],
            "level": "ERROR",
            "propagate": False,
        },
        "django.db.backends": {
            "handlers": ["console"],
            "level": "ERROR",  # Set to DEBUG to see SQL queries
            "propagate": False,
        },
        # Application code
        "apps": {
            "handlers": ["console", "file_info", "file_error", "file_json"],
            "level": "DEBUG",
            "propagate": False,
        },
        # Celery
        "celery": {
            "handlers": ["console", "file_error"],
            "level": "INFO",
            "propagate": False,
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
}

# ═══════════════════════════════════════════════════
# Email
# ═══════════════════════════════════════════════════

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = env.str("EMAIL_HOST", default="localhost")
EMAIL_PORT = env.int("EMAIL_PORT", default=587)
EMAIL_HOST_USER = env.str("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = env.str("EMAIL_HOST_PASSWORD", default="")
EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=True)
DEFAULT_FROM_EMAIL = env.str("DEFAULT_FROM_EMAIL", default="noreply@example.com")
SERVER_EMAIL = env.str("SERVER_EMAIL", default="server@example.com")

# ═══════════════════════════════════════════════════
# Site
# ═══════════════════════════════════════════════════

SITE_ID = 1
SITE_NAME = env.str("SITE_NAME", default="Person Blog")
SITE_URL = env.str("SITE_URL", default="http://localhost:8000")
FRONTEND_URL = env.str("FRONTEND_URL", default="http://localhost:5173")

# ═══════════════════════════════════════════════════
# Security: Content-Security-Policy (django-csp)
# ═══════════════════════════════════════════════════

CSP_DEFAULT_SRC = ("'self'",)
CSP_SCRIPT_SRC = ("'self'",)
CSP_STYLE_SRC = ("'self'", "'unsafe-inline'")
CSP_IMG_SRC = ("'self'", "data:", "https:")
CSP_FONT_SRC = ("'self'",)
CSP_FRAME_ANCESTORS = ("'none'",)
