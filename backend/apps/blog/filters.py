"""django-filter FilterSet classes for blog app."""

import django_filters

from .models import Category, Post, Tag


class PostFilter(django_filters.FilterSet):
    """Advanced filtering for Post list endpoint.

    Query parameters:
    - ?status=PUBLISHED          Filter by status
    - ?category=slug             Filter by category slug
    - ?tag=slug                  Filter by tag slug
    - ?author=username           Filter by author username
    - ?search=keyword            Full-text search (title + content)
    - ?featured=true             Featured posts only
    - ?year=2024&month=6         Archive by date
    - ?ordering=-published_at    Sort order
    """

    category = django_filters.CharFilter(field_name="category__slug", lookup_expr="exact")
    tag = django_filters.CharFilter(field_name="tags__slug", lookup_expr="exact")
    author = django_filters.CharFilter(field_name="author__username", lookup_expr="exact")
    featured = django_filters.BooleanFilter(field_name="is_featured")
    year = django_filters.NumberFilter(field_name="published_at__year")
    month = django_filters.NumberFilter(field_name="published_at__month")

    class Meta:
        model = Post
        fields = {
            "status": ["exact"],
        }


class CategoryFilter(django_filters.FilterSet):
    """Filtering for Category list."""

    is_active = django_filters.BooleanFilter()
    parent = django_filters.CharFilter(field_name="parent__slug")

    class Meta:
        model = Category
        fields = ["is_active"]


class TagFilter(django_filters.FilterSet):
    """Filtering for Tag list."""

    class Meta:
        model = Tag
        fields = {
            "name": ["exact", "icontains"],
        }
