"""
API v1 URL configuration.

All API endpoints are registered here with Django REST Framework's DefaultRouter.
The router is included at /api/v1/ in config/urls.py.
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.accounts.views import SubscriberViewSet
from apps.blog.views import CategoryViewSet, PostViewSet, SiteSettingViewSet, TagViewSet
from apps.comments.views import CommentViewSet
from apps.media_library.views import MediaViewSet
from apps.notifications.views import NotificationViewSet

# ── Main Router ──────────────────────────────────
router = DefaultRouter()
router.register(r"posts", PostViewSet, basename="post")
router.register(r"categories", CategoryViewSet, basename="category")
router.register(r"tags", TagViewSet, basename="tag")
router.register(r"comments", CommentViewSet, basename="comment")
router.register(r"media", MediaViewSet, basename="media")
router.register(r"settings", SiteSettingViewSet, basename="sitesetting")
router.register(r"subscribers", SubscriberViewSet, basename="subscriber")
router.register(r"notifications", NotificationViewSet, basename="notification")

urlpatterns = [
    path("", include(router.urls)),
    path("auth/", include("apps.accounts.urls")),
]
