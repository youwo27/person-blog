"""
Staging settings — pre-production environment, mirrors production with relaxed security.

Usage:
    DJANGO_SETTINGS_MODULE=config.settings.staging
"""
from .base import *  # noqa: F403, F401

# ═══════════════════════════════════════════════════
# Debug
# ═══════════════════════════════════════════════════

DEBUG = False
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS")  # noqa: F405

# ═══════════════════════════════════════════════════
# Database — separate staging database
# ═══════════════════════════════════════════════════

# Uses DATABASE_URL from env; typically points to a staging PostgreSQL instance

# ═══════════════════════════════════════════════════
# Browsable API — enabled for manual testing
# ═══════════════════════════════════════════════════

REST_FRAMEWORK["DEFAULT_RENDERER_CLASSES"] += [  # type: ignore[index]
    "rest_framework.renderers.BrowsableAPIRenderer",
]

# ═══════════════════════════════════════════════════
# Relaxed rate limiting for testing
# ═══════════════════════════════════════════════════

REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"].update({  # type: ignore[index]
    "anon": "500/hour",
    "user": "5000/hour",
})

# ═══════════════════════════════════════════════════
# Email — real backend for testing email flows
# ═══════════════════════════════════════════════════

# Uses base.py EMAIL_* settings from environment variables
# Typically configured to use a test SMTP service (Mailpit, Mailhog, etc.)

# ═══════════════════════════════════════════════════
# Sentry — separate staging project
# ═══════════════════════════════════════════════════

# SENTRY_DSN from env is used in base.py
# Set SENTRY_ENVIRONMENT=staging in .env

# ═══════════════════════════════════════════════════
# Disable SSL redirect in staging
# ═══════════════════════════════════════════════════

SECURE_SSL_REDIRECT = False
