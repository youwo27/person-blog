"""Helper utilities for accounts app — token generation, validation."""

import uuid
from datetime import datetime, timedelta, timezone

import jwt
from django.conf import settings


def generate_verification_token() -> str:
    """Generate a unique email verification token (UUID-based)."""
    return uuid.uuid4().hex


def generate_password_reset_token(user_id: int) -> str:
    """
    Generate a time-limited password reset token.

    Encodes user_id and expiry in a JWT signed with SECRET_KEY.
    Token expires after PASSWORD_RESET_TIMEOUT seconds (default 1 hour).
    """
    timeout = getattr(settings, "PASSWORD_RESET_TIMEOUT", 3600)
    payload = {
        "user_id": user_id,
        "type": "password_reset",
        "exp": datetime.now(timezone.utc) + timedelta(seconds=timeout),
        "iat": datetime.now(timezone.utc),
        "jti": uuid.uuid4().hex,
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")


def verify_password_reset_token(token: str) -> int | None:
    """
    Validate a password reset token and return the user_id, or None if invalid/expired.
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        if payload.get("type") != "password_reset":
            return None
        return payload.get("user_id")
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None


def get_client_ip(request) -> str:
    """Extract client IP address from request META."""
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "0.0.0.0")


def get_user_agent(request) -> str:
    """Extract user agent string from request (truncated to 500 chars)."""
    return request.META.get("HTTP_USER_AGENT", "")[:500]
