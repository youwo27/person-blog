"""
Root URL configuration for person-blog.

- Django admin: /admin/
- API documentation: /api/docs/ (Swagger), /api/redoc/ (ReDoc)
- API schema: /api/schema/
- Health check: /api/health/
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import HttpResponse
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView


def health_check(request):
    """Simple health check endpoint — returns 200 OK."""
    return HttpResponse("OK", content_type="text/plain")


urlpatterns = [
    # ── Django Admin ──────────────────────────────
    path("admin/", admin.site.urls),

    # ── Health Check ──────────────────────────────
    path("api/health/", health_check, name="health-check"),

    # ── API Documentation (OpenAPI 3.0) ───────────
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path(
        "api/redoc/",
        SpectacularRedocView.as_view(url_name="schema"),
        name="redoc",
    ),

    # ── API v1 ─────────────────────────────────────
    path("api/v1/", include("config.api_urls")),
]

# ── Serve media files during development ──────────
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
