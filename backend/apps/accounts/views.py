"""
DRF ViewSets for accounts app.

Endpoints (will be expanded in Round 3):
- /api/v1/users/me/     Current user profile
- /api/v1/subscribers/  Newsletter subscribers
"""

from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser, IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response

from .models import Subscriber
from .serializers import (
    SubscriberCreateSerializer,
    SubscriberSerializer,
    UserProfileSerializer,
    UserUpdateSerializer,
)


@extend_schema_view(
    list=extend_schema(summary="List subscribers", description="List newsletter subscribers. Admin only."),
    create=extend_schema(summary="Subscribe", description="Subscribe to the newsletter."),
    destroy=extend_schema(summary="Unsubscribe", description="Remove a subscriber. Admin only."),
)
class SubscriberViewSet(viewsets.ModelViewSet):
    """
    Newsletter subscriber management.

    - List/Destroy: Admin only
    - Create: Public
    """

    queryset = Subscriber.objects.all()

    def get_serializer_class(self):
        if self.action == "create":
            return SubscriberCreateSerializer
        return SubscriberSerializer

    def get_permissions(self):
        if self.action in ("list", "destroy", "update", "partial_update"):
            return [IsAdminUser()]
        return []

    def create(self, request, *args, **kwargs):
        """Subscribe — no auth required."""
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"success": False, "error": {"code": "bad_request", "message": str(serializer.errors)}},
                status=400,
            )
        subscriber = serializer.save()
        return Response(
            {"success": True, "message": "Successfully subscribed.", "data": SubscriberSerializer(subscriber).data},
            status=201,
        )
