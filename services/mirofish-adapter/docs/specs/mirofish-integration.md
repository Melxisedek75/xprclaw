# XPRClaw × MiroFish — Integration Spec

**Owner:** Serhiy (`Melxisedek75`)
**Target executor:** Claude Code (in the XPRClaw repo)
**Spec version:** 1.0
**Status:** Ready to implement

---

## How to use this spec

1. Save this file as `docs/specs/mirofish-integration.md` in the XPRClaw repo.
2. Create a feature branch: `git checkout -b feat/mirofish-integration`.
3. Run one of:
   - `/plan-eng-review docs/specs/mirofish-integration.md` — sanity-check the plan first.
   - `/investigate docs/specs/mirofish-integration.md` — if you want Claude Code to study MiroFish source first.
   - `/ship docs/specs/mirofish-integration.md` — to implement directly.
4. Implement **phase by phase**. Do not skip phases. Each phase has its own acceptance criteria and must pass before the next phase starts.
5. Push back on this spec where it conflicts with reality in the actual repo. The spec is a target, not a contract.

---

## 0. Context

**XPRClaw** is an autonomous AI agent platform on XPR Network with a DeFi self-funding engine: XPR staking, Proton Loan, Metal X DEX arbitrage. Existing surface:
- Node.js bot with LLM auto-rotation
- PWA landing page
- Cloudflare D1 database `gcsc-brain` (ID `948f767e-ff2c-4df0-8798-824ac98d2927`, account `b457272dab63e8b60c2f939e7e55be9a`) for persistent state

**MiroFish** (`github.com/666ghj/MiroFish`) is an open-source multi-agent simulation engine. Architecture:
- Vue 3 frontend (port 3000) — not used by us
- Flask + Python backend (port 5001) — **this is our integration target**
- LLM via OpenAI-compatible API (any provider)
- Zep Cloud for long-term agent memory (or Neo4j in the offline fork)
- OASIS framework underneath for the actual swarm simulation
- Stages: Graph Build → Env Setup → Simulation → Report

**Why integrate:** XPRClaw makes capital-allocation decisions (stake more, take a loan, arbitrage on Metal X). Today those decisions are rules-based. MiroFish lets us run a many-agent simulation of how the XPR market and community might react to a given action, and use that as a probabilistic input into the bot's decision engine.

---

## 1. Goals & non-goals

### In scope
- A typed Python adapter (`xprclaw-mirofish` package) that talks to MiroFish's HTTP API.
- A Node.js client used by the existing XPRClaw bot to call the adapter as a sidecar.
- A decision-engine layer that converts a MiroFish report into a concrete action recommendation with a confidence score.
- Caching of simulation results in Cloudflare D1 (simulations are expensive; we cache by content hash).
- Graceful fallback to deterministic rules when MiroFish is unreachable.
- Docker compose stack so the whole thing comes up with one command.
- Smoke tests + unit tests for the adapter and the decision engine.

### Out of scope (explicitly)
- Modifying MiroFish itself. We treat it as a black-box service. Vendor it as a git submodule or pull the public Docker image.
- Replacing the existing rules-based logic in XPRClaw. MiroFish is an *input* to that logic, not a replacement.
- Reusing the MiroFish Vue frontend.
- On-chain execution. The adapter returns recommendations only; the existing bot still signs and submits transactions.
- Real-money testing in this PR. All Phase 5 tests use testnet or mock data.

---

## 2. Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                       XPRClaw Bot (Node.js)                    │
│                                                                │
│   existing rules engine ─┐                                     │
│                          ├──► decision-engine.js ──► action    │
│   mirofish-client.js ────┘                                     │
└────────────┬───────────────────────────────────────────────────┘
             │ HTTP (localhost:8088)
             ▼
┌────────────────────────────────────────────────────────────────┐
│              xprclaw-mirofish adapter (Python)                 │
│  FastAPI sidecar. Owns:                                        │
│   • seed_builder    — turns market state into MiroFish seed    │
│   • personas        — DeFi-flavoured agent personas            │
│   • client          — HTTP client to MiroFish backend          │
│   • simulator       — orchestrates a full run                  │
│   • cache           — D1-backed result cache                   │
└────────────┬───────────────────────────────────────────────────┘
             │ HTTP (localhost:5001)
             ▼
┌────────────────────────────────────────────────────────────────┐
│                 MiroFish backend (vendored, unmodified)        │
│  Flask app. Endpoints used:                                    │
│    POST /api/graph/build                                       │
│    POST /api/simulation/prepare                                │
│    POST /api/simulation/start                                  │
│    GET  /api/simulation/status/<sim_id>                        │
│    POST /api/report/generate                                   │
│    GET  /api/report/status/<report_id>                         │
└────────────────────────────────────────────────────────────────┘
```

**Why a Python sidecar instead of calling MiroFish directly from Node.js?**
- MiroFish's API is undocumented and has long-running operations (graph build, simulation). The sidecar gives us a single, typed, stable contract for the bot to depend on.
- Persona templates and seed-building logic are easier to maintain in Python with Pydantic.
- Lets us swap MiroFish for the offline fork or another simulator later without touching the bot.

---

## 3. File structure

Create exactly this structure inside the XPRClaw repo:

```
xprclaw/
├── docs/
│   └── specs/
│       └── mirofish-integration.md          ← this file
│
├── services/
│   └── mirofish-adapter/                    ← Python sidecar
│       ├── pyproject.toml
│       ├── README.md
│       ├── Dockerfile
│       ├── .env.example
│       ├── src/
│       │   └── xprclaw_mirofish/
│       │       ├── __init__.py
│       │       ├── api.py                   ← FastAPI app (HTTP surface)
│       │       ├── client.py                ← MiroFish HTTP client
│       │       ├── config.py                ← Pydantic Settings
│       │       ├── exceptions.py
│       │       ├── models.py                ← Pydantic request/response models
│       │       ├── personas.py              ← DeFi persona templates
│       │       ├── scenarios.py             ← Scenario presets
│       │       ├── seed_builder.py          ← market state → seed material
│       │       ├── simulator.py             ← orchestrator
│       │       ├── cache.py                 ← D1-backed cache
│       │       └── decision.py              ← report → recommendation
│       └── tests/
│           ├── conftest.py
│           ├── test_seed_builder.py
│           ├── test_personas.py
│           ├── test_simulator.py            ← uses mocked client
│           ├── test_cache.py
│           └── test_decision.py
│
├── bot/                                     ← existing Node.js bot
│   └── src/
│       ├── mirofish/
│       │   ├── client.js                    ← HTTP client to the sidecar
│       │   ├── decision-engine.js           ← merges rules + simulation
│       │   └── index.js
│       └── …existing files…
│
├── migrations/d1/
│   └── 0XX_mirofish_cache.sql               ← bump XX to next number in repo
│
├── docker-compose.mirofish.yml              ← profile-gated extension
├── .env.example                             ← updated, see §7
└── third_party/
    └── mirofish/                            ← git submodule of 666ghj/MiroFish
                                                pinned to a known-good tag
```

**Note on MiroFish vendoring:** prefer a git submodule pinned to a release tag (currently `v0.1.2`). If submodules are not desirable in this repo, fall back to pulling the public Docker image in `docker-compose.mirofish.yml` and skip the `third_party/mirofish/` directory.

---

## 4. Implementation phases

Each phase ends with a working, mergeable state. Run tests at the end of each phase.

### Phase 1 — Python adapter scaffold (no MiroFish calls yet)

Create the package skeleton with all modules empty-but-importable. Wire up:
- `pyproject.toml` (Python 3.11+, deps below)
- `pytest` + `ruff` + `mypy --strict`
- The FastAPI app in `api.py` with one route: `GET /healthz` returning `{"status": "ok", "version": "..."}`
- `Dockerfile` based on `python:3.12-slim` (multi-stage; final image runs as non-root)

**Dependencies (pyproject.toml):**
- `fastapi>=0.115`
- `uvicorn[standard]>=0.32`
- `httpx>=0.27` (async HTTP, for both MiroFish and D1 REST API)
- `pydantic>=2.9`
- `pydantic-settings>=2.6`
- `tenacity>=9.0` (retry policies)
- `structlog>=24.4` (structured logging)
- Dev: `pytest>=8.3`, `pytest-asyncio>=0.24`, `respx>=0.21` (httpx mocking), `mypy>=1.13`, `ruff>=0.7`

**Acceptance:**
- `pytest` passes (zero tests required, but the runner must be wired).
- `mypy --strict src/` passes.
- `docker build` succeeds.
- `curl localhost:8088/healthz` returns 200.

### Phase 2 — Models, personas, seed builder

Implement, with full type hints and docstrings:

- `config.AdapterConfig` — Pydantic Settings, loaded from env. See §7 for fields.
- `models` — see §6 for the exact schema.
- `personas` — six DeFi persona templates (see §6.4). Each persona is a pure-data Pydantic model, not a class with behaviour.
- `seed_builder.build_seed(state: MarketState, scenario: ScenarioType) -> SeedMaterial` — converts a market snapshot into the markdown document MiroFish ingests. Output is deterministic given the same inputs (important for caching).
- `exceptions` — `MiroFishConfigError`, `MiroFishAPIError`, `MiroFishTimeoutError`, `SimulationFailedError`. All inherit from a common base `XPRClawMiroFishError`.

**Tests in this phase:**
- `test_personas.py`: every persona round-trips through Pydantic.
- `test_seed_builder.py`: same `(state, scenario)` always produces byte-identical output. Snapshot test against a checked-in fixture.

**Acceptance:**
- `pytest` passes ≥10 tests.
- Calling `build_seed` with a sample `MarketState` produces a markdown document that includes scenario name, timestamp (rounded to the hour for cache stability — see §8.3), all persona names, and the numeric market state.

### Phase 3 — MiroFish HTTP client

Implement `client.MiroFishClient`:
- Async, built on `httpx.AsyncClient`.
- Constructor takes `base_url`, `timeout`, `max_retries`.
- One method per MiroFish endpoint we use (see §5.1).
- Retry only on transient errors (network errors, 502/503/504). Never retry on 4xx.
- Backoff: `tenacity` with exponential, jitter, max 3 attempts.
- Long-poll helpers `wait_for_simulation(sim_id, poll_interval=2.0, deadline=600.0)` and `wait_for_report(report_id, ...)`.

**Tests with `respx`:**
- 200 happy path for each endpoint.
- 503 → retry → 200.
- 503 → 503 → 503 → raises `MiroFishAPIError` with retry count.
- Timeout → raises `MiroFishTimeoutError`.
- Polling helper: returns when status flips to `completed`; raises on `failed`; raises `MiroFishTimeoutError` on deadline.

**Acceptance:** All client tests green. Mypy strict still passes.

### Phase 4 — Simulator + decision engine

`simulator.XPRSimulator`:
- Composes `MiroFishClient`, `SeedBuilder`, `Cache`, and persona templates.
- Public API: `async def simulate(request: SimulationRequest) -> SimulationResult`.
- Flow:
  1. Compute cache key (see §8.3). Hit cache → return.
  2. Build seed material.
  3. POST graph build → wait for graph ready (poll).
  4. POST simulation prepare → poll until profiles generated.
  5. POST simulation start with `max_rounds` from request → poll until finished or deadline.
  6. POST report generate → poll until report ready.
  7. Pull the report markdown + machine-readable verdict (`verdict.json` if present, else parse markdown — see §5.2).
  8. Run `decision.evaluate(verdict, request)` → produces a `Recommendation`.
  9. Write to cache.
  10. Return `SimulationResult`.
- Every step structured-logs with the project_id, sim_id, report_id, and elapsed time.

`decision.evaluate(verdict, request) -> Recommendation`:
- Pure function. No I/O.
- Inputs: parsed verdict (sentiment scores, predicted price drift, social-volume delta) + the originating request (so we know thresholds).
- Output: `Recommendation` (action: `proceed | reduce | hold | abort`, confidence in [0.0, 1.0], rationale text, raw signals echoed back).
- Decision rules — see §6.6.

**Tests:**
- `test_simulator.py` mocks the client end-to-end and asserts the orchestration sequence + cache write.
- `test_decision.py` is a parameterized table over verdict shapes asserting the right action label.
- One test asserts that a cache hit short-circuits and never calls the client.

**Acceptance:** ≥30 tests total, all green. Mypy strict green.

### Phase 5 — D1 cache + FastAPI surface

#### 5a. D1 schema migration

`migrations/d1/0XX_mirofish_cache.sql`:

```sql
CREATE TABLE IF NOT EXISTS mirofish_simulations (
    cache_key       TEXT PRIMARY KEY,
    scenario        TEXT NOT NULL,
    request_json    TEXT NOT NULL,
    result_json     TEXT NOT NULL,
    confidence      REAL NOT NULL,
    action          TEXT NOT NULL,
    created_at      INTEGER NOT NULL,   -- unix seconds
    expires_at      INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_mirofish_simulations_expires
    ON mirofish_simulations(expires_at);

CREATE INDEX IF NOT EXISTS idx_mirofish_simulations_scenario
    ON mirofish_simulations(scenario, created_at DESC);
```

Apply via `wrangler d1 migrations apply gcsc-brain`. Document the command in `migrations/README.md`.

#### 5b. Cache implementation

`cache.D1Cache`:
- Talks to D1 via Cloudflare's REST API (`https://api.cloudflare.com/client/v4/accounts/<acct>/d1/database/<db_id>/query`) using `httpx`.
- Methods: `async def get(key: str) -> SimulationResult | None`, `async def set(key, result, ttl_seconds)`, `async def evict_expired() -> int`.
- TTL default: 30 minutes for staking scenarios, 5 minutes for arbitrage scenarios (volatile), configurable per scenario.
- Reads on cache miss must be cheap (one query). Writes idempotent (`ON CONFLICT(cache_key) DO UPDATE`).

#### 5c. FastAPI surface

`api.py`:
- `POST /v1/simulate` — body: `SimulationRequest`, response: `SimulationResult`.
- `GET /v1/healthz` — checks adapter, downstream MiroFish (`/api/health` or fall back to TCP probe), and D1 reachability. Return per-component status.
- `GET /v1/scenarios` — lists available `ScenarioType` values with human descriptions.
- `POST /v1/cache/evict` — admin endpoint (gated by `X-Admin-Token` header matching env var). Calls `evict_expired`.

All endpoints emit a request-id header (`X-Request-ID`, generated if missing) and structured logs.

**Tests:**
- `test_cache.py` against a sqlite in-memory fake (a small `D1Cache` subclass that targets sqlite for tests; production uses the REST API).
- API integration tests using `httpx.AsyncClient` against the FastAPI app, with the simulator's client mocked.

**Acceptance:**
- D1 migration applied successfully against a dev database.
- `curl -X POST localhost:8088/v1/simulate -d @sample.json` returns a recommendation in <30s when MiroFish is mocked.
- `/v1/healthz` correctly reports `degraded` when MiroFish is down but adapter and D1 are up.

### Phase 6 — Node.js bot integration

In `bot/src/mirofish/`:

- `client.js` — thin wrapper over `fetch` for the adapter. Methods: `simulate(request)`, `health()`. 5s default timeout, configurable. Emits the same `X-Request-ID` it received from upstream so logs stay correlated.
- `decision-engine.js` — exports `decide(rulesOutput, simulationResult)`. Merge policy:
  - If simulation is unavailable or `confidence < MIN_CONFIDENCE` (default 0.55) → fall through to rules-only output.
  - If rules say `proceed` and simulation says `proceed` → proceed, log both signals.
  - If rules say `proceed` but simulation says `abort` with confidence ≥0.75 → abort, log a "veto" event.
  - Anything else → `hold` and log for human review.
- `index.js` — re-exports the public surface.

Wire into the bot's main loop **behind a feature flag** (`USE_MIROFISH=true`). Default off for the first deploy.

**Tests:** standard bot test framework already in the repo (Jest/Vitest — match what's there). Mock the adapter HTTP surface with `nock` or `msw`. ≥6 tests covering the merge-policy table.

**Acceptance:**
- Bot tests pass.
- With `USE_MIROFISH=false` the bot's behaviour is byte-identical to before this PR (regression-tested by replaying a recorded action log if available; otherwise a manual smoke run).
- With `USE_MIROFISH=true` and a stub adapter returning a known recommendation, the bot's decision-engine output matches the expected merge-policy outcome.

### Phase 7 — Docker + deployment

- `services/mirofish-adapter/Dockerfile` — multi-stage, non-root, healthcheck hits `/v1/healthz`.
- `docker-compose.mirofish.yml` — defines three services:
  - `mirofish-backend` (vendored or pulled image) on `:5001`, internal network only
  - `mirofish-adapter` on `:8088`, depends on `mirofish-backend`, healthcheck-gated
  - `mirofish-redis` (optional, only if we add Redis caching later — leave commented out for now)
- The compose file is profile-gated so `docker compose up` (without the profile) does not start it. Use `docker compose --profile mirofish up`.
- Document in `services/mirofish-adapter/README.md`:
  - Local dev (uvicorn with `--reload`)
  - Docker dev (compose profile)
  - Required env vars
  - How to run tests
  - How to apply D1 migrations
  - How to flip the bot feature flag

**Acceptance:**
- `docker compose --profile mirofish up -d` brings the stack up.
- Healthcheck on the adapter container reports healthy within 60s.
- Bot connects from the host to the adapter on `localhost:8088` successfully.

---

## 5. API contracts

### 5.1 MiroFish endpoints we call

These come from `backend/app/api/{graph,simulation,report}.py` in the upstream repo. Verify exact request shapes by reading the source — the spec below is the *contract we depend on*; if upstream differs, adapt the client and update this doc.

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/api/graph/build` | Submit seed material, get `project_id` back. |
| `GET`  | `/api/graph/status/{project_id}` | Poll until graph ready. |
| `POST` | `/api/simulation/prepare` | Generate agent profiles for a project. Body includes persona configs. |
| `GET`  | `/api/simulation/status/{simulation_id}` | Poll prepare and run states. |
| `POST` | `/api/simulation/start` | Start the actual simulation. Body includes `max_rounds`, `platform`. |
| `POST` | `/api/simulation/stop` | Cancel a running simulation. Use on adapter shutdown. |
| `POST` | `/api/report/generate` | Generate a report from a finished simulation. |
| `GET`  | `/api/report/status/{report_id}` | Poll. |
| `GET`  | `/api/report/{report_id}` | Fetch the final report (markdown + structured verdict if present). |

If MiroFish does not expose a structured verdict, we parse the markdown in `simulator._extract_verdict()`. See §5.2.

### 5.2 Verdict extraction (fallback)

If the report does not include a `verdict.json`, parse the markdown for these signals (in priority order):
1. A YAML front-matter block at the top of the report. Extract directly.
2. A section titled `## Verdict` or `## Prediction Summary` containing key-value pairs.
3. Heuristic NLP fallback: count positive vs negative sentiment markers in the conclusion section and return a low-confidence (≤0.5) verdict.

Always return a `Verdict` object with `sentiment: float in [-1, 1]`, `predicted_price_drift_pct: float`, `social_volume_delta_pct: float`, `confidence: float in [0, 1]`. Missing fields default to `0.0` with `confidence` capped at `0.4`.

### 5.3 Adapter HTTP API

```
POST /v1/simulate
Content-Type: application/json

{
  "scenario": "staking_optimization",
  "market_state": {
    "xpr_price_usd": 0.0042,
    "staking_apy": 0.085,
    "loan_apy": 0.061,
    "metalx_xpr_usd_spread_bps": 23,
    "treasury_xpr": 1250000,
    "open_loan_xpr": 300000,
    "timestamp": "2026-04-24T20:15:00Z"
  },
  "horizon_hours": 24,
  "max_rounds": 30,
  "min_confidence": 0.55
}

200 OK

{
  "request_id": "req_01HX...",
  "cache_hit": false,
  "duration_ms": 18420,
  "scenario": "staking_optimization",
  "verdict": {
    "sentiment": 0.31,
    "predicted_price_drift_pct": 1.8,
    "social_volume_delta_pct": 12.4,
    "confidence": 0.71
  },
  "recommendation": {
    "action": "proceed",
    "confidence": 0.71,
    "rationale": "Positive sentiment and modest predicted upside; staking APY remains attractive vs loan APY.",
    "signals": { ... }
  },
  "report_url": "/v1/reports/<report_id>"
}
```

---

## 6. Data models

### 6.1 `ScenarioType` (str enum)
- `staking_optimization` — should we increase/decrease XPR staked?
- `loan_management` — should we open/close/resize a Proton Loan?
- `arbitrage_window` — is the current Metal X spread worth taking?
- `treasury_rebalance` — broader portfolio shift across XPR / stables / collateral.
- `news_reaction` — react to a specific external event injected into the seed.

### 6.2 `MarketState` (Pydantic model)
All numeric fields validated with `Field(..., ge=...)` constraints where applicable. `timestamp` is a `datetime` and is rounded to the hour by the seed builder for cache stability. Required fields: `xpr_price_usd`, `staking_apy`, `loan_apy`, `metalx_xpr_usd_spread_bps`, `treasury_xpr`, `open_loan_xpr`, `timestamp`. Optional: `external_news` (list of strings injected into the seed verbatim).

### 6.3 `SimulationRequest`
- `scenario: ScenarioType`
- `market_state: MarketState`
- `horizon_hours: int = 24` (validated 1..168)
- `max_rounds: int = 30` (validated 5..200)
- `min_confidence: float = 0.55` (validated 0..1)
- `cache_ttl_override_seconds: int | None = None`

### 6.4 `AgentPersona`
- `id: str` (slug)
- `name: str`
- `description: str` (1–3 sentences, used as LLM prompt)
- `bias: Literal["bullish", "bearish", "neutral", "contrarian"]`
- `risk_tolerance: float in [0, 1]`
- `time_horizon_days: int`

Six default personas to ship with:
1. `whale-holder` — long-term XPR holder, low-frequency, bullish-biased.
2. `yield-farmer` — APY-chasing, neutral sentiment, high time-preference.
3. `arbitrage-bot-operator` — pure profit, neutral, very short horizon.
4. `news-trader` — reactive, contrarian on overreactions.
5. `protocol-skeptic` — bearish, high risk-aversion.
6. `community-member` — sentiment-led, social signals drive behaviour.

### 6.5 `Verdict`
See §5.2.

### 6.6 `Recommendation`
- `action: Literal["proceed", "reduce", "hold", "abort"]`
- `confidence: float in [0, 1]`
- `rationale: str`
- `signals: dict[str, float]` — passes through key numbers from the verdict for the bot to log.

**Decision rules** in `decision.evaluate`:

| Verdict signal pattern | Action |
|---|---|
| `confidence < 0.4` | `hold` (not enough signal) |
| `predicted_price_drift_pct ≥ +1.0` and `sentiment ≥ 0.2` | `proceed` |
| `predicted_price_drift_pct ≤ -1.0` and `sentiment ≤ -0.2` | `abort` |
| `predicted_price_drift_pct in [-1.0, +1.0]` | `reduce` if scenario is leverage-related (`loan_management`), else `hold` |
| Mixed (drift ↑ but sentiment ↓ or vice versa) | `hold` |

Confidence in the recommendation is `min(verdict.confidence, abs(predicted_price_drift_pct) / 5.0 + 0.4)` capped to `[0, 1]`.

### 6.7 `SimulationResult`
- `request_id: str`
- `cache_hit: bool`
- `duration_ms: int`
- `scenario: ScenarioType`
- `verdict: Verdict`
- `recommendation: Recommendation`
- `report_url: str | None`
- `created_at: datetime`

---

## 7. Configuration

`AdapterConfig` (pydantic-settings, env prefix `XPRMF_`):

| Env var | Type | Default | Notes |
|---|---|---|---|
| `XPRMF_MIROFISH_BASE_URL` | str | `http://mirofish-backend:5001` | |
| `XPRMF_MIROFISH_TIMEOUT_S` | float | `60.0` | per-request |
| `XPRMF_MIROFISH_MAX_RETRIES` | int | `3` | |
| `XPRMF_SIMULATION_DEADLINE_S` | float | `600.0` | full pipeline deadline |
| `XPRMF_POLL_INTERVAL_S` | float | `2.0` | |
| `XPRMF_D1_ACCOUNT_ID` | str | _required_ | `b457272dab63e8b60c2f939e7e55be9a` |
| `XPRMF_D1_DATABASE_ID` | str | _required_ | `948f767e-ff2c-4df0-8798-824ac98d2927` |
| `XPRMF_D1_API_TOKEN` | str | _required_ | from Cloudflare |
| `XPRMF_DEFAULT_TTL_S` | int | `1800` | 30 min |
| `XPRMF_ARBITRAGE_TTL_S` | int | `300` | 5 min |
| `XPRMF_ADMIN_TOKEN` | str | _required_ | for `/v1/cache/evict` |
| `XPRMF_LOG_LEVEL` | str | `INFO` | |
| `XPRMF_STRICT_MODE` | bool | `false` | if true, MiroFish failure raises instead of returning fallback recommendation |

Bot-side env (Node.js):

| Env var | Default | Notes |
|---|---|---|
| `MIROFISH_ADAPTER_URL` | `http://localhost:8088` | |
| `MIROFISH_TIMEOUT_MS` | `30000` | |
| `MIROFISH_MIN_CONFIDENCE` | `0.55` | merge-policy threshold |
| `USE_MIROFISH` | `false` | feature flag |

Update `.env.example` at the repo root with all the above, with values redacted.

---

## 8. Error handling, retries, and caching

### 8.1 Retry policy
- HTTP-level retries only on network errors and 502/503/504. `tenacity` with exponential backoff (base 0.5s, max 8s), max 3 attempts, jitter on.
- Never retry POSTs that are not idempotent without a request key. MiroFish's POSTs are idempotent enough for our use because each one creates a new resource — duplicate creates are wasteful but not wrong. Log a warning if a retry happens after a 200 was lost.

### 8.2 Fallback behaviour (when `STRICT_MODE=false`)
On any unrecoverable MiroFish error, return a `SimulationResult` with:
- `verdict.confidence = 0.0`
- `recommendation.action = "hold"`
- `recommendation.confidence = 0.0`
- `recommendation.rationale = "MiroFish unavailable: <reason>; falling back to rules-only path."`

The bot's decision engine treats this as "no simulation signal" and runs rules-only. Log at WARN.

### 8.3 Cache key

```
cache_key = sha256(
    scenario
    + "|" + market_state.canonical_json(sorted_keys=True, hour_rounded_timestamp=True)
    + "|" + str(horizon_hours)
    + "|" + str(max_rounds)
    + "|" + persona_set_version
).hexdigest()[:32]
```

`persona_set_version` is a string baked into `personas.py` and bumped any time we change persona templates. This guarantees old cache entries become unreachable when persona logic changes.

Timestamp is rounded to the hour so two requests in the same hour with identical market state hit the same cache entry. This is the right tradeoff for staking; arbitrage scenarios use a 5-minute TTL anyway so they don't hit the cache for long.

---

## 9. Testing plan

- **Unit:** every module in `xprclaw_mirofish/` has a corresponding test file. Mypy strict must pass.
- **Integration (mocked):** `respx`-mocked MiroFish for the full simulator flow. ≥1 test per phase boundary.
- **Integration (live):** one end-to-end test in `tests/integration/test_live.py`, skipped by default (`pytest -m live`). Brings up the MiroFish docker image, runs one tiny simulation (5 rounds, 6 personas), asserts a `SimulationResult` comes back with non-zero confidence. CI does not run this.
- **Bot:** ≥6 tests for the merge-policy decision engine.
- **Smoke:** a `scripts/smoke.sh` that runs the live integration test plus a round-trip through the FastAPI surface.

CI must run unit + mocked integration on every PR. Live integration is manual.

---

## 10. Logging & observability

- All Python logs via `structlog` in JSON mode (one line per event). Mandatory keys: `event`, `request_id`, `cache_key`, `phase`, `elapsed_ms`.
- Log every state transition in the simulator: `seed_built`, `graph_submitted`, `graph_ready`, `prepare_submitted`, `prepare_ready`, `simulation_started`, `simulation_finished`, `report_generated`, `verdict_extracted`, `cache_written`.
- On error: include `error.type`, `error.message`, and (for HTTP) `http.status`, `http.url`.
- Bot side: log the same `request_id` propagated from `X-Request-ID` so a single decision is traceable across processes.

---

## 11. Security

- The adapter has no inbound auth on `/v1/simulate` because it binds to localhost only inside the docker network. Document this and refuse to start if `XPRMF_BIND_HOST` is anything other than `127.0.0.1` or a private/Docker network IP — emit a clear error if the user tries to expose it publicly.
- `/v1/cache/evict` requires `X-Admin-Token` matching `XPRMF_ADMIN_TOKEN`. Constant-time comparison (`hmac.compare_digest`).
- Do not log raw API tokens. The config object's `__repr__` must redact any field whose name contains `token` or `key`.
- D1 API token has read+write only on `gcsc-brain`. Document this in the README and provide the wrangler command to create such a scoped token.

---

## 12. Acceptance criteria (definition of done)

The PR is mergeable when **all** of the following are true:

1. All 7 phases are complete and individually pass their acceptance criteria.
2. `pytest` is green with ≥40 tests; coverage on `xprclaw_mirofish/` is ≥80%.
3. `mypy --strict` is green.
4. `ruff check` is green.
5. Bot tests are green; bot behaviour with `USE_MIROFISH=false` is unchanged from `main`.
6. `docker compose --profile mirofish up` brings the stack up; `/v1/healthz` reports `ok` for all components within 60s.
7. The D1 migration applies cleanly to `gcsc-brain` (dev environment).
8. `services/mirofish-adapter/README.md` covers local dev, Docker dev, env vars, tests, and the bot feature flag.
9. A new file `docs/decisions/0XX-mirofish-integration.md` exists with a short ADR (context, decision, consequences) — the existing repo's ADR numbering scheme should be followed.
10. CHANGELOG entry added under "Unreleased".

---

## 13. Open questions (decide before Phase 4)

These are not blockers for Phase 1–3 but must be resolved before we wire the decision engine:

1. **LLM provider for MiroFish.** Qwen-plus (Alibaba) is the upstream default but bills in CNY and routes through Bailian. Options:
   - Use Qwen-plus as documented.
   - Use OpenAI/Anthropic via an OpenAI-compatible proxy.
   - Use the offline fork (`nikmcfly/MiroFish-Offline`) with local Ollama + Neo4j — zero ongoing cost, higher hardware requirement.
   Decide in Phase 1 since it determines the docker-compose shape.

2. **Persona set lock-in.** Should `personas.py` be hardcoded (versioned via the constant in §8.3) or loaded from a YAML file in `config/`? Hardcoded is simpler and safer; YAML is more flexible. Default to hardcoded for v1.

3. **Cache eviction trigger.** Cron job, on-demand only, or LRU-on-write? Default: on-demand only (manual `/v1/cache/evict` call) for v1.

4. **How does the bot decide *when* to call the simulator?** Out of scope for this spec — assume the bot has an existing decision tick, and we only define the contract for the call. The bot team owns the policy of when to pull the trigger.

---

## 14. Rollout

1. Land the PR with `USE_MIROFISH=false`. The whole stack can be deployed without affecting bot behaviour.
2. Run live integration tests against a staging MiroFish instance for 48 hours. Watch logs for unexpected fallbacks.
3. Flip `USE_MIROFISH=true` for 1% of decision ticks (if the bot supports gradual rollout) or for one specific scenario type only (e.g. `arbitrage_window` first, since the cost of a wrong call there is bounded by the position size).
4. Expand to all scenarios after a week of clean operation.
5. After two weeks, write a retro: `/retro mirofish-rollout`.

---

*End of spec.*
