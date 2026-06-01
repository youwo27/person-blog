"""
Elasticsearch sync management command.

Usage:
  python manage.py es_sync              # Sync all published posts
  python manage.py es_sync --create     # Create index + sync all
  python manage.py es_sync --delete     # Delete ES index
  python manage.py es_sync --rebuild    # Delete + create + sync
"""

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Sync blog posts to Elasticsearch index."

    def add_arguments(self, parser):
        parser.add_argument("--create", action="store_true", help="Create index mapping")
        parser.add_argument("--delete", action="store_true", help="Delete index")
        parser.add_argument("--rebuild", action="store_true", help="Delete + create + sync all")

    def handle(self, *args, **options):
        from apps.blog.models import Post
        from apps.search_index.backends import ElasticsearchBackend

        backend = ElasticsearchBackend()

        if options.get("delete") or options.get("rebuild"):
            self.stdout.write(self.style.WARNING("Deleting index..."))
            try:
                client = backend._get_client()
                client.indices.delete(index=backend.index_name, ignore=[404])
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Delete failed: {e}"))

        if options.get("create") or options.get("rebuild"):
            self.stdout.write(self.style.NOTICE("Creating index..."))
            try:
                client = backend._get_client()
                if not client.indices.exists(index=backend.index_name):
                    client.indices.create(
                        index=backend.index_name,
                        body={
                            "settings": {
                                "number_of_shards": 1,
                                "number_of_replicas": 0,
                                "analysis": {
                                    "analyzer": {
                                        "default": {"type": "standard"},
                                    }
                                },
                            },
                            "mappings": {
                                "properties": {
                                    "title": {"type": "text", "analyzer": "standard", "boost": 3},
                                    "content": {"type": "text", "analyzer": "standard", "boost": 1.5},
                                    "excerpt": {"type": "text"},
                                    "slug": {"type": "keyword"},
                                    "status": {"type": "keyword"},
                                    "published_at": {"type": "date"},
                                    "author": {"type": "keyword"},
                                    "category": {"type": "keyword"},
                                    "tags": {"type": "keyword"},
                                    "title_suggest": {"type": "completion"},
                                }
                            },
                        },
                    )
                    self.stdout.write(self.style.SUCCESS("Index created."))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Create failed: {e}"))
                return

        if not options.get("delete"):
            self.stdout.write(self.style.NOTICE("Syncing posts..."))
            posts = Post.objects.filter(status=Post.Status.PUBLISHED).select_related("author", "category").prefetch_related("tags")
            count = 0
            for post in posts:
                backend.index_post(post)
                count += 1
                if count % 50 == 0:
                    self.stdout.write(f"  Synced {count}...")
            self.stdout.write(self.style.SUCCESS(f"Synced {count} posts to Elasticsearch."))
