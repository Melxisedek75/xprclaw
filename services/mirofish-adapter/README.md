# XPRClaw MiroFish Adapter

FastAPI sidecar for MiroFish multi-agent simulation engine. Provides typed HTTP interface between XPRClaw bot and MiroFish backend.

## Features

- **Typed API** — Pydantic models for all requests/responses
- **Async-first** — FastAPI + uvicorn with structured logging
- **Caching** — D1-backed result cache (deterministic content hash)
- **Resilience** — Retry logic, graceful fallback to rules-based decisions
- **Testing** — Full test suite (unit, integration, smoke)
- **Docker** — Multi-stage build, non-root user, health checks

## Quick start

### Local dev

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Type check (strict)
mypy --strict src/

# Lint
ruff check src/ tests/

# Run server
uvicorn xprclaw_mirofish.api:app --reload --port 8088
```

### Docker

```bash
docker build -t xprclaw-mirofish:latest .
docker run -p 8088:8088 \
  -e LOG_LEVEL=debug \
  -e MIROFISH_BASE_URL=http://mirofish:5001 \
  xprclaw-mirofish:latest
```

## API

### Health

```
GET /healthz
200 OK: {"status": "ok", "version": "0.1.0"}
```

### Endpoints (Phase 2+)

- `POST /simulate` — Run a market simulation, return decision
- `GET /simulate/<sim_id>` — Poll status
- `GET /cache/<content_hash>` — Retrieve cached result

## Phases

1. ✅ **Phase 1** — Scaffold (pytest, mypy, FastAPI, Docker)
2. ⏳ **Phase 2** — Models, personas, seed builder
3. ⏳ **Phase 3** — MiroFish HTTP client
4. ⏳ **Phase 4** — Simulator + decision engine
5. ⏳ **Phase 5** — D1 cache + endpoints
6. ⏳ **Phase 6** — Node.js bot integration
7. ⏳ **Phase 7** — Docker Compose + deploy

## Environment

See `.env.example` for all configuration variables.

**Critical:**
- `MIROFISH_BASE_URL` — where Flask backend runs
- `LLM_PROVIDER` + `LLM_API_KEY` — for agent prompting
- `CF_ACCOUNT_ID`, `CF_API_TOKEN`, `D1_DATABASE_ID` — Cloudflare integration

## Integration

The adapter is called by XPRClaw bot via `bot/src/mirofish/client.js`. See [MiroFish Integration Spec](../../docs/specs/mirofish-integration.md) for full architecture.
