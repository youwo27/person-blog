"""
Storage backends — local FileSystemStorage (dev) + S3/MinIO (prod).

Configuration is read from Django settings (set via .env):

Development (default):
    Uses Django's default FileSystemStorage with MEDIA_ROOT

Production (S3):
    AWS_ACCESS_KEY_ID=xxx
    AWS_SECRET_ACCESS_KEY=xxx
    AWS_STORAGE_BUCKET_NAME=my-blog-media
    AWS_S3_REGION_NAME=us-east-1
    AWS_S3_ENDPOINT_URL=https://s3.amazonaws.com  # AWS S3
    # or for MinIO:
    AWS_S3_ENDPOINT_URL=http://minio:9000

CDN:
    If MEDIA_URL starts with https://, all file URLs use the CDN domain directly.
    Example: MEDIA_URL=https://cdn.example.com/media/ → https://cdn.example.com/media/2024/01/photo.jpg

Usage:
    from apps.media_library.storages import get_storage

    storage = get_storage()
    url = storage.url("media/2024/01/photo.jpg")
"""

from django.conf import settings
from django.core.files.storage import default_storage


def get_storage():
    """Return the active media storage backend."""
    return default_storage


def get_media_url(file_name: str) -> str:
    """
    Generate a full media URL — CDN if configured, otherwise local.

    In production, MEDIA_URL should be set to the CDN domain:
        MEDIA_URL=https://cdn.yourdomain.com/media/
    """
    base = settings.MEDIA_URL
    if not base.endswith("/"):
        base += "/"
    return f"{base}{file_name}"


def is_using_s3() -> bool:
    """Check if S3/MinIO storage is active."""
    storage_backend = getattr(settings, "STORAGES", {}).get("default", {}).get("BACKEND", "")
    return "s3" in storage_backend.lower() or "storages.backends.s3" in storage_backend


# ── S3 Storage class (for direct use) ────────────
class S3MediaStorage:
    """
    S3-compatible storage with configurable endpoint.

    Supports:
    - AWS S3
    - MinIO (self-hosted)
    - Alibaba Cloud OSS (via S3-compatible API)
    - Any S3-compatible object storage

    Configure via .env:
        AWS_ACCESS_KEY_ID=xxx
        AWS_SECRET_ACCESS_KEY=xxx
        AWS_STORAGE_BUCKET_NAME=my-blog-media
        AWS_S3_ENDPOINT_URL=https://s3.amazonaws.com  # or http://minio:9000
        AWS_S3_REGION_NAME=us-east-1
    """

    def __init__(self):
        import boto3

        self.bucket_name = getattr(settings, "AWS_STORAGE_BUCKET_NAME", "")
        self.endpoint_url = getattr(settings, "AWS_S3_ENDPOINT_URL", None)
        self.region = getattr(settings, "AWS_S3_REGION_NAME", "us-east-1")
        self.access_key = getattr(settings, "AWS_ACCESS_KEY_ID", "")
        self.secret_key = getattr(settings, "AWS_SECRET_ACCESS_KEY", "")

        self.client = boto3.client(
            "s3",
            endpoint_url=self.endpoint_url,
            region_name=self.region,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
        )

    def upload_file(self, local_path: str, s3_key: str, content_type: str | None = None) -> str:
        """
        Upload a file to S3.

        Returns the object URL.
        """
        extra_args = {"ACL": "public-read"}
        if content_type:
            extra_args["ContentType"] = content_type

        self.client.upload_file(
            local_path,
            self.bucket_name,
            s3_key,
            ExtraArgs=extra_args,
        )

        # Generate URL
        if self.endpoint_url:
            return f"{self.endpoint_url.rstrip('/')}/{self.bucket_name}/{s3_key}"
        return f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com/{s3_key}"

    def delete_file(self, s3_key: str):
        """Delete a file from S3."""
        self.client.delete_object(Bucket=self.bucket_name, Key=s3_key)

    def generate_presigned_url(self, s3_key: str, expires: int = 3600) -> str:
        """Generate a pre-signed URL for temporary private access."""
        return self.client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket_name, "Key": s3_key},
            ExpiresIn=expires,
        )
