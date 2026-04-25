"""Tests for seed material builder."""

from datetime import datetime, timezone

import pytest

from xprclaw_mirofish.models import MarketState, ScenarioType
from xprclaw_mirofish.seed_builder import build_seed


@pytest.fixture
def sample_state() -> MarketState:
    """A typical market state snapshot."""
    return MarketState(
        xpr_price_usd=0.0042,
        staking_apy=0.085,
        loan_apy=0.061,
        metalx_xpr_usd_spread_bps=23.0,
        treasury_xpr=1250000.0,
        open_loan_xpr=300000.0,
        timestamp=datetime(2026, 4, 24, 15, 37, 42, tzinfo=timezone.utc),
    )


def test_build_seed_deterministic(sample_state: MarketState) -> None:
    """Same (state, scenario) always produces byte-identical markdown."""
    seed1 = build_seed(sample_state, ScenarioType.STAKING_OPTIMIZATION)
    seed2 = build_seed(sample_state, ScenarioType.STAKING_OPTIMIZATION)
    assert seed1 == seed2
    assert seed1.encode() == seed2.encode()


def test_build_seed_includes_scenario_name(sample_state: MarketState) -> None:
    """Generated seed includes the scenario name."""
    seed = build_seed(sample_state, ScenarioType.ARBITRAGE_WINDOW)
    assert "arbitrage_window" in seed


def test_build_seed_includes_all_personas(sample_state: MarketState) -> None:
    """Generated seed lists all six personas."""
    seed = build_seed(sample_state, ScenarioType.STAKING_OPTIMIZATION)
    assert "Whale Holder" in seed
    assert "Yield Farmer" in seed
    assert "Arbitrage Bot Operator" in seed
    assert "News Trader" in seed
    assert "Protocol Skeptic" in seed
    assert "Community Member" in seed


def test_build_seed_includes_market_state(sample_state: MarketState) -> None:
    """Generated seed includes numeric market state."""
    seed = build_seed(sample_state, ScenarioType.STAKING_OPTIMIZATION)
    assert "$0.004200" in seed  # xpr_price_usd
    assert "8.50%" in seed  # staking_apy
    assert "6.10%" in seed  # loan_apy
    assert "23.0" in seed  # metalx spread


def test_build_seed_rounds_timestamp_to_hour(sample_state: MarketState) -> None:
    """Timestamp is rounded to hour for cache stability."""
    # 15:37:42 → should round down to 15:00:00
    seed = build_seed(sample_state, ScenarioType.STAKING_OPTIMIZATION)
    assert "2026-04-24T15:00:00Z" in seed


def test_build_seed_different_scenarios_different_context(
    sample_state: MarketState,
) -> None:
    """Different scenarios produce different briefing text."""
    seed_staking = build_seed(sample_state, ScenarioType.STAKING_OPTIMIZATION)
    seed_loan = build_seed(sample_state, ScenarioType.LOAN_MANAGEMENT)
    seed_arb = build_seed(sample_state, ScenarioType.ARBITRAGE_WINDOW)

    # Each should have unique scenario-specific text
    assert "staking position" in seed_staking
    assert "Proton Loan" in seed_loan
    assert "Metal X spread" in seed_arb


def test_build_seed_with_external_news(sample_state: MarketState) -> None:
    """External news is included in seed."""
    state_with_news = sample_state.model_copy(
        update={"external_news": ["XRP lawsuit settled", "New XRP DEX launched"]}
    )
    seed = build_seed(state_with_news, ScenarioType.NEWS_REACTION)
    assert "External Events" in seed
    assert "XRP lawsuit settled" in seed
    assert "New XRP DEX launched" in seed
