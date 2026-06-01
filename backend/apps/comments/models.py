"""
Database models for comments app.

Models:
- Comment: Nested comment system with approval workflow and spam detection
- CommentLike: User likes on comments
"""

from django.conf import settings
from django.db import models


# ═══════════════════════════════════════════════════
# Comment Model
# ═══════════════════════════════════════════════════


class Comment(models.Model):
    """
    Nested blog comment.

    Supports infinite nesting via `parent` FK, with visual display limited
    to 3 levels. New comments require moderation (is_approved=False by default).
    """

    post = models.ForeignKey(
        "blog.Post",
        on_delete=models.CASCADE,
        related_name="comments",
        verbose_name="post",
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="comments",
        verbose_name="author",
    )
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="replies",
        verbose_name="parent comment",
    )

    content = models.TextField(
        verbose_name="content (Markdown)",
    )
    content_html = models.TextField(
        blank=True,
        verbose_name="content (HTML)",
    )

    # ── Moderation ────────────────────────────────
    is_approved = models.BooleanField(
        default=False,
        db_index=True,
        verbose_name="is approved",
    )
    is_spam = models.BooleanField(
        default=False,
        verbose_name="is spam",
    )

    # ── Metadata ──────────────────────────────────
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name="IP address",
    )
    user_agent = models.CharField(
        max_length=500,
        blank=True,
        verbose_name="user agent",
    )
    likes_count = models.PositiveIntegerField(
        default=0,
        verbose_name="likes count",
    )

    # ── Timestamps ────────────────────────────────
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="created at",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="updated at",
    )

    class Meta:
        db_table = "blog_comment"
        verbose_name = "comment"
        verbose_name_plural = "comments"
        ordering = ["created_at"]
        indexes = [
            # Primary: approved comments for a post
            models.Index(fields=["post", "is_approved", "created_at"], name="comment_post_approved_idx"),
            # User's comments
            models.Index(fields=["author", "created_at"], name="comment_author_idx"),
            # Parent for nested queries
            models.Index(fields=["parent"], name="comment_parent_idx"),
        ]

    def __str__(self):
        return f"Comment by {self.author} on {self.post}"

    def save(self, *args, **kwargs):
        # Render Markdown to HTML
        if self.content and not self.content_html:
            self.content_html = self._render_markdown(self.content)
        super().save(*args, **kwargs)

    @staticmethod
    def _render_markdown(content: str) -> str:
        """Convert Markdown content to safe HTML subset."""
        if not content:
            return ""
        try:
            import bleach
            import markdown

            allowed_tags = [
                "p", "br", "strong", "em", "b", "i", "u", "a", "code", "pre",
                "blockquote", "ul", "ol", "li", "span",
            ]
            allowed_attrs = {"a": ["href", "title"], "span": ["class"]}

            html = markdown.markdown(
                content,
                extensions=["markdown.extensions.fenced_code", "markdown.extensions.nl2br"],
            )
            return bleach.clean(html, tags=allowed_tags, attributes=allowed_attrs, strip=True)
        except ImportError:
            return content

    @property
    def nesting_level(self) -> int:
        """Calculate the nesting depth of this comment (0 for top-level)."""
        level = 0
        current = self
        while current.parent is not None:
            level += 1
            current = current.parent
        return level

    @property
    def is_top_level(self) -> bool:
        """Check if this is a top-level comment (no parent)."""
        return self.parent is None

    def approve(self):
        """Approve this comment."""
        self.is_approved = True
        self.is_spam = False
        self.save(update_fields=["is_approved", "is_spam"])

    def mark_spam(self):
        """Mark this comment as spam."""
        self.is_spam = True
        self.is_approved = False
        self.save(update_fields=["is_approved", "is_spam"])


# ═══════════════════════════════════════════════════
# CommentLike Model
# ═══════════════════════════════════════════════════


class CommentLike(models.Model):
    """Track which users have liked which comments."""

    comment = models.ForeignKey(
        Comment,
        on_delete=models.CASCADE,
        related_name="likes",
        verbose_name="comment",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="comment_likes",
        verbose_name="user",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="created at",
    )

    class Meta:
        db_table = "blog_commentlike"
        verbose_name = "comment like"
        verbose_name_plural = "comment likes"
        unique_together = [("comment", "user")]
        indexes = [
            models.Index(fields=["comment"]),
            models.Index(fields=["user"]),
        ]

    def __str__(self):
        return f"{self.user} liked comment #{self.comment_id}"
