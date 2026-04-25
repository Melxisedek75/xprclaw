"""Orchestrator: coordinate full simulation flow with MiroFish backend."""

import hashlib
import json
import logging
from datetime import datetime, timezone

from xprclaw_mirofish.client import MiroFishClient
from xprclaw_mirofish.decision import evaluate
from xprclaw_mirofish.exceptions import MiroFishAPIError, SimulationFailedError
from xprclaw_mirofish.models import (
    Recommendation,
    SimulationRequest,
    SimulationResult,
    Verdict,
)
from xprclaw_mirofish.seed_builder import build_seed

log = logging.getLogger(__name__)


class XPRSimulator:
    """Orchestrate MiroFish simulation flow: seed → graph → simulation → report → verdict."""

    def __init__(self, client: MiroFishClient):
        """Initialize with MiroFish client."""
        self.client = client

    def _compute_cache_key(self, request: SimulationRequest) -> str:
        """Hash (scenario, market_state) for deterministic caching."""
        key_dict = {
            "scenario": request.scenario.value,
            "market_state": request.market_state.model_dump(
                exclude={"external_news"}, mode="json"
            ),
        }
        key_json = json.dumps(key_dict, sort_keys=True, default=str)
        return hashlib.sha256(key_json.encode()).hexdigest()[:16]

    async def run(self, request: SimulationRequest) -> SimulationResult:
        """Execute full simulation: build → graph → simulation → report → verdict.

        Returns:
            SimulationResult with verdict, recommendation, and metadata.

        Raises:
            SimulationFailedError: If any stage fails after retries.
        """
        start_time = datetime.now(timezone.utc)
        request_id = self._compute_cache_key(request)

        try:
            # Step 1: Build seed material
            seed = build_seed(request.market_state, request.scenario)
            log.info(f"seed_built: req_id={request_id}, scenario={request.scenario.value}")

            # Step 2: Submit seed to MiroFish, get project_id
            project_id = await self.client.graph_build(seed, project_name=request_id)
            log.info(f"graph_build_submitted: req_id={request_id}, project_id={project_id}")

            # Step 3: Poll graph until ready
            await self.client.wait_for_graph(
                project_id,
                poll_interval=2.0,
                deadline=request.cache_ttl_override_seconds or 600.0,
            )
            log.info(f"graph_ready: req_id={request_id}")

            # Step 4: Prepare simulation with personas
            from xprclaw_mirofish.personas import get_all_personas

            personas = [p.model_dump() for p in get_all_personas()]
            sim_id = await self.client.simulation_prepare(project_id, personas)
            log.info(f"simulation_prepared: req_id={request_id}, sim_id={sim_id}")

            # Step 5: Start simulation
            await self.client.simulation_start(
                sim_id,
                max_rounds=request.max_rounds,
                platform="xprclaw",
            )
            log.info(f"simulation_started: req_id={request_id}, max_rounds={request.max_rounds}")

            # Step 6: Poll simulation until complete
            await self.client.wait_for_simulation(
                sim_id,
                poll_interval=2.0,
                deadline=request.cache_ttl_override_seconds or 600.0,
            )
            log.info(f"simulation_complete: req_id={request_id}")

            # Step 7: Generate report
            report_id = await self.client.report_generate(sim_id)
            log.info(f"report_generation_requested: req_id={request_id}, report_id={report_id}")

            # Step 8: Poll report until ready
            await self.client.wait_for_report(
                report_id,
                poll_interval=2.0,
                deadline=request.cache_ttl_override_seconds or 600.0,
            )
            log.info(f"report_ready: req_id={request_id}")

            # Step 9: Fetch report markdown
            report_markdown = await self.client.report_get(report_id)
            log.info(f"report_fetched: req_id={request_id}, len={len(report_markdown)}")

            # Step 10: Extract verdict from report (stub: hardcode for now)
            verdict = self._extract_verdict(report_markdown, request)
            recommendation = evaluate(verdict)
            log.info(f"decision_made: req_id={request_id}, action={recommendation.action}")

            # Build result
            duration_ms = int((datetime.now(timezone.utc) - start_time).total_seconds() * 1000)
            result = SimulationResult(
                request_id=request_id,
                cache_hit=False,
                duration_ms=duration_ms,
                scenario=request.scenario,
                verdict=verdict,
                recommendation=recommendation,
                report_url=None,  # Could be S3 URL in production
                created_at=start_time,
            )
            log.info(f"simulation_result_complete: req_id={request_id}, duration_ms={duration_ms}")
            return result

        except Exception as e:
            log.error(f"simulation_failed: req_id={request_id}, error={e}", exc_info=True)
            raise SimulationFailedError(f"Simulation failed: {e}") from e

    def _extract_verdict(self, report_markdown: str, request: SimulationRequest) -> Verdict:
        """Extract verdict from report markdown (stub: placeholder logic).

        In production, this would use Claude to parse the report and extract
        consensus sentiment, price drift prediction, etc.
        """
        # Placeholder: return neutral verdict
        # Real implementation would parse report_markdown
        return Verdict(
            sentiment=0.0,
            predicted_price_drift_pct=0.0,
            social_volume_delta_pct=0.0,
            confidence=0.5,
        )
