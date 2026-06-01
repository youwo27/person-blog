"""Factory Boy factories for all models."""
import factory
from django.utils import timezone


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "accounts.User"

    username = factory.Sequence(lambda n: f"user_{n}")
    email = factory.Sequence(lambda n: f"user_{n}@test.com")
    password = factory.PostGenerationMethodCall("set_password", "Test1234")
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    role = "AUTHOR"
    email_verified = True
    is_active = True
    bio = factory.Faker("text", max_nb_chars=200)

    class Params:
        admin = factory.Trait(role="ADMIN", is_staff=True, is_superuser=True)
        editor = factory.Trait(role="EDITOR")
        unverified = factory.Trait(email_verified=False)
        locked = factory.Trait(
            login_attempts=5,
            locked_until=factory.LazyFunction(lambda: timezone.now() + timezone.timedelta(minutes=15)),
        )


class CategoryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "blog.Category"

    name = factory.Sequence(lambda n: f"Category {n}")
    slug = factory.Sequence(lambda n: f"category-{n}")
    description = factory.Faker("text", max_nb_chars=100)
    order = 0
    is_active = True

    class Params:
        with_parent = factory.Trait(
            parent=factory.SubFactory("tests.factories.CategoryFactory"),
        )


class TagFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "blog.Tag"

    name = factory.Sequence(lambda n: f"Tag {n}")
    slug = factory.Sequence(lambda n: f"tag-{n}")


class PostFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "blog.Post"

    title = factory.Sequence(lambda n: f"Post Title {n}")
    slug = factory.Sequence(lambda n: f"post-slug-{n}")
    content = factory.Faker("paragraph", nb_sentences=10)
    author = factory.SubFactory(UserFactory)
    category = factory.SubFactory(CategoryFactory)
    status = "DRAFT"

    class Params:
        published = factory.Trait(
            status="PUBLISHED",
            published_at=factory.LazyFunction(timezone.now),
        )
        featured = factory.Trait(is_featured=True)
        archived = factory.Trait(status="ARCHIVED")
        scheduled = factory.Trait(
            status="SCHEDULED",
            scheduled_at=factory.LazyFunction(lambda: timezone.now() + timezone.timedelta(days=7)),
        )
        with_tags = factory.Trait(
            tags=factory.PostGeneration(lambda obj, create, extracted, **kwargs: [
                TagFactory.create() for _ in range(3)
            ] if create else [])
        )

    @factory.post_generation
    def tags(self, create, extracted, **kwargs):
        if not create or not extracted:
            return
        self.tags.add(*extracted)


class CommentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "comments.Comment"

    post = factory.SubFactory(PostFactory, published=True)
    author = factory.SubFactory(UserFactory)
    content = factory.Faker("sentence")
    is_approved = True
    is_spam = False

    class Params:
        pending = factory.Trait(is_approved=False)
        spam = factory.Trait(is_spam=True)
        with_parent = factory.Trait(
            parent=factory.SubFactory("tests.factories.CommentFactory"),
        )


class CommentLikeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "comments.CommentLike"

    comment = factory.SubFactory(CommentFactory)
    user = factory.SubFactory(UserFactory)


class MediaFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "media_library.Media"

    filename = factory.Sequence(lambda n: f"file_{n}.jpg")
    original_filename = factory.Sequence(lambda n: f"original_{n}.jpg")
    mime_type = "image/jpeg"
    file_size = 102400
    width = 800
    height = 600
    uploaded_by = factory.SubFactory(UserFactory)

    class Params:
        pdf = factory.Trait(
            filename=factory.Sequence(lambda n: f"doc_{n}.pdf"),
            mime_type="application/pdf",
            width=None,
            height=None,
        )


class SubscriberFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "accounts.Subscriber"

    email = factory.Sequence(lambda n: f"subscriber_{n}@test.com")
    name = factory.Faker("name")
    is_verified = True

    class Params:
        unverified = factory.Trait(is_verified=False)


class NotificationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "notifications.Notification"

    recipient = factory.SubFactory(UserFactory)
    actor = factory.SubFactory(UserFactory)
    type = "POST_COMMENT"
    message = factory.Faker("sentence")
    is_read = False

    class Params:
        read = factory.Trait(is_read=True)


class SiteSettingFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "blog.SiteSetting"

    key = factory.Sequence(lambda n: f"setting_key_{n}")
    value = factory.Faker("word")
    description = factory.Faker("sentence")
