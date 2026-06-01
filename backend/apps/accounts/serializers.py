"""DRF serializers for accounts app — user profiles + auth flows."""

from django.contrib.auth import authenticate
from django.utils import timezone
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Subscriber, User


# ═══════════════════════════════════════════════════
# User Serializers
# ═══════════════════════════════════════════════════


class UserBriefSerializer(serializers.ModelSerializer):
    """Lightweight user representation for nested display."""

    display_name = serializers.CharField(read_only=True)
    avatar_url = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "display_name",
            "avatar_url",
            "role",
        ]
        read_only_fields = fields

    def get_avatar_url(self, obj):
        if obj.avatar:
            try:
                return obj.avatar.url
            except Exception:
                return ""
        return ""


class UserProfileSerializer(serializers.ModelSerializer):
    """Full user profile — for /api/auth/me/ endpoint."""

    display_name = serializers.CharField(read_only=True)
    avatar_url = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "display_name",
            "avatar",
            "avatar_url",
            "bio",
            "website",
            "role",
            "email_verified",
            "date_joined",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "username",
            "email",
            "email_verified",
            "role",
            "date_joined",
            "created_at",
        ]

    def get_avatar_url(self, obj):
        if obj.avatar:
            try:
                return obj.avatar.url
            except Exception:
                return ""
        return ""


class UserUpdateSerializer(serializers.ModelSerializer):
    """Profile update — avatar, bio, website, name."""

    class Meta:
        model = User
        fields = [
            "first_name",
            "last_name",
            "avatar",
            "bio",
            "website",
        ]


# ═══════════════════════════════════════════════════
# Registration Serializer
# ═══════════════════════════════════════════════════


class RegisterSerializer(serializers.ModelSerializer):
    """User registration with strong password validation."""

    password = serializers.CharField(
        write_only=True,
        min_length=8,
        style={"input_type": "password"},
    )
    password_confirm = serializers.CharField(
        write_only=True,
        style={"input_type": "password"},
    )

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "password",
            "password_confirm",
            "first_name",
            "last_name",
        ]

    def validate_username(self, value):
        if len(value) < 3:
            raise serializers.ValidationError("Username must be at least 3 characters.")
        if not value.isalnum():
            raise serializers.ValidationError("Username can only contain letters and numbers.")
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError("This username is already taken.")
        return value

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def validate_password(self, value):
        """Password strength: 8+ chars, upper+lower+digit."""
        errors = []
        if len(value) < 8:
            errors.append("at least 8 characters")
        if not any(c.isupper() for c in value):
            errors.append("one uppercase letter")
        if not any(c.islower() for c in value):
            errors.append("one lowercase letter")
        if not any(c.isdigit() for c in value):
            errors.append("one digit")
        if errors:
            raise serializers.ValidationError(f"Password must contain: {', '.join(errors)}.")
        return value

    def validate(self, data):
        if data.get("password") != data.get("password_confirm"):
            raise serializers.ValidationError({"password_confirm": "Passwords do not match."})
        return data

    def create(self, validated_data):
        validated_data.pop("password_confirm", None)
        password = validated_data.pop("password")
        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
        return user


# ═══════════════════════════════════════════════════
# Auth — Login / Token
# ═══════════════════════════════════════════════════


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom JWT token serializer with security checks:

    - Verifies user is_active (disabled users cannot log in)
    - Checks account lockout (too many failed attempts)
    - Tracks login attempts & IP for brute-force protection
    - Adds custom claims: role, email_verified, display_name
    """

    def validate(self, attrs):
        username = attrs.get("username", "")
        password = attrs.get("password", "")

        # Find user by username
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise serializers.ValidationError("Invalid username or password.")

        # Check if account is disabled
        if not user.is_active:
            raise serializers.ValidationError("This account has been disabled. Contact support.")

        # Check account lockout
        if user.is_locked:
            remaining = (user.locked_until - timezone.now()).seconds // 60
            raise serializers.ValidationError(
                f"Account locked due to too many failed attempts. Try again in {remaining} minutes."
            )

        # Authenticate
        authenticated_user = authenticate(request=self.context.get("request"), username=username, password=password)

        if not authenticated_user:
            # Track failed login
            user.increment_login_attempts()
            remaining = max(0, 5 - user.login_attempts)
            msg = "Invalid username or password."
            if remaining > 0:
                msg += f" {remaining} attempt(s) remaining."
            raise serializers.ValidationError(msg)

        # Successful login — reset attempts & track IP
        user.reset_login_attempts()
        self._update_login_meta(user)

        # Generate tokens with custom claims
        refresh = self.get_token(user)
        refresh["role"] = user.role
        refresh["email_verified"] = user.email_verified
        refresh["display_name"] = user.display_name

        data = {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "user": {
                "id": user.id,
                "username": user.username,
                "display_name": user.display_name,
                "email": user.email,
                "role": user.role,
                "email_verified": user.email_verified,
                "avatar_url": user.avatar.url if user.avatar else "",
            },
        }

        return data

    def _update_login_meta(self, user):
        """Update last_login_ip from request metadata."""
        request = self.context.get("request")
        if request:
            from .utils import get_client_ip

            user.last_login_ip = get_client_ip(request)
            user.save(update_fields=["last_login_ip"])


class LogoutSerializer(serializers.Serializer):
    """Blacklist a refresh token on logout."""

    refresh = serializers.CharField()

    def validate_refresh(self, value):
        return value


# ═══════════════════════════════════════════════════
# Auth — Password Management
# ═══════════════════════════════════════════════════


class ChangePasswordSerializer(serializers.Serializer):
    """Change password — requires old password for verification."""

    old_password = serializers.CharField(write_only=True, style={"input_type": "password"})
    new_password = serializers.CharField(write_only=True, min_length=8, style={"input_type": "password"})
    new_password_confirm = serializers.CharField(write_only=True, style={"input_type": "password"})

    def validate_old_password(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Current password is incorrect.")
        return value

    def validate_new_password(self, value):
        errors = []
        if len(value) < 8:
            errors.append("at least 8 characters")
        if not any(c.isupper() for c in value):
            errors.append("one uppercase letter")
        if not any(c.islower() for c in value):
            errors.append("one lowercase letter")
        if not any(c.isdigit() for c in value):
            errors.append("one digit")
        if errors:
            raise serializers.ValidationError(f"Password must contain: {', '.join(errors)}.")
        return value

    def validate(self, data):
        if data.get("new_password") != data.get("new_password_confirm"):
            raise serializers.ValidationError({"new_password_confirm": "Passwords do not match."})
        if data.get("new_password") == data.get("old_password"):
            raise serializers.ValidationError({"new_password": "New password must differ from the old password."})
        return data


class ForgotPasswordSerializer(serializers.Serializer):
    """Request a password reset email."""

    email = serializers.EmailField()

    def validate_email(self, value):
        if not User.objects.filter(email__iexact=value, is_active=True).exists():
            # Don't reveal whether the email exists (security best practice)
            pass
        return value


class ResetPasswordSerializer(serializers.Serializer):
    """Reset password using a time-limited token."""

    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True, min_length=8, style={"input_type": "password"})
    new_password_confirm = serializers.CharField(write_only=True, style={"input_type": "password"})

    def validate_token(self, value):
        from .utils import verify_password_reset_token

        user_id = verify_password_reset_token(value)
        if user_id is None:
            raise serializers.ValidationError("Invalid or expired reset token.")
        try:
            user = User.objects.get(pk=user_id, is_active=True)
        except User.DoesNotExist:
            raise serializers.ValidationError("Invalid or expired reset token.")
        self.context["reset_user"] = user
        return value

    def validate_new_password(self, value):
        errors = []
        if len(value) < 8:
            errors.append("at least 8 characters")
        if not any(c.isupper() for c in value):
            errors.append("one uppercase letter")
        if not any(c.islower() for c in value):
            errors.append("one lowercase letter")
        if not any(c.isdigit() for c in value):
            errors.append("one digit")
        if errors:
            raise serializers.ValidationError(f"Password must contain: {', '.join(errors)}.")
        return value

    def validate(self, data):
        if data.get("new_password") != data.get("new_password_confirm"):
            raise serializers.ValidationError({"new_password_confirm": "Passwords do not match."})
        return data


# ═══════════════════════════════════════════════════
# Auth — Email Verification
# ═══════════════════════════════════════════════════


class VerifyEmailSerializer(serializers.Serializer):
    """Verify email address with a verification token."""

    token = serializers.CharField()

    def validate_token(self, value):
        try:
            user = User.objects.get(email_verification_token=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("Invalid or expired verification token.")
        self.context["verify_user"] = user
        return value


# ═══════════════════════════════════════════════════
# Subscriber Serializers
# ═══════════════════════════════════════════════════


class SubscriberSerializer(serializers.ModelSerializer):
    """Subscriber read — admin only."""

    class Meta:
        model = Subscriber
        fields = [
            "id",
            "email",
            "name",
            "is_verified",
            "subscribed_at",
            "unsubscribed_at",
        ]
        read_only_fields = ["is_verified", "subscribed_at"]


class SubscriberCreateSerializer(serializers.ModelSerializer):
    """Public subscription — email only."""

    class Meta:
        model = Subscriber
        fields = ["email", "name"]

    def validate_email(self, value):
        if Subscriber.objects.filter(email=value, unsubscribed_at__isnull=True).exists():
            raise serializers.ValidationError("This email is already subscribed.")
        return value
