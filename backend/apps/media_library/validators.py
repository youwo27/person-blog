"""
File upload validators — type whitelist, size limits, MIME detection, dimensions.

Security layers:
1. Extension whitelist (first pass, fast)
2. MIME type detection via python-magic (second pass, reliable)
3. File size limits (images ≤10MB, docs ≤20MB)
4. Image dimension validation (min/max resolution)
5. Filename sanitization
"""

import os
from dataclasses import dataclass

from django.core.exceptions import ValidationError
from django.utils.deconstruct import deconstructible


# ═══════════════════════════════════════════════════
# Configuration
# ═══════════════════════════════════════════════════

ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg"}
ALLOWED_DOC_EXTENSIONS = {".pdf", ".doc", ".docx"}
ALLOWED_EXTENSIONS = ALLOWED_IMAGE_EXTENSIONS | ALLOWED_DOC_EXTENSIONS

ALLOWED_IMAGE_MIMES = {
    "image/jpeg", "image/png", "image/gif", "image/webp",
    "image/svg+xml",
}
ALLOWED_DOC_MIMES = {
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}
ALLOWED_MIMES = ALLOWED_IMAGE_MIMES | ALLOWED_DOC_MIMES

MAX_IMAGE_SIZE = 10 * 1024 * 1024   # 10 MB
MAX_DOC_SIZE = 20 * 1024 * 1024     # 20 MB
MAX_FILE_SIZE = MAX_DOC_SIZE

MIN_IMAGE_DIMENSION = (100, 100)     # min width x height
MAX_IMAGE_DIMENSION = (8000, 8000)   # max width x height


@dataclass
class ValidationResult:
    is_valid: bool
    mime_type: str = ""
    file_size: int = 0
    width: int | None = None
    height: int | None = None
    errors: list[str] = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []


# ═══════════════════════════════════════════════════
# Validation Functions
# ═══════════════════════════════════════════════════

def validate_file_upload(file_obj, user=None) -> ValidationResult:
    """
    Full validation pipeline for uploaded files.

    Returns ValidationResult with metadata on success, errors on failure.
    """
    result = ValidationResult(is_valid=True)

    # 1. Filename sanitization
    safe_name = _sanitize_filename(file_obj.name)
    if not safe_name:
        result.errors.append("Invalid filename.")
        result.is_valid = False
        return result

    # 2. Extension check
    ext = os.path.splitext(safe_name)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        result.errors.append(f"File type '{ext}' is not allowed. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}")
        result.is_valid = False
        return result

    # 3. File size check
    file_obj.seek(0, os.SEEK_END)
    file_size = file_obj.tell()
    file_obj.seek(0)
    result.file_size = file_size

    is_image = ext in ALLOWED_IMAGE_EXTENSIONS
    max_size = MAX_IMAGE_SIZE if is_image else MAX_DOC_SIZE
    if file_size > max_size:
        max_mb = max_size / (1024 * 1024)
        result.errors.append(f"File size {file_size / (1024 * 1024):.1f}MB exceeds limit of {max_mb:.0f}MB.")
        result.is_valid = False
        return result

    # 4. Real MIME type detection
    detected_mime = _detect_mime(file_obj)
    if detected_mime not in ALLOWED_MIMES:
        result.errors.append(f"MIME type '{detected_mime}' is not allowed. Allowed: image/*, application/pdf")
        result.is_valid = False
        return result

    # Extension-MIME mismatch (e.g., .jpg renamed from .exe)
    expected_mime_category = "image" if is_image else "application"
    if not detected_mime.startswith(expected_mime_category):
        result.errors.append(f"File extension '{ext}' does not match detected type '{detected_mime}'.")
        result.is_valid = False
        return result

    result.mime_type = detected_mime

    # 5. Image dimension validation
    if is_image:
        try:
            from PIL import Image as PILImage
            img = PILImage.open(file_obj)
            width, height = img.size
            result.width = width
            result.height = height

            min_w, min_h = MIN_IMAGE_DIMENSION
            max_w, max_h = MAX_IMAGE_DIMENSION
            if width < min_w or height < min_h:
                result.errors.append(f"Image too small. Minimum: {min_w}x{min_h}, got: {width}x{height}")
                result.is_valid = False
            if width > max_w or height > max_h:
                result.errors.append(f"Image too large. Maximum: {max_w}x{max_h}, got: {width}x{height}")
                result.is_valid = False
        except Exception:
            # Not a valid image despite extension
            result.errors.append("File is not a valid image.")
            result.is_valid = False

    file_obj.seek(0)
    return result


def _detect_mime(file_obj) -> str:
    """Detect real MIME type using python-magic (primary) or mimetypes (fallback)."""
    try:
        import magic
        file_obj.seek(0)
        # Read first 2048 bytes for detection
        chunk = file_obj.read(2048)
        file_obj.seek(0)
        mime = magic.from_buffer(chunk, mime=True)
        return mime
    except ImportError:
        import mimetypes
        mime, _ = mimetypes.guess_type(file_obj.name)
        return mime or "application/octet-stream"


def _sanitize_filename(filename: str) -> str:
    """
    Sanitize filename:
    - Remove path separators
    - Remove null bytes
    - Limit length
    - Keep only safe characters
    """
    import re
    # Remove path components
    name = os.path.basename(filename)
    # Remove null bytes
    name = name.replace("\x00", "")
    # Replace dangerous chars
    name = re.sub(r"[^\w.\-() ]", "_", name)
    # Limit length
    if len(name) > 200:
        base, ext = os.path.splitext(name)
        name = base[:200 - len(ext)] + ext
    return name.strip() or None
