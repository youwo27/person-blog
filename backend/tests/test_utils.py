"""Tests for common/utils.py — slug, cache key, reading time, sanitize, etc."""

import pytest
from common.utils import (
    estimate_reading_time,
    generate_cache_key,
    generate_slug_from_title,
    generate_uuid_filename,
    mask_sensitive_data,
    truncate_html,
)


class TestGenerateUuidFilename:
    def test_preserves_extension(self):
        result = generate_uuid_filename("photo.jpg")
        assert result.endswith(".jpg")
        assert len(result) == 36  # 32 hex + dot + 3 ext = 36

    def test_no_extension(self):
        result = generate_uuid_filename("noextension")
        assert "." not in result
        assert len(result) == 32

    def test_multi_dot_filename(self):
        result = generate_uuid_filename("archive.tar.gz")
        assert result.endswith(".gz")


class TestGenerateCacheKey:
    def test_deterministic(self):
        key1 = generate_cache_key("blog", "post", "hello-world")
        key2 = generate_cache_key("blog", "post", "hello-world")
        assert key1 == key2
        assert len(key1) == 32  # MD5 hex

    def test_different_inputs(self):
        key1 = generate_cache_key("blog", "post", "a")
        key2 = generate_cache_key("blog", "post", "b")
        assert key1 != key2


class TestTruncateHtml:
    def test_short_content_unchanged(self):
        result = truncate_html("Hello", length=200)
        assert result == "Hello"

    def test_long_content_truncated(self):
        result = truncate_html("A" * 500, length=200)
        assert len(result) <= 203  # 200 + "..."
        assert result.endswith("...")

    def test_html_tags_stripped(self):
        result = truncate_html("<p>Hello <b>World</b></p>", length=200)
        assert "<p>" not in result
        assert result == "Hello World"


class TestEstimateReadingTime:
    def test_english_text(self):
        words = "word " * 300
        result = estimate_reading_time(words)
        assert result == 1  # 300 words / 300 wpm

    def test_long_text(self):
        words = "word " * 900
        result = estimate_reading_time(words)
        assert result == 3

    def test_minimum_one_minute(self):
        result = estimate_reading_time("hi")
        assert result == 1

    def test_chinese_text(self):
        # Chinese: character-based counting
        result = estimate_reading_time("你好世界" * 100)
        assert result >= 1

    def test_html_tags_ignored(self):
        result = estimate_reading_time("<p>word " * 300 + "</p>")
        assert result == 1


class TestGenerateSlugFromTitle:
    def test_english_title(self):
        slug = generate_slug_from_title("Hello World Post")
        assert slug == "hello-world-post"

    def test_chinese_title(self):
        slug = generate_slug_from_title("你好世界")
        assert slug.startswith("post-")
        assert len(slug) == 13  # post- + 8 hex

    def test_mixed_title(self):
        slug = generate_slug_from_title("Python 入门指南")
        assert len(slug) > 0


class TestMaskSensitiveData:
    def test_masks_password(self):
        data = {"username": "admin", "password": "secret123", "email": "a@b.com"}
        result = mask_sensitive_data(data)
        assert result["username"] == "admin"
        assert result["password"] == "[REDACTED]"
        assert result["email"] == "a@b.com"

    def test_masks_token(self):
        data = {"access_token": "eyJhbGciOi...", "name": "test"}
        result = mask_sensitive_data(data)
        assert result["access_token"] == "[REDACTED]"
        assert result["name"] == "test"

    def test_masks_nested(self):
        data = {"user": {"password": "nested_secret", "name": "test"}}
        result = mask_sensitive_data(data)
        assert result["user"]["password"] == "[REDACTED]"

    def test_custom_fields(self):
        data = {"api_key": "sk-12345", "name": "test"}
        result = mask_sensitive_data(data, fields={"api_key"})
        assert result["api_key"] == "[REDACTED]"
