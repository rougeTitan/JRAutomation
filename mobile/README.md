# JobAI Mobile — Capacitor Native App

Native Android + iOS wrapper for the JobAI Flask web app.

## Prerequisites

| Tool | Required for | Download |
|------|-------------|----------|
| Node.js 18+ | Capacitor CLI | https://nodejs.org |
| Android Studio | Android APK | https://developer.android.com/studio |
| Xcode 15+ | iOS IPA | Mac only — App Store |
| Google Play account | Play Store | $25 one-time — https://play.google.com/console |
| Apple Developer | App Store | $99/year — https://developer.apple.com |

---

## Step 1 — Deploy Flask backend to Railway (required)

1. Go to https://railway.app → **New Project** → **Deploy from GitHub repo**
2. Select `rougeTitan/JRAutomation`
3. Railway auto-detects Python via `nixpacks.toml`
4. Run `python export_token.py` locally, copy the output
5. In Railway → **Variables**, add:
   ```
   GMAIL_TOKEN_B64        = <from export_token.py>
   GMAIL_CREDENTIALS_JSON = <from export_token.py>
   GROQ_API_KEY           = <your key>
   OPENAI_API_KEY         = <your key>
   FLASK_ENV              = production
   ```
6. Copy your Railway public URL (e.g. `https://jrautomation.railway.app`)

---

## Step 2 — Update Capacitor config

Edit `capacitor.config.json` → replace `YOUR-APP.railway.app`:
```json
"server": {
  "url": "https://jrautomation.railway.app"
}
```

---

## Step 3 — Build Android APK

```bash
cd mobile
npm install
npx cap add android
npx cap sync android
npx cap open android
```

In Android Studio:
- Wait for Gradle sync to finish
- **Build → Generate Signed Bundle/APK** → APK
- Create a keystore (save it safely — you need it for every update)
- Build release APK

---

## Step 4 — Publish to Google Play

1. Go to https://play.google.com/console → **Create app**
2. Upload the signed APK under **Internal testing** first
3. Fill in store listing (description, screenshots, icon)
4. Submit for review (~1–3 days)

---

## Step 5 — Build iOS IPA (Mac required)

```bash
npx cap add ios
npx cap sync ios
npx cap open ios
```

In Xcode:
- Set your **Team** (Apple Developer account)
- Set **Bundle Identifier** = `com.rougetitan.jobai`
- **Product → Archive**
- **Distribute App → App Store Connect**

---

## App Details

| Field | Value |
|-------|-------|
| App ID | `com.rougetitan.jobai` |
| App Name | JobAI |
| Version | 1.0.0 |
| Min Android | API 22 (Android 5.1) |
| Min iOS | iOS 13 |
