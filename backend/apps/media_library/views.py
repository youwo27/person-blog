"""
DRF ViewSets for media_library app.

Endpoints:
- /api/v1/media/            Media list (paginated, filterable)
- /api/v1/media/{id}/       Media detail
- /api/v1/media/upload/     Upload file (POST)
"""

from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response

from common.permissions import IsEditorOrAdmin
from common.throttling import UploadRateThrottle

from .models import Media
from .serializers import MediaDetailSerializer, MediaListSerializer, MediaUploadSerializer


@extend_schema_view(
    list=extend_schema(
        summary="List media files",
        description="Return paginated list of uploaded media files.",
        parameters=[
            OpenApiParameter(name="mime_type", description="Filter by MIME type prefix (e.g. 'image/')"),
            OpenApiParameter(name="search", description="Search by filename"),
            OpenApiParameter(name="ordering", description="Sort: -created_at, file_size"),
        ],
    ),
    retrieve=extend_schema(summary="Get media detail"),
    destroy=extend_schema(summary="Delete media file", description="Delete a media file. Editor/Admin only."),
)
class MediaViewSet(viewsets.ModelViewSet):
    """
    Media file management.

    - List: Public read
    - Upload: Authenticated users
    - Delete: Editor/Admin only
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

    @extend_schema(
        summary="Upload file",
        description="Upload a single file. Supported: images (jpg, png, gif, webp), documents (pdf). Max 10MB for images, 20MB for other files.",
        request={"multipart/form-data": {"type": "object", "properties": {"file": {"type": "string", "format": "binary"}, "alt_text": {"type": "string"}}}},
    )
    @action(detail=False, methods=["post"], parser_classes=[MultiPartParser, FormParser])
    def upload(self, request):
        """Upload a single file."""
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response({"success": False, "error": {"code": "bad_request", "message": str(serializer.errors)}}, status=status.HTTP_400_BAD_REQUEST)

        media = serializer.save()

        # Return detail view of the uploaded file
        detail_serializer = MediaDetailSerializer(media, context={"request": request})
        return Response({"success": True, "data": detail_serializer.data}, status=status.HTTP_201_CREATED)

    @extend_schema(summary="My uploads", description="Return media uploaded by the current user.")
    @action(detail=False, methods=["get"])
    def my_uploads(self, request):
        """Media uploaded by the current user."""
        if not request.user.is_authenticated:
            return Response({"success": False, "error": {"code": "authentication_failed", "message": "Authentication required."}}, status=status.HTTP_401_UNAUTHORIZED)

        media = self.get_queryset().filter(uploaded_by=request.user)
        page = self.paginate_queryset(media)
        if page is not None:
            serializer = MediaListSerializer(page, many=True, context={"request": request})
            return self.get_paginated_response(serializer.data)

        serializer = MediaListSerializer(media, many=True, context={"request": request})
        return Response({"success": True, "results": serializer.data})
