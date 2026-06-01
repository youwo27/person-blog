"""
DRF ViewSets for blog app — complete CRUD.

Endpoints:
  Posts:
    GET    /api/v1/posts/               List (filtered, paginated)
    POST   /api/v1/posts/               Create (Editor/Admin)
    GET    /api/v1/posts/{slug}/        Detail
    PUT    /api/v1/posts/{slug}/        Full update
    PATCH  /api/v1/posts/{slug}/        Partial update
    DELETE /api/v1/posts/{slug}/        Delete
    GET    /api/v1/posts/featured/      Featured posts
    GET    /api/v1/posts/archive/       Monthly archive
    GET    /api/v1/posts/my_posts/      Current user's posts

  Categories:
    GET    /api/v1/categories/          Tree list
    POST   /api/v1/categories/          Create (Editor/Admin)
    GET    /api/v1/categories/{id}/     Detail
    PUT    /api/v1/categories/{id}/     Update
    PATCH  /api/v1/categories/{id}/     Partial update
    DELETE /api/v1/categories/{id}/     Delete

  Tags:
    GET    /api/v1/tags/                List with post counts
    POST   /api/v1/tags/                Create (Editor/Admin)
    GET    /api/v1/tags/{id}/           Detail
    PUT    /api/v1/tags/{id}/           Update
    PATCH  /api/v1/tags/{id}/           Partial update
    DELETE /api/v1/tags/{id}/           Delete

  Site Settings:
    GET    /api/v1/settings/            Key-value dict
"""

import django_filters
from django.db.models import Count, Q
from django.utils import timezone
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response

from common.pagination import StandardPageNumberPagination
from common.permissions import IsAuthorOrReadOnly, IsEditorOrAdmin

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
# Post ViewSet — complete CRUD
# ═══════════════════════════════════════════════════


@extend_schema_view(
    list=extend_schema(
        summary="List posts",
        description="Paginated post list with filtering, search, ordering.",
        parameters=[
            OpenApiParameter(name="status", description="DRAFT / PUBLISHED / ARCHIVED / SCHEDULED"),
            OpenApiParameter(name="category", description="Filter by category slug"),
            OpenApiParameter(name="tag", description="Filter by tag slug"),
            OpenApiParameter(name="author", description="Filter by author username"),
            OpenApiParameter(name="featured", description="true / false"),
            OpenApiParameter(name="year", description="Publication year", type=int),
            OpenApiParameter(name="month", description="Publication month (1-12)", type=int),
            OpenApiParameter(name="search", description="Search title + content"),
            OpenApiParameter(name="page", description="Page number", type=int),
            OpenApiParameter(name="page_size", description="Results per page (max 100)", type=int),
            OpenApiParameter(name="ordering", description="-published_at / -view_count / -created_at"),
        ],
    ),
    retrieve=extend_schema(summary="Get post", description="Full post detail with HTML, SEO, prev/next nav, comment count. Increments view count."),
    create=extend_schema(summary="Create post", description="Create a new post. Requires EDITOR or ADMIN role. Author auto-set to current user."),
    update=extend_schema(summary="Replace post", description="Full update. Author or Admin only."),
    partial_update=extend_schema(summary="Patch post", description="Partial update. Author or Admin only."),
    destroy=extend_schema(summary="Delete post", description="Delete a post. Author or Admin only."),
)
class PostViewSet(viewsets.ModelViewSet):
    """
    Blog post CRUD.

    Permissions:
    - List / Retrieve: public (anon sees published only)
    - Create: Editor or Admin
    - Update / Delete: Author or Admin
    """

    lookup_field = "slug"
    pagination_class = StandardPageNumberPagination
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = PostFilter
    search_fields = ["title", "content", "excerpt"]
    ordering_fields = ["published_at", "view_count", "created_at", "reading_time_minutes", "title"]
    ordering = ["-published_at"]

    def get_serializer_class(self):
        if self.action == "list":
            return PostListSerializer
        if self.action in ("create", "update", "partial_update"):
            return PostCreateUpdateSerializer
        return PostDetailSerializer

    def get_queryset(self):
        qs = Post.objects.select_related("author", "category", "cover_image").prefetch_related("tags")

        if not self.request.user.is_authenticated:
            return qs.filter(status=Post.Status.PUBLISHED)

        if self.request.user.is_staff:
            return qs

        return qs.filter(Q(status=Post.Status.PUBLISHED) | Q(author=self.request.user))

    def get_permissions(self):
        if self.action == "create":
            return [IsEditorOrAdmin()]
        if self.action in ("update", "partial_update", "destroy"):
            return [IsAuthorOrReadOnly()]
        return [IsAuthenticatedOrReadOnly()]

    # ── C (Create) ──────────────────────────────────

    def perform_create(self, serializer):
        """Auto-set author to current user."""
        serializer.save(author=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return self._error_response(serializer.errors, status.HTTP_400_BAD_REQUEST)
        self.perform_create(serializer)
        detail = PostDetailSerializer(serializer.instance, context={"request": request})
        return Response({"success": True, "data": detail.data}, status=status.HTTP_201_CREATED)

    # ── R (Retrieve) ───────────────────────────────

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.increment_view_count()
        serializer = self.get_serializer(instance)
        return Response({"success": True, "data": serializer.data})

    # ── U (Update) ──────────────────────────────────

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if not serializer.is_valid():
            return self._error_response(serializer.errors, status.HTTP_400_BAD_REQUEST)
        self.perform_update(serializer)
        detail = PostDetailSerializer(serializer.instance, context={"request": request})
        return Response({"success": True, "data": detail.data})

    def partial_update(self, request, *args, **kwargs):
        kwargs["partial"] = True
        return self.update(request, *args, **kwargs)

    # ── D (Delete) ──────────────────────────────────

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return Response({"success": True, "message": "Post deleted."}, status=status.HTTP_200_OK)

    # ── Extra Actions ───────────────────────────────

    @extend_schema(summary="Featured posts", description="Up to 6 featured published posts.")
    @action(detail=False, methods=["get"])
    def featured(self, request):
        posts = (
            Post.objects.filter(status=Post.Status.PUBLISHED, is_featured=True)
            .select_related("author", "category")
            .prefetch_related("tags")
            .order_by("-published_at")[:6]
        )
        serializer = PostListSerializer(posts, many=True)
        return Response({"success": True, "results": serializer.data})

    @extend_schema(summary="Monthly archive", description="Published post counts grouped by year-month.")
    @action(detail=False, methods=["get"])
    def archive(self, request):
        from django.db.models.functions import TruncMonth

        archives = (
            Post.objects.filter(status=Post.Status.PUBLISHED)
            .annotate(month=TruncMonth("published_at"))
            .values("month")
            .annotate(count=Count("id"))
            .order_by("-month")
        )
        return Response({"success": True, "results": list(archives)})

    @extend_schema(summary="My posts", description="All posts by the current user (including drafts).")
    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticated])
    def my_posts(self, request):
        posts = self.get_queryset().filter(author=request.user).order_by("-created_at")
        page = self.paginate_queryset(posts)
        if page is not None:
            serializer = PostListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = PostListSerializer(posts, many=True)
        return Response({"success": True, "results": serializer.data})

    # ── Helpers ─────────────────────────────────────

    @staticmethod
    def _error_response(errors, http_status):
        return Response(
            {"success": False, "error": {"code": "bad_request", "message": str(errors)}},
            status=http_status,
        )


# ═══════════════════════════════════════════════════
# Category ViewSet — complete CRUD
# ═══════════════════════════════════════════════════


@extend_schema_view(
    list=extend_schema(summary="List categories", description="Root categories as tree with nested children and post counts."),
    retrieve=extend_schema(summary="Get category", description="Single category detail."),
    create=extend_schema(summary="Create category", description="Create a new category. Editor/Admin only. Auto-generates slug from name."),
    update=extend_schema(summary="Replace category", description="Full update. Editor/Admin only."),
    partial_update=extend_schema(summary="Patch category", description="Partial update. Editor/Admin only."),
    destroy=extend_schema(summary="Delete category", description="Delete a category. Editor/Admin only. Posts are set to null."),
)
class CategoryViewSet(viewsets.ModelViewSet):
    """Category CRUD — tree display, full write support."""

    queryset = Category.objects.prefetch_related("children").order_by("order", "name")
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend, SearchFilter]
    filterset_class = CategoryFilter
    search_fields = ["name", "description"]
    pagination_class = None

    def get_serializer_class(self):
        if self.action == "list":
            return CategoryTreeSerializer
        return CategorySerializer

    def get_queryset(self):
        qs = super().get_queryset()
        # Annotate post_count for all categories
        return qs.annotate(post_count=Count("posts", filter=Q(posts__status=Post.Status.PUBLISHED)))

    def get_permissions(self):
        if self.action in ("create", "update", "partial_update", "destroy"):
            return [IsEditorOrAdmin()]
        return [IsAuthenticatedOrReadOnly()]

    def list(self, request, *args, **kwargs):
        root_categories = self.get_queryset().filter(parent__isnull=True)
        serializer = self.get_serializer(root_categories, many=True)
        return Response({"success": True, "results": serializer.data})

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return self._error(serializer.errors)
        serializer.save()
        return Response({"success": True, "data": serializer.data}, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        partial = kwargs.pop("partial", False)
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if not serializer.is_valid():
            return self._error(serializer.errors)
        serializer.save()
        return Response({"success": True, "data": serializer.data})

    def partial_update(self, request, *args, **kwargs):
        kwargs["partial"] = True
        return self.update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return Response({"success": True, "message": f"Category '{instance.name}' deleted."})

    @staticmethod
    def _error(errors):
        return Response(
            {"success": False, "error": {"code": "bad_request", "message": str(errors)}},
            status=status.HTTP_400_BAD_REQUEST,
        )


# ═══════════════════════════════════════════════════
# Tag ViewSet — complete CRUD
# ═══════════════════════════════════════════════════


@extend_schema_view(
    list=extend_schema(summary="List tags", description="All tags with published post counts."),
    retrieve=extend_schema(summary="Get tag", description="Single tag detail with post count."),
    create=extend_schema(summary="Create tag", description="Create a new tag. Editor/Admin only. Auto-generates slug from name."),
    update=extend_schema(summary="Replace tag", description="Full update. Editor/Admin only."),
    partial_update=extend_schema(summary="Patch tag", description="Partial update. Editor/Admin only."),
    destroy=extend_schema(summary="Delete tag", description="Delete a tag. Editor/Admin only. Removes from all posts."),
)
class TagViewSet(viewsets.ModelViewSet):
    """Tag CRUD — annotated post counts, full write support."""

    queryset = Tag.objects.annotate(post_count=Count("posts", filter=Q(posts__status=Post.Status.PUBLISHED)))
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["name"]
    ordering_fields = ["name", "post_count"]
    ordering = ["name"]
    pagination_class = None

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

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return self._error(serializer.errors)
        serializer.save()
        return Response({"success": True, "data": serializer.data}, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        partial = kwargs.pop("partial", False)
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if not serializer.is_valid():
            return self._error(serializer.errors)
        serializer.save()
        return Response({"success": True, "data": serializer.data})

    def partial_update(self, request, *args, **kwargs):
        kwargs["partial"] = True
        return self.update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return Response({"success": True, "message": f"Tag '{instance.name}' deleted."})

    @staticmethod
    def _error(errors):
        return Response(
            {"success": False, "error": {"code": "bad_request", "message": str(errors)}},
            status=status.HTTP_400_BAD_REQUEST,
        )


# ═══════════════════════════════════════════════════
# SiteSetting ViewSet — read-only public, admin write
# ═══════════════════════════════════════════════════


@extend_schema_view(
    list=extend_schema(summary="List site settings", description="All settings as key-value map. Public read."),
    retrieve=extend_schema(summary="Get site setting"),
)
class SiteSettingViewSet(viewsets.ReadOnlyModelViewSet):
    """Site settings — read-only public, admin can update via Django admin."""

    queryset = SiteSetting.objects.all()
    serializer_class = SiteSettingSerializer
    pagination_class = None

    def list(self, request, *args, **kwargs):
        settings_dict = {item.key: item.value for item in self.get_queryset()}
        return Response({"success": True, "results": settings_dict})
