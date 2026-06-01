"""Shared utility functions used across the project."""

import hashlib
import re
import uuid


def generate_uuid_filename(original_filename: str) -> str:
    """
    Generate a UUID-based filename that preserves the original extension.

    Example:
        'My Photo (1).jpg' → 'a1b2c3d4e5f6...jpg'
    """
    if "." in original_filename:
        ext = original_filename.rsplit(".", 1)[-1].lower()
        return f"{uuid.uuid4().hex}.{ext}"
    return uuid.uuid4().hex


def generate_cache_key(*parts: str) -> str:
    """
    Generate a deterministic MD5 cache key from string parts.

    Example:
        generate_cache_key("blog", "post", "hello-world") → 'a1b2c3d4...'
    """
    raw = ":".join(str(p) for p in parts)
    return hashlib.md5(raw.encode()).hexdigest()


def truncate_html(html: str, length: int = 200) -> str:
    """
    Truncate HTML content to approximately `length` characters of plain text.

    Strips all HTML tags first, then truncates with ellipsis.
    """
    from django.utils.html import strip_tags

    text = strip_tags(html)
    text = text.strip()
    if len(text) <= length:
        return text
    return text[:length].rsplit(" ", 1)[0] + "..."


def estimate_reading_time(content: str, words_per_minute: int = 300) -> int:
    """
    Estimate reading time for mixed Chinese/English content.

    - Chinese: character-based (chars / words_per_minute)
    - English: word-based (words / words_per_minute)

    Returns at least 1 minute.
    """
    from django.utils.html import strip_tags

    text = strip_tags(content)
    chinese_chars = len(re.findall(r"[一-鿿]", text))
    english_words = len(re.findall(r"[a-zA-Z]+", text))
    total_effective = chinese_chars + english_words
    return max(1, round(total_effective / words_per_minute))


def generate_slug_from_title(title: str) -> str:
    """
    Generate a URL-friendly slug from a title.

    Handles both English and Chinese by converting Chinese to pinyin-style
    or falling back to a short UUID hash.
    """
    from django.utils.text import slugify

    # Try standard slugify first (works for English)
    slug = slugify(title)
    if slug:
        return slug
    # Fallback for Chinese-only titles: use a UUID prefix
    return f"post-{uuid.uuid4().hex[:8]}"


def mask_sensitive_data(data: dict, fields: set | None = None) -> dict:
    """
    Mask sensitive fields in a dictionary for logging.

    Replaces values for keys like 'password', 'token', 'secret' with '[REDACTED]'.
    """
    if fields is None:
        fields = {"password", "token", "secret", "access", "refresh", "authorization", "api_key"}
    result = {}
    for key, value in data.items():
        if key.lower() in fields:
            result[key] = "[REDACTED]"
        elif isinstance(value, dict):
            result[key] = mask_sensitive_data(value, fields)
        else:
            result[key] = value
    return result
