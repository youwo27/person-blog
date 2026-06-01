"""Pytest fixtures — factories, test data, shared helpers."""

import pytest
from django.utils import timezone


@pytest.fixture(autouse=True)
def enable_db_access_for_all_tests(db):
    """Enable database access for all tests."""
    pass


@pytest.fixture
def admin_user():
    from apps.accounts.models import User
    return User.objects.create_superuser(
        username="admin",
        email="admin@test.com",
        password="admin123456",
        role=User.Role.ADMIN,
        email_verified=True,
    )


@pytest.fixture
def editor_user():
    from apps.accounts.models import User
    return User.objects.create_user(
        username="editor",
        email="editor@test.com",
        password="editor123456",
        role=User.Role.EDITOR,
        email_verified=True,
    )


@pytest.fixture
def author_user():
    from apps.accounts.models import User
    return User.objects.create_user(
        username="author",
        email="author@test.com",
        password="author123456",
        role=User.Role.AUTHOR,
        email_verified=True,
    )


@pytest.fixture
def regular_user():
    from apps.accounts.models import User
    return User.objects.create_user(
        username="user",
        email="user@test.com",
        password="user123456",
        role=User.Role.USER,
        email_verified=False,
    )


@pytest.fixture
def category():
    from apps.blog.models import Category
    return Category.objects.create(
        name="Python",
        slug="python",
        description="Python programming",
        order=1,
        is_active=True,
    )


@pytest.fixture
def subcategory(category):
    from apps.blog.models import Category
    return Category.objects.create(
        name="Django",
        slug="django",
        description="Django framework",
        parent=category,
        order=1,
        is_active=True,
    )


@pytest.fixture
def tag():
    from apps.blog.models import Tag
    return Tag.objects.create(name="Django", slug="django")


@pytest.fixture
def published_post(author_user, category, tag):
    from apps.blog.models import Post
    post = Post.objects.create(
        title="Test Post",
        slug="test-post",
        content="This is a test post content with enough text to be meaningful.",
        author=author_user,
        category=category,
        status=Post.Status.PUBLISHED,
        published_at=timezone.now(),
        view_count=100,
        reading_time_minutes=5,
    )
    post.tags.add(tag)
    return post


@pytest.fixture
def draft_post(author_user):
    from apps.blog.models import Post
    return Post.objects.create(
        title="Draft Post",
        slug="draft-post",
        content="Draft content here.",
        author=author_user,
        status=Post.Status.DRAFT,
    )


@pytest.fixture
def comment(published_post, regular_user):
    from apps.comments.models import Comment
    return Comment.objects.create(
        post=published_post,
        author=regular_user,
        content="Great article!",
        is_approved=True,
    )


@pytest.fixture
def media_item(admin_user):
    from apps.media_library.models import Media
    return Media.objects.create(
        filename="test.jpg",
        original_filename="test.jpg",
        mime_type="image/jpeg",
        file_size=102400,
        width=800,
        height=600,
        alt_text="test image",
        uploaded_by=admin_user,
    )
