"""Pydantic models for simulator requests, responses, verdicts, and personas."""

from datetime import datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ScenarioType(str, Enum):
    """Available simulation scenarios."""

    STAKING_OPTIMIZATION = "staking_optimization"
    LOAN_MANAGEMENT = "loan_management"
    ARBITRAGE_WINDOW = "arbitrage_window"
    TREASURY_REBALANCE = "treasury_rebalance"
    NEWS_REACTION = "news_reaction"


class MarketState(BaseModel):
    """Current market and treasury state snapshot."""

    xpr_price_usd: float = Field(gt=0, description="XPR price in USD")
    staking_apy: float = Field(ge=0, le=1, description="Annual percentage yield for staking")
    loan_apy: float = Field(ge=0, le=1, description="Annual percentage yield for borrowing")
    metalx_xpr_usd_spread_bps: float = Field(
        ge=0, description="Metal X XPR/USD spread in basis points"
    )
    treasury_xpr: float = Field(ge=0, description="Treasury XPR balance")
    open_loan_xpr: float = Field(ge=0, description="Current outstanding XPR loan")
    timestamp: datetime = Field(description="State snapshot timestamp (rounded to hour)")
    external_news: list[str] = Field(
        default_factory=list, description="Optional external events to inject into simulation"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "xpr_price_usd": 0.0042,
                "staking_apy": 0.085,
                "loan_apy": 0.061,
                "metalx_xpr_usd_spread_bps": 23,
                "treasury_xpr": 1250000,
                "open_loan_xpr": 300000,
                "timestamp": "2026-04-24T20:00:00Z",
                "external_news": [],
            }
        }
    )


class SimulationRequest(BaseModel):
    """Request to run a simulation."""

    scenario: ScenarioType
    market_state: MarketState
    horizon_hours: int = Field(default=24, ge=1, le=168)
    max_rounds: int = Field(default=30, ge=5, le=200)
    min_confidence: float = Field(default=0.55, ge=0, le=1)
    cache_ttl_override_seconds: int | None = Field(default=None, ge=60)


class Verdict(BaseModel):
    """Market simulation verdict extracted from MiroFish report."""

    sentiment: float = Field(default=0.0, ge=-1, le=1)
    predicted_price_drift_pct: float = Field(default=0.0)
    social_volume_delta_pct: float = Field(default=0.0)
    confidence: float = Field(default=0.0, ge=0, le=1)


class Recommendation(BaseModel):
    """Decision recommendation based on verdict."""

    action: Literal["proceed", "reduce", "hold", "abort"]
    confidence: float = Field(ge=0, le=1)
    rationale: str
    signals: dict[str, float] = Field(
        default_factory=dict, description="Key verdict signals for logging"
    )


class SimulationResult(BaseModel):
    """Complete result of a simulation run."""

    request_id: str
    cache_hit: bool
    duration_ms: int
    scenario: ScenarioType
    verdict: Verdict
    recommendation: Recommendation
    report_url: str | None = None
    created_at: datetime


class AgentPersona(BaseModel):
    """Agent personality template for simulation."""

    id: str = Field(description="Slug identifier")
    name: str
    description: str = Field(description="1-3 sentence persona prompt")
    bias: Literal["bullish", "bearish", "neutral", "contrarian"]
    risk_tolerance: float = Field(ge=0, le=1)
    time_horizon_days: int = Field(gt=0)
