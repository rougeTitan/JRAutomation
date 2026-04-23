# JobAI — React Native (Option C)

Fully self-contained native Android + iOS app.  
**No Flask server. No cloud backend. All API calls go directly from the device.**

```
Device → Gmail REST API   (email fetch / send)
Device → Groq REST API    (AI email reply, job analysis)
Device → OpenAI REST API  (deep job analysis, resume tailoring)
```

---

## Project Structure

```
mobile-rn/
├── App.js                        Root navigation + auth gate
├── app.json                      Expo config (bundle ID, icons)
├── src/
│   ├── api/
│   │   ├── gmail.js              Gmail REST API (fetch, send, delete)
│   │   ├── groq.js               Groq API (reply gen, quick analysis)
│   │   └── openai.js             OpenAI API (deep analysis, resume tailoring)
│   ├── utils/
│   │   ├── storage.js            SecureStore wrapper (tokens + API keys)
│   │   └── jobAnalyzer.js        Regex-based job analysis (offline fallback)
│   └── screens/
│       ├── LoginScreen.js        Google OAuth sign-in
│       ├── DashboardScreen.js    Job email list + refresh + AI analyze
│       ├── JobDetailScreen.js    Job detail + compose + send reply
│       └── SettingsScreen.js     API keys + sign out
└── src/components/
    ├── JobCard.js                Email card with skills, work type, AI badge
    └── StatBar.js                Total / Remote / Analyzed stats
```

---

## Prerequisites

| Tool | Install |
|------|---------|
| Node.js 18+ | https://nodejs.org |
| Expo CLI | `npm install -g expo-cli` |
| EAS CLI | `npm install -g eas-cli` |
| Android Studio | https://developer.android.com/studio |
| Expo Go app | Play Store on your phone (for dev testing) |

---

## Setup

### 1. Install dependencies
```bash
cd mobile-rn
npm install
```

### 2. Set up Google OAuth credentials for Mobile

You need a **separate** OAuth client for Android (different from the web one):

1. Go to https://console.cloud.google.com → APIs & Services → Credentials
2. **Create Credentials → OAuth 2.0 Client ID → Android**
3. Package name: `com.rougetitan.jobai`
4. SHA-1 fingerprint: run `cd android && ./gradlew signingReport` (after `npx expo prebuild`)
5. Copy the **Android Client ID** (no client secret — mobile OAuth doesn't use one)
6. Paste it into `src/screens/LoginScreen.js`:
   ```js
   const ANDROID_CLIENT_ID = 'YOUR_ANDROID_CLIENT_ID.apps.googleusercontent.com';
   ```
7. Repeat for iOS: **Create Credentials → OAuth 2.0 Client ID → iOS**
   ```js
   const IOS_CLIENT_ID = 'YOUR_IOS_CLIENT_ID.apps.googleusercontent.com';
   ```

### 3. Test on your phone with Expo Go (fastest)
```bash
npx expo start
```
Scan the QR code with **Expo Go** on your phone — app loads instantly, no build needed.

> ⚠️ Google Sign-In doesn't work in Expo Go (sandbox limitation).  
> For full sign-in testing, use a **dev build** (step 4).

### 4. Build a dev APK for your phone
```bash
npx expo prebuild          # generates android/ folder
npx expo run:android       # builds + installs on connected phone via USB
```

Or use EAS (cloud build, no Android Studio needed):
```bash
eas build --platform android --profile preview
```
EAS emails you the APK download link — install it directly on your phone.

---

## Adding API Keys

After signing in, go to **Settings** tab in the app:
- **Groq API Key** → https://console.groq.com/keys (free)
- **OpenAI API Key** → https://platform.openai.com/api-keys (optional)

Keys are stored using `expo-secure-store` (Android Keystore / iOS Keychain).  
They are never transmitted anywhere except directly to Groq/OpenAI.

---

## Build for Play Store

```bash
eas build --platform android --profile production
```

Then upload the `.aab` to https://play.google.com/console

---

## Key Differences from Flask Version (Option A)

| | Flask + Capacitor (Option A) | React Native (Option C) |
|--|--|--|
| Backend needed | Yes (Railway) | No |
| Works offline | No | Partial (cached data) |
| App store ready | Yes | Yes |
| Codebase | Python + HTML/JS | JavaScript only |
| API keys location | Server `.env` | Device SecureStore |
| Gmail auth | Server OAuth | Mobile OAuth (PKCE) |
