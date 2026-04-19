# GCSC CLAW — Download Site Deployment Guide

## What you're deploying

A professional download landing page that lets visitors install GCSC CLAW as a **Progressive Web App (PWA)** on iOS, Android, and desktop — no app stores required.

**Files in `xprclaw-download/`:**
- `index.html` — The landing page (what users see)
- `xprclaw_standalone.html` — The actual app (opens after install)
- `manifest.json` — PWA configuration
- `sw.js` — Service Worker (offline support)
- `icon-192.png` + `icon-512.png` — App icons
- `xprclaw_project.zip` — Full source code for download
- `xprclaw_whitepaper.pdf` — White Paper for download

## ⚠️ Important: PWA requires HTTPS

**PWA install will NOT work from `file://` or `http://`.** You MUST host this on HTTPS. Good news: this is free and takes 5 minutes.

---

## Option 1: Deploy to GitHub Pages (FREE, 5 minutes)

**Recommended for most users.**

### Steps:

1. Create a GitHub account at https://github.com (if you don't have one).

2. Create a new repository called `xprclaw` (or any name you want).

3. Upload all files from the `xprclaw-download/` folder to the repo.
   - Drag and drop in the web UI, or use `git push`.

4. Go to repository **Settings → Pages**.

5. Under "Source", select:
   - **Branch:** `main`
   - **Folder:** `/ (root)`
   - Click **Save**.

6. Wait 2 minutes. Your site will be live at:
   ```
   https://YOUR_USERNAME.github.io/xprclaw/
   ```

7. Share that URL. Users visit it → tap "Install App" → PWA installed on their phone.

### Custom domain (optional)

In repo **Settings → Pages → Custom domain**, enter your domain (e.g. `app.gcscclaw.com`).
Add these DNS records at your domain registrar:
```
Type: A      Value: 185.199.108.153
Type: A      Value: 185.199.109.153
Type: A      Value: 185.199.110.153
Type: A      Value: 185.199.111.153
```

HTTPS will be automatic (via Let's Encrypt).

---

## Option 2: Netlify (FREE, drag & drop)

1. Go to https://app.netlify.com/drop
2. Drag the `xprclaw-download` folder onto the page.
3. Done. Your site is live at a URL like `https://random-name.netlify.app/`.
4. You can rename it in **Site settings**.
5. Custom domain: free with auto-HTTPS.

---

## Option 3: Vercel (FREE)

1. Install Vercel CLI: `npm install -g vercel`
2. In the `xprclaw-download/` folder, run: `vercel`
3. Follow prompts. Site deploys in under 60 seconds.

---

## Option 4: Your own server

Any web server with HTTPS will work:
- **Nginx:** put files in `/var/www/xprclaw/`, point server block to it.
- **Apache:** put files in `/var/www/html/xprclaw/`.
- **Caddy** (easiest with auto-HTTPS):
  ```
  xprclaw.yourdomain.com {
      root * /path/to/xprclaw-download
      file_server
  }
  ```

---

## Testing the install

After deploying, test on each platform:

### iPhone (Safari only)
1. Open site in Safari (not Chrome).
2. Tap Share button (⬆️ at bottom).
3. Scroll → "Add to Home Screen" → Add.
4. Icon appears on home screen.

### Android (Chrome/Brave)
1. Open site in Chrome.
2. Should see "Install app" banner at bottom (or tap the Install button).
3. If not: ⋮ menu → "Install app" → Install.
4. App installs like a regular Android app.

### Desktop (Chrome/Edge/Brave)
1. Open site.
2. Look for install icon (⊕) in address bar, or button on page.
3. Click → Install.
4. Opens as a standalone app window.

---

## How to update the app later

1. Edit `xprclaw_standalone.html` (or rebuild from the full source in `xprclaw_project.zip`).
2. Update the cache version in `sw.js`:
   ```js
   const CACHE_VERSION = 'gcsc-claw-v1.1'; // bump version
   ```
3. Upload new files to your host.
4. Users get the update on next open (Service Worker fetches new version).

---

## Going further: native iOS/Android apps

If later you want native apps in the App Store and Google Play:

1. Use **Capacitor** (https://capacitorjs.com) to wrap the PWA:
   ```bash
   npm install @capacitor/core @capacitor/cli @capacitor/ios @capacitor/android
   npx cap init "GCSC CLAW" com.gcscdao.claw
   npx cap add ios
   npx cap add android
   ```
2. Build and submit:
   - **iOS:** Xcode + Apple Developer account ($99/year)
   - **Android:** Android Studio + Google Play Console ($25 one-time)

But the PWA approach avoids all store restrictions, commissions, and review delays. It's what most serious dApps use today.

---

## Contact

- Email: gcscdao@gmail.com
- GitHub: https://github.com/Melxisedek75/gcsc-website

White Paper v1.0 — 2025
