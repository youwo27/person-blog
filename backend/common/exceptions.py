"""Custom DRF exception handler with uniform error response format.

All API errors are wrapped as:
{
    "success": false,
    "error": {
        "code": "authentication_failed",
        "message": "Authentication credentials were not provided.",
        "details": {...}
    }
}
"""

from rest_framework.views import exception_handler


def custom_exception_handler(exc, context):
    """
    Wrap all DRF exceptions in a uniform {success, error} envelope.

    Falls back to DRF's built-in exception_handler for the initial response,
    then rewraps the data.
    """
    response = exception_handler(exc, context)

    if response is not None:
        # Build uniform error envelope
        error_data = {
            "success": False,
            "error": {
                "code": _get_error_code(exc, response.status_code),
                "message": _get_error_message(exc, response),
            },
        }

        # Include field-level detail for validation errors
        if hasattr(exc, "detail") and isinstance(exc.detail, dict):
            error_data["error"]["details"] = exc.detail

        response.data = error_data

    return response


def _get_error_code(exc, status_code: int) -> str:
    """Map HTTP status code to a machine-readable error code."""
    codes = {
        400: "bad_request",
        401: "authentication_failed",
        403: "permission_denied",
        404: "not_found",
        405: "method_not_allowed",
        406: "not_acceptable",
        409: "conflict",
        410: "gone",
        415: "unsupported_media_type",
        422: "unprocessable_entity",
        429: "throttled",
        500: "internal_error",
    }
    return codes.get(status_code, "error")


def _get_error_message(exc, response) -> str:
    """Extract a human-readable error message from the exception."""
    if hasattr(exc, "detail"):
        detail = exc.detail
        if isinstance(detail, str):
            return detail
        if isinstance(detail, list) and len(detail) > 0:
            return str(detail[0])
        if isinstance(detail, dict):
            # Return first field error message
            for key, value in detail.items():
                if isinstance(value, list):
                    return f"{key}: {value[0]}"
                return f"{key}: {value}"
        return str(detail)
    return str(exc)
