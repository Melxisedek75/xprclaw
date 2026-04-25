"""Decision logic: convert verdict to actionable recommendation."""

from xprclaw_mirofish.models import Recommendation, Verdict


def evaluate(verdict: Verdict) -> Recommendation:
    """Convert simulation verdict to trading recommendation.

    Decision rules:
    - sentiment + price drift determine bullish/bearish bias
    - confidence gates execution (low confidence → hold or abort)
    - social volume confirms or contradicts price signal
    """
    sentiment = verdict.sentiment
    drift = verdict.predicted_price_drift_pct
    social = verdict.social_volume_delta_pct
    confidence = verdict.confidence

    # Extract signals for logging
    signals = {
        "sentiment": sentiment,
        "predicted_price_drift_pct": drift,
        "social_volume_delta_pct": social,
        "confidence": confidence,
    }

    # Low confidence → conservative
    if confidence < 0.4:
        return Recommendation(
            action="hold",
            confidence=confidence,
            rationale="Confidence too low to act confidently. Awaiting clearer signals.",
            signals=signals,
        )

    # High drift + strong sentiment alignment
    if abs(drift) > 15 and abs(sentiment) > 0.6:
        if drift > 0 and sentiment > 0:
            return Recommendation(
                action="proceed",
                confidence=min(1.0, confidence * (1 + abs(sentiment))),
                rationale="Strong bullish consensus: positive sentiment, upward price drift, confirmed by social volume.",
                signals=signals,
            )
        elif drift < 0 and sentiment < -0.6:
            return Recommendation(
                action="abort",
                confidence=min(1.0, confidence * (1 + abs(sentiment))),
                rationale="Strong bearish signal: negative sentiment, downward price drift, high social volatility.",
                signals=signals,
            )

    # Moderate drift with weaker sentiment
    if 5 < drift <= 15 and 0.3 < sentiment <= 0.6:
        return Recommendation(
            action="proceed",
            confidence=confidence * 0.8,
            rationale="Moderate bullish lean: modest price drift and positive sentiment, but await confirmation.",
            signals=signals,
        )

    # Moderate bearish
    if -15 <= drift < -5 and -0.6 <= sentiment < -0.3:
        return Recommendation(
            action="reduce",
            confidence=confidence * 0.75,
            rationale="Moderate bearish signal: reduce exposure, monitor for reversal.",
            signals=signals,
        )

    # Drift but sentiment mismatch → skepticism
    if abs(drift) > 10 and abs(sentiment) < 0.3:
        return Recommendation(
            action="hold",
            confidence=confidence * 0.5,
            rationale="Price drifting but weak sentiment agreement. Possible momentum without conviction. Hold and reassess.",
            signals=signals,
        )

    # Positive sentiment but no price drift → early signal
    if drift < 5 and sentiment > 0.4 and social > 10:
        return Recommendation(
            action="proceed",
            confidence=confidence * 0.6,
            rationale="Bullish sentiment building with social volume spike, but price hasn't moved yet. Early entry signal.",
            signals=signals,
        )

    # Default: low drift, neutral sentiment → hold
    return Recommendation(
        action="hold",
        confidence=confidence,
        rationale="Signals mixed or weak. Hold current position; risk/reward not compelling.",
        signals=signals,
    )
