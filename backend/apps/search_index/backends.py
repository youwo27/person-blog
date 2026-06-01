"""
Search backends — pluggable search engine implementations.

- PostgresFTSBackend: PostgreSQL full-text search (default, zero-dependency)
- ElasticsearchBackend: Elasticsearch 8.x (optional, requires ES running)
"""

from django.conf import settings
from django.db import connection
from django.db.models import F, Q, TextField, Value
from django.db.models.functions import Cast


class PostgresFTSBackend:
    """
    Search backend with automatic database adaptation.

    PostgreSQL: Uses to_tsvector + ts_query + ts_rank (weighted FTS)
    SQLite:      Uses ILIKE + icontains fallback
    """

    def _is_postgres(self):
        return connection.vendor == "postgresql"

    def search(self, queryset, query: str):
        if not query or len(query.strip()) < 2:
            return queryset
        query = query.strip()

        if self._is_postgres():
            return self._pg_search(queryset, query)
        return self._sqlite_search(queryset, query)

    def _pg_search(self, queryset, query: str):
        """PostgreSQL: ranked FTS with trigram fallback."""
        from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector, TrigramSimilarity

        search_query = SearchQuery(query, config="simple", search_type="websearch")
        search_vector = SearchVector("search_vector", config="simple")

        return (
            queryset
            .annotate(
                rank=SearchRank(search_vector, search_query),
                title_similarity=TrigramSimilarity("title", query),
            )
            .filter(
                Q(search_vector__icontains=query)
                | Q(title__icontains=query)
                | Q(title_similarity__gt=0.1)
            )
            .order_by("-rank", "-title_similarity", "-published_at")
        )

    def _sqlite_search(self, queryset, query: str):
        """SQLite: ILIKE-based search."""
        return queryset.filter(
            Q(title__icontains=query)
            | Q(content__icontains=query)
            | Q(excerpt__icontains=query)
        ).order_by("-published_at")

    def suggest(self, queryset, prefix: str, limit: int = 8):
        """Autocomplete suggestions based on title prefix."""
        if not prefix or len(prefix.strip()) < 1:
            return queryset.none()
        prefix = prefix.strip()

        if self._is_postgres():
            from django.contrib.postgres.search import TrigramSimilarity
            return (
                queryset
                .annotate(similarity=TrigramSimilarity("title", prefix))
                .filter(similarity__gt=0.15)
                .order_by("-similarity")
                .values("id", "title", "slug")
            )[:limit]

        # SQLite: simple icontains
        return queryset.filter(title__icontains=prefix).values("id", "title", "slug").order_by("-published_at")[:limit]


class ElasticsearchBackend:
    """
    Elasticsearch 8.x search backend (optional).

    Requires:
    - elasticsearch-py installed
    - ES_HOST configured in settings
    - Index created via `python manage.py es_sync --create`
    """

    def __init__(self):
        self.client = None
        self.index_name = getattr(settings, "ES_INDEX_NAME", "blog_posts")

    def _get_client(self):
        if self.client is None:
            try:
                from elasticsearch import Elasticsearch
            except ImportError:
                raise ImportError("elasticsearch-py required. Install with: pip install elasticsearch")
            es_host = getattr(settings, "ES_HOST", "http://localhost:9200")
            self.client = Elasticsearch(es_host)
        return self.client

    def search(self, queryset, query: str):
        if not query or len(query.strip()) < 2:
            return queryset
        try:
            client = self._get_client()
            body = {
                "query": {
                    "multi_match": {
                        "query": query,
                        "fields": ["title^3", "content^1.5", "excerpt^1"],
                        "type": "best_fields",
                        "fuzziness": "AUTO",
                    }
                },
                "_source": False,
                "size": 100,
            }
            response = client.search(index=self.index_name, body=body)
            ids = [int(hit["_id"]) for hit in response["hits"]["hits"]]
            if not ids:
                return queryset.none()
            preserved = {item_id: i for i, item_id in enumerate(ids)}
            from django.db.models import Case, When
            whens = [When(id=item_id, then=Value(pos)) for pos, item_id in preserved.items()]
            return queryset.filter(id__in=ids).order_by(Case(*whens, default=Value(len(ids))))
        except Exception:
            return PostgresFTSBackend().search(queryset, query)

    def suggest(self, queryset, prefix: str, limit: int = 8):
        try:
            client = self._get_client()
            body = {
                "suggest": {
                    "title_suggest": {
                        "prefix": prefix,
                        "completion": {"field": "title_suggest", "size": limit},
                    }
                }
            }
            response = client.search(index=self.index_name, body=body)
            options = (response.get("suggest", {}).get("title_suggest", [{}])[0].get("options", []))
            return [{"id": o["_id"], "title": o["text"], "slug": o["_source"]["slug"]} for o in options]
        except Exception:
            return []

    def index_post(self, post):
        try:
            client = self._get_client()
            doc = {
                "title": post.title, "content": post.content, "excerpt": post.excerpt,
                "slug": post.slug, "status": post.status,
                "published_at": post.published_at.isoformat() if post.published_at else None,
                "author": post.author.display_name,
                "category": post.category.name if post.category else None,
                "tags": [t.name for t in post.tags.all()],
                "title_suggest": {"input": [post.title]},
            }
            client.index(index=self.index_name, id=post.id, body=doc, refresh=True)
        except Exception:
            pass

    def remove_post(self, post):
        try:
            self._get_client().delete(index=self.index_name, id=post.id, ignore=[404])
        except Exception:
            pass


def get_search_backend():
    backend_name = getattr(settings, "SEARCH_BACKEND", "postgres")
    if backend_name == "elasticsearch":
        try:
            return ElasticsearchBackend()
        except ImportError:
            pass
    return PostgresFTSBackend()
