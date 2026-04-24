# GCSC CLAW — Download & Install

Public landing page to install **GCSC CLAW** as a Progressive Web App on iOS, Android, and desktop — no app stores required.

> **Status:** Private Beta — Q2 2026
> **Network:** XPR (Proton) · **Token:** `$XLAW` · **Audience:** B2B Enterprises

**Live:** `https://melxisedek75.github.io/xprclaw/` *(replace with actual URL after deploy)*

---

## What's here

| File | Purpose |
|---|---|
| `index.html` | Public landing page (PWA install + downloads) |
| `xprclaw_standalone.html` | The app itself (opens after install) |
| `manifest.json` | PWA configuration |
| `sw.js` | Service Worker (offline cache) |
| `icon-192.png`, `icon-512.png` | App icons |
| `xprclaw_project.zip` | Full source bundle (download) |
| `xprclaw_whitepaper.pdf` | White Paper v1.0 |
| `DEPLOY.md` | Hosting instructions (GitHub Pages, Netlify, Vercel, own server) |
| `PRIVACY.md`, `TERMS.md` | Legal basics |
| `.github/workflows/pages.yml` | Auto-deploy to GitHub Pages on push to `main` |

---

## Deploy in 5 minutes

```bash
git init
git add .
git commit -m "Initial: download site + PWA + workflow"
git branch -M main
git remote add origin https://github.com/<your-user>/xprclaw.git
git push -u origin main
```

Then in GitHub repo: **Settings → Pages → Source: GitHub Actions**. The included workflow publishes `index.html` + static assets automatically on every push.

Full hosting options (Netlify, Vercel, self-hosted) are in [DEPLOY.md](DEPLOY.md).

---

## Local preview

No build step required — zero-dependency static site.

```bash
# Python
python -m http.server 8000

# or Node
npx serve .
```

Then open `http://localhost:8000`.

> PWA install requires HTTPS — won't work from `file://` or plain `http://` (except `localhost`). Deploy to GitHub Pages / Netlify / Vercel to test the full install flow.

---

## Updating the app

1. Edit `xprclaw_standalone.html` (or rebuild from the full source in `xprclaw_project.zip`).
2. Bump the cache version in `sw.js`:
   ```js
   const CACHE_VERSION = 'gcsc-claw-v1.1';
   ```
3. Push — Service Worker fetches the new version on next open.

---

## Links

- GitHub (website): <https://github.com/Melxisedek75/gcsc-website>
- Contact: <gcscdao@gmail.com>
- White Paper: [xprclaw_whitepaper.pdf](xprclaw_whitepaper.pdf)

---

White Paper v1.0 — 2025–2026
