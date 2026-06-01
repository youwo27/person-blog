"""DRF ViewSet for notifications — read, mark read, unread count."""

from django.db.models import Count
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Notification
from .serializers import NotificationSerializer


@extend_schema_view(
    list=extend_schema(summary="List notifications", description="Return current user's notifications, newest first."),
    retrieve=extend_schema(summary="Get notification"),
)
class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    """User notifications — read-only, mark as read."""

    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user).select_related("actor", "content_type")

    @extend_schema(summary="Mark all as read")
    @action(detail=False, methods=["post"])
    def read_all(self, request):
        """Mark all notifications as read."""
        updated = self.get_queryset().filter(is_read=False).update(is_read=True)
        return Response({"success": True, "marked_read": updated})

    @extend_schema(summary="Mark single as read")
    @action(detail=True, methods=["post"])
    def read(self, request, pk=None):
        """Mark a single notification as read."""
        notification = self.get_object()
        notification.is_read = True
        notification.save(update_fields=["is_read"])
        return Response({"success": True})

    @extend_schema(summary="Unread count")
    @action(detail=False, methods=["get"])
    def unread_count(self, request):
        """Get number of unread notifications."""
        count = self.get_queryset().filter(is_read=False).count()
        return Response({"success": True, "unread_count": count})
