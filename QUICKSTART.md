# GCSC CLAW — Quick Start Guide

## Overview

**Посадочная страница:** [index.html](index.html) — для привлечения пользователей и сбора waitlist

**PWA-приложение:** [app.html](app.html) — для тестирования с beta-пользователями

**Backend:** FastAPI adapter + MiroFish simulator в Docker

---

## 1. Frontend (Frontend)

### Landing Page
```bash
# Default — just open in browser
open index.html
# Or run local server
npx http-server . -p 8080
```

**Features:**
- Waitlist form (emails stored in localStorage for MVP)
- PWA installable
- Offline-ready (Service Worker cache)
- OG-preview ready (Twitter, Telegram, etc.)

### App Dashboard
```bash
open app.html
# Or navigate to http://localhost:8080/app.html
```

**Features:**
- Mock wallet connection (ready for @proton/web-sdk)
- Shows adapter health status
- Displays agent status
- Paper trading mode info

---

## 2. Backend (Local Development with Docker)

### Prerequisites
- Docker 20.10+
- Docker Compose 1.29+
- `ANTHROPIC_API_KEY` environment variable

### Setup & Run
```bash
# Set your Anthropic API key
export ANTHROPIC_API_KEY="sk-ant-..."

# Start the full stack (adapter + MiroFish)
docker-compose -f docker-compose.mirofish.yml up -d

# Verify health
curl http://localhost:8088/healthz
curl http://localhost:5001/health
```

### Test Adapter
```bash
# Health check
curl http://localhost:8088/healthz

# Run a simulation
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
      "timestamp": "2026-04-25T15:00:00Z"
    },
    "horizon_hours": 24,
    "max_rounds": 30
  }'
```

---

## 3. Node.js Trading Bot

### Test Decision Engine
```bash
cd services/trading-bot
node decision-engine.test.js
# All 10 tests pass ✅
```

### Use Bot in Your App
```javascript
const SimulatorClient = require('./services/trading-bot/client');
const { makeDecision } = require('./services/trading-bot/decision-engine');

const client = new SimulatorClient('http://localhost:8088');
const result = await client.simulate({
  scenario: 'staking_optimization',
  market_state: { /* ... */ },
  horizon_hours: 24,
  max_rounds: 30,
});

const decision = makeDecision(result);
console.log('Decision:', decision.decision);
console.log('Should Execute:', decision.should_execute);
```

---

## 4. Full Stack Integration

### Architecture
```
Frontend (index.html / app.html)
    ↓ POST /v1/simulate
FastAPI Adapter (port 8088)
    ↓ HTTP
MiroFish Simulator (port 5001)
    ↓
Decision Engine (JavaScript)
    ↓
Trading Bot (paper mode by default)
```

### Test End-to-End
1. Open `app.html` in browser
2. Run backend: `docker-compose -f docker-compose.mirofish.yml up -d`
3. Click "Connect Wallet" (mock)
4. Check "Adapter Status" — should show "Online ✓"
5. Backend auto-tests the adapter health endpoint

---

## 5. Next Steps

### For Private Beta (Week 1-2)
- [ ] Install `@proton/web-sdk` in app.html
- [ ] Connect to real XPR testnet wallet
- [ ] Deploy adapter to Railway / Render
- [ ] Update app.html to call live backend
- [ ] Enable paper trading mode for first 20-50 beta users

### For Production (Week 3+)
- [ ] Real XPR mainnet integration
- [ ] Trading execution (with user confirmation)
- [ ] API authentication + rate limiting
- [ ] Sentry monitoring
- [ ] Real email notifications (Buttondown / ConvertKit)

---

## Configuration Files

| File | Purpose |
|------|---------|
| [DEPLOYMENT.md](DEPLOYMENT.md) | Complete deployment guide (Railway, K8s, D1) |
| [docker-compose.mirofish.yml](docker-compose.mirofish.yml) | Local dev stack orchestration |
| [services/mirofish-adapter/](services/mirofish-adapter/) | FastAPI adapter source |
| [services/trading-bot/](services/trading-bot/) | Decision engine + client |
| [manifest.json](manifest.json) | PWA manifest |

---

## Troubleshooting

**"Connection refused" to MiroFish**
```bash
docker ps | grep mirofish
docker logs xprclaw-mirofish
```

**Adapter health check fails**
```bash
# Check if ports are already in use
lsof -i :8088
lsof -i :5001
# Kill if needed: kill -9 <PID>
```

**Service Worker caching issues**
```javascript
// In DevTools Console
navigator.serviceWorker.getRegistrations().then(regs => {
  regs.forEach(r => r.unregister());
});
// Then refresh
```

---

## Contact & Support

- **Telegram:** https://t.me/gcsc_claw
- **GitHub Issues:** https://github.com/Melxisedek75/xprclaw/issues
- **Email:** rivnesergiy@gmail.com

**Status:** Private Beta — Q2 2026
