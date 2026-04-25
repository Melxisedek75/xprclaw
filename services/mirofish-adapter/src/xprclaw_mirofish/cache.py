"""In-memory cache for simulation results (extensible to D1)."""

import asyncio
import time
from typing import Optional

from xprclaw_mirofish.models import SimulationResult


class SimulationCache:
    """In-memory cache with TTL support. Extensible to Cloudflare D1."""

    def __init__(self, default_ttl_seconds: int = 3600):
        """Initialize cache.

        Args:
            default_ttl_seconds: Default time-to-live for cached entries (default 1 hour).
        """
        self.default_ttl = default_ttl_seconds
        self._cache: dict[str, tuple[SimulationResult, float]] = {}
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> Optional[SimulationResult]:
        """Retrieve cached result if exists and not expired."""
        async with self._lock:
            if key not in self._cache:
                return None

            result, expiry_time = self._cache[key]
            if time.time() > expiry_time:
                del self._cache[key]
                return None

            return result

    async def set(self, key: str, result: SimulationResult, ttl_seconds: Optional[int] = None) -> None:
        """Store result in cache with TTL."""
        ttl = ttl_seconds or self.default_ttl
        expiry_time = time.time() + ttl

        async with self._lock:
            self._cache[key] = (result, expiry_time)

    async def clear(self) -> None:
        """Clear all cached entries."""
        async with self._lock:
            self._cache.clear()

    async def stats(self) -> dict[str, int]:
        """Return cache statistics."""
        async with self._lock:
            now = time.time()
            valid_count = sum(1 for _, expiry in self._cache.values() if now < expiry)
            expired_count = len(self._cache) - valid_count
            return {
                "total_entries": len(self._cache),
                "valid_entries": valid_count,
                "expired_entries": expired_count,
            }
