"""Cache for simulation results: in-memory with optional D1 backend."""

import asyncio
import json
import logging
import time
from abc import ABC, abstractmethod
from typing import Optional

from xprclaw_mirofish.models import SimulationResult

log = logging.getLogger(__name__)


class CacheBackend(ABC):
    """Abstract cache backend interface."""

    @abstractmethod
    async def get(self, key: str) -> Optional[SimulationResult]:
        """Retrieve cached result if exists and not expired."""
        pass

    @abstractmethod
    async def set(self, key: str, result: SimulationResult, ttl_seconds: int) -> None:
        """Store result in cache with TTL."""
        pass

    @abstractmethod
    async def clear(self) -> None:
        """Clear all cached entries."""
        pass

    @abstractmethod
    async def stats(self) -> dict[str, int]:
        """Return cache statistics."""
        pass


class InMemoryCache(CacheBackend):
    """In-memory cache with TTL support."""

    def __init__(self, default_ttl_seconds: int = 3600):
        """Initialize in-memory cache.

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

    async def set(self, key: str, result: SimulationResult, ttl_seconds: int) -> None:
        """Store result in cache with TTL."""
        expiry_time = time.time() + ttl_seconds
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


class D1Cache(CacheBackend):
    """Cloudflare D1 cache backend (stub: direct API would be implemented via CF API client)."""

    def __init__(self, account_id: str, api_token: str, database_id: str, table_name: str = "mirofish_simulations"):
        """Initialize D1 cache.

        Args:
            account_id: Cloudflare account ID
            api_token: Cloudflare API token
            database_id: D1 database ID
            table_name: Table name for cache entries
        """
        self.account_id = account_id
        self.api_token = api_token
        self.database_id = database_id
        self.table_name = table_name
        log.info(f"D1Cache initialized: db_id={database_id}, table={table_name}")

    async def get(self, key: str) -> Optional[SimulationResult]:
        """Retrieve cached result from D1 if exists and not expired."""
        # Stub: In production, use Cloudflare API to execute:
        # SELECT result_json FROM {table_name} WHERE cache_key = ? AND expires_at > UNIXEPOCH()
        log.debug(f"D1Cache.get: key={key} (stub)")
        return None

    async def set(self, key: str, result: SimulationResult, ttl_seconds: int) -> None:
        """Store result in D1 cache with TTL."""
        # Stub: In production, use Cloudflare API to execute:
        # INSERT INTO {table_name} (cache_key, result_json, scenario, request_id, duration_ms, expires_at, created_at, updated_at)
        # VALUES (?, ?, ?, ?, ?, ?, UNIXEPOCH(), UNIXEPOCH())
        now = int(time.time())
        expires_at = now + ttl_seconds
        log.debug(f"D1Cache.set: key={key}, expires_at={expires_at} (stub)")

    async def clear(self) -> None:
        """Clear all cached entries from D1."""
        # Stub: In production, use Cloudflare API to execute:
        # DELETE FROM {table_name}
        log.debug("D1Cache.clear (stub)")

    async def stats(self) -> dict[str, int]:
        """Return D1 cache statistics."""
        # Stub: In production, use Cloudflare API to execute:
        # SELECT COUNT(*) as total FROM {table_name}
        # SELECT COUNT(*) as expired FROM {table_name} WHERE expires_at <= UNIXEPOCH()
        log.debug("D1Cache.stats (stub)")
        return {
            "total_entries": 0,
            "valid_entries": 0,
            "expired_entries": 0,
        }


class SimulationCache:
    """Unified cache interface supporting both in-memory and D1 backends."""

    def __init__(self, backend: CacheBackend, default_ttl_seconds: int = 3600):
        """Initialize cache with a backend.

        Args:
            backend: CacheBackend instance (InMemoryCache, D1Cache, etc.)
            default_ttl_seconds: Default time-to-live for cached entries (default 1 hour).
        """
        self.backend = backend
        self.default_ttl = default_ttl_seconds

    async def get(self, key: str) -> Optional[SimulationResult]:
        """Retrieve cached result if exists and not expired."""
        return await self.backend.get(key)

    async def set(self, key: str, result: SimulationResult, ttl_seconds: Optional[int] = None) -> None:
        """Store result in cache with TTL."""
        ttl = ttl_seconds or self.default_ttl
        await self.backend.set(key, result, ttl)

    async def clear(self) -> None:
        """Clear all cached entries."""
        await self.backend.clear()

    async def stats(self) -> dict[str, int]:
        """Return cache statistics."""
        return await self.backend.stats()
