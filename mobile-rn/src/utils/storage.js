import * as SecureStore from 'expo-secure-store';

const KEYS = {
  ACCESS_TOKEN: 'gmail_access_token',
  REFRESH_TOKEN: 'gmail_refresh_token',
  TOKEN_EXPIRY: 'gmail_token_expiry',
  GROQ_API_KEY: 'groq_api_key',
  OPENAI_API_KEY: 'openai_api_key',
  JOBS_CACHE: 'jobs_cache',
  USER_EMAIL: 'user_email',
};

// ── OAuth Token ────────────────────────────────────────────────────────────
export async function saveTokens({ accessToken, refreshToken, expiresIn }) {
  await SecureStore.setItemAsync(KEYS.ACCESS_TOKEN, accessToken);
  if (refreshToken) await SecureStore.setItemAsync(KEYS.REFRESH_TOKEN, refreshToken);
  const expiry = Date.now() + (expiresIn || 3600) * 1000;
  await SecureStore.setItemAsync(KEYS.TOKEN_EXPIRY, String(expiry));
}

export async function getAccessToken() {
  return SecureStore.getItemAsync(KEYS.ACCESS_TOKEN);
}

export async function getRefreshToken() {
  return SecureStore.getItemAsync(KEYS.REFRESH_TOKEN);
}

export async function isTokenExpired() {
  const expiry = await SecureStore.getItemAsync(KEYS.TOKEN_EXPIRY);
  if (!expiry) return true;
  return Date.now() > parseInt(expiry, 10) - 60_000;
}

export async function clearTokens() {
  await SecureStore.deleteItemAsync(KEYS.ACCESS_TOKEN);
  await SecureStore.deleteItemAsync(KEYS.REFRESH_TOKEN);
  await SecureStore.deleteItemAsync(KEYS.TOKEN_EXPIRY);
}

// ── API Keys ───────────────────────────────────────────────────────────────
export async function saveGroqKey(key) {
  await SecureStore.setItemAsync(KEYS.GROQ_API_KEY, key);
}
export async function getGroqKey() {
  return SecureStore.getItemAsync(KEYS.GROQ_API_KEY);
}

export async function saveOpenAIKey(key) {
  await SecureStore.setItemAsync(KEYS.OPENAI_API_KEY, key);
}
export async function getOpenAIKey() {
  return SecureStore.getItemAsync(KEYS.OPENAI_API_KEY);
}

// ── Jobs Cache (AsyncStorage-style via SecureStore for small data) ────────
export async function saveJobsCache(jobs) {
  try {
    await SecureStore.setItemAsync(KEYS.JOBS_CACHE, JSON.stringify(jobs));
  } catch {}
}

export async function getJobsCache() {
  try {
    const raw = await SecureStore.getItemAsync(KEYS.JOBS_CACHE);
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

// ── User info ──────────────────────────────────────────────────────────────
export async function saveUserEmail(email) {
  await SecureStore.setItemAsync(KEYS.USER_EMAIL, email);
}
export async function getUserEmail() {
  return SecureStore.getItemAsync(KEYS.USER_EMAIL);
}
