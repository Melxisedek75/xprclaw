"""Tests for simulation result caching."""

import asyncio
from datetime import datetime, timezone

import pytest

from xprclaw_mirofish.cache import SimulationCache
from xprclaw_mirofish.models import (
    Recommendation,
    ScenarioType,
    SimulationResult,
    Verdict,
)


@pytest.fixture
def sample_result() -> SimulationResult:
    """A sample simulation result for testing."""
    return SimulationResult(
        request_id="test_req_123",
        cache_hit=False,
        duration_ms=5000,
        scenario=ScenarioType.STAKING_OPTIMIZATION,
        verdict=Verdict(sentiment=0.5, confidence=0.8),
        recommendation=Recommendation(
            action="proceed",
            confidence=0.75,
            rationale="Test rationale",
            signals={"test": 1.0},
        ),
        created_at=datetime.now(timezone.utc),
    )


@pytest.mark.asyncio
async def test_cache_stores_and_retrieves(sample_result: SimulationResult) -> None:
    """Cache stores and retrieves results."""
    cache = SimulationCache()
    await cache.set("key1", sample_result)

    retrieved = await cache.get("key1")
    assert retrieved is not None
    assert retrieved.request_id == "test_req_123"
    assert retrieved.scenario == ScenarioType.STAKING_OPTIMIZATION


@pytest.mark.asyncio
async def test_cache_returns_none_for_missing_key() -> None:
    """Cache returns None for non-existent keys."""
    cache = SimulationCache()
    result = await cache.get("nonexistent")
    assert result is None


@pytest.mark.asyncio
async def test_cache_respects_ttl(sample_result: SimulationResult) -> None:
    """Expired entries are removed on retrieval."""
    cache = SimulationCache()
    await cache.set("key1", sample_result, ttl_seconds=1)

    # Still available immediately
    retrieved = await cache.get("key1")
    assert retrieved is not None

    # Wait for expiry
    await asyncio.sleep(1.1)
    expired = await cache.get("key1")
    assert expired is None


@pytest.mark.asyncio
async def test_cache_uses_default_ttl(sample_result: SimulationResult) -> None:
    """Cache uses default TTL if not specified."""
    cache = SimulationCache(default_ttl_seconds=2)
    await cache.set("key1", sample_result)

    # Still available after 1 second
    await asyncio.sleep(1)
    retrieved = await cache.get("key1")
    assert retrieved is not None

    # Expired after default TTL
    await asyncio.sleep(1.1)
    expired = await cache.get("key1")
    assert expired is None


@pytest.mark.asyncio
async def test_cache_clear_removes_all(sample_result: SimulationResult) -> None:
    """clear() removes all entries."""
    cache = SimulationCache()
    await cache.set("key1", sample_result)
    await cache.set("key2", sample_result)

    await cache.clear()

    assert await cache.get("key1") is None
    assert await cache.get("key2") is None


@pytest.mark.asyncio
async def test_cache_stats_counts_valid_and_expired(sample_result: SimulationResult) -> None:
    """stats() reports valid and expired entries."""
    cache = SimulationCache()
    await cache.set("key1", sample_result, ttl_seconds=10)  # valid
    await cache.set("key2", sample_result, ttl_seconds=1)  # will expire

    stats1 = await cache.stats()
    assert stats1["total_entries"] == 2
    assert stats1["valid_entries"] == 2
    assert stats1["expired_entries"] == 0

    await asyncio.sleep(1.1)
    stats2 = await cache.stats()
    assert stats2["total_entries"] == 2  # Still in dict
    assert stats2["valid_entries"] == 1  # But only one not expired
    assert stats2["expired_entries"] == 1


@pytest.mark.asyncio
async def test_cache_concurrent_access(sample_result: SimulationResult) -> None:
    """Cache handles concurrent reads/writes safely."""
    cache = SimulationCache()

    async def write_task(key: str) -> None:
        await cache.set(key, sample_result)

    async def read_task(key: str) -> None:
        result = await cache.get(key)
        assert result is not None

    # Concurrent operations
    await asyncio.gather(
        write_task("k1"),
        write_task("k2"),
        read_task("k1"),
        read_task("k2"),
    )

    assert await cache.get("k1") is not None
    assert await cache.get("k2") is not None
