# Android APK via Bubblewrap (PWA → TWA)

This project ships an Android APK as a **Trusted Web Activity (TWA)** that
wraps the PWA at the production URL. The APK auto-updates with the web
app — no rebuild needed per spec iteration.

## Prerequisites (one-time)

```bash
# Install Bubblewrap CLI (Node 16+)
npm install -g @bubblewrap/cli

# JDK 17+ and Android SDK (Bubblewrap will offer to install if missing)
```

## Build the APK

```bash
# 1. The PWA lives at REACT_APP_BACKEND_URL/ — the manifest is at /manifest.json
PWA_URL=https://<your-deploy>.preview.emergentagent.com

# 2. Initialise the TWA project
bubblewrap init --manifest "$PWA_URL/manifest.json"
#    Accept defaults; package name suggested: org.interdependentway.a0p

# 3. Build the signed APK / AAB
bubblewrap build
#    Output: app-release-signed.apk (sideload) and app-release-bundle.aab (Play Store)
```

## Sideload to a device

```bash
adb install -r app-release-signed.apk
```

## Play Store

Upload `app-release-bundle.aab`. One-time $25 dev account fee.

## Why option B (TWA) was chosen

- The app iterates weekly (donation-funded research instrument). A TWA
  auto-tracks the web app — no APK rebuild per spec change.
- No JS port of the AIMMH patterns + provider adapters required (option C
  pocket-runner is a separate future workstream).
- Bubblewrap is ~90 minutes start-to-finish vs. a couple of days for a
  Capacitor or React-Native wrap.

## Trade-offs accepted

- Phone has to reach the hosted backend (no offline-first).
- Some Play Store policies (background services, deep FS access) blocked.
- Detachable-agent runtime stays server-mediated for now.

## hmmm

- `bubblewrap` requires interactive prompts; CI integration not wired.
- Asset link verification (`.well-known/assetlinks.json`) must be served
  from the production origin before Play Store upload. Currently absent.
- App icon is SVG; Bubblewrap will rasterise but a PNG fallback is wiser.
