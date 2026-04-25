# Deploy FastAPI Adapter to Railway

Simple one-click deployment for production backend.

## Prerequisites

1. **GitHub Account** (repo already set up: `Melxisedek75/xprclaw`)
2. **Railway Account** (free at https://railway.app)
3. **Anthropic API Key** (get at https://console.anthropic.com)

## Step 1: Connect to Railway

```bash
# No setup needed — Railway auto-detects Dockerfile in services/mirofish-adapter
# Just go to: https://railway.app
```

Click "New Project" → "Deploy from GitHub" → Select `Melxisedek75/xprclaw` repo.

## Step 2: Configure Environment Variables

In Railway dashboard, set:

```
LOG_LEVEL=info
MIROFISH_BASE_URL=http://mirofish:5001
MIROFISH_TIMEOUT_SECONDS=300

LLM_PROVIDER=anthropic
LLM_API_KEY=sk-ant-...  ← PASTE YOUR KEY HERE
LLM_MODEL=claude-3-sonnet-20240229

SIM_TIMEOUT_SECONDS=300
SIM_MAX_AGENTS=50
CACHE_EVICTION_MODE=lru
CACHE_MAX_AGE_SECONDS=3600

ENV=production
```

⚠️ **IMPORTANT**: Keep `LLM_API_KEY` secret — never commit to git.

## Step 3: Deploy

Railway auto-deploys on push to GitHub. Or click "Deploy" in dashboard.

**Expected:** Service starts on Railway's public URL (e.g., `https://xprclaw-adapter.railway.app`)

## Step 4: Verify

```bash
# Test health endpoint
curl https://xprclaw-adapter.railway.app/healthz

# Expected response:
# {"status": "ok", "version": "0.1.0", "cache": {...}}
```

## Step 5: Update Frontend

Update `.env` in root directory:

```bash
VITE_API_URL=https://xprclaw-adapter.railway.app
```

Or hardcode in `src/config.js`:

```javascript
ADAPTER_URL: 'https://xprclaw-adapter.railway.app',
```

Push to GitHub → app.html automatically uses the new URL.

## Step 6: Link MiroFish Backend (Optional)

If you want to run MiroFish in production (separate container):

1. Deploy MiroFish to Railway separately
2. Update `MIROFISH_BASE_URL` in environment variables
3. Ensure network connectivity between containers

For MVP, you can use a public MiroFish instance or mock data.

---

## Troubleshooting

### "Build failed"
Check Railway logs. Common causes:
- Missing environment variables
- Python version incompatibility (needs 3.12+)
- Dockerfile issues

### "Service crashed"
View logs in Railway dashboard. Check:
- `LLM_API_KEY` is valid
- `MIROFISH_BASE_URL` is reachable
- Sufficient memory (Railway free tier has limits)

### Health check fails
```bash
curl -v https://xprclaw-adapter.railway.app/healthz
# Should return 200 OK with JSON body
```

---

## Scaling

Railway auto-scales based on traffic. For high load:
1. Upgrade to paid plan
2. Increase replica count in Railway dashboard
3. Use Cloudflare D1 for distributed caching

## Costs

**Free tier:**
- 500 hours/month CPU
- Sufficient for private beta (20-50 users)

**Paid tier:** $5/month + usage

---

## Next: Connect Frontend to Backend

After Railway deployment, update:
- `.env` → `VITE_API_URL`
- Test in `app.html` → should show "Adapter Status: Online ✓"
- Click "Connect Wallet" → UI ready for real XPR integration

All changes auto-deploy via GitHub Pages workflow.

---

**See Also:** [DEPLOYMENT.md](DEPLOYMENT.md) for full architecture options.
