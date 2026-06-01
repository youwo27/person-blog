"""Tests for Comment and CommentLike models."""

import pytest
from apps.comments.models import Comment, CommentLike


class TestComment:
    def test_create_comment(self, published_post, regular_user):
        comment = Comment.objects.create(
            post=published_post, author=regular_user,
            content="Great post!", is_approved=True
        )
        assert comment.content == "Great post!"
        assert comment.is_approved is True
        assert comment.is_spam is False
        assert comment.likes_count == 0

    def test_comment_default_not_approved(self, published_post, regular_user):
        comment = Comment.objects.create(post=published_post, author=regular_user, content="Nice")
        assert comment.is_approved is False  # Default is False

    def test_nested_reply(self, published_post, regular_user, author_user):
        parent = Comment.objects.create(post=published_post, author=author_user, content="Parent", is_approved=True)
        reply = Comment.objects.create(post=published_post, author=regular_user, content="Reply", parent=parent, is_approved=True)
        assert reply.parent == parent
        assert parent.replies.count() == 1
        assert reply.is_top_level is False
        assert parent.is_top_level is True

    def test_comment_nesting_level(self, published_post, regular_user, author_user, admin_user):
        level0 = Comment.objects.create(post=published_post, author=admin_user, content="L0", is_approved=True)
        level1 = Comment.objects.create(post=published_post, author=regular_user, content="L1", parent=level0, is_approved=True)
        level2 = Comment.objects.create(post=published_post, author=author_user, content="L2", parent=level1, is_approved=True)
        assert level0.nesting_level == 0
        assert level1.nesting_level == 1
        assert level2.nesting_level == 2

    def test_approve_method(self, published_post, regular_user):
        comment = Comment.objects.create(post=published_post, author=regular_user, content="Pending")
        assert comment.is_approved is False
        comment.approve()
        comment.refresh_from_db()
        assert comment.is_approved is True
        assert comment.is_spam is False

    def test_mark_spam_method(self, published_post, regular_user):
        comment = Comment.objects.create(post=published_post, author=regular_user, content="Buy now!", is_approved=True)
        comment.mark_spam()
        comment.refresh_from_db()
        assert comment.is_spam is True
        assert comment.is_approved is False

    def test_comment_str(self, published_post, regular_user):
        comment = Comment.objects.create(post=published_post, author=regular_user, content="Hi")
        assert "Comment by" in str(comment)


class TestCommentLike:
    def test_create_like(self, published_post, regular_user, author_user):
        comment = Comment.objects.create(post=published_post, author=author_user, content="C", is_approved=True)
        like = CommentLike.objects.create(comment=comment, user=regular_user)
        assert like.comment == comment
        assert like.user == regular_user

    def test_unique_together(self, published_post, regular_user, author_user):
        comment = Comment.objects.create(post=published_post, author=author_user, content="C", is_approved=True)
        CommentLike.objects.create(comment=comment, user=regular_user)
        with pytest.raises(Exception):
            CommentLike.objects.create(comment=comment, user=regular_user)


class TestCommentSpamDetection:
    def test_spam_keywords_detected(self):
        from apps.comments.spam_detector import detect_spam
        is_spam, reason = detect_spam("Buy now! Click here to get free money online!")
        assert is_spam is True
        assert len(reason) > 0

    def test_clean_content_passes(self):
        from apps.comments.spam_detector import detect_spam
        is_spam, reason = detect_spam("Great article! I learned a lot from this post.")
        assert is_spam is False

    def test_too_many_links_detected(self):
        from apps.comments.spam_detector import detect_spam
        content = "Check this http://a.com and http://b.com and http://c.com"
        is_spam, reason = detect_spam(content)
        assert is_spam is True
        assert "links" in reason.lower()

    def test_excessive_caps_detected(self):
        from apps.comments.spam_detector import detect_spam
        content = "THIS IS REALLY AMAZING YOU MUST BUY THIS PRODUCT NOW CLICK HERE PLEASE"
        is_spam, reason = detect_spam(content)
        assert is_spam is True
