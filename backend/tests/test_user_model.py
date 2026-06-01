"""Tests for custom User model — creation, roles, lockout, login tracking."""

import pytest
from django.utils import timezone
from apps.accounts.models import User


class TestUserCreation:
    """User creation and field defaults."""

    def test_create_user(self, db):
        user = User.objects.create_user(username="test", email="test@test.com", password="Test1234")
        assert user.username == "test"
        assert user.email == "test@test.com"
        assert user.role == User.Role.AUTHOR
        assert user.email_verified is False
        assert user.is_active is True
        assert user.is_staff is False
        assert user.is_superuser is False
        assert user.check_password("Test1234")

    def test_create_superuser(self, db):
        user = User.objects.create_superuser(username="admin", email="admin@test.com", password="Admin1234")
        assert user.role == User.Role.ADMIN
        assert user.is_staff is True
        assert user.is_superuser is True
        assert user.email_verified is True

    def test_create_user_without_email_raises(self, db):
        with pytest.raises(ValueError, match="Email is required"):
            User.objects.create_user(username="noemail", email="", password="Test1234")

    def test_username_unique(self, db):
        User.objects.create_user(username="John", email="john@test.com", password="Test1234")
        with pytest.raises(Exception):
            User.objects.create_user(username="John", email="john2@test.com", password="Test1234")

    def test_email_duplicate_allowed_at_db_level(self, db):
        """Email uniqueness is enforced at serializer level, not DB level (by design)."""
        u1 = User.objects.create_user(username="u1", email="same@test.com", password="Test1234")
        u2 = User.objects.create_user(username="u2", email="same@test.com", password="Test1234")
        assert u1.email == u2.email  # DB allows duplicates; serializer handles this


class TestUserFields:
    """Profile and security fields."""

    def test_default_role_is_author(self, db):
        user = User.objects.create_user(username="a", email="a@t.com", password="Test1234")
        assert user.role == User.Role.AUTHOR

    def test_role_choices(self, db):
        for role in [User.Role.ADMIN, User.Role.EDITOR, User.Role.AUTHOR, User.Role.USER]:
            user = User.objects.create_user(
                username=f"u_{role}", email=f"{role}@t.com", password="Test1234", role=role
            )
            assert user.role == role

    def test_display_name_returns_full_name(self, db):
        user = User.objects.create_user(
            username="test", email="t@t.com", password="Test1234",
            first_name="Zhang", last_name="San"
        )
        assert user.display_name == "Zhang San"

    def test_display_name_falls_back_to_username(self, db):
        user = User.objects.create_user(username="testuser", email="t@t.com", password="Test1234")
        assert user.display_name == "testuser"

    def test_bio_and_website_save(self, db):
        user = User.objects.create_user(
            username="bio", email="bio@t.com", password="Test1234",
            bio="Hello world", website="https://example.com"
        )
        assert user.bio == "Hello world"
        assert user.website == "https://example.com"


class TestLoginSecurity:
    """Account lockout and login tracking."""

    def test_increment_login_attempts(self, db):
        user = User.objects.create_user(username="lock", email="l@t.com", password="Test1234")
        assert user.login_attempts == 0
        user.increment_login_attempts()
        assert user.login_attempts == 1

    def test_account_locks_after_5_failures(self, db):
        user = User.objects.create_user(username="lock5", email="l5@t.com", password="Test1234")
        for _ in range(5):
            user.increment_login_attempts()
        user.refresh_from_db()
        assert user.login_attempts == 5
        assert user.locked_until is not None
        assert user.is_locked is True

    def test_reset_login_attempts(self, db):
        user = User.objects.create_user(username="reset", email="r@t.com", password="Test1234")
        user.increment_login_attempts()
        user.increment_login_attempts()
        user.reset_login_attempts()
        user.refresh_from_db()
        assert user.login_attempts == 0
        assert user.locked_until is None
        assert user.is_locked is False

    def test_is_locked_returns_false_when_expired(self, db):
        user = User.objects.create_user(username="exp", email="e@t.com", password="Test1234")
        user.locked_until = timezone.now() - timezone.timedelta(minutes=1)
        user.save()
        assert user.is_locked is False

    def test_last_login_ip_tracks(self, db):
        user = User.objects.create_user(username="ip", email="ip@t.com", password="Test1234")
        user.last_login_ip = "192.168.1.1"
        user.save()
        user.refresh_from_db()
        assert user.last_login_ip == "192.168.1.1"


class TestUserStr:
    def test_str_returns_full_name(self, db):
        user = User.objects.create_user(username="s", email="s@t.com", password="Test1234", first_name="Li", last_name="Si")
        assert str(user) == "Li Si"

    def test_str_falls_back_to_username(self, db):
        user = User.objects.create_user(username="testuser", email="t@t.com", password="Test1234")
        assert str(user) == "testuser"
