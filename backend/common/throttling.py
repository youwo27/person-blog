"""Custom throttling classes for different API endpoints."""

from rest_framework.throttling import AnonRateThrottle, ScopedRateThrottle, UserRateThrottle


class LoginRateThrottle(AnonRateThrottle):
    """Throttle for login endpoint: 5 requests per minute per IP."""

    scope = "login"


class RegisterRateThrottle(AnonRateThrottle):
    """Throttle for registration endpoint: 3 requests per hour per IP."""

    scope = "register"


class CommentRateThrottle(UserRateThrottle):
    """Throttle for comment creation: 20 requests per minute per authenticated user."""

    scope = "comment"


class UploadRateThrottle(UserRateThrottle):
    """Throttle for file upload: 50 requests per day per authenticated user."""

    scope = "upload"
    rate = "50/day"
