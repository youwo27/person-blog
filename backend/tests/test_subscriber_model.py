"""Tests for Subscriber model."""

import pytest
from datetime import timedelta
from django.utils import timezone
from apps.accounts.models import Subscriber


class TestSubscriber:
    def test_create_subscriber(self, db):
        sub = Subscriber.objects.create(email="test@test.com", name="Test User")
        assert sub.email == "test@test.com"
        assert sub.name == "Test User"
        assert sub.is_verified is False
        assert sub.is_active is True

    def test_unsubscribed_is_inactive(self, db):
        sub = Subscriber.objects.create(
            email="unsub@test.com", unsubscribed_at=timezone.now()
        )
        assert sub.is_active is False

    def test_str_with_name(self, db):
        sub = Subscriber.objects.create(email="a@b.com", name="Alice")
        assert str(sub) == "Alice <a@b.com>"

    def test_str_without_name(self, db):
        sub = Subscriber.objects.create(email="a@b.com")
        assert str(sub) == "a@b.com"

    def test_email_unique(self, db):
        Subscriber.objects.create(email="dup@test.com")
        with pytest.raises(Exception):
            Subscriber.objects.create(email="dup@test.com")
