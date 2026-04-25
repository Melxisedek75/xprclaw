"""FastAPI application and HTTP routes."""

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from xprclaw_mirofish import __version__

app = FastAPI(
    title="XPRClaw MiroFish Adapter",
    description="Multi-agent simulator sidecar for autonomous trading decisions",
    version=__version__,
)


@app.get("/healthz", tags=["health"])
async def healthz() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok", "version": __version__}


@app.get("/", tags=["meta"])
async def root() -> dict[str, str]:
    """Root endpoint."""
    return {
        "service": "xprclaw-mirofish",
        "version": __version__,
        "docs": "/docs",
    }


@app.exception_handler(Exception)
async def global_exception_handler(request: object, exc: Exception) -> JSONResponse:
    """Global exception handler."""
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc)},
    )
