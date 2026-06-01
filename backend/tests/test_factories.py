"""Smoke tests — verify all factories produce valid models."""

import pytest
from tests.factories import (
    UserFactory, CategoryFactory, TagFactory, PostFactory,
    CommentFactory, CommentLikeFactory, MediaFactory,
    SubscriberFactory, NotificationFactory, SiteSettingFactory,
)


class TestUserFactory:
    def test_default_user(self, db):
        user = UserFactory()
        assert user.username.startswith("user_")
        assert user.role == "AUTHOR"
        assert user.email_verified is True
        assert user.check_password("Test1234")

    def test_admin_trait(self, db):
        user = UserFactory(admin=True)
        assert user.role == "ADMIN"
        assert user.is_staff is True
        assert user.is_superuser is True

    def test_editor_trait(self, db):
        user = UserFactory(editor=True)
        assert user.role == "EDITOR"

    def test_unverified_trait(self, db):
        user = UserFactory(unverified=True)
        assert user.email_verified is False

    def test_locked_trait(self, db):
        user = UserFactory(locked=True)
        assert user.login_attempts == 5
        assert user.is_locked is True

    def test_batch_create(self, db):
        users = UserFactory.create_batch(5)
        assert len(users) == 5
        assert all(u.email_verified for u in users)


class TestPostFactory:
    def test_default_post_is_draft(self, db):
        post = PostFactory()
        assert post.status == "DRAFT"
        assert post.title.startswith("Post Title")

    def test_published_trait(self, db):
        post = PostFactory(published=True)
        assert post.status == "PUBLISHED"
        assert post.published_at is not None

    def test_featured_trait(self, db):
        post = PostFactory(featured=True)
        assert post.is_featured is True

    def test_archived_trait(self, db):
        post = PostFactory(archived=True)
        assert post.status == "ARCHIVED"

    def test_scheduled_trait(self, db):
        post = PostFactory(scheduled=True)
        assert post.status == "SCHEDULED"
        assert post.scheduled_at is not None


class TestCommentFactory:
    def test_default_comment(self, db):
        comment = CommentFactory()
        assert comment.is_approved is True
        assert comment.is_spam is False

    def test_pending_trait(self, db):
        comment = CommentFactory(pending=True)
        assert comment.is_approved is False

    def test_spam_trait(self, db):
        comment = CommentFactory(spam=True)
        assert comment.is_spam is True


class TestMediaFactory:
    def test_image_media(self, db):
        media = MediaFactory()
        assert media.is_image is True
        assert media.mime_type == "image/jpeg"

    def test_pdf_media(self, db):
        media = MediaFactory(pdf=True)
        assert media.is_image is False
        assert media.mime_type == "application/pdf"


class TestSubscriberFactory:
    def test_default(self, db):
        sub = SubscriberFactory()
        assert sub.is_verified is True

    def test_unverified(self, db):
        sub = SubscriberFactory(unverified=True)
        assert sub.is_verified is False


class TestNotificationFactory:
    def test_default(self, db):
        notif = NotificationFactory()
        assert notif.is_read is False
        assert notif.type == "POST_COMMENT"

    def test_read_trait(self, db):
        notif = NotificationFactory(read=True)
        assert notif.is_read is True
