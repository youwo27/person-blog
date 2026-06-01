"""Tests for Notification model."""

import pytest
from apps.notifications.models import Notification


class TestNotification:
    def test_create_notification(self, db, regular_user, admin_user):
        notif = Notification.objects.create(
            recipient=regular_user,
            actor=admin_user,
            type=Notification.Type.POST_COMMENT,
            message="Admin commented on your post",
        )
        assert notif.recipient == regular_user
        assert notif.actor == admin_user
        assert notif.type == Notification.Type.POST_COMMENT
        assert notif.is_read is False
        assert "Admin commented" in str(notif)

    def test_notification_types(self, db, regular_user, admin_user):
        for ntype in Notification.Type.values:
            notif = Notification.objects.create(
                recipient=regular_user,
                actor=admin_user,
                type=ntype,
                message=f"Test {ntype}",
            )
            assert notif.type == ntype

    def test_mark_as_read(self, db, regular_user, admin_user):
        notif = Notification.objects.create(
            recipient=regular_user, actor=admin_user,
            type=Notification.Type.COMMENT_REPLY, message="Reply"
        )
        assert notif.is_read is False
        notif.is_read = True
        notif.save()
        notif.refresh_from_db()
        assert notif.is_read is True

    def test_notification_ordering(self, db, regular_user, admin_user):
        n1 = Notification.objects.create(recipient=regular_user, actor=admin_user, type="POST_COMMENT", message="Old")
        n2 = Notification.objects.create(recipient=regular_user, actor=admin_user, type="POST_COMMENT", message="New")
        notifs = Notification.objects.all()
        assert notifs[0] == n2  # Newest first


class TestSiteSetting:
    def test_create_setting(self, db):
        from apps.blog.models import SiteSetting
        setting = SiteSetting.objects.create(key="blog_title", value="My Blog", description="Title")
        assert setting.key == "blog_title"
        assert setting.value == "My Blog"
        assert str(setting) == "blog_title"

    def test_key_unique(self, db):
        from apps.blog.models import SiteSetting
        SiteSetting.objects.create(key="unique_key", value="A")
        with pytest.raises(Exception):
            SiteSetting.objects.create(key="unique_key", value="B")
