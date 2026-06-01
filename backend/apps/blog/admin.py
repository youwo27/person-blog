"""Django Admin configuration for blog app."""

from django.contrib import admin

from .models import Category, Post, SiteSetting, Tag


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """Category admin with tree hierarchy support."""

    list_display = ["name", "slug", "parent", "order", "is_active", "created_at"]
    list_filter = ["is_active", "created_at"]
    search_fields = ["name", "slug"]
    prepopulated_fields = {"slug": ("name",)}
    ordering = ["order", "name"]
    list_editable = ["order", "is_active"]


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """Tag admin."""

    list_display = ["name", "slug", "created_at"]
    search_fields = ["name", "slug"]
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    """Post admin with full content management."""

    list_display = [
        "title",
        "author",
        "category",
        "status",
        "is_featured",
        "view_count",
        "published_at",
        "created_at",
    ]
    list_filter = ["status", "is_featured", "category", "tags", "author", "created_at", "published_at"]
    search_fields = ["title", "slug", "content", "excerpt"]
    prepopulated_fields = {"slug": ("title",)}
    filter_horizontal = ["tags"]
    readonly_fields = [
        "content_html",
        "reading_time_minutes",
        "view_count",
        "created_at",
        "updated_at",
    ]
    fieldsets = (
        (
            "Content",
            {
                "fields": (
                    "title",
                    "slug",
                    "content",
                    "content_html",
                    "excerpt",
                    "cover_image",
                )
            },
        ),
        (
            "Organization",
            {
                "fields": (
                    "author",
                    "category",
                    "tags",
                )
            },
        ),
        (
            "Status & Visibility",
            {
                "fields": (
                    "status",
                    "is_featured",
                    "published_at",
                    "scheduled_at",
                )
            },
        ),
        (
            "SEO",
            {
                "fields": ("meta_title", "meta_description"),
                "classes": ("collapse",),
            },
        ),
        (
            "Stats",
            {
                "fields": ("view_count", "reading_time_minutes"),
            },
        ),
        (
            "Timestamps",
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    actions = ["publish_posts", "archive_posts", "feature_posts", "unfeature_posts"]

    @admin.action(description="Publish selected posts")
    def publish_posts(self, request, queryset):
        for post in queryset:
            post.publish()

    @admin.action(description="Archive selected posts")
    def archive_posts(self, request, queryset):
        queryset.update(status=Post.Status.ARCHIVED)

    @admin.action(description="Mark as featured")
    def feature_posts(self, request, queryset):
        queryset.update(is_featured=True)

    @admin.action(description="Remove featured")
    def unfeature_posts(self, request, queryset):
        queryset.update(is_featured=False)


@admin.register(SiteSetting)
class SiteSettingAdmin(admin.ModelAdmin):
    """SiteSetting admin — key-value configuration."""

    list_display = ["key", "description", "updated_at"]
    search_fields = ["key", "description"]
    readonly_fields = ["updated_at"]
