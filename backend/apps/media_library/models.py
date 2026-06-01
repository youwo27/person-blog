"""
Database models for media_library app.

Models:
- Media: Uploaded files/images with metadata and thumbnail support
- MediaTag: Tags for organizing media files
"""

from django.conf import settings
from django.db import models

from common.utils import generate_uuid_filename


# ═══════════════════════════════════════════════════
# MediaTag Model
# ═══════════════════════════════════════════════════


class MediaTag(models.Model):
    """Tag for organizing and categorizing media files."""

    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="name",
    )
    slug = models.SlugField(
        max_length=120,
        unique=True,
        verbose_name="slug",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="created at",
    )

    class Meta:
        db_table = "media_tag"
        verbose_name = "media tag"
        verbose_name_plural = "media tags"
        ordering = ["name"]

    def __str__(self):
        return self.name


# ═══════════════════════════════════════════════════
# Media Model
# ═══════════════════════════════════════════════════


class Media(models.Model):
    """
    Uploaded file/media with metadata.

    Supports images, documents, and other file types. Images automatically
    capture width/height dimensions on save.
    """

    file = models.FileField(
        upload_to="media/%Y/%m/",
        verbose_name="file",
    )
    filename = models.CharField(
        max_length=255,
        verbose_name="filename",
    )
    original_filename = models.CharField(
        max_length=255,
        verbose_name="original filename",
    )
    mime_type = models.CharField(
        max_length=100,
        verbose_name="MIME type",
    )
    file_size = models.PositiveIntegerField(
        default=0,
        verbose_name="file size (bytes)",
    )
    # Image-specific fields
    width = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="width (px)",
    )
    height = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="height (px)",
    )
    alt_text = models.CharField(
        max_length=500,
        blank=True,
        verbose_name="alt text",
    )
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="uploaded_media",
        verbose_name="uploaded by",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="created at",
    )

    class Meta:
        db_table = "media"
        verbose_name = "media"
        verbose_name_plural = "media"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["uploaded_by", "created_at"]),
            models.Index(fields=["mime_type"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return self.filename

    def save(self, *args, **kwargs):
        """Auto-populate metadata on first save."""
        if not self.filename and self.file:
            self.filename = self.file.name.split("/")[-1]
        if not self.original_filename and self.file:
            self.original_filename = self.file.name.split("/")[-1]
        # Capture image dimensions
        if self.file and not self.width and hasattr(self.file, "image"):
            try:
                self.width = self.file.image.width
                self.height = self.file.image.height
            except Exception:
                pass
        super().save(*args, **kwargs)

    @property
    def is_image(self) -> bool:
        """Check if the media file is an image."""
        return self.mime_type and self.mime_type.startswith("image/")

    @property
    def file_size_display(self) -> str:
        """Human-readable file size."""
        sizes = ["B", "KB", "MB", "GB"]
        size = float(self.file_size)
        for unit in sizes:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"

    @property
    def url(self) -> str:
        """Get the file URL."""
        try:
            return self.file.url
        except Exception:
            return ""
