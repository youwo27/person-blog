"""
DRF serializers for blog app.

Pattern:
- ListSerializer: lightweight fields for list endpoints
- DetailSerializer: full nested data for detail endpoints
- CreateUpdateSerializer: write-only fields for mutations
"""

from rest_framework import serializers

from apps.media_library.models import Media

from .models import Category, Post, SiteSetting, Tag


# ═══════════════════════════════════════════════════
# Reusable Nested Serializers
# ═══════════════════════════════════════════════════


class AuthorBriefSerializer(serializers.Serializer):
    """Minimal author info embedded in post responses."""

    id = serializers.IntegerField(read_only=True)
    username = serializers.CharField(read_only=True)
    display_name = serializers.CharField(read_only=True)
    avatar_url = serializers.SerializerMethodField()
    role = serializers.CharField(read_only=True)

    def get_avatar_url(self, obj):
        try:
            return obj.avatar.url if obj.avatar else ""
        except Exception:
            return ""


class CategoryBriefSerializer(serializers.ModelSerializer):
    """Minimal category info for post listing."""

    class Meta:
        model = Category
        fields = ["id", "name", "slug"]


class CategoryTreeSerializer(serializers.ModelSerializer):
    """Recursive category tree — for category list endpoint."""

    children = serializers.SerializerMethodField()
    post_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Category
        fields = ["id", "name", "slug", "description", "order", "is_active", "post_count", "children"]

    def get_children(self, obj):
        children = obj.children_active.all()
        if children.exists():
            return CategoryTreeSerializer(children, many=True).data
        return []


class TagBriefSerializer(serializers.ModelSerializer):
    """Minimal tag info for post listing."""

    post_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Tag
        fields = ["id", "name", "slug", "post_count"]


# ═══════════════════════════════════════════════════
# Post Serializers
# ═══════════════════════════════════════════════════


class PostListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for post list endpoint."""

    author = AuthorBriefSerializer(read_only=True)
    category = CategoryBriefSerializer(read_only=True)
    tags = TagBriefSerializer(many=True, read_only=True)
    cover_image_url = serializers.CharField(read_only=True)

    class Meta:
        model = Post
        fields = [
            "id",
            "title",
            "slug",
            "excerpt",
            "cover_image_url",
            "author",
            "category",
            "tags",
            "status",
            "is_featured",
            "view_count",
            "reading_time_minutes",
            "published_at",
            "created_at",
        ]
        read_only_fields = fields


class PostDetailSerializer(serializers.ModelSerializer):
    """Full post detail including raw content, SEO, and navigation."""

    author = AuthorBriefSerializer(read_only=True)
    category = CategoryBriefSerializer(read_only=True)
    tags = TagBriefSerializer(many=True, read_only=True)
    cover_image_url = serializers.CharField(read_only=True)
    comment_count = serializers.IntegerField(read_only=True)
    prev_post = serializers.SerializerMethodField()
    next_post = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = [
            "id",
            "title",
            "slug",
            "content",
            "content_html",
            "excerpt",
            "cover_image_url",
            "author",
            "category",
            "tags",
            "status",
            "is_featured",
            "view_count",
            "reading_time_minutes",
            "published_at",
            "scheduled_at",
            "meta_title",
            "meta_description",
            "comment_count",
            "prev_post",
            "next_post",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields

    def get_prev_post(self, obj):
        prev = obj.prev_post
        if prev:
            return {"id": prev.id, "title": prev.title, "slug": prev.slug}
        return None

    def get_next_post(self, obj):
        nxt = obj.next_post
        if nxt:
            return {"id": nxt.id, "title": nxt.title, "slug": nxt.slug}
        return None


class PostCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating posts.

    - category_id / tag_ids / cover_image_id: write-only FK/M2M fields
    - Auto-generates slug and content_html in model save()
    """

    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.filter(is_active=True),
        source="category",
        write_only=True,
        required=False,
        allow_null=True,
    )
    tag_ids = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        source="tags",
        many=True,
        write_only=True,
        required=False,
    )
    cover_image_id = serializers.PrimaryKeyRelatedField(
        queryset=Media.objects.all(),
        source="cover_image",
        write_only=True,
        required=False,
        allow_null=True,
    )

    class Meta:
        model = Post
        fields = [
            "title",
            "slug",
            "content",
            "excerpt",
            "category_id",
            "tag_ids",
            "cover_image_id",
            "status",
            "is_featured",
            "scheduled_at",
            "meta_title",
            "meta_description",
        ]
        extra_kwargs = {
            "slug": {"required": False},
        }

    def validate_title(self, value):
        if not value.strip():
            raise serializers.ValidationError("Title cannot be empty.")
        return value.strip()

    def validate_content(self, value):
        if not value.strip():
            raise serializers.ValidationError("Content cannot be empty.")
        return value

    def validate(self, data):
        """Validate business rules."""
        status = data.get("status", self.instance.status if self.instance else Post.Status.DRAFT)
        scheduled_at = data.get("scheduled_at")

        # Scheduled posts must have a future date
        if status == Post.Status.SCHEDULED:
            if not scheduled_at and (not self.instance or not self.instance.scheduled_at):
                raise serializers.ValidationError(
                    {"scheduled_at": "Scheduled posts must have a scheduled_at date in the future."}
                )

        # Prevent changing status to PUBLISHED if slug already exists as published
        if status == Post.Status.PUBLISHED:
            slug = data.get("slug", self.instance.slug if self.instance else None)
            if slug:
                existing = Post.objects.filter(slug=slug, status=Post.Status.PUBLISHED)
                if self.instance:
                    existing = existing.exclude(pk=self.instance.pk)
                if existing.exists():
                    raise serializers.ValidationError(
                        {"slug": "A published post with this slug already exists."}
                    )

        return data


# ═══════════════════════════════════════════════════
# Category Serializers
# ═══════════════════════════════════════════════════


class CategorySerializer(serializers.ModelSerializer):
    """Category create/update — flat representation."""

    parent_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.filter(is_active=True),
        source="parent",
        write_only=True,
        required=False,
        allow_null=True,
    )
    post_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Category
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "parent",
            "parent_id",
            "order",
            "is_active",
            "post_count",
            "created_at",
        ]
        read_only_fields = ["id", "created_at", "post_count"]
        extra_kwargs = {
            "slug": {"required": False},
        }

    def validate(self, data):
        """Prevent a category from being its own parent."""
        if self.instance and data.get("parent") == self.instance:
            raise serializers.ValidationError({"parent": "A category cannot be its own parent."})
        return data


# ═══════════════════════════════════════════════════
# Tag Serializers
# ═══════════════════════════════════════════════════


class TagSerializer(serializers.ModelSerializer):
    """Tag serializer with post count — for create/update/detail."""

    post_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Tag
        fields = ["id", "name", "slug", "post_count", "created_at"]
        read_only_fields = ["id", "created_at", "post_count"]
        extra_kwargs = {
            "slug": {"required": False},
        }


# ═══════════════════════════════════════════════════
# SiteSetting Serializers
# ═══════════════════════════════════════════════════


class SiteSettingSerializer(serializers.ModelSerializer):
    """SiteSetting read/write."""

    class Meta:
        model = SiteSetting
        fields = ["id", "key", "value", "description", "updated_at"]
        read_only_fields = ["updated_at"]
