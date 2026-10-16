"""Dynamic static asset hashing and service worker cache version management.

Computes 8-character SHA-1 content hashes for static files with process-level caching.
When static file contents change, the hash changes automatically, preventing stale caches
and removing the need for manual cache buster query parameters or Ctrl+F5.
"""
import hashlib
from pathlib import Path
from django.conf import settings

_ASSET_HASH_CACHE = {}


def get_asset_hash(rel_path: str) -> str:
    """Return an 8-character SHA-1 content hash of the given static asset."""
    clean_path = rel_path.strip().lstrip("/").removeprefix("static/")
    if clean_path in _ASSET_HASH_CACHE:
        return _ASSET_HASH_CACHE[clean_path]

    full_path = Path(settings.BASE_DIR) / "static" / clean_path
    if full_path.is_file():
        h = hashlib.sha1(full_path.read_bytes()).hexdigest()[:8]
    else:
        h = "dynamic"
    _ASSET_HASH_CACHE[clean_path] = h
    return h


def get_service_worker_cache_version() -> str:
    """Compute active Service Worker cache name derived from core asset content hashes."""
    core_assets = [
        "css/ui_tokens.css",
        "css/components.css",
        "css/app_shell.css",
        "js/theme.js",
        "js/app_shell.js",
    ]
    hasher = hashlib.sha1()
    for asset in core_assets:
        hasher.update(get_asset_hash(asset).encode("ascii"))
    bundle_hash = hasher.hexdigest()[:8]
    return f"ihrms-static-v33-{bundle_hash}"


def clear_asset_hash_cache() -> None:
    """Clear memory cache of asset hashes (useful in tests when files change)."""
    _ASSET_HASH_CACHE.clear()

