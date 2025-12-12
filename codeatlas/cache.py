"""File-based caching for scan results."""

import hashlib
import json
import os
from pathlib import Path
from typing import Any, Dict, Optional


class ScanCache:
    """File-based cache for scan results keyed by file mtime and content hash."""

    def __init__(self, cache_dir: Path):
        """Initialize cache with directory."""
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _get_file_key(self, file_path: Path) -> str:
        """Generate cache key from file path."""
        return hashlib.sha256(str(file_path).encode()).hexdigest()

    def _get_cache_path(self, file_key: str) -> Path:
        """Get cache file path for a key."""
        return self.cache_dir / f"{file_key}.json"

    def get(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """
        Get cached scan result for a file.

        Args:
            file_path: Path to the file

        Returns:
            Cached data or None if not found/invalid
        """
        if not file_path.exists():
            return None

        try:
            stat = file_path.stat()
            file_key = self._get_file_key(file_path)
            cache_path = self._get_cache_path(file_key)

            if not cache_path.exists():
                return None

            with open(cache_path, "r", encoding="utf-8") as f:
                cached = json.load(f)

            # Verify mtime matches
            if cached.get("mtime") != stat.st_mtime:
                return None

            # Verify content hash
            content_hash = self._compute_hash(file_path)
            if cached.get("hash") != content_hash:
                return None

            return cached.get("data")
        except Exception:
            return None

    def set(self, file_path: Path, data: Dict[str, Any]) -> None:
        """
        Cache scan result for a file.

        Args:
            file_path: Path to the file
            data: Data to cache
        """
        try:
            stat = file_path.stat()
            file_key = self._get_file_key(file_path)
            cache_path = self._get_cache_path(file_key)

            content_hash = self._compute_hash(file_path)

            cache_entry = {
                "mtime": stat.st_mtime,
                "hash": content_hash,
                "data": data,
            }

            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(cache_entry, f)
        except Exception:
            pass  # Silently fail on cache errors

    def _compute_hash(self, file_path: Path) -> str:
        """Compute SHA256 hash of file content."""
        sha256 = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    sha256.update(chunk)
            return sha256.hexdigest()
        except Exception:
            return ""

    def clear(self) -> None:
        """Clear all cached entries."""
        try:
            for cache_file in self.cache_dir.glob("*.json"):
                cache_file.unlink()
        except Exception:
            pass

    def invalidate(self, file_path: Path) -> None:
        """Invalidate cache for a specific file."""
        file_key = self._get_file_key(file_path)
        cache_path = self._get_cache_path(file_key)
        if cache_path.exists():
            try:
                cache_path.unlink()
            except Exception:
                pass

