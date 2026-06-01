"""
DRF ViewSets for blog app.

Endpoints:
- /api/v1/posts/            Post list (filtered, paginated)
- /api/v1/posts/{slug}/     Post detail
- /api/v1/categories/       Category list (tree)
- /api/v1/categories/{id}/  Category detail
- /api/v1/tags/             Tag list
- /api/v1/tags/{id}/        Tag detail
- /api/v1/settings/         Site settings
"""

import django_filters
from django.db.models import Count, Q
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response

from common.permissions import IsAuthorOrReadOnly, IsEditorOrAdmin
from common.pagination import StandardPageNumberPagination, SmallPageNumberPagination

from .filters import CategoryFilter, PostFilter
from .models import Category, Post, SiteSetting, Tag
from .serializers import (
    CategorySerializer,
    CategoryTreeSerializer,
    PostCreateUpdateSerializer,
    PostDetailSerializer,
    PostListSerializer,
    SiteSettingSerializer,
    TagBriefSerializer,
    TagSerializer,
)


# ═══════════════════════════════════════════════════
# Post ViewSet
# ═══════════════════════════════════════════════════


@extend_schema_view(
    list=extend_schema(
        summary="List posts",
        description="Return paginated list of posts with filtering, search, and ordering.",
        parameters=[
            OpenApiParameter(name="status", description="Filter by status (PUBLISHED/DRAFT/ARCHIVED/SCHEDULED)"),
            OpenApiParameter(name="category", description="Filter by category slug"),
            OpenApiParameter(name="tag", description="Filter by tag slug"),
            OpenApiParameter(name="author", description="Filter by author username"),
            OpenApiParameter(name="featured", description="Filter featured posts (true/false)"),
            OpenApiParameter(name="year", description="Filter by publication year"),
            OpenApiParameter(name="month", description="Filter by publication month"),
            OpenApiParameter(name="search", description="Search in title and content"),
            OpenApiParameter(name="ordering", description="Sort: -published_at, -view_count, -created_at"),
        ],
    ),
    retrieve=extend_schema(summary="Get post detail", description="Return full post detail including content HTML and navigation."),
    create=extend_schema(summary="Create post", description="Create a new blog post. Requires EDITOR or ADMIN role."),
    update=extend_schema(summary="Update post", description="Update an existing post. Author or admin only."),
    partial_update=extend_schema(summary="Partial update post", description="Partially update a post."),
    destroy=extend_schema(summary="Delete post", description="Soft-delete a post. Admin only."),
)
class PostViewSet(viewsets.ModelViewSet):
    """
    Blog post CRUD.

    - List: Public (published posts only for anonymous users)
    - Detail: Public for published, draft visible to author/admin
    - Create: EDITOR/ADMIN only
    - Update/Delete: Author or ADMIN only
    """

    lookup_field = "slug"
    pagination_class = StandardPageNumberPagination
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = PostFilter
    search_fields = ["title", "content", "excerpt"]
    ordering_fields = ["published_at", "view_count", "created_at", "reading_time_minutes"]
    ordering = ["-published_at"]

    def get_serializer_class(self):
        if self.action == "list":
            return PostListSerializer
        if self.action in ("create", "update", "partial_update"):
            return PostCreateUpdateSerializer
        return PostDetailSerializer

    def get_queryset(self):
        """Optimize queryset based on action."""
        qs = Post.objects.select_related("author", "category", "cover_image").prefetch_related("tags")

        # Anonymous users see only published posts
        if not self.request.user.is_authenticated:
            return qs.published()

        # Staff users see all posts
        if self.request.user.is_staff:
            return qs

        # Regular authenticated users: see published + their own posts
        return qs.filter(
            Q(status=Post.Status.PUBLISHED) | Q(author=self.request.user)
        )

    def get_permissions(self):
        if self.action in ("create",):
            return [IsEditorOrAdmin()]
        if self.action in ("update", "partial_update", "destroy"):
            return [IsAuthorOrReadOnly()]
        return [IsAuthenticatedOrReadOnly()]

    def retrieve(self, request, *args, **kwargs):
        """Get detail and increment view count."""
        instance = self.get_object()
        # Increment view count (simple version; production should add IP-based dedup)
        instance.increment_view_count()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @extend_schema(summary="Featured posts", description="Return a short list of featured published posts.")
    @action(detail=False, methods=["get"])
    def featured(self, request):
        posts = Post.objects.published().featured().select_related("author", "category").prefetch_related("tags")[:6]
        serializer = PostListSerializer(posts, many=True)
        return Response({"success": True, "results": serializer.data})

    @extend_schema(summary="Archive by year/month", description="Return posts grouped by year and month.")
    @action(detail=False, methods=["get"])
    def archive(self, request):
        from django.db.models.functions import TruncMonth

        archives = (
            Post.objects.published()
            .annotate(month=TruncMonth("published_at"))
            .values("month")
            .annotate(count=Count("id"))
            .order_by("-month")
        )
        return Response({"success": True, "results": list(archives)})


# ═══════════════════════════════════════════════════
# Category ViewSet
# ═══════════════════════════════════════════════════


@extend_schema_view(
    list=extend_schema(summary="List categories", description="Return categories as a tree structure."),
    retrieve=extend_schema(summary="Get category detail"),
    create=extend_schema(summary="Create category", description="Create a new category. Editor/Admin only."),
    update=extend_schema(summary="Update category"),
    destroy=extend_schema(summary="Delete category"),
)
class CategoryViewSet(viewsets.ModelViewSet):
    """Category CRUD — tree representation in list."""

    queryset = Category.objects.prefetch_related("children").order_by("order", "name")
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend, SearchFilter]
    filterset_class = CategoryFilter
    search_fields = ["name", "description"]
    pagination_class = None  # Categories are typically not paginated

    def get_serializer_class(self):
        if self.action == "list":
            return CategoryTreeSerializer
        return CategorySerializer

    def get_permissions(self):
        if self.action in ("create", "update", "partial_update", "destroy"):
            return [IsEditorOrAdmin()]
        return [IsAuthenticatedOrReadOnly()]

    def list(self, request, *args, **kwargs):
        """Return root categories with nested children."""
        root_categories = self.get_queryset().filter(parent__isnull=True)
        serializer = self.get_serializer(root_categories, many=True)
        return Response({"success": True, "results": serializer.data})


# ═══════════════════════════════════════════════════
# Tag ViewSet
# ═══════════════════════════════════════════════════


@extend_schema_view(
    list=extend_schema(summary="List tags", description="Return all tags with post counts."),
    retrieve=extend_schema(summary="Get tag detail"),
    create=extend_schema(summary="Create tag"),
    update=extend_schema(summary="Update tag"),
    destroy=extend_schema(summary="Delete tag"),
)
class TagViewSet(viewsets.ModelViewSet):
    """Tag CRUD — annotated with post counts."""

    queryset = Tag.objects.annotate(post_count=Count("posts", filter=Q(posts__status=Post.Status.PUBLISHED)))
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["name"]
    ordering_fields = ["name", "post_count"]
    ordering = ["name"]
    pagination_class = None  # Tags are typically not paginated

    def get_serializer_class(self):
        if self.action == "list":
            return TagBriefSerializer
        return TagSerializer

    def get_permissions(self):
        if self.action in ("create", "update", "partial_update", "destroy"):
            return [IsEditorOrAdmin()]
        return [IsAuthenticatedOrReadOnly()]

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response({"success": True, "results": serializer.data})


# ═══════════════════════════════════════════════════
# SiteSetting ViewSet
# ═══════════════════════════════════════════════════


@extend_schema_view(
    list=extend_schema(summary="List site settings", description="Return all site settings as key-value pairs."),
)
class SiteSettingViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only site settings — public."""

    queryset = SiteSetting.objects.all()
    serializer_class = SiteSettingSerializer
    pagination_class = None

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        # Return as dict for easy frontend consumption
        settings_dict = {item.key: item.value for item in queryset}
        return Response({"success": True, "results": settings_dict})

