# GCSC CLAW — Self-Evolving AI on XPR Network

Self-Evolving AI Economic Loop: autonomous agents + multi-agent simulator + trading bot for XPR Network. Private beta waitlist opening Q2 2026.

> **Status:** Private Beta — Q2 2026  
> **Network:** XPR (Proton) · **Token:** `$XLAW` · **Audience:** B2B Enterprises, Crypto Funds

**Live Waitlist:** https://melxisedek75.github.io/xprclaw/  
**App Dashboard:** https://melxisedek75.github.io/xprclaw/app.html  
**Docs:** [QUICKSTART.md](QUICKSTART.md) | [DEPLOYMENT.md](DEPLOYMENT.md)

---

## Architecture

```
┌─────────────────────────────────┐
│  Frontend (GitHub Pages)        │
│  ├─ index.html (landing)        │
│  ├─ app.html (dashboard)        │
│  └─ PWA + Service Worker        │
└────────────┬────────────────────┘
             │ POST /v1/simulate
┌────────────▼────────────────────┐
│  FastAPI Adapter (Docker)       │
│  ├─ Decision engine             │
│  ├─ Cache (in-memory or D1)     │
│  └─ Simulator orchestrator      │
└────────────┬────────────────────┘
             │ HTTP
┌────────────▼────────────────────┐
│  MiroFish Simulator (Flask)     │
│  ├─ Graph builder               │
│  ├─ Multi-agent simulation      │
│  └─ Verdict extraction          │
└─────────────────────────────────┘
```

## What's Here

| Component | Files | Purpose |
|-----------|-------|---------|
| **Frontend Landing** | `index.html` | Public-facing waitlist + app description |
| **PWA Dashboard** | `app.html` | Dashboard with wallet connection + agent status |
| **Backend Adapter** | `services/mirofish-adapter/` | FastAPI orchestrator for MiroFish + decision logic |
| **Trading Bot** | `services/trading-bot/` | Node.js decision engine + client |
| **Docker** | `docker-compose.mirofish.yml` | Local dev stack (adapter + MiroFish) |
| **Config** | `manifest.json`, `sw.js` | PWA manifest + offline cache |
| **Docs** | `QUICKSTART.md`, `DEPLOYMENT.md` | Setup guide + production deployment |

---

## Quick Start

### 1. Frontend
```bash
# Landing page (public waitlist)
open https://melxisedek75.github.io/xprclaw/

# App dashboard (beta testing)
open https://melxisedek75.github.io/xprclaw/app.html

# Local dev
npx http-server . -p 8000
```

### 2. Backend (Local Docker)
```bash
export ANTHROPIC_API_KEY="sk-ant-..."
docker-compose -f docker-compose.mirofish.yml up -d

# Test
curl http://localhost:8088/healthz
```

### 3. Testing
```bash
# Test decision engine
cd services/trading-bot
node decision-engine.test.js  # ✅ 10/10 tests pass

# Test adapter
cd services/mirofish-adapter
python -m pytest tests/
```

**Full setup:** See [QUICKSTART.md](QUICKSTART.md)

---

## Architecture Overview

**Agents (5 personas)**
- Liquidity Data Analyzer (LDA)
- Dynamic Asset Allocator (DAA)
- KYC Agent (KYC-A)
- Economic Flow Analyzer (EFA)
- Research & Execution Agent (REA)

**Simulator**
- MiroFish multi-agent engine (Flask)
- Market scenario modeling
- Multi-round deliberation
- Verdict extraction via LLM (Claude)

**Adapter** (FastAPI)
- Orchestrates graph building → simulation → verdict extraction
- Decides: proceed | reduce | hold | abort
- Confidence thresholds (default 0.55)
- Caches via in-memory or Cloudflare D1

**Trading Bot** (Node.js)
- Decision engine merges agent opinions
- Paper trading by default (safe)
- Zero real transactions until manual override
- Auditable decision log

---

## Development

### Stack
- Frontend: Vanilla HTML/CSS/JS (no build required)
- Backend: Python 3.12 + FastAPI + Pydantic v2
- Bot: Node.js 18+ (no frameworks)
- Container: Docker + Docker Compose
- Cache: In-memory (dev) or Cloudflare D1 (prod)
- LLM: Anthropic Claude (via adapter)

### Testing
```bash
# Frontend (no tests needed for static site)

# Backend
cd services/mirofish-adapter
python -m pytest tests/ -v

# Bot
cd services/trading-bot
node decision-engine.test.js
```

### Deployment
- **Frontend:** GitHub Pages (auto via workflow)
- **Backend:** Railway, Render, or Fly.io (see DEPLOYMENT.md)
- **D1 Cache:** Cloudflare D1 + wrangler migrations

---

## Status & Roadmap

### Week 0 (Done) ✅
- [x] Landing page + waitlist form
- [x] PWA app dashboard
- [x] FastAPI adapter + decision engine
- [x] Node.js trading bot (test suite)
- [x] Docker Compose setup
- [x] GitHub Pages auto-deploy

### Week 1-2 (Next)
- [ ] @proton/web-sdk integration in app.html
- [ ] Real XPR testnet wallet connection
- [ ] Deploy adapter to Railway
- [ ] Live backend in app dashboard
- [ ] Paper trading for 20-50 beta users

### Week 3+
- [ ] Production readiness (monitoring, auth, rate limits)
- [ ] Real XPR mainnet support
- [ ] Trading execution (post-approval)
- [ ] Mobile optimization
- [ ] API documentation + SDKs

---

## Contact

- **Telegram:** https://t.me/gcsc_claw
- **GitHub Issues:** https://github.com/Melxisedek75/xprclaw/issues
- **Email:** rivnesergiy@gmail.com
- **White Paper:** [xprclaw_whitepaper.pdf](xprclaw_whitepaper.pdf)

---

**Built with:** Python, Node.js, FastAPI, Docker, Anthropic Claude  
**License:** See [TERMS.md](TERMS.md)  
**Version:** 0.1.0 (Private Beta — Q2 2026)
