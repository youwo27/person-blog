"""
DRF ViewSets for comments app.

Endpoints:
- /api/v1/comments/                   Comment list (all approved)
- /api/v1/comments/{id}/              Comment detail
- /api/v1/posts/{slug}/comments/      Comments for a specific post (nested)
"""

from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response

from common.permissions import CanManageComments, IsOwnerOrAdmin
from common.throttling import CommentRateThrottle

from .models import Comment, CommentLike
from .serializers import CommentCreateSerializer, CommentDetailSerializer, CommentListSerializer


@extend_schema_view(
    list=extend_schema(summary="List comments", description="Return paginated list of approved comments."),
    retrieve=extend_schema(summary="Get comment detail", description="Return full comment with nested replies."),
    create=extend_schema(summary="Create comment", description="Create a new comment on a post. Requires authentication."),
    destroy=extend_schema(summary="Delete comment", description="Soft-delete comment. Owner or admin only."),
)
class CommentViewSet(viewsets.ModelViewSet):
    """
    Comment CRUD — nested under posts.

    - List: Public (approved, non-spam only for anon)
    - Create: Authenticated users
    - Update/Delete: Owner or admin
    """

    lookup_field = "id"
    filter_backends = [OrderingFilter]
    ordering_fields = ["created_at", "likes_count"]
    ordering = ["created_at"]

    def get_serializer_class(self):
        if self.action == "list":
            return CommentListSerializer
        if self.action == "create":
            return CommentCreateSerializer
        return CommentDetailSerializer

    def get_queryset(self):
        """Return approved comments; staff sees all."""
        qs = Comment.objects.select_related("author", "parent").prefetch_related("replies__author")
        if not self.request.user.is_staff:
            qs = qs.filter(is_approved=True, is_spam=False)
        return qs

    def get_permissions(self):
        if self.action in ("create",):
            return [IsAuthenticated()]
        if self.action in ("update", "partial_update", "destroy"):
            return [IsOwnerOrAdmin()]
        return [IsAuthenticatedOrReadOnly()]

    def get_throttles(self):
        if self.action == "create":
            return [CommentRateThrottle()]
        return super().get_throttles()

    @extend_schema(summary="Toggle like", description="Like or unlike a comment. Requires authentication.")
    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def like(self, request, id=None):
        """Toggle like/unlike on a comment."""
        comment = self.get_object()
        like, created = CommentLike.objects.get_or_create(comment=comment, user=request.user)

        if not created:
            # User already liked → unlike
            like.delete()
            comment.likes_count = max(0, comment.likes_count - 1)
            comment.save(update_fields=["likes_count"])
            return Response({"success": True, "liked": False, "likes_count": comment.likes_count})

        # New like
        comment.likes_count += 1
        comment.save(update_fields=["likes_count"])
        return Response({"success": True, "liked": True, "likes_count": comment.likes_count})

    @extend_schema(summary="Approve comment", description="Approve a pending comment. Moderator only.")
    @action(detail=True, methods=["post"], permission_classes=[CanManageComments])
    def approve(self, request, id=None):
        """Approve a pending comment."""
        comment = self.get_object()
        comment.approve()
        return Response({"success": True, "message": "Comment approved."})

    @extend_schema(summary="Mark as spam", description="Mark a comment as spam. Moderator only.")
    @action(detail=True, methods=["post"], permission_classes=[CanManageComments])
    def spam(self, request, id=None):
        """Mark a comment as spam."""
        comment = self.get_object()
        comment.mark_spam()
        return Response({"success": True, "message": "Comment marked as spam."})
