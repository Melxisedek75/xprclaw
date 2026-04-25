"""FastAPI application and HTTP routes."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from xprclaw_mirofish import __version__
from xprclaw_mirofish.cache import SimulationCache
from xprclaw_mirofish.client import MiroFishClient
from xprclaw_mirofish.models import SimulationRequest, SimulationResult
from xprclaw_mirofish.simulator import XPRSimulator

log = logging.getLogger(__name__)

# Global state
_client: MiroFishClient | None = None
_cache: SimulationCache | None = None
_simulator: XPRSimulator | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):  # type: ignore
    """Manage client lifecycle: startup and shutdown."""
    global _client, _cache, _simulator

    # Startup
    _client = MiroFishClient()
    _cache = SimulationCache(default_ttl_seconds=3600)
    _simulator = XPRSimulator(_client)
    log.info(f"adapter_startup: mirofish_url={_client.base_url}")

    yield

    # Shutdown
    if _client:
        await _client.close()
    if _cache:
        await _cache.clear()
    log.info("adapter_shutdown complete")


app = FastAPI(
    title="XPRClaw MiroFish Adapter",
    description="Multi-agent simulator sidecar for autonomous trading decisions",
    version=__version__,
    lifespan=lifespan,
)


@app.get("/healthz", tags=["health"])
async def healthz() -> dict[str, str]:
    """Health check endpoint."""
    cache_stats = await _cache.stats() if _cache else {"error": "cache not initialized"}
    return {
        "status": "ok",
        "version": __version__,
        "cache": str(cache_stats),
    }


@app.get("/", tags=["meta"])
async def root() -> dict[str, str]:
    """Root endpoint."""
    return {
        "service": "xprclaw-mirofish",
        "version": __version__,
        "docs": "/docs",
    }


@app.post("/v1/simulate", tags=["simulate"], response_model=SimulationResult)
async def simulate(request: SimulationRequest) -> SimulationResult:
    """Run market simulation: seed → graph → simulation → report → verdict → recommendation.

    Returns:
        SimulationResult with verdict, recommendation, and metadata.

    Raises:
        400: Invalid request.
        500: Simulation failed (MiroFish error, timeout, etc).
    """
    if not _simulator or not _cache:
        raise RuntimeError("Simulator not initialized")

    # Compute cache key
    cache_key = _simulator._compute_cache_key(request)
    log.info(f"simulate_request: scenario={request.scenario.value}, cache_key={cache_key}")

    # Check cache
    cached = await _cache.get(cache_key)
    if cached:
        log.info(f"simulate_cache_hit: cache_key={cache_key}")
        # Mark as cache hit
        cached.cache_hit = True
        return cached

    # Run simulation
    result = await _simulator.run(request)

    # Store in cache
    ttl = request.cache_ttl_override_seconds or 3600
    await _cache.set(cache_key, result, ttl_seconds=ttl)

    log.info(f"simulate_complete: action={result.recommendation.action}, duration_ms={result.duration_ms}")
    return result


@app.exception_handler(Exception)
async def global_exception_handler(request: object, exc: Exception) -> JSONResponse:
    """Global exception handler."""
    log.error(f"unhandled_exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc)},
    )
