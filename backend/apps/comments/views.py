"""
DRF ViewSet for comments — nested comments, spam detection, like, approve.

Spam detection: Auto-flags comments with >2 links, blacklisted keywords,
excessive caps, or suspicious patterns. New users (<24h) get stricter filtering.
"""

from django.utils import timezone
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response

from common.permissions import CanManageComments, IsOwnerOrAdmin
from common.throttling import CommentRateThrottle

from .models import Comment, CommentLike
from .serializers import CommentCreateSerializer, CommentDetailSerializer, CommentListSerializer
from .spam_detector import detect_spam, is_probable_spam
from .tasks import notify_comment_approved, notify_comment_reply, notify_post_author


@extend_schema_view(
    list=extend_schema(summary="List comments", description="Return approved comments, newest first."),
    retrieve=extend_schema(summary="Get comment", description="Full comment with nested replies (3 levels)."),
    create=extend_schema(summary="Create comment", description="Add a comment. Auto-detects spam. Requires authentication."),
    destroy=extend_schema(summary="Delete comment", description="Delete comment. Owner or admin only."),
)
class CommentViewSet(viewsets.ModelViewSet):
    """
    Comment CRUD with spam detection and email notifications.

    - List: Public (approved, non-spam)
    - Create: Authenticated users (auto spam check)
    - Update/Delete: Owner or admin
    - Like: Authenticated users
    - Approve/Spam: Editor/Admin
    """

    filter_backends = [OrderingFilter]
    ordering_fields = ["created_at", "likes_count"]
    ordering = ["-created_at"]

    def get_serializer_class(self):
        if self.action == "list":
            return CommentListSerializer
        if self.action == "create":
            return CommentCreateSerializer
        return CommentDetailSerializer

    def get_queryset(self):
        qs = Comment.objects.select_related("author", "parent").prefetch_related("replies__author")

        # Staff sees all comments including spam
        if self.request.user.is_staff:
            # Filter by post if query param present
            post_id = self.request.query_params.get("post")
            if post_id:
                qs = qs.filter(post_id=post_id)
            return qs

        # Public: only approved, non-spam
        qs = qs.filter(is_approved=True, is_spam=False)
        post_id = self.request.query_params.get("post")
        if post_id:
            qs = qs.filter(post_id=post_id)

        # Top-level only for list
        if self.action == "list":
            qs = qs.filter(parent__isnull=True)

        return qs

    def get_permissions(self):
        if self.action == "create":
            return [IsAuthenticated()]
        if self.action in ("update", "partial_update", "destroy"):
            return [IsOwnerOrAdmin()]
        return [IsAuthenticatedOrReadOnly()]

    def get_throttles(self):
        if self.action == "create":
            return [CommentRateThrottle()]
        return super().get_throttles()

    # ── Create (with spam detection) ──────────────

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"success": False, "error": {"code": "bad_request", "message": str(serializer.errors)}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        comment = serializer.save()

        # ── Spam Detection ─────────────────────────
        user_is_new = (timezone.now() - request.user.date_joined).total_seconds() < 86400
        auto_approve = True

        if is_probable_spam(comment.content, user_is_new=user_is_new):
            comment.is_approved = False
            comment.is_spam = True
            auto_approve = False
            comment.save(update_fields=["is_approved", "is_spam"])
        elif request.user.is_staff:
            # Staff comments auto-approved
            comment.is_approved = True
            comment.save(update_fields=["is_approved"])
        # else: leave default is_approved=False (awaiting moderation)

        # ── Notifications ──────────────────────────
        if auto_approve:
            # Notify post author (unless commenter is the author)
            self._trigger_notifications(comment)

        return Response(
            {
                "success": True,
                "data": CommentDetailSerializer(comment, context={"request": request}).data,
                "spam_flagged": comment.is_spam,
                "message": "Comment submitted for review." if not comment.is_approved and not comment.is_spam else None,
            },
            status=status.HTTP_201_CREATED,
        )

    def _trigger_notifications(self, comment: Comment):
        """Fire async notification tasks."""
        # 1. Notify post author (Celery)
        try:
            notify_post_author.delay(comment.id)
        except Exception:
            pass

        # 2. Notify parent comment author if this is a reply
        if comment.parent:
            try:
                notify_comment_reply.delay(comment.id)
            except Exception:
                pass

        # 3. Create in-app notification for post author
        if comment.post.author_id != comment.author_id:
            from apps.notifications.models import Notification
            from django.contrib.contenttypes.models import ContentType

            comment_ct = ContentType.objects.get_for_model(Comment)
            Notification.objects.create(
                recipient=comment.post.author,
                actor=comment.author,
                type=Notification.Type.POST_COMMENT,
                message=f"{comment.author.display_name} 评论了你的文章《{comment.post.title}》",
                content_type=comment_ct,
                object_id=comment.id,
            )

        # 4. In-app notification for parent comment author (if reply)
        if comment.parent and comment.parent.author_id != comment.author_id:
            from apps.notifications.models import Notification
            from django.contrib.contenttypes.models import ContentType

            comment_ct = ContentType.objects.get_for_model(Comment)
            Notification.objects.create(
                recipient=comment.parent.author,
                actor=comment.author,
                type=Notification.Type.COMMENT_REPLY,
                message=f"{comment.author.display_name} 回复了你的评论",
                content_type=comment_ct,
                object_id=comment.id,
            )

    # ── Like / Unlike ─────────────────────────────

    @extend_schema(summary="Toggle like", description="Like or unlike a comment. Requires authentication.")
    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def like(self, request, pk=None):
        comment = self.get_object()
        like, created = CommentLike.objects.get_or_create(comment=comment, user=request.user)

        if not created:
            like.delete()
            comment.likes_count = max(0, comment.likes_count - 1)
            comment.save(update_fields=["likes_count"])
            return Response({"success": True, "liked": False, "likes_count": comment.likes_count})

        comment.likes_count += 1
        comment.save(update_fields=["likes_count"])
        return Response({"success": True, "liked": True, "likes_count": comment.likes_count})

    # ── Moderation ────────────────────────────────

    @extend_schema(summary="Approve comment", description="Approve a pending comment. Sends notification to author.")
    @action(detail=True, methods=["post"], permission_classes=[CanManageComments])
    def approve(self, request, pk=None):
        comment = self.get_object()
        was_pending = not comment.is_approved

        comment.approve()

        # Send approval notification
        if was_pending:
            try:
                notify_comment_approved.delay(comment.id)
            except Exception:
                pass

            # Also trigger post author + reply notifications now
            self._trigger_notifications(comment)

        return Response({"success": True, "message": "Comment approved."})

    @extend_schema(summary="Mark as spam", description="Mark a comment as spam. Moderator only.")
    @action(detail=True, methods=["post"], permission_classes=[CanManageComments])
    def spam(self, request, pk=None):
        comment = self.get_object()
        comment.mark_spam()
        return Response({"success": True, "message": "Comment marked as spam."})
