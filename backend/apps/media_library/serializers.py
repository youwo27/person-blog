"""DRF serializers for media_library app."""

from rest_framework import serializers

from .models import Media, MediaTag


class MediaTagSerializer(serializers.ModelSerializer):
    """MediaTag CRUD serializer."""

    class Meta:
        model = MediaTag
        fields = ["id", "name", "slug", "created_at"]
        read_only_fields = ["created_at"]


class MediaListSerializer(serializers.ModelSerializer):
    """Lightweight list — with thumbnail URLs."""

    uploaded_by_username = serializers.CharField(source="uploaded_by.username", read_only=True)
    file_size_display = serializers.CharField(read_only=True)
    is_image = serializers.BooleanField(read_only=True)
    thumbnail_url = serializers.SerializerMethodField()

    class Meta:
        model = Media
        fields = [
            "id", "url", "thumbnail_url",
            "filename", "original_filename", "mime_type",
            "file_size_display", "width", "height",
            "is_image", "alt_text",
            "uploaded_by_username", "created_at",
        ]

    def get_thumbnail_url(self, obj):
        if obj.thumbnails and "thumbnail" in obj.thumbnails:
            thumb = obj.thumbnails["thumbnail"]
            path = thumb.get("path", "")
            if path:
                # Convert absolute path to relative URL
                import os
                from django.conf import settings
                try:
                    rel = os.path.relpath(path, settings.MEDIA_ROOT)
                    return f"{settings.MEDIA_URL}{rel.replace(os.sep, '/')}"
                except Exception:
                    return ""
        return obj.url or ""


class MediaDetailSerializer(serializers.ModelSerializer):
    """Full detail — with all thumbnails and WebP variants."""

    uploaded_by_username = serializers.CharField(source="uploaded_by.username", read_only=True)
    file_size_display = serializers.CharField(read_only=True)
    is_image = serializers.BooleanField(read_only=True)
    thumbnail_url = serializers.SerializerMethodField()

    class Meta:
        model = Media
        fields = [
            "id", "url", "file",
            "filename", "original_filename", "mime_type",
            "file_size", "file_size_display",
            "width", "height",
            "is_image", "alt_text",
            "thumbnails", "thumbnail_url",
            "uploaded_by", "uploaded_by_username",
            "created_at",
        ]
        read_only_fields = [
            "filename", "mime_type", "file_size",
            "width", "height", "thumbnails", "created_at",
        ]

    def get_thumbnail_url(self, obj):
        if obj.thumbnails and "thumbnail" in obj.thumbnails:
            return obj.thumbnails["thumbnail"].get("url", "")
        return obj.url or ""


class MediaUploadSerializer(serializers.ModelSerializer):
    """File upload — validates then delegates to the upload pipeline."""

    class Meta:
        model = Media
        fields = ["file", "alt_text"]
