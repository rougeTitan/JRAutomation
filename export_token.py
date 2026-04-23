"""
export_token.py — Run this ONCE locally to generate the environment variables
needed for Railway/Render cloud deployment.

Usage:
    python export_token.py

Copy the printed values into Railway → Variables dashboard.
"""
import os
import pickle
import base64
import json

AGENT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'gmail_agent')
TOKEN_FILE = os.path.join(AGENT_DIR, 'token.pickle')
CREDS_FILE = os.path.join(AGENT_DIR, 'credentials.json')

print("=" * 60)
print("  Railway / Render Environment Variable Exporter")
print("=" * 60)

# ── Export GMAIL_TOKEN_B64 ─────────────────────────────────
if os.path.exists(TOKEN_FILE):
    with open(TOKEN_FILE, 'rb') as f:
        token_b64 = base64.b64encode(f.read()).decode()
    print("\n✅ GMAIL_TOKEN_B64 (paste into Railway Variables):")
    print("-" * 60)
    print(token_b64)
    print("-" * 60)
else:
    print(f"\n❌ token.pickle not found at {TOKEN_FILE}")
    print("   Run the app locally first to generate it.")

# ── Export GMAIL_CREDENTIALS_JSON ─────────────────────────
if os.path.exists(CREDS_FILE):
    with open(CREDS_FILE, 'r') as f:
        creds_content = f.read().strip()
    print("\n✅ GMAIL_CREDENTIALS_JSON (paste into Railway Variables):")
    print("-" * 60)
    print(creds_content)
    print("-" * 60)
else:
    print(f"\n❌ credentials.json not found at {CREDS_FILE}")

print("""
📋 Next steps:
  1. Go to https://railway.app → your project → Variables
  2. Add:  GMAIL_TOKEN_B64       = (value above)
  3. Add:  GMAIL_CREDENTIALS_JSON = (value above)
  4. Add:  GROQ_API_KEY           = your_groq_key
  5. Add:  OPENAI_API_KEY         = your_openai_key
  6. Add:  FLASK_ENV              = production
""")
