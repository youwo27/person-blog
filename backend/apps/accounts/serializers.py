"""DRF serializers for accounts app."""

from rest_framework import serializers

from .models import Subscriber, User


# ═══════════════════════════════════════════════════
# User Serializers
# ═══════════════════════════════════════════════════


class UserBriefSerializer(serializers.ModelSerializer):
    """Lightweight user representation for nested display."""

    display_name = serializers.CharField(read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "display_name",
            "avatar",
            "role",
        ]
        read_only_fields = fields


class UserProfileSerializer(serializers.ModelSerializer):
    """Full user profile — for /api/me/ endpoint."""

    display_name = serializers.CharField(read_only=True)

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
            "bio",
            "website",
            "role",
            "email_verified",
            "date_joined",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "email",
            "email_verified",
            "role",
            "date_joined",
            "created_at",
        ]


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


class RegisterSerializer(serializers.ModelSerializer):
    """User registration with password validation."""

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
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("A user with this username already exists.")
        return value

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def validate_password(self, value):
        """Password strength validation."""
        if len(value) < 8:
            raise serializers.ValidationError("Password must be at least 8 characters.")
        if not any(c.isupper() for c in value):
            raise serializers.ValidationError("Password must contain at least one uppercase letter.")
        if not any(c.islower() for c in value):
            raise serializers.ValidationError("Password must contain at least one lowercase letter.")
        if not any(c.isdigit() for c in value):
            raise serializers.ValidationError("Password must contain at least one digit.")
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
