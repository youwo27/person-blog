"""Custom pagination classes with uniform response format."""

from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class StandardPageNumberPagination(PageNumberPagination):
    """
    Standard page-number pagination with configurable page size.

    Response format:
    {
        "success": true,
        "count": 100,
        "next": "http://...",
        "previous": "http://...",
        "total_pages": 5,
        "current_page": 1,
        "results": [...]
    }
    """

    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100
    page_query_param = "page"

    def get_paginated_response(self, data):
        return Response(
            {
                "success": True,
                "count": self.page.paginator.count,
                "next": self.get_next_link(),
                "previous": self.get_previous_link(),
                "total_pages": self.page.paginator.num_pages,
                "current_page": self.page.number,
                "results": data,
            }
        )


class SmallPageNumberPagination(StandardPageNumberPagination):
    """Smaller page size for sidebar widgets, related items, etc."""

    page_size = 10
    max_page_size = 50
