"""DRF serializers for comments app."""

from rest_framework import serializers

from .models import Comment, CommentLike


# ═══════════════════════════════════════════════════
# Reusable Serializers
# ═══════════════════════════════════════════════════


class CommentAuthorSerializer(serializers.Serializer):
    """Minimal author info for comment display."""

    id = serializers.IntegerField(read_only=True)
    username = serializers.CharField(read_only=True)
    display_name = serializers.CharField(read_only=True)
    avatar = serializers.ImageField(read_only=True)


# ═══════════════════════════════════════════════════
# Comment Serializers
# ═══════════════════════════════════════════════════


class CommentListSerializer(serializers.ModelSerializer):
    """Lightweight comment for listing — with replies up to 3 levels."""

    author = CommentAuthorSerializer(read_only=True)
    replies = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = [
            "id",
            "post",
            "author",
            "parent",
            "content_html",
            "is_approved",
            "likes_count",
            "created_at",
            "replies",
        ]
        read_only_fields = fields

    def get_replies(self, obj):
        """Return approved replies up to remaining nesting depth."""
        depth = self.context.get("depth", 0)
        if depth >= 2:
            return []
        replies = obj.replies.filter(is_approved=True, is_spam=False).select_related("author")[:10]
        return CommentListSerializer(replies, many=True, context={"depth": depth + 1}).data


class CommentDetailSerializer(serializers.ModelSerializer):
    """Full comment detail."""

    author = CommentAuthorSerializer(read_only=True)
    replies = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = [
            "id",
            "post",
            "author",
            "parent",
            "content_html",
            "is_approved",
            "is_spam",
            "ip_address",
            "likes_count",
            "created_at",
            "updated_at",
            "replies",
        ]
        read_only_fields = fields

    def get_replies(self, obj):
        """Return approved replies up to remaining nesting depth."""
        depth = self.context.get("depth", 1)
        if depth > 3:
            return []
        replies = obj.replies.filter(is_approved=True, is_spam=False).select_related("author")[:10]
        return CommentDetailSerializer(replies, many=True, context={"depth": depth + 1}).data


class CommentCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating comments."""

    post_id = serializers.IntegerField(write_only=True)
    parent_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)

    class Meta:
        model = Comment
        fields = [
            "post_id",
            "parent_id",
            "content",
        ]

    def validate_post_id(self, value):
        from blog.models import Post

        if not Post.objects.filter(id=value).exists():
            raise serializers.ValidationError("Post not found.")
        return value

    def validate_parent_id(self, value):
        if value is not None:
            if not Comment.objects.filter(id=value).exists():
                raise serializers.ValidationError("Parent comment not found.")
        return value

    def create(self, validated_data):
        post_id = validated_data.pop("post_id")
        parent_id = validated_data.pop("parent_id", None)

        # Get request metadata
        request = self.context.get("request")
        ip_address = None
        user_agent = ""
        if request:
            ip_address = self._get_client_ip(request)
            user_agent = request.META.get("HTTP_USER_AGENT", "")[:500]

        comment = Comment.objects.create(
            post_id=post_id,
            parent_id=parent_id,
            author=request.user,
            ip_address=ip_address,
            user_agent=user_agent,
            **validated_data,
        )
        return comment

    @staticmethod
    def _get_client_ip(request):
        """Extract client IP from request."""
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            return x_forwarded_for.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR")


# ═══════════════════════════════════════════════════
# CommentLike Serializers
# ═══════════════════════════════════════════════════


class CommentLikeSerializer(serializers.ModelSerializer):
    """Like/unlike a comment."""

    class Meta:
        model = CommentLike
        fields = ["id", "comment", "user", "created_at"]
        read_only_fields = ["user", "created_at"]
