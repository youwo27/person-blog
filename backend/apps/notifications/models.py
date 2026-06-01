"""
Database models for notifications app.

Models:
- Notification: User notification with GenericForeignKey for flexible targets
"""

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models


class Notification(models.Model):
    """
    User notification tied to any model via GenericForeignKey.

    Types: COMMENT_REPLY, COMMENT_APPROVED, POST_LIKED, NEW_SUBSCRIBER, etc.
    """

    class Type(models.TextChoices):
        COMMENT_REPLY = "COMMENT_REPLY", "Comment Reply"
        COMMENT_APPROVED = "COMMENT_APPROVED", "Comment Approved"
        POST_COMMENT = "POST_COMMENT", "New Comment on Post"
        POST_PUBLISHED = "POST_PUBLISHED", "Post Published"
        WELCOME = "WELCOME", "Welcome"

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
        verbose_name="recipient",
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="actions",
        verbose_name="actor",
    )
    type = models.CharField(
        max_length=30,
        choices=Type.choices,
        db_index=True,
        verbose_name="type",
    )
    message = models.TextField(
        verbose_name="message",
    )
    is_read = models.BooleanField(
        default=False,
        db_index=True,
        verbose_name="is read",
    )

    # Generic FK — target can be Comment, Post, User, etc.
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    object_id = models.PositiveIntegerField(
        null=True,
        blank=True,
    )
    content_object = GenericForeignKey("content_type", "object_id")

    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        verbose_name="created at",
    )

    class Meta:
        db_table = "notification"
        verbose_name = "notification"
        verbose_name_plural = "notifications"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["recipient", "is_read", "-created_at"]),
            models.Index(fields=["recipient", "-created_at"]),
        ]

    def __str__(self):
        return f"[{self.type}] {self.recipient}: {self.message[:50]}"
