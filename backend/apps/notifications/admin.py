"""Django Admin for notifications."""

from django.contrib import admin

from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ["recipient", "type", "short_message", "is_read", "created_at"]
    list_filter = ["type", "is_read", "created_at"]
    search_fields = ["recipient__username", "message"]
    readonly_fields = ["recipient", "actor", "type", "message", "content_type", "object_id", "created_at"]

    def short_message(self, obj):
        return obj.message[:80] + ("..." if len(obj.message) > 80 else "")

    short_message.short_description = "message"  # type: ignore
