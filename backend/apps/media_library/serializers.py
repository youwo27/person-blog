"""DRF serializers for media_library app."""

from rest_framework import serializers

from .models import Media, MediaTag


# ═══════════════════════════════════════════════════
# MediaTag Serializers
# ═══════════════════════════════════════════════════


class MediaTagSerializer(serializers.ModelSerializer):
    """MediaTag CRUD serializer."""

    class Meta:
        model = MediaTag
        fields = ["id", "name", "slug", "created_at"]
        read_only_fields = ["created_at"]


# ═══════════════════════════════════════════════════
# Media Serializers
# ═══════════════════════════════════════════════════


class MediaListSerializer(serializers.ModelSerializer):
    """Lightweight media list — for media library browsing."""

    uploaded_by_username = serializers.CharField(source="uploaded_by.username", read_only=True)
    file_size_display = serializers.CharField(read_only=True)
    is_image = serializers.BooleanField(read_only=True)

    class Meta:
        model = Media
        fields = [
            "id",
            "url",
            "filename",
            "original_filename",
            "mime_type",
            "file_size_display",
            "width",
            "height",
            "is_image",
            "alt_text",
            "uploaded_by_username",
            "created_at",
        ]


class MediaDetailSerializer(serializers.ModelSerializer):
    """Full media detail."""

    uploaded_by_username = serializers.CharField(source="uploaded_by.username", read_only=True)
    file_size_display = serializers.CharField(read_only=True)
    is_image = serializers.BooleanField(read_only=True)
    dimensions = serializers.CharField(read_only=True)

    class Meta:
        model = Media
        fields = [
            "id",
            "url",
            "file",
            "filename",
            "original_filename",
            "mime_type",
            "file_size",
            "file_size_display",
            "width",
            "height",
            "dimensions",
            "is_image",
            "alt_text",
            "uploaded_by",
            "uploaded_by_username",
            "created_at",
        ]
        read_only_fields = [
            "filename",
            "mime_type",
            "file_size",
            "width",
            "height",
            "created_at",
        ]


class MediaUploadSerializer(serializers.ModelSerializer):
    """File upload serializer — accepts file + optional alt_text."""

    class Meta:
        model = Media
        fields = ["file", "alt_text"]

    def create(self, validated_data):
        file_obj = validated_data.get("file")
        # Auto-populate metadata from the file
        validated_data["original_filename"] = file_obj.name
        validated_data["filename"] = file_obj.name.split("/")[-1]
        validated_data["file_size"] = file_obj.size

        # Guess MIME type
        import mimetypes

        mime_type, _ = mimetypes.guess_type(file_obj.name)
        validated_data["mime_type"] = mime_type or "application/octet-stream"

        # Set uploader from request
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            validated_data["uploaded_by"] = request.user

        media = Media.objects.create(**validated_data)

        # Detect image dimensions
        if media.is_image:
            try:
                from PIL import Image as PILImage

                img = PILImage.open(media.file.path)
                media.width = img.width
                media.height = img.height
                media.save(update_fields=["width", "height"])
            except Exception:
                pass

        return media
