"""Tests for Media and MediaTag models."""

import pytest
from apps.media_library.models import Media, MediaTag


class TestMediaTag:
    def test_create_tag(self, db):
        tag = MediaTag.objects.create(name="Photos", slug="photos")
        assert tag.name == "Photos"
        assert str(tag) == "Photos"

    def test_tag_slug_unique(self, db):
        MediaTag.objects.create(name="A", slug="a")
        with pytest.raises(Exception):
            MediaTag.objects.create(name="B", slug="a")


class TestMedia:
    def test_create_media(self, db, admin_user):
        media = Media.objects.create(
            filename="photo.jpg", original_filename="DSC001.jpg",
            mime_type="image/jpeg", file_size=2048000,
            width=1920, height=1080, alt_text="A photo",
            uploaded_by=admin_user,
        )
        assert media.filename == "photo.jpg"
        assert media.original_filename == "DSC001.jpg"
        assert media.is_image is True
        assert media.file_size_display == "2.0 MB"

    def test_media_is_image_false_for_pdf(self, db, admin_user):
        media = Media.objects.create(
            filename="doc.pdf", original_filename="doc.pdf",
            mime_type="application/pdf", file_size=512000,
            uploaded_by=admin_user,
        )
        assert media.is_image is False

    def test_file_size_display_bytes(self, db, admin_user):
        media = Media.objects.create(filename="s.jpg", original_filename="s.jpg", mime_type="image/jpeg", file_size=500, uploaded_by=admin_user)
        assert media.file_size_display == "500.0 B"

    def test_file_size_display_kb(self, db, admin_user):
        media = Media.objects.create(filename="s.jpg", original_filename="s.jpg", mime_type="image/jpeg", file_size=50000, uploaded_by=admin_user)
        assert "KB" in media.file_size_display

    def test_file_size_display_gb(self, db, admin_user):
        media = Media.objects.create(filename="s.jpg", original_filename="s.jpg", mime_type="image/jpeg", file_size=3000000000, uploaded_by=admin_user)
        assert "GB" in media.file_size_display

    def test_media_str(self, db, admin_user):
        media = Media.objects.create(filename="photo.jpg", original_filename="original.jpg", mime_type="image/jpeg", file_size=1000, uploaded_by=admin_user)
        assert str(media) == "photo.jpg"

    def test_media_uploaded_by_nullable(self, db):
        media = Media.objects.create(filename="anon.jpg", original_filename="anon.jpg", mime_type="image/jpeg", file_size=1000)
        assert media.uploaded_by is None

    def test_media_thumbnails_default(self, db, admin_user):
        media = Media.objects.create(filename="t.jpg", original_filename="t.jpg", mime_type="image/jpeg", file_size=1000, uploaded_by=admin_user)
        assert media.thumbnails == {}


class TestFileValidators:
    def test_allowed_extensions(self):
        from apps.media_library.validators import ALLOWED_EXTENSIONS
        assert ".jpg" in ALLOWED_EXTENSIONS
        assert ".png" in ALLOWED_EXTENSIONS
        assert ".webp" in ALLOWED_EXTENSIONS
        assert ".exe" not in ALLOWED_EXTENSIONS

    def test_allowed_mimes(self):
        from apps.media_library.validators import ALLOWED_MIMES
        assert "image/jpeg" in ALLOWED_MIMES
        assert "image/png" in ALLOWED_MIMES
        assert "text/html" not in ALLOWED_MIMES

    def test_sanitize_filename(self):
        from apps.media_library.validators import _sanitize_filename
        assert _sanitize_filename("../../../etc/passwd") is not None
        assert _sanitize_filename("normal.jpg") is not None
