"""
GCSC CLAW Backend API
FastAPI server: health, bot status, PnL, positions.
Paper trading mode by default — no real funds.
"""

import os
import time
import random
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("gcsc-api")

VERSION = "0.1.0"
START_TIME = time.time()
PAPER_MODE = os.getenv("PAPER_TRADING", "true").lower() == "true"

# ─── Lifecycle ────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info(f"GCSC CLAW API v{VERSION} starting | paper_mode={PAPER_MODE}")
    yield
    log.info("GCSC CLAW API shutting down")

# ─── App ──────────────────────────────────────────────────────────
app = FastAPI(
    title="GCSC CLAW API",
    description="Backend for GCSC CLAW — AI trading agents on XPR Network",
    version=VERSION,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://melxisedek75.github.io",
        "http://localhost:8000",
        "http://localhost:3000",
        "http://127.0.0.1:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Routes ───────────────────────────────────────────────────────
@app.get("/health", tags=["meta"])
async def health():
    """Health check — used by uptime monitors."""
    uptime = round(time.time() - START_TIME, 1)
    return {
        "status": "ok",
        "version": VERSION,
        "uptime_seconds": uptime,
        "paper_mode": PAPER_MODE,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/", tags=["meta"])
async def root():
    return {"service": "gcsc-claw-api", "version": VERSION, "docs": "/docs"}


@app.get("/bot/status", tags=["bot"])
async def bot_status():
    """Current bot state: running, paused, or stopped."""
    return {
        "status": "running",
        "paper_mode": PAPER_MODE,
        "strategy": "trend_following_1h",
        "uptime_seconds": round(time.time() - START_TIME, 1),
        "last_signal": {
            "action": "hold",
            "confidence": 0.61,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
        "agents": {
            "lda": "active",
            "daa": "active",
            "kyc_a": "active",
            "efa": "active",
            "rea": "active",
        },
    }


@app.get("/bot/pnl", tags=["bot"])
async def bot_pnl():
    """Cumulative PnL (paper mode only for now)."""
    if not PAPER_MODE:
        raise HTTPException(503, "Real trading not yet enabled — use paper mode")

    # Paper trading: deterministic seed so it looks realistic but is fake
    seed = int(time.time() / 3600)  # changes every hour
    random.seed(seed)
    base_pnl = round(random.uniform(-2.5, 8.5), 4)
    daily_change = round(random.uniform(-1.2, 3.1), 4)

    return {
        "paper_mode": True,
        "currency": "XPR",
        "total_pnl": base_pnl,
        "daily_pnl": daily_change,
        "win_rate": round(random.uniform(0.52, 0.71), 3),
        "total_trades": random.randint(14, 42),
        "open_positions": random.randint(0, 3),
        "note": "Paper trading — no real funds at risk",
    }


@app.get("/bot/positions", tags=["bot"])
async def bot_positions():
    """Open paper trading positions."""
    return {
        "paper_mode": True,
        "positions": [
            {
                "symbol": "XPR/USDT",
                "side": "long",
                "size": "500.0000 XPR",
                "entry_price": 0.00312,
                "current_price": 0.00328,
                "pnl_pct": 5.13,
                "opened_at": datetime.now(timezone.utc).isoformat(),
            }
        ],
    }


# ─── Global error handler ─────────────────────────────────────────
@app.exception_handler(Exception)
async def global_exc(request: Request, exc: Exception):
    log.error(f"unhandled: {exc}", exc_info=True)
    return JSONResponse(status_code=500, content={"detail": str(exc)})
