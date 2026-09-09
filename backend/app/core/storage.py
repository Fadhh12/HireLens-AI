"""
Supabase Storage wrapper for candidate CV/certificate files.

Bucket is private (SDD §6: "bukan publicly accessible URL — akses via
signed URL berbatas waktu"). We only ever store the object *path* in
the DB (candidates.cv_file_url / certificate_urls) and mint a signed
URL on read, never a public one.
"""

from functools import lru_cache

from supabase import Client, create_client

from app.core.config import get_settings

settings = get_settings()

DEFAULT_SIGNED_URL_TTL_SECONDS = 3600


@lru_cache
def get_supabase() -> Client:
    return create_client(settings.supabase_url, settings.supabase_key)


def upload_file(path: str, content: bytes, content_type: str) -> str:
    """Uploads to the private bucket. Returns the object path (not a URL) —
    that's what gets persisted on the candidate record."""
    client = get_supabase()
    client.storage.from_(settings.supabase_storage_bucket).upload(
        path,
        content,
        file_options={"content-type": content_type, "upsert": "true"},
    )
    return path


def get_signed_url(path: str, expires_in: int = DEFAULT_SIGNED_URL_TTL_SECONDS) -> str:
    client = get_supabase()
    result = client.storage.from_(settings.supabase_storage_bucket).create_signed_url(path, expires_in)
    # supabase-py has returned both "signedURL" and "signedUrl" across
    # versions — check both instead of pinning to one.
    return result.get("signedURL") or result.get("signedUrl")


def delete_files(paths: list[str]) -> None:
    if not paths:
        return
    client = get_supabase()
    client.storage.from_(settings.supabase_storage_bucket).remove(paths)
