"""
Development settings — local machine, DEBUG=True.

Usage:
    python manage.py runserver
    DJANGO_SETTINGS_MODULE=config.settings.development
"""
from .base import *  # noqa: F403, F401

# ═══════════════════════════════════════════════════
# Debug
# ═══════════════════════════════════════════════════

DEBUG = True
ALLOWED_HOSTS = ["*"]

# ═══════════════════════════════════════════════════
# Email — print to console instead of sending
# ═══════════════════════════════════════════════════

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# ═══════════════════════════════════════════════════
# Debug Toolbar
# ═══════════════════════════════════════════════════

INSTALLED_APPS += [  # noqa: F405
    "django_extensions",
    "debug_toolbar",
]

MIDDLEWARE.insert(  # noqa: F405
    0, "debug_toolbar.middleware.DebugToolbarMiddleware"
)

INTERNAL_IPS = [
    "127.0.0.1",
    "localhost",
]

# Show toolbar regardless of IP when DEBUG=True
DEBUG_TOOLBAR_CONFIG = {
    "SHOW_TOOLBAR_CALLBACK": lambda request: DEBUG,
}

# ═══════════════════════════════════════════════════
# CORS — allow all origins in development
# ═══════════════════════════════════════════════════

CORS_ALLOW_ALL_ORIGINS = True

# ═══════════════════════════════════════════════════
# Disable Sentry in local development
# ═══════════════════════════════════════════════════

SENTRY_DSN = ""

# ═══════════════════════════════════════════════════
# Logging — more verbose in development
# ═══════════════════════════════════════════════════

LOGGING["loggers"]["django.db.backends"]["level"] = "ERROR"  # noqa: F405
LOGGING["loggers"]["apps"]["level"] = "DEBUG"  # noqa: F405

# ═══════════════════════════════════════════════════
# Django Extensions
# ═══════════════════════════════════════════════════

SHELL_PLUS = "ipython"
SHELL_PLUS_PRINT_SQL = True
