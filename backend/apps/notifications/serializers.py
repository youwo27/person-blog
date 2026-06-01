"""DRF serializers for notifications app."""

from rest_framework import serializers

from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    """Notification read-only serializer."""

    actor_name = serializers.CharField(source="actor.display_name", read_only=True)
    target_type = serializers.SerializerMethodField()
    target_id = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = [
            "id",
            "type",
            "message",
            "is_read",
            "actor_name",
            "target_type",
            "target_id",
            "created_at",
        ]
        read_only_fields = fields

    def get_target_type(self, obj):
        if obj.content_type:
            return obj.content_type.model
        return None

    def get_target_id(self, obj):
        return obj.object_id
