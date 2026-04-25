"""Tests for XPRSimulator orchestration."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from xprclaw_mirofish.models import MarketState, ScenarioType, SimulationRequest
from xprclaw_mirofish.simulator import XPRSimulator


@pytest.fixture
def sample_request() -> SimulationRequest:
    """A typical simulation request."""
    return SimulationRequest(
        scenario=ScenarioType.STAKING_OPTIMIZATION,
        market_state=MarketState(
            xpr_price_usd=0.0042,
            staking_apy=0.085,
            loan_apy=0.061,
            metalx_xpr_usd_spread_bps=23.0,
            treasury_xpr=1250000.0,
            open_loan_xpr=300000.0,
            timestamp=datetime(2026, 4, 24, 15, 0, 0, tzinfo=timezone.utc),
        ),
        horizon_hours=24,
        max_rounds=30,
    )


@pytest.mark.asyncio
async def test_compute_cache_key_deterministic(sample_request: SimulationRequest) -> None:
    """Same request always produces same cache key."""
    mock_client = AsyncMock()
    sim = XPRSimulator(mock_client)

    key1 = sim._compute_cache_key(sample_request)
    key2 = sim._compute_cache_key(sample_request)
    assert key1 == key2
    assert len(key1) == 16  # Truncated SHA256


@pytest.mark.asyncio
async def test_compute_cache_key_different_for_different_scenarios(
    sample_request: SimulationRequest,
) -> None:
    """Different scenarios produce different keys."""
    mock_client = AsyncMock()
    sim = XPRSimulator(mock_client)

    req1 = sample_request.model_copy(update={"scenario": ScenarioType.STAKING_OPTIMIZATION})
    req2 = sample_request.model_copy(update={"scenario": ScenarioType.ARBITRAGE_WINDOW})

    key1 = sim._compute_cache_key(req1)
    key2 = sim._compute_cache_key(req2)
    assert key1 != key2


@pytest.mark.asyncio
async def test_compute_cache_key_ignores_external_news(sample_request: SimulationRequest) -> None:
    """Cache key ignores external_news (deterministic across content variations)."""
    mock_client = AsyncMock()
    sim = XPRSimulator(mock_client)

    req1 = sample_request.model_copy(
        update={"market_state": sample_request.market_state.model_copy(update={"external_news": []})}
    )
    req2 = sample_request.model_copy(
        update={
            "market_state": sample_request.market_state.model_copy(
                update={"external_news": ["XRP lawsuit settled"]}
            )
        }
    )

    key1 = sim._compute_cache_key(req1)
    key2 = sim._compute_cache_key(req2)
    assert key1 == key2


@pytest.mark.asyncio
async def test_run_full_orchestration_success(sample_request: SimulationRequest) -> None:
    """Full orchestration flow: seed → graph → simulation → report → verdict."""
    mock_client = AsyncMock()

    # Mock each stage
    mock_client.graph_build.return_value = "proj_123"
    mock_client.wait_for_graph.return_value = None
    mock_client.simulation_prepare.return_value = "sim_456"
    mock_client.simulation_start.return_value = None
    mock_client.wait_for_simulation.return_value = None
    mock_client.report_generate.return_value = "rep_789"
    mock_client.wait_for_report.return_value = None
    mock_client.report_get.return_value = "# Simulation Report\nAnalysis complete."

    sim = XPRSimulator(mock_client)
    result = await sim.run(sample_request)

    # Verify result structure
    assert result.request_id is not None
    assert result.cache_hit is False
    assert result.duration_ms > 0
    assert result.scenario == ScenarioType.STAKING_OPTIMIZATION
    assert result.verdict is not None
    assert result.recommendation is not None
    assert result.created_at is not None

    # Verify orchestration calls
    assert mock_client.graph_build.called
    assert mock_client.wait_for_graph.called
    assert mock_client.simulation_prepare.called
    assert mock_client.simulation_start.called
    assert mock_client.wait_for_simulation.called
    assert mock_client.report_generate.called
    assert mock_client.wait_for_report.called
    assert mock_client.report_get.called


@pytest.mark.asyncio
async def test_run_passes_correct_parameters(sample_request: SimulationRequest) -> None:
    """Verify parameters passed to each orchestration stage."""
    mock_client = AsyncMock()
    mock_client.graph_build.return_value = "proj_123"
    mock_client.wait_for_graph.return_value = None
    mock_client.simulation_prepare.return_value = "sim_456"
    mock_client.simulation_start.return_value = None
    mock_client.wait_for_simulation.return_value = None
    mock_client.report_generate.return_value = "rep_789"
    mock_client.wait_for_report.return_value = None
    mock_client.report_get.return_value = "# Report"

    sim = XPRSimulator(mock_client)
    await sim.run(sample_request)

    # Verify graph_build call
    graph_call_args = mock_client.graph_build.call_args
    assert graph_call_args[0][0]  # seed material (non-empty)
    assert graph_call_args[1]["project_name"] is not None

    # Verify simulation_start call
    sim_call_args = mock_client.simulation_start.call_args
    assert sim_call_args[1]["max_rounds"] == 30
    assert sim_call_args[1]["platform"] == "xprclaw"


@pytest.mark.asyncio
async def test_run_respects_cache_ttl_override(sample_request: SimulationRequest) -> None:
    """Custom cache_ttl_override_seconds affects polling deadlines."""
    mock_client = AsyncMock()
    mock_client.graph_build.return_value = "proj_123"
    mock_client.wait_for_graph.return_value = None
    mock_client.simulation_prepare.return_value = "sim_456"
    mock_client.simulation_start.return_value = None
    mock_client.wait_for_simulation.return_value = None
    mock_client.report_generate.return_value = "rep_789"
    mock_client.wait_for_report.return_value = None
    mock_client.report_get.return_value = "# Report"

    request_with_ttl = sample_request.model_copy(update={"cache_ttl_override_seconds": 300})
    sim = XPRSimulator(mock_client)
    await sim.run(request_with_ttl)

    # Verify wait calls used custom TTL
    graph_wait_args = mock_client.wait_for_graph.call_args
    assert graph_wait_args[1]["deadline"] == 300

    sim_wait_args = mock_client.wait_for_simulation.call_args
    assert sim_wait_args[1]["deadline"] == 300


@pytest.mark.asyncio
async def test_run_fails_on_client_error(sample_request: SimulationRequest) -> None:
    """Simulator raises SimulationFailedError if client raises."""
    mock_client = AsyncMock()
    mock_client.graph_build.side_effect = Exception("Connection failed")

    sim = XPRSimulator(mock_client)

    from xprclaw_mirofish.exceptions import SimulationFailedError

    with pytest.raises(SimulationFailedError):
        await sim.run(sample_request)


@pytest.mark.asyncio
async def test_extract_verdict_returns_verdict() -> None:
    """_extract_verdict returns valid Verdict object."""
    mock_client = AsyncMock()
    sim = XPRSimulator(mock_client)

    request = SimulationRequest(
        scenario=ScenarioType.STAKING_OPTIMIZATION,
        market_state=MarketState(
            xpr_price_usd=0.0042,
            staking_apy=0.085,
            loan_apy=0.061,
            metalx_xpr_usd_spread_bps=23.0,
            treasury_xpr=1250000.0,
            open_loan_xpr=300000.0,
            timestamp=datetime(2026, 4, 24, 15, 0, 0, tzinfo=timezone.utc),
        ),
    )

    verdict = sim._extract_verdict("# Report\nContent", request)
    assert verdict is not None
    assert -1 <= verdict.sentiment <= 1
    assert 0 <= verdict.confidence <= 1
