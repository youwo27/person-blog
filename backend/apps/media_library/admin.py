"""Django Admin configuration for media_library app."""

from django.contrib import admin
from django.utils.html import format_html

from .models import Media, MediaTag


@admin.register(MediaTag)
class MediaTagAdmin(admin.ModelAdmin):
    """MediaTag admin."""

    list_display = ["name", "slug", "created_at"]
    search_fields = ["name", "slug"]
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Media)
class MediaAdmin(admin.ModelAdmin):
    """Media admin with image preview and metadata display."""

    list_display = [
        "thumbnail_preview",
        "filename",
        "mime_type",
        "file_size_display",
        "dimensions",
        "uploaded_by",
        "created_at",
    ]
    list_filter = ["mime_type", "created_at"]
    search_fields = ["filename", "original_filename", "alt_text"]
    readonly_fields = [
        "filename",
        "original_filename",
        "mime_type",
        "file_size",
        "file_size_display",
        "width",
        "height",
        "preview",
        "created_at",
    ]
    fieldsets = (
        ("File", {"fields": ("file", "alt_text", "uploaded_by")}),
        (
            "Metadata",
            {"fields": ("filename", "original_filename", "mime_type", "file_size_display")},
        ),
        (
            "Image Info",
            {"fields": ("width", "height", "preview")},
        ),
        ("Timestamps", {"fields": ("created_at",)}),
    )

    def thumbnail_preview(self, obj):
        """Small thumbnail preview in list view."""
        if obj.is_image and obj.url:
            return format_html(
                '<img src="{}" style="max-height:50px; max-width:80px; border-radius:4px;" />',
                obj.url,
            )
        return "—"

    thumbnail_preview.short_description = "preview"  # type: ignore[attr-defined]

    def preview(self, obj):
        """Large preview in detail view."""
        if obj.is_image and obj.url:
            return format_html(
                '<img src="{}" style="max-height:400px; max-width:600px; border-radius:6px;" />',
                obj.url,
            )
        return "No preview available"

    preview.short_description = "image preview"  # type: ignore[attr-defined]

    def dimensions(self, obj):
        """Display image dimensions."""
        if obj.width and obj.height:
            return f"{obj.width} × {obj.height}"
        return "—"

    dimensions.short_description = "dimensions"  # type: ignore[attr-defined]
