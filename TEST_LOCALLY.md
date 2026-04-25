# Test GCSC CLAW Locally (E2E)

Complete end-to-end test: frontend → FastAPI adapter → MiroFish simulator → decision.

## Prerequisites

- Docker & Docker Compose installed
- Anthropic API key (set as `ANTHROPIC_API_KEY` env var)
- This repo cloned locally

## Step 1: Start Backend Stack

```bash
export ANTHROPIC_API_KEY="sk-ant-..."

cd /path/to/xprclaw
docker-compose -f docker-compose.mirofish.yml up -d
```

**Expected:**
```bash
docker ps | grep xprclaw
# xprclaw-mirofish-adapter (port 8088)
# xprclaw-mirofish (port 5001)
```

**Verify health:**
```bash
curl http://localhost:8088/healthz
# {"status": "ok", "version": "0.1.0", ...}

curl http://localhost:5001/health
# MiroFish health response
```

## Step 2: Start Frontend

```bash
cd /path/to/xprclaw
npm run dev
# or: npx http-server . -p 8000
```

Open: **http://localhost:8000/app.html**

## Step 3: Test Full Flow

### 3a. Check Backend Status
- Look at "Simulator" card
- Should show: "Adapter Status: Online ✓ (v0.1.0)"
- If offline: Docker not running

### 3b. Connect Wallet (Mock)
- Click "Connect WebAuth Wallet" button
- Shows mock address (for MVP testing)
- Uses `src/wallet.js` module

### 3c. Run Simulation
- Click "Run Simulation" button in agent card
- Backend makes requests to MiroFish
- Shows decision (proceed/reduce/hold/abort)
- Shows confidence % and rationale

**Expected result:**
```
Decision: PROCEED or REDUCE or HOLD or ABORT
Confidence: 65% (or similar)
Rationale: "Merged 5 agent opinions..."
```

## Step 4: Watch Logs

**Frontend (browser DevTools):**
```javascript
// Open Console (F12)
// See logs like:
// "Adapter online: {status: 'ok', version: '0.1.0', ...}"
// "Simulation result: {decision: 'proceed', confidence: 0.75, ...}"
```

**Backend (adapter):**
```bash
docker logs xprclaw-mirofish-adapter -f
# See requests, cache hits, simulation steps
```

**MiroFish (simulator):**
```bash
docker logs xprclaw-mirofish -f
# See graph building, simulation progress
```

## Step 5: Test Paper Trading (Future)

When paper trading UI is complete:
```javascript
// In browser console
window.CONFIG.FEATURES.PAPER_TRADING = true
// Run simulation → shows trade execution preview
```

---

## Debugging

### "Adapter Status: Offline"
**Check:**
```bash
# Is Docker running?
docker ps

# Are containers up?
docker-compose -f docker-compose.mirofish.yml ps

# Can you reach the endpoint?
curl -v http://localhost:8088/healthz
```

### "Simulation failed"
**Check:**
```bash
# Look at adapter logs
docker logs xprclaw-mirofish-adapter | tail -20

# Check ANTHROPIC_API_KEY
echo $ANTHROPIC_API_KEY

# Is MiroFish running?
curl http://localhost:5001/health
```

### "Decision is always HOLD"
- Normal if agents disagree
- Check bot status: look at `confidence` value
- Low confidence (< 0.55) → hold by default

---

## Clean Up

```bash
# Stop containers
docker-compose -f docker-compose.mirofish.yml down

# Stop frontend
# (Ctrl+C in terminal)
```

---

## Next Steps After Testing

1. **Deploy backend** (see [RAILWAY_DEPLOY.md](RAILWAY_DEPLOY.md))
2. **Update frontend URL** in `src/config.js` or `.env`
3. **Real XPR integration** in `src/wallet.js` (await @proton/web-sdk)
4. **Paper trading** UI for decision confirmation

---

## Architecture Verification

This test verifies:
- ✅ Frontend loads + Service Worker cache
- ✅ Wallet module can connect (mock)
- ✅ API client makes HTTP requests
- ✅ Backend adapter accepts requests
- ✅ Decision engine produces output
- ✅ MiroFish simulator runs
- ✅ Verdict extraction works
- ✅ Full E2E latency (should be ~5-30 seconds)

If all pass, you're ready for:
- Railway deployment
- Real XPR testnet
- Beta user testing

---

**Questions?** Check logs or open an issue on GitHub.
