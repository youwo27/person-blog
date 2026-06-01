"""Tests for Post, Category, Tag models — CRUD, status workflow, queries."""

import pytest
from datetime import timedelta
from django.utils import timezone
from apps.blog.models import Post, Category, Tag


class TestCategory:
    def test_create_category(self, db):
        cat = Category.objects.create(name="Python", slug="python")
        assert cat.name == "Python"
        assert cat.slug == "python"
        assert cat.is_active is True
        assert cat.order == 0

    def test_category_str(self, db):
        cat = Category.objects.create(name="Python", slug="python")
        assert str(cat) == "Python"

    def test_category_with_parent_str(self, db):
        parent = Category.objects.create(name="Tech", slug="tech")
        child = Category.objects.create(name="Python", slug="python", parent=parent)
        assert str(child) == "Tech > Python"

    def test_category_is_root(self, db):
        parent = Category.objects.create(name="Tech", slug="tech")
        child = Category.objects.create(name="Python", slug="python", parent=parent)
        assert parent.is_root is True
        assert child.is_root is False

    def test_category_children_active(self, db):
        parent = Category.objects.create(name="Tech", slug="tech")
        Category.objects.create(name="Active", slug="active", parent=parent, is_active=True)
        Category.objects.create(name="Inactive", slug="inactive", parent=parent, is_active=False)
        assert parent.children_active.count() == 1

    def test_category_slug_unique(self, db):
        Category.objects.create(name="A", slug="a")
        with pytest.raises(Exception):
            Category.objects.create(name="B", slug="a")


class TestTag:
    def test_create_tag(self, db):
        tag = Tag.objects.create(name="Django", slug="django")
        assert tag.name == "Django"
        assert tag.slug == "django"
        assert str(tag) == "Django"

    def test_tag_slug_unique(self, db):
        Tag.objects.create(name="A", slug="a")
        with pytest.raises(Exception):
            Tag.objects.create(name="B", slug="a")


class TestPostCreation:
    def test_create_post(self, db, author_user, category):
        post = Post.objects.create(
            title="My Post", slug="my-post", content="Hello world content here.",
            author=author_user, category=category, status=Post.Status.DRAFT
        )
        assert post.title == "My Post"
        assert post.slug == "my-post"
        assert post.status == Post.Status.DRAFT
        assert post.author == author_user
        assert post.category == category
        assert str(post) == "My Post"

    def test_auto_slug_generation(self, db, author_user):
        post = Post.objects.create(title="Auto Slug Test", content="Content", author=author_user)
        assert post.slug != ""
        assert len(post.slug) > 0

    def test_auto_reading_time(self, db, author_user):
        post = Post.objects.create(
            title="Reading Time Test",
            content="word " * 500,  # ~500 words
            author=author_user,
        )
        assert post.reading_time_minutes >= 1

    def test_auto_excerpt(self, db, author_user):
        long_content = "This is a very long content. " * 50
        post = Post.objects.create(title="Excerpt Test", content=long_content, author=author_user)
        assert post.excerpt != ""
        assert len(post.excerpt) <= 260  # 250 + buffer

    def test_auto_published_at_on_publish(self, db, author_user):
        post = Post.objects.create(title="Pub Test", content="Content", author=author_user)
        assert post.published_at is None
        post.status = Post.Status.PUBLISHED
        post.save()
        assert post.published_at is not None

    def test_auto_meta_title(self, db, author_user):
        post = Post.objects.create(title="SEO Test Title", content="Content", author=author_user)
        assert post.meta_title == "SEO Test Title"

    def test_cover_image_url_empty(self, db, author_user):
        post = Post.objects.create(title="No Cover", content="Content", author=author_user)
        assert post.cover_image_url == ""


class TestPostStatus:
    def test_publish_method(self, db, author_user):
        post = Post.objects.create(title="Pub", content="Content", author=author_user, status=Post.Status.DRAFT)
        post.publish()
        post.refresh_from_db()
        assert post.status == Post.Status.PUBLISHED
        assert post.published_at is not None

    def test_archive_method(self, db, author_user):
        post = Post.objects.create(title="Arch", content="Content", author=author_user, status=Post.Status.PUBLISHED)
        post.archive()
        post.refresh_from_db()
        assert post.status == Post.Status.ARCHIVED

    def test_increment_view_count(self, db, author_user):
        post = Post.objects.create(title="View", content="Content", author=author_user, view_count=0)
        post.increment_view_count()
        post.refresh_from_db()
        assert post.view_count == 1


class TestPostManager:
    def test_published_manager(self, db, author_user):
        Post.objects.create(title="Pub", content="C", author=author_user, status=Post.Status.PUBLISHED, published_at=timezone.now())
        Post.objects.create(title="Draft", content="C", author=author_user, status=Post.Status.DRAFT)
        assert Post.objects.published().count() == 1

    def test_featured_manager(self, db, author_user):
        Post.objects.create(title="F", content="C", author=author_user, status=Post.Status.PUBLISHED, published_at=timezone.now(), is_featured=True)
        Post.objects.create(title="NF", content="C", author=author_user, status=Post.Status.PUBLISHED, published_at=timezone.now(), is_featured=False)
        assert Post.objects.featured().count() == 1

    def test_drafted_manager(self, db, author_user):
        Post.objects.create(title="D", content="C", author=author_user, status=Post.Status.DRAFT)
        assert Post.objects.drafted().count() == 1

    def test_by_author_manager(self, db, author_user, editor_user):
        Post.objects.create(title="A", content="C", author=author_user, status=Post.Status.PUBLISHED, published_at=timezone.now())
        Post.objects.create(title="B", content="C", author=editor_user, status=Post.Status.PUBLISHED, published_at=timezone.now())
        assert Post.objects.by_author(author_user).count() == 1


class TestPostNavigation:
    def test_prev_next_posts(self, db, author_user):
        now = timezone.now()
        p1 = Post.objects.create(title="First", content="C", author=author_user, status=Post.Status.PUBLISHED, published_at=now - timedelta(days=3))
        p2 = Post.objects.create(title="Second", content="C", author=author_user, status=Post.Status.PUBLISHED, published_at=now - timedelta(days=2))
        p3 = Post.objects.create(title="Third", content="C", author=author_user, status=Post.Status.PUBLISHED, published_at=now - timedelta(days=1))

        assert p2.prev_post == p1
        assert p2.next_post == p3
        assert p1.prev_post is None
        assert p3.next_post is None

    def test_comment_count(self, db, published_post, regular_user):
        from apps.comments.models import Comment
        assert published_post.comment_count == 0
        Comment.objects.create(post=published_post, author=regular_user, content="Nice!", is_approved=True)
        Comment.objects.create(post=published_post, author=regular_user, content="Spam", is_approved=False)
        assert published_post.comment_count == 1  # Only approved


class TestPostTags:
    def test_add_tags(self, db, author_user):
        post = Post.objects.create(title="Tagged", content="C", author=author_user)
        t1 = Tag.objects.create(name="Python", slug="python")
        t2 = Tag.objects.create(name="Django", slug="django2")
        post.tags.add(t1, t2)
        assert post.tags.count() == 2
