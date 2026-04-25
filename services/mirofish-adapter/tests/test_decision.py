"""Tests for decision evaluation logic."""

import pytest

from xprclaw_mirofish.decision import evaluate
from xprclaw_mirofish.models import Verdict


def test_low_confidence_yields_hold() -> None:
    """Low confidence (<0.4) always results in hold."""
    verdict = Verdict(sentiment=0.9, predicted_price_drift_pct=20, confidence=0.2)
    recommendation = evaluate(verdict)
    assert recommendation.action == "hold"
    assert recommendation.confidence == 0.2


def test_high_bullish_consensus_yields_proceed() -> None:
    """High drift + strong bullish sentiment → proceed."""
    verdict = Verdict(sentiment=0.75, predicted_price_drift_pct=20, confidence=0.8)
    recommendation = evaluate(verdict)
    assert recommendation.action == "proceed"
    assert recommendation.confidence > 0.8  # Boosted by sentiment


def test_high_bearish_consensus_yields_abort() -> None:
    """High negative drift + strong bearish sentiment → abort."""
    verdict = Verdict(sentiment=-0.75, predicted_price_drift_pct=-20, confidence=0.8)
    recommendation = evaluate(verdict)
    assert recommendation.action == "abort"
    assert recommendation.confidence > 0.8


def test_moderate_bullish_yields_proceed() -> None:
    """Moderate drift (5-15) + positive sentiment → proceed (confidence reduced)."""
    verdict = Verdict(sentiment=0.5, predicted_price_drift_pct=10, confidence=0.7)
    recommendation = evaluate(verdict)
    assert recommendation.action == "proceed"
    assert recommendation.confidence < 0.7  # Reduced for less certain signal


def test_moderate_bearish_yields_reduce() -> None:
    """Moderate negative drift + bearish sentiment → reduce."""
    verdict = Verdict(sentiment=-0.4, predicted_price_drift_pct=-10, confidence=0.6)
    recommendation = evaluate(verdict)
    assert recommendation.action == "reduce"
    assert recommendation.confidence < 0.6


def test_drift_sentiment_mismatch_yields_hold() -> None:
    """Large drift but weak sentiment (disagreement) → hold."""
    verdict = Verdict(sentiment=0.1, predicted_price_drift_pct=15, confidence=0.7)
    recommendation = evaluate(verdict)
    assert recommendation.action == "hold"
    assert recommendation.confidence < 0.7


def test_early_signal_positive_sentiment_no_drift() -> None:
    """Positive sentiment + high social volume, but no price drift yet → proceed (early)."""
    verdict = Verdict(sentiment=0.6, predicted_price_drift_pct=2, social_volume_delta_pct=15, confidence=0.6)
    recommendation = evaluate(verdict)
    assert recommendation.action == "proceed"
    assert recommendation.confidence < 0.6  # Less confident than full signal


def test_neutral_mixed_signals_yields_hold() -> None:
    """Neutral sentiment + low drift → hold."""
    verdict = Verdict(sentiment=0.0, predicted_price_drift_pct=2, confidence=0.5)
    recommendation = evaluate(verdict)
    assert recommendation.action == "hold"
    assert "mixed" in recommendation.rationale.lower()


def test_signals_included_in_recommendation() -> None:
    """Recommendation includes all verdict signals for logging."""
    verdict = Verdict(sentiment=0.5, predicted_price_drift_pct=10, social_volume_delta_pct=5, confidence=0.7)
    recommendation = evaluate(verdict)
    assert "sentiment" in recommendation.signals
    assert recommendation.signals["sentiment"] == 0.5
    assert recommendation.signals["confidence"] == 0.7
