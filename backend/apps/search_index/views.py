"""
Search API endpoints — FTS, suggestions, trending terms.

Endpoints:
  GET /api/v1/search/           Full-text search
  GET /api/v1/search/suggest/   Autocomplete suggestions
  GET /api/v1/search/trending/  Trending search terms
"""

from django.core.cache import cache
from django.db.models import Count, Q
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from apps.blog.models import Post
from apps.blog.serializers import PostListSerializer
from common.pagination import StandardPageNumberPagination

from .backends import get_search_backend


@extend_schema(
    summary="Full-text search",
    description="Search posts by keyword with ranked results. Uses PostgreSQL FTS with trigram fallback.",
    parameters=[
        OpenApiParameter(name="q", description="Search keyword", required=True),
        OpenApiParameter(name="page", description="Page number", type=int),
        OpenApiParameter(name="page_size", description="Results per page", type=int),
    ],
    tags=["search"],
)
@api_view(["GET"])
@permission_classes([AllowAny])
def search_posts(request):
    """Full-text search with ranking."""
    query = request.query_params.get("q", "").strip()
    if not query:
        return Response({"success": True, "results": [], "count": 0, "query": ""})

    # Track search term in cache for trending
    _track_search(query)

    base_qs = Post.objects.filter(status=Post.Status.PUBLISHED).select_related("author", "category").prefetch_related("tags")

    backend = get_search_backend()
    qs = backend.search(base_qs, query)

    # Potentially capture headline highlights if using PG backend
    if isinstance(backend, __import__("apps.search_index.backends", fromlist=["PostgresFTSBackend"]).PostgresFTSBackend):
        try:
            qs = backend.search_highlight(base_qs, query)
        except Exception:
            pass

    paginator = StandardPageNumberPagination()
    page = paginator.paginate_queryset(qs, request)
    if page is not None:
        serializer = PostListSerializer(page, many=True)
        # Attach headline if present
        data = serializer.data
        for i, item in enumerate(data):
            if hasattr(page[i] if i < len(page) else None, "headline"):
                data[i]["headline"] = getattr(page[i], "headline", "")
        return paginator.get_paginated_response(data)

    serializer = PostListSerializer(qs, many=True)
    return Response({"success": True, "results": serializer.data, "count": qs.count(), "query": query})


@extend_schema(
    summary="Search suggestions / autocomplete",
    description="Return title suggestions as you type. Uses trigram similarity.",
    parameters=[
        OpenApiParameter(name="q", description="Prefix to match", required=True),
    ],
    tags=["search"],
)
@api_view(["GET"])
@permission_classes([AllowAny])
def search_suggestions(request):
    """Autocomplete — title suggestions based on typed prefix."""
    prefix = request.query_params.get("q", "").strip()
    if not prefix or len(prefix) < 1:
        return Response({"success": True, "results": []})

    base_qs = Post.objects.filter(status=Post.Status.PUBLISHED)
    backend = get_search_backend()
    suggestions = backend.suggest(base_qs, prefix, limit=8)

    return Response({"success": True, "results": list(suggestions)})


@extend_schema(
    summary="Trending search terms",
    description="Top 10 most searched terms (last 7 days).",
    tags=["search"],
)
@api_view(["GET"])
@permission_classes([AllowAny])
def trending_terms(request):
    """Return trending search terms from Redis or cache."""
    trending = cache.get("trending_searches", [])
    return Response({"success": True, "results": trending})


# ── Helper ──────────────────────────────────────
def _track_search(query: str):
    """Track search terms in Redis sorted set for trending."""
    query = query.strip().lower()[:100]
    if len(query) < 2:
        return

    try:
        from django_redis import get_redis_connection

        redis = get_redis_connection("default")
        key = "trending_searches"
        # Increment score in sorted set
        redis.zincrby(key, 1, query)
        # Expire entries older than 7 days (cleanup on read)
        redis.expire(key, 7 * 86400)

        # Update cache
        top = redis.zrevrange(key, 0, 9, withscores=True)
        cache.set("trending_searches", [{"term": t[0].decode() if isinstance(t[0], bytes) else t[0], "count": int(t[1])} for t in top], 3600)
    except Exception:
        pass
