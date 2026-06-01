"""
Database models for accounts app.

Models:
- User: Custom user model extending AbstractUser with role, avatar, bio, login tracking
- Subscriber: Newsletter/email subscription model
"""

from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils import timezone


# ═══════════════════════════════════════════════════
# Custom User Manager
# ═══════════════════════════════════════════════════


class UserManager(BaseUserManager):
    """Custom manager for User model — uses email as the unique identifier."""

    def _create_user(self, username, email, password, **extra_fields):
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email)
        username = self.model.normalize_username(username)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, username, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(username, email, password, **extra_fields)

    def create_superuser(self, username, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", User.Role.ADMIN)
        extra_fields.setdefault("email_verified", True)
        return self._create_user(username, email, password, **extra_fields)

    def authors(self):
        """Return users with AUTHOR role or higher."""
        return self.filter(role__in=(User.Role.AUTHOR, User.Role.EDITOR, User.Role.ADMIN))


# ═══════════════════════════════════════════════════
# Custom User Model
# ═══════════════════════════════════════════════════


class User(AbstractUser):
    """
    Custom user model with role-based permissions and profile fields.

    Role hierarchy: ADMIN > EDITOR > AUTHOR > USER
    """

    class Role(models.TextChoices):
        ADMIN = "ADMIN", "Administrator"
        EDITOR = "EDITOR", "Editor"
        AUTHOR = "AUTHOR", "Author"
        USER = "USER", "User"

    # ── Profile fields ────────────────────────────
    avatar = models.ImageField(
        upload_to="avatars/%Y/%m/",
        blank=True,
        verbose_name="avatar",
    )
    bio = models.TextField(
        blank=True,
        verbose_name="biography",
    )
    website = models.URLField(
        blank=True,
        verbose_name="website",
    )

    # ── Role & Permissions ────────────────────────
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.AUTHOR,
        db_index=True,
        verbose_name="role",
    )

    # ── Email Verification ────────────────────────
    email_verified = models.BooleanField(
        default=False,
        verbose_name="email verified",
    )
    email_verification_token = models.CharField(
        max_length=128,
        blank=True,
        verbose_name="email verification token",
    )

    # ── Login Security ────────────────────────────
    login_attempts = models.IntegerField(
        default=0,
        verbose_name="login attempts",
    )
    locked_until = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="locked until",
    )
    last_login_ip = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name="last login IP",
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

    objects = UserManager()

    # Django uses 'email' as the unique identifier for auth by default;
    # our custom manager enforces email uniqueness.
    EMAIL_FIELD = "email"
    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["email"]

    class Meta:
        db_table = "accounts_user"
        verbose_name = "user"
        verbose_name_plural = "users"
        ordering = ["-date_joined"]
        indexes = [
            models.Index(fields=["role"]),
            models.Index(fields=["email_verified"]),
        ]

    def __str__(self):
        return self.get_full_name() or self.username

    @property
    def display_name(self) -> str:
        """Display name: full name → username → email prefix."""
        return self.get_full_name() or self.username

    @property
    def is_locked(self) -> bool:
        """Check if the account is currently locked due to login attempts."""
        if self.locked_until and self.locked_until > timezone.now():
            return True
        return False

    def increment_login_attempts(self):
        """Increment failed login attempts; lock account after 5 failures."""
        self.login_attempts += 1
        if self.login_attempts >= 5:
            self.locked_until = timezone.now() + timezone.timedelta(minutes=15)
        self.save(update_fields=["login_attempts", "locked_until"])

    def reset_login_attempts(self):
        """Reset login attempts after successful login."""
        self.login_attempts = 0
        self.locked_until = None
        self.save(update_fields=["login_attempts", "locked_until"])


# ═══════════════════════════════════════════════════
# Subscriber Model
# ═══════════════════════════════════════════════════


class Subscriber(models.Model):
    """
    Newsletter/email subscription model.

    Subscribers receive email notifications for new posts and updates.
    """

    email = models.EmailField(
        unique=True,
        verbose_name="email",
    )
    name = models.CharField(
        max_length=150,
        blank=True,
        verbose_name="name",
    )
    is_verified = models.BooleanField(
        default=False,
        verbose_name="is verified",
    )
    verification_token = models.CharField(
        max_length=128,
        unique=True,
        blank=True,
        verbose_name="verification token",
    )
    subscribed_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="subscribed at",
    )
    unsubscribed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="unsubscribed at",
    )

    class Meta:
        db_table = "accounts_subscriber"
        verbose_name = "subscriber"
        verbose_name_plural = "subscribers"
        ordering = ["-subscribed_at"]
        indexes = [
            models.Index(fields=["is_verified"]),
            models.Index(fields=["subscribed_at"]),
        ]

    def __str__(self):
        return f"{self.name} <{self.email}>" if self.name else self.email

    @property
    def is_active(self) -> bool:
        """Check if the subscriber is currently active."""
        return self.unsubscribed_at is None
