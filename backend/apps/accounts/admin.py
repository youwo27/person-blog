"""Django Admin configuration for accounts app."""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

from .models import Subscriber, User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Custom User admin with role, profile, and security fields."""

    list_display = [
        "username",
        "email",
        "role",
        "is_staff",
        "is_active",
        "email_verified",
        "date_joined",
    ]
    list_filter = [
        "role",
        "is_staff",
        "is_superuser",
        "is_active",
        "email_verified",
        "date_joined",
    ]
    search_fields = ["username", "email", "first_name", "last_name"]
    ordering = ["-date_joined"]

    fieldsets = (
        (None, {"fields": ("username", "password")}),
        (_("Personal info"), {"fields": ("first_name", "last_name", "email", "avatar", "bio", "website")}),
        (
            _("Role & Permissions"),
            {"fields": ("role", "is_active", "is_staff", "is_superuser", "groups", "user_permissions")},
        ),
        (
            _("Email Verification"),
            {"fields": ("email_verified", "email_verification_token")},
        ),
        (
            _("Login Security"),
            {"fields": ("login_attempts", "locked_until", "last_login_ip")},
        ),
        (_("Important dates"), {"fields": ("last_login", "date_joined", "created_at", "updated_at")}),
    )
    readonly_fields = ["created_at", "updated_at", "last_login", "date_joined"]
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("username", "email", "password1", "password2", "role"),
            },
        ),
    )


@admin.register(Subscriber)
class SubscriberAdmin(admin.ModelAdmin):
    """Subscriber admin."""

    list_display = ["email", "name", "is_verified", "is_active", "subscribed_at"]
    list_filter = ["is_verified", "subscribed_at"]
    search_fields = ["email", "name"]
    readonly_fields = ["subscribed_at", "unsubscribed_at"]
    actions = ["mark_verified"]

    @admin.action(description="Mark selected subscribers as verified")
    def mark_verified(self, request, queryset):
        queryset.update(is_verified=True)
