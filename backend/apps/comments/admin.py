"""Django Admin configuration for comments app."""

from django.contrib import admin

from .models import Comment, CommentLike


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    """Comment admin with moderation tools."""

    list_display = [
        "id",
        "post_link",
        "author",
        "short_content",
        "is_approved",
        "is_spam",
        "likes_count",
        "created_at",
    ]
    list_filter = ["is_approved", "is_spam", "created_at"]
    search_fields = ["content", "author__username", "post__title"]
    readonly_fields = ["content_html", "likes_count", "created_at", "updated_at"]
    actions = ["approve_comments", "mark_as_spam", "unmark_spam"]

    def post_link(self, obj):
        """Link to the associated post in admin."""
        from django.urls import reverse
        from django.utils.html import format_html

        url = reverse("admin:blog_post_change", args=[obj.post_id])
        return format_html('<a href="{}">{}</a>', url, obj.post.title[:50])

    post_link.short_description = "post"  # type: ignore[attr-defined]

    def short_content(self, obj):
        """Truncated content for list display."""
        return obj.content[:80] + "..." if len(obj.content) > 80 else obj.content

    short_content.short_description = "content"  # type: ignore[attr-defined]

    @admin.action(description="Approve selected comments")
    def approve_comments(self, request, queryset):
        for comment in queryset:
            comment.approve()
        self.message_user(request, f"{queryset.count()} comments approved.")

    @admin.action(description="Mark selected as spam")
    def mark_as_spam(self, request, queryset):
        for comment in queryset:
            comment.mark_spam()
        self.message_user(request, f"{queryset.count()} comments marked as spam.")

    @admin.action(description="Unmark spam")
    def unmark_spam(self, request, queryset):
        queryset.update(is_spam=False)
        self.message_user(request, f"{queryset.count()} comments unmarked as spam.")


@admin.register(CommentLike)
class CommentLikeAdmin(admin.ModelAdmin):
    """CommentLike admin — read-only tracking."""

    list_display = ["comment", "user", "created_at"]
    list_filter = ["created_at"]
    search_fields = ["comment__content", "user__username"]
    readonly_fields = ["comment", "user", "created_at"]
