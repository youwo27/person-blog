"""
Media library views — upload with security validation + image processing.

Upload pipeline:
1. Validate file (extension, MIME, size, dimensions) via validators.py
2. Save file to storage (local or S3)
3. Process images: generate thumbnails + WebP variants via processors.py
4. Store variant metadata in Media.thumbnails JSON
5. Return full Media object with thumbnail URLs
"""

import os

from django.conf import settings
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response

from common.permissions import IsEditorOrAdmin
from common.throttling import UploadRateThrottle

from .models import Media
from .processors import ImageProcessor
from .serializers import MediaDetailSerializer, MediaListSerializer, MediaUploadSerializer
from .validators import validate_file_upload


@extend_schema_view(
    list=extend_schema(
        summary="List media files",
        description="Paginated media list with thumbnail URLs.",
        parameters=[
            OpenApiParameter(name="mime_type", description="Filter by MIME prefix (e.g. 'image/')"),
            OpenApiParameter(name="search", description="Search by filename"),
            OpenApiParameter(name="ordering", description="-created_at / file_size / filename"),
        ],
    ),
    retrieve=extend_schema(summary="Get media detail", description="Full detail with all thumbnails and WebP variants."),
    destroy=extend_schema(summary="Delete media", description="Delete file + all variants. Editor/Admin only."),
)
class MediaViewSet(viewsets.ModelViewSet):
    """
    Media file management with upload security and image processing.

    Permissions:
    - List / Retrieve: Public read
    - Upload: Authenticated users
    - Delete: Editor / Admin only
    """

    queryset = Media.objects.select_related("uploaded_by").order_by("-created_at")
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["filename", "original_filename", "alt_text"]
    ordering_fields = ["created_at", "file_size", "filename"]
    ordering = ["-created_at"]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_serializer_class(self):
        if self.action == "list":
            return MediaListSerializer
        if self.action == "upload":
            return MediaUploadSerializer
        return MediaDetailSerializer

    def get_permissions(self):
        if self.action in ("create", "upload"):
            return [IsAuthenticated()]
        if self.action in ("destroy",):
            return [IsEditorOrAdmin()]
        return [IsAuthenticatedOrReadOnly()]

    def get_throttles(self):
        if self.action in ("upload", "create"):
            return [UploadRateThrottle()]
        return super().get_throttles()

    # ── Upload (full pipeline) ─────────────────────

    @extend_schema(
        summary="Upload file",
        description=(
            "Upload a file with security validation and automatic image processing.\n\n"
            "**Security checks:**\n"
            "- Extension whitelist: .jpg .png .gif .webp .svg .pdf\n"
            "- MIME type verification via python-magic (not trusting Content-Type)\n"
            "- Size limits: images ≤10MB, documents ≤20MB\n"
            "- Image dimension: 100-8000px\n\n"
            "**Image processing (automatic):**\n"
            "- Thumbnail: 150x150 JPEG (80% quality)\n"
            "- Medium: 768x proportional JPEG (85% quality)\n"
            "- Large: 1920x proportional JPEG (85% quality)\n"
            "- WebP variants of all sizes (85% quality)\n\n"
            "**Storage:** Local FileSystemStorage (dev) or S3/MinIO via django-storages (prod)"
        ),
        request={"multipart/form-data": {"type": "object", "properties": {"file": {"type": "string", "format": "binary"}, "alt_text": {"type": "string"}}}},
        tags=["media"],
    )
    @action(detail=False, methods=["post"], parser_classes=[MultiPartParser, FormParser])
    def upload(self, request):
        """Upload a file with full validation and image processing pipeline."""
        file_obj = request.FILES.get("file")
        if not file_obj:
            return Response(
                {"success": False, "error": {"code": "bad_request", "message": "No file provided."}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ── Step 1: Validation ──────────────────────
        validation = validate_file_upload(file_obj, user=request.user)
        if not validation.is_valid:
            return Response(
                {"success": False, "error": {"code": "bad_request", "message": "; ".join(validation.errors)}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ── Step 2: Save media record ───────────────
        media = Media(
            file=file_obj,
            original_filename=file_obj.name,
            filename=file_obj.name.split("/")[-1],
            mime_type=validation.mime_type,
            file_size=validation.file_size,
            width=validation.width,
            height=validation.height,
            alt_text=request.data.get("alt_text", ""),
            uploaded_by=request.user if request.user.is_authenticated else None,
        )
        media.save()

        # ── Step 3: Image processing ────────────────
        if media.is_image and not media.mime_type == "image/svg+xml":
            try:
                file_path = media.file.path
                processor = ImageProcessor(file_path)
                variants = processor.process()

                # Build thumbnails metadata dict
                thumbs = {}
                for v in variants:
                    # Generate URL for each variant
                    rel_path = os.path.relpath(v["path"], settings.MEDIA_ROOT)
                    variant_url = f"{settings.MEDIA_URL}{rel_path.replace(os.sep, '/')}"
                    thumbs[v["name"]] = {
                        "path": v["path"],
                        "url": variant_url,
                        "width": v["width"],
                        "height": v["height"],
                        "format": v["format"],
                        "file_size": v["file_size"],
                    }

                media.thumbnails = thumbs
                media.save(update_fields=["thumbnails"])
            except Exception as exc:
                # Image processing failed but upload succeeded — log and continue
                pass

        detail = MediaDetailSerializer(media, context={"request": request})
        return Response({"success": True, "data": detail.data}, status=status.HTTP_201_CREATED)

    # ── CRUD ───────────────────────────────────────

    def destroy(self, request, *args, **kwargs):
        """Delete media file + all generated variants."""
        instance = self.get_object()

        # Delete variant files
        if instance.thumbnails:
            for variant in instance.thumbnails.values():
                variant_path = variant.get("path", "")
                if variant_path and os.path.isfile(variant_path):
                    try:
                        os.remove(variant_path)
                    except OSError:
                        pass

        # Delete original file
        if instance.file:
            try:
                file_path = instance.file.path
                if os.path.isfile(file_path):
                    os.remove(file_path)
            except Exception:
                pass

        instance.delete()
        return Response({"success": True, "message": "Media deleted."})

    @extend_schema(summary="My uploads", description="Media files uploaded by the current user.")
    @action(detail=False, methods=["get"])
    def my_uploads(self, request):
        if not request.user.is_authenticated:
            return Response(
                {"success": False, "error": {"code": "authentication_failed", "message": "Authentication required."}},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        media = self.get_queryset().filter(uploaded_by=request.user)
        page = self.paginate_queryset(media)
        if page is not None:
            serializer = MediaListSerializer(page, many=True, context={"request": request})
            return self.get_paginated_response(serializer.data)

        serializer = MediaListSerializer(media, many=True, context={"request": request})
        return Response({"success": True, "results": serializer.data})
