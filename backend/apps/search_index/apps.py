"""App configuration for search_index."""

from django.apps import AppConfig


class SearchIndexConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.search_index"
    verbose_name = "Search Index"
