"""
Production settings — full security hardening, S3 storage, Sentry enabled.

Usage:
    DJANGO_SETTINGS_MODULE=config.settings.production
"""
from .base import *  # noqa: F403, F401

# ═══════════════════════════════════════════════════
# Debug — NEVER True in production
# ═══════════════════════════════════════════════════

DEBUG = False
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS")  # noqa: F405

# ═══════════════════════════════════════════════════
# Security Hardening
# ═══════════════════════════════════════════════════

SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"

# ═══════════════════════════════════════════════════
# JSON-only renderer (remove browsable API)
# ═══════════════════════════════════════════════════

REST_FRAMEWORK["DEFAULT_RENDERER_CLASSES"] = [  # type: ignore[index]
    "rest_framework.renderers.JSONRenderer",
]

# ═══════════════════════════════════════════════════
# Storage — S3 / MinIO via django-storages
# ═══════════════════════════════════════════════════

AWS_ACCESS_KEY_ID = env.str("AWS_ACCESS_KEY_ID")  # noqa: F405
AWS_SECRET_ACCESS_KEY = env.str("AWS_SECRET_ACCESS_KEY")  # noqa: F405
AWS_STORAGE_BUCKET_NAME = env.str("AWS_STORAGE_BUCKET_NAME")  # noqa: F405
AWS_S3_ENDPOINT_URL = env.str("AWS_S3_ENDPOINT_URL", default=None)  # noqa: F405
AWS_S3_REGION_NAME = env.str("AWS_S3_REGION_NAME", default="us-east-1")  # noqa: F405
AWS_S3_SIGNATURE_VERSION = "s3v4"
AWS_DEFAULT_ACL = "private"
AWS_S3_OBJECT_PARAMETERS = {
    "CacheControl": "max-age=86400",
}
AWS_QUERYSTRING_AUTH = False
AWS_S3_FILE_OVERWRITE = False
AWS_LOCATION = "media"

# Use S3 for media files, keep WhiteNoise for static files
STORAGES = {
    "default": {
        "BACKEND": "storages.backends.s3boto3.S3Boto3Storage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

# ═══════════════════════════════════════════════════
# Sentry — enabled by default in production
# ═══════════════════════════════════════════════════

# SENTRY_DSN from env is used in base.py
# Ensure SENTRY_ENVIRONMENT=production is set in .env

# ═══════════════════════════════════════════════════
# Email — real SMTP backend
# ═══════════════════════════════════════════════════

# Uses base.py EMAIL_* settings from environment variables
# Ensure EMAIL_HOST, EMAIL_HOST_USER, EMAIL_HOST_PASSWORD are set in .env

# ═══════════════════════════════════════════════════
# Admins — receive error notifications
# ═══════════════════════════════════════════════════

ADMINS = env.tuple("ADMINS", default=())  # noqa: F405
MANAGERS = ADMINS

# ═══════════════════════════════════════════════════
# Logging — prod level
# ═══════════════════════════════════════════════════

LOGGING["loggers"]["django"]["level"] = "WARNING"  # noqa: F405
LOGGING["loggers"]["apps"]["level"] = "INFO"  # noqa: F405
LOGGING["loggers"]["django.request"]["handlers"].append("mail_admins")  # noqa: F405
