# XPRClaw MiroFish Adapter — Deployment Guide

End-to-end deployment instructions for the MiroFish multi-agent simulator adapter.

## Architecture

```
┌──────────────────────────────────────────────────────────┐
│  XPRClaw Frontend (Web/PWA)                              │
│  ├─ Landing page (index.html)                            │
│  └─ Calls /v1/simulate on adapter backend                │
└────────────┬─────────────────────────────────────────────┘
             │ HTTP POST
             ↓
┌──────────────────────────────────────────────────────────┐
│  FastAPI Adapter (xprclaw-mirofish-adapter)              │
│  ├─ POST /v1/simulate                                    │
│  ├─ GET /healthz                                         │
│  ├─ Cache layer (in-memory or D1)                        │
│  └─ Simulator orchestrator                               │
└────────────┬─────────────────────────────────────────────┘
             │ HTTP
             ↓
┌──────────────────────────────────────────────────────────┐
│  MiroFish Backend (Flask, port 5001)                     │
│  ├─ POST /api/graph/build                                │
│  ├─ GET /api/graph/status/{project_id}                   │
│  ├─ POST /api/simulation/prepare                         │
│  ├─ POST /api/simulation/start                           │
│  ├─ GET /api/simulation/status/{sim_id}                  │
│  ├─ POST /api/report/generate                            │
│  └─ GET /api/report/{report_id}                          │
└──────────────────────────────────────────────────────────┘
```

## Local Development (Docker)

### Prerequisites

- Docker 20.10+
- Docker Compose 1.29+
- ANTHROPIC_API_KEY set in environment

### Setup

1. **Clone and prepare:**
```bash
git clone <repo-url> xprclaw
cd xprclaw/services/mirofish-adapter
```

2. **Create .env file:**
```bash
cat > .env << 'EOF'
LOG_LEVEL=info
MIROFISH_BASE_URL=http://mirofish:5001
MIROFISH_TIMEOUT_SECONDS=300

LLM_PROVIDER=anthropic
LLM_API_KEY=${ANTHROPIC_API_KEY}
LLM_MODEL=claude-3-sonnet-20240229

CF_ACCOUNT_ID=
CF_API_TOKEN=
D1_DATABASE_ID=

SIM_TIMEOUT_SECONDS=300
SIM_MAX_AGENTS=50
CACHE_EVICTION_MODE=lru
CACHE_MAX_AGE_SECONDS=3600

ENV=development
EOF
```

3. **Start stack:**
```bash
cd ../..
docker-compose -f docker-compose.mirofish.yml up -d
```

4. **Verify health:**
```bash
curl http://localhost:8088/healthz
# Expected: {"status": "ok", "version": "0.1.0", "cache": {...}}

curl http://localhost:5001/health
# Expected: MiroFish health response
```

5. **Run example simulation:**
```bash
curl -X POST http://localhost:8088/v1/simulate \
  -H "Content-Type: application/json" \
  -d '{
    "scenario": "staking_optimization",
    "market_state": {
      "xpr_price_usd": 0.0042,
      "staking_apy": 0.085,
      "loan_apy": 0.061,
      "metalx_xpr_usd_spread_bps": 23,
      "treasury_xpr": 1250000,
      "open_loan_xpr": 300000,
      "timestamp": "2026-04-24T15:00:00Z"
    },
    "horizon_hours": 24,
    "max_rounds": 30
  }'
```

## Production Deployment

### Railway (Recommended)

1. **Connect GitHub:**
```bash
# Push to GitHub (if not already done)
git push origin main
```

2. **Create Railway project:**
- Go to https://railway.app
- Connect GitHub repo
- Railway auto-detects Dockerfile in services/mirofish-adapter

3. **Set environment variables:**
- LLM_API_KEY (required)
- MIROFISH_BASE_URL (set to external MiroFish service)
- CF_ACCOUNT_ID, CF_API_TOKEN, D1_DATABASE_ID (if using D1)

4. **Deploy:**
```bash
railway up
```

5. **Configure domain:**
- Railway assigns `<project>.railway.app`
- Add custom domain in Railway dashboard

### Docker Swarm / Kubernetes

**Dockerfile already includes:**
- Multi-stage build (optimized image size)
- Non-root user (security)
- Health checks
- Python 3.12-slim base

**For Kubernetes:**
```bash
kubectl create namespace xprclaw
kubectl apply -f k8s/mirofish-adapter-deployment.yaml
kubectl expose deployment xprclaw-mirofish-adapter \
  --type=LoadBalancer --port=8088
```

### Cloudflare D1 Integration

**Prerequisite:** D1 database created in Cloudflare account

1. **Run migrations:**
```bash
wrangler migrations run --name d1_db
# This executes migrations/001_init_cache.sql
```

2. **Update .env:**
```bash
CF_ACCOUNT_ID=your_account_id
CF_API_TOKEN=your_api_token
D1_DATABASE_ID=your_database_id
```

3. **Restart adapter:**
```bash
docker-compose -f docker-compose.mirofish.yml restart xprclaw-mirofish-adapter
```

Cache backend automatically switches to D1 if credentials provided.

## Monitoring

### Logging

```bash
# View adapter logs
docker logs xprclaw-mirofish-adapter -f

# View MiroFish logs
docker logs xprclaw-mirofish -f
```

### Health Checks

Continuous health monitoring (already configured in docker-compose):
```bash
# Check adapter health
curl http://localhost:8088/healthz

# Check MiroFish health
curl http://localhost:5001/health
```

### Metrics

Optional: Add Sentry for error tracking
```python
import sentry_sdk
sentry_sdk.init(dsn=os.environ.get("SENTRY_DSN"))
```

## Scaling

### For High Load

1. **Increase worker processes:**
   - Update Dockerfile: `uvicorn ... --workers 4`
   - Or use Gunicorn: `gunicorn -w 4 ...`

2. **Cache optimization:**
   - Use D1 for persistent caching across instances
   - Redis optional for multi-instance coordination

3. **Load balancing:**
   - Railway auto-scales horizontally
   - Kubernetes: adjust replicas in deployment

## Troubleshooting

### "Connection refused" to MiroFish

```bash
# Verify MiroFish is running
docker ps | grep mirofish

# Check network connectivity
docker exec xprclaw-mirofish-adapter \
  curl -v http://mirofish:5001/health
```

### Cache misses

```bash
# Check cache stats
curl http://localhost:8088/healthz | jq '.cache'

# D1 debug: verify database
wrangler d1 execute d1_db --command "SELECT COUNT(*) FROM mirofish_simulations"
```

### Slow simulations

- Increase MIROFISH_TIMEOUT_SECONDS (default 300s)
- Check MiroFish service load
- Monitor network latency between services

## Rollback

```bash
# Docker Compose
docker-compose -f docker-compose.mirofish.yml down
docker-compose -f docker-compose.mirofish.yml up -d

# Railway
railway rollback <previous-deployment-id>

# Kubernetes
kubectl rollout undo deployment/xprclaw-mirofish-adapter
```

## Security Checklist

- [ ] LLM_API_KEY is secret-managed (not in git)
- [ ] CF credentials stored securely
- [ ] HTTPS enforced on public endpoints
- [ ] Rate limiting enabled (planned)
- [ ] Input validation on all endpoints
- [ ] CORS configured for allowed origins

## Next Steps

1. **Monitor in production** (first 24 hours)
2. **Set up alerting** (response time, error rate)
3. **Optimize cache TTL** based on usage patterns
4. **Add API key authentication** if needed
5. **Document SLAs** (latency, availability targets)
