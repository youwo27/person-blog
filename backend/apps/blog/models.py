"""
Database models for blog app.

Models:
- Category: Hierarchical post categories (tree via parent FK)
- Tag: Flat post tags
- Post: Blog post with Markdown content, status workflow, SEO metadata
- SiteSetting: Key-value site configuration
"""

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.html import strip_tags
from django.utils.text import slugify

from common.utils import estimate_reading_time, generate_slug_from_title


# ═══════════════════════════════════════════════════
# Post Manager
# ═══════════════════════════════════════════════════


class PostQuerySet(models.QuerySet):
    """Custom QuerySet for Post model with chainable filters."""

    def published(self):
        """Return only published posts."""
        return self.filter(status=Post.Status.PUBLISHED, published_at__lte=timezone.now())

    def featured(self):
        """Return only featured posts."""
        return self.filter(is_featured=True)

    def drafted(self):
        """Return draft posts."""
        return self.filter(status=Post.Status.DRAFT)

    def scheduled(self):
        """Return posts scheduled for future publication."""
        return self.filter(status=Post.Status.SCHEDULED, scheduled_at__gt=timezone.now())

    def by_author(self, user):
        """Return posts by a specific author."""
        return self.filter(author=user)

    def in_category(self, category_slug):
        """Return posts in a specific category (including children)."""
        return self.filter(category__slug=category_slug)

    def with_tag(self, tag_slug):
        """Return posts with a specific tag."""
        return self.filter(tags__slug=tag_slug)

    def from_year_month(self, year, month):
        """Return posts from a specific year/month."""
        return self.filter(published_at__year=year, published_at__month=month)


class PostManager(models.Manager):
    """Custom manager for Post model."""

    def get_queryset(self):
        return PostQuerySet(self.model, using=self._db)

    def published(self):
        return self.get_queryset().published()

    def featured(self):
        return self.get_queryset().featured()

    def drafted(self):
        return self.get_queryset().drafted()

    def scheduled(self):
        return self.get_queryset().scheduled()

    def by_author(self, user):
        return self.get_queryset().by_author(user)

    def in_category(self, category_slug):
        return self.get_queryset().in_category(category_slug)


# ═══════════════════════════════════════════════════
# Category Model
# ═══════════════════════════════════════════════════


class Category(models.Model):
    """
    Hierarchical blog category.

    Supports multi-level nesting via `parent` self-referencing FK.
    """

    name = models.CharField(
        max_length=100,
        verbose_name="name",
    )
    slug = models.SlugField(
        max_length=120,
        unique=True,
        verbose_name="slug",
    )
    description = models.TextField(
        blank=True,
        verbose_name="description",
    )
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="children",
        verbose_name="parent category",
    )
    order = models.IntegerField(
        default=0,
        verbose_name="display order",
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="is active",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="created at",
    )

    class Meta:
        db_table = "blog_category"
        verbose_name = "category"
        verbose_name_plural = "categories"
        ordering = ["order", "name"]
        indexes = [
            models.Index(fields=["slug"]),
            models.Index(fields=["is_active"]),
            models.Index(fields=["parent"]),
        ]

    def __str__(self):
        if self.parent:
            return f"{self.parent.name} > {self.name}"
        return self.name

    @property
    def post_count(self) -> int:
        """Number of posts in this category (including subcategories)."""
        return self.posts.published().count()

    @property
    def is_root(self) -> bool:
        """Check if this is a root-level category."""
        return self.parent is None

    @property
    def children_active(self):
        """Return only active child categories."""
        return self.children.filter(is_active=True)


# ═══════════════════════════════════════════════════
# Tag Model
# ═══════════════════════════════════════════════════


class Tag(models.Model):
    """Flat blog post tag."""

    name = models.CharField(
        max_length=100,
        verbose_name="name",
    )
    slug = models.SlugField(
        max_length=120,
        unique=True,
        verbose_name="slug",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="created at",
    )

    class Meta:
        db_table = "blog_tag"
        verbose_name = "tag"
        verbose_name_plural = "tags"
        ordering = ["name"]
        indexes = [
            models.Index(fields=["slug"]),
            models.Index(fields=["name"]),
        ]

    def __str__(self):
        return self.name

    @property
    def post_count(self) -> int:
        """Number of published posts with this tag."""
        return self.posts.published().count()


# ═══════════════════════════════════════════════════
# Post Model
# ═══════════════════════════════════════════════════


class Post(models.Model):
    """
    Blog post with full content management.

    Supports Markdown content, status workflow (Draft → Published/Archived),
    SEO metadata, and view tracking.
    """

    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        PUBLISHED = "PUBLISHED", "Published"
        ARCHIVED = "ARCHIVED", "Archived"
        SCHEDULED = "SCHEDULED", "Scheduled"

    # ── Core Content ──────────────────────────────
    title = models.CharField(
        max_length=255,
        verbose_name="title",
    )
    slug = models.SlugField(
        max_length=300,
        verbose_name="slug",
    )
    content = models.TextField(
        verbose_name="content (Markdown)",
    )
    content_html = models.TextField(
        blank=True,
        verbose_name="content (HTML)",
    )
    excerpt = models.TextField(
        blank=True,
        verbose_name="excerpt",
    )

    # ── Media ─────────────────────────────────────
    cover_image = models.ForeignKey(
        "media_library.Media",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="post_covers",
        verbose_name="cover image",
    )

    # ── Relationships ─────────────────────────────
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="posts",
        verbose_name="author",
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="posts",
        verbose_name="category",
    )
    tags = models.ManyToManyField(
        Tag,
        related_name="posts",
        blank=True,
        verbose_name="tags",
    )

    # ── Status & Visibility ───────────────────────
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
        db_index=True,
        verbose_name="status",
    )
    is_featured = models.BooleanField(
        default=False,
        db_index=True,
        verbose_name="is featured",
    )

    # ── Analytics ─────────────────────────────────
    view_count = models.PositiveIntegerField(
        default=0,
        db_index=True,
        verbose_name="view count",
    )
    reading_time_minutes = models.PositiveSmallIntegerField(
        default=1,
        verbose_name="reading time (minutes)",
    )

    # ── Publication Dates ─────────────────────────
    published_at = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
        verbose_name="published at",
    )
    scheduled_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="scheduled at",
    )

    # ── SEO ───────────────────────────────────────
    meta_title = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="meta title",
    )
    meta_description = models.TextField(
        max_length=500,
        blank=True,
        verbose_name="meta description",
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

    objects = PostManager()

    class Meta:
        db_table = "blog_post"
        verbose_name = "post"
        verbose_name_plural = "posts"
        ordering = ["-published_at", "-created_at"]
        indexes = [
            # Primary query patterns
            models.Index(fields=["status", "published_at"], name="blog_post_status_pub_idx"),
            models.Index(fields=["slug", "status"], name="blog_post_slug_status_idx"),
            # Category + status filtering
            models.Index(fields=["category", "status", "published_at"], name="blog_post_cat_status_pub_idx"),
            # Author + status
            models.Index(fields=["author", "status"], name="blog_post_author_status_idx"),
            # Featured section
            models.Index(fields=["is_featured", "status", "published_at"], name="blog_post_featured_idx"),
            # Popular posts
            models.Index(fields=["view_count"], name="blog_post_views_idx"),
            # Archive queries
            models.Index(fields=["published_at"], name="blog_post_pub_date_idx"),
        ]
        constraints = [
            # Ensure slug is unique within the same status (prevent duplicate published slugs)
            models.UniqueConstraint(
                fields=["slug", "status"],
                name="unique_slug_per_status",
            ),
        ]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        # Auto-generate slug from title
        if not self.slug:
            self.slug = generate_slug_from_title(self.title)

        # Render Markdown to HTML
        if self.content and (not self.content_html or self._content_changed()):
            self.content_html = self._render_markdown(self.content)

        # Auto-calculate reading time
        if self.content and not self.reading_time_minutes:
            self.reading_time_minutes = estimate_reading_time(self.content)

        # Auto-generate excerpt
        if not self.excerpt and self.content:
            plain = strip_tags(self.content_html or self.content)
            self.excerpt = plain[:250].rsplit(" ", 1)[0] if len(plain) > 250 else plain

        # Set published_at when status changes to PUBLISHED
        if self.status == self.Status.PUBLISHED and not self.published_at:
            self.published_at = timezone.now()

        # Use the meta_title as default if not set
        if not self.meta_title:
            self.meta_title = self.title[:255]

        super().save(*args, **kwargs)

    def _content_changed(self) -> bool:
        """Check if content field has changed since last save."""
        if not self.pk:
            return True
        try:
            old = Post.objects.only("content").get(pk=self.pk)
            return old.content != self.content
        except Post.DoesNotExist:
            return True

    @staticmethod
    def _render_markdown( content: str | None) -> str:
        """Convert Markdown content to HTML."""
        if not content:
            return ""
        try:
            import markdown
            return markdown.markdown(
                content,
                extensions=[
                    "markdown.extensions.fenced_code",
                    "markdown.extensions.tables",
                    "markdown.extensions.codehilite",
                    "markdown.extensions.toc",
                    "markdown.extensions.nl2br",
                ],
            )
        except ImportError:
            return content

    @property
    def comment_count(self) -> int:
        """Number of approved comments."""
        return self.comments.filter(is_approved=True, is_spam=False).count()

    @property
    def prev_post(self):
        """Previous published post by published_at."""
        return (
            Post.objects.published()
            .filter(published_at__lt=self.published_at)
            .order_by("-published_at")
            .first()
        )

    @property
    def next_post(self):
        """Next published post by published_at."""
        return (
            Post.objects.published()
            .filter(published_at__gt=self.published_at)
            .order_by("published_at")
            .first()
        )

    @property
    def cover_image_url(self) -> str:
        """URL of the cover image, or empty string."""
        if self.cover_image:
            return self.cover_image.url
        return ""

    def increment_view_count(self):
        """Atomically increment view_count."""
        Post.objects.filter(pk=self.pk).update(view_count=models.F("view_count") + 1)

    def publish(self):
        """Publish the post immediately."""
        self.status = self.Status.PUBLISHED
        self.published_at = timezone.now()
        self.save(update_fields=["status", "published_at"])

    def archive(self):
        """Archive the post."""
        self.status = self.Status.ARCHIVED
        self.save(update_fields=["status"])


# ═══════════════════════════════════════════════════
# SiteSetting Model
# ═══════════════════════════════════════════════════


class SiteSetting(models.Model):
    """
    Key-value site configuration.

    Examples:
    - blog_title: "My Blog"
    - blog_description: "A personal blog about tech"
    - posts_per_page: 12
    - enable_comments: true
    """

    key = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="key",
    )
    value = models.JSONField(
        verbose_name="value",
    )
    description = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="description",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="updated at",
    )

    class Meta:
        db_table = "blog_sitesetting"
        verbose_name = "site setting"
        verbose_name_plural = "site settings"

    def __str__(self):
        return self.key
