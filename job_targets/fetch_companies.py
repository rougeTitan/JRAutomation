"""
fetch_companies.py  –  Build a curated list of US companies that hire SWEs.

Sources:
  1. S&P 500 from Wikipedia (auto-scraped)
  2. Curated non-S&P tech companies with strong East Coast presence

Outputs:
  job_targets/companies.json
  job_targets/companies.csv

Run:
  python job_targets/fetch_companies.py
"""

import io
import json
import re
import sys
from pathlib import Path

import pandas as pd
import requests

OUT_DIR = Path(__file__).parent
JSON_OUT = OUT_DIR / "companies.json"
CSV_OUT  = OUT_DIR / "companies.csv"

# ── East Coast states ─────────────────────────────────────────────────────────
EAST_COAST_STATES = {
    "ME", "NH", "VT", "MA", "RI", "CT",
    "NY", "NJ", "PA", "DE", "MD", "DC",
    "VA", "WV", "NC", "SC", "GA", "FL",
}

# ── Software-hiring relevance by GICS sector ─────────────────────────────────
SECTOR_SCORE = {
    "Information Technology":    10,
    "Communication Services":     9,
    "Financials":                 7,   # Wall St. / fintech = massive SWE demand
    "Health Care":                6,
    "Consumer Discretionary":     6,
    "Industrials":                4,
    "Consumer Staples":           3,
    "Energy":                     3,
    "Utilities":                  3,
    "Real Estate":                2,
    "Materials":                  2,
}

# Known hyper-hirers regardless of sector
BOOSTED = {
    "Amazon.com Inc",
    "Alphabet Inc (Class A)", "Alphabet Inc (Class C)",
    "Meta Platforms Inc",
    "Microsoft Corp",
    "Apple Inc",
    "Netflix Inc",
    "Salesforce Inc",
    "Oracle Corp",
    "Accenture PLC",
    "International Business Machines Corp",
    "Cognizant Technology Solutions Corp",
    "Fidelity National Information Services Inc",
    "Fiserv Inc",
    "Global Payments Inc",
    "Automatic Data Processing Inc",
    "PayPal Holdings Inc",
    "Block Inc",
    "Twilio Inc",
    "Workday Inc",
    "ServiceNow Inc",
    "Snowflake Inc",
    "Datadog Inc",
    "MongoDB Inc",
    "Palo Alto Networks Inc",
    "CrowdStrike Holdings Inc",
    "Fortinet Inc",
    "Broadcom Inc",
    "QUALCOMM Inc",
    "Texas Instruments Inc",
    "Micron Technology Inc",
    "Western Digital Corp",
    "Lam Research Corp",
    "Applied Materials Inc",
}

# ── Curated non-S&P companies with strong East Coast + SW hiring ──────────────
EXTRA_COMPANIES = [
    # NYC / NJ / CT fintech & tech
    {"name": "Bloomberg L.P.",         "sector": "Financials / Technology", "hq_city": "New York", "hq_state": "NY", "east_coast": True,  "sw_score": 9,  "sp500": False, "notes": "Major SWE employer; builds financial data platform"},
    {"name": "Two Sigma",              "sector": "Financials / Technology", "hq_city": "New York", "hq_state": "NY", "east_coast": True,  "sw_score": 10, "sp500": False, "notes": "Quant hedge fund; heavy ML/SWE hiring"},
    {"name": "Jane Street",            "sector": "Financials / Technology", "hq_city": "New York", "hq_state": "NY", "east_coast": True,  "sw_score": 10, "sp500": False, "notes": "Quant trading; hires SWE & quant devs"},
    {"name": "DE Shaw Group",          "sector": "Financials / Technology", "hq_city": "New York", "hq_state": "NY", "east_coast": True,  "sw_score": 10, "sp500": False, "notes": "Quant fund; strong SWE culture"},
    {"name": "Citadel",                "sector": "Financials / Technology", "hq_city": "New York", "hq_state": "NY", "east_coast": True,  "sw_score": 10, "sp500": False, "notes": "Quant fund; tech-first"},
    {"name": "BetterCloud",            "sector": "Information Technology",  "hq_city": "New York", "hq_state": "NY", "east_coast": True,  "sw_score": 8,  "sp500": False, "notes": "SaaS platform"},
    {"name": "MongoDB Inc",            "sector": "Information Technology",  "hq_city": "New York", "hq_state": "NY", "east_coast": True,  "sw_score": 9,  "sp500": False, "notes": "Database company; HQ NYC"},
    {"name": "Etsy Inc",               "sector": "Consumer Discretionary",  "hq_city": "New York", "hq_state": "NY", "east_coast": True,  "sw_score": 8,  "sp500": False, "notes": "E-commerce; engineering-heavy"},
    {"name": "AppNexus (Xandr)",       "sector": "Communication Services",  "hq_city": "New York", "hq_state": "NY", "east_coast": True,  "sw_score": 8,  "sp500": False, "notes": "AdTech; part of Microsoft"},
    {"name": "Datadog Inc",            "sector": "Information Technology",  "hq_city": "New York", "hq_state": "NY", "east_coast": True,  "sw_score": 9,  "sp500": False, "notes": "Cloud monitoring; HQ NYC"},
    {"name": "Squarespace Inc",        "sector": "Information Technology",  "hq_city": "New York", "hq_state": "NY", "east_coast": True,  "sw_score": 8,  "sp500": False, "notes": "Web platform"},
    {"name": "Compass Inc",            "sector": "Real Estate / Technology","hq_city": "New York", "hq_state": "NY", "east_coast": True,  "sw_score": 7,  "sp500": False, "notes": "PropTech; big engineering team"},
    {"name": "Peloton Interactive",    "sector": "Consumer Discretionary",  "hq_city": "New York", "hq_state": "NY", "east_coast": True,  "sw_score": 7,  "sp500": False, "notes": "Hardware+software platform"},
    # Boston / MA
    {"name": "HubSpot Inc",            "sector": "Information Technology",  "hq_city": "Cambridge",  "hq_state": "MA", "east_coast": True, "sw_score": 9, "sp500": False, "notes": "CRM/marketing SaaS"},
    {"name": "Wayfair Inc",            "sector": "Consumer Discretionary",  "hq_city": "Boston",     "hq_state": "MA", "east_coast": True, "sw_score": 8, "sp500": False, "notes": "E-commerce; large eng org"},
    {"name": "Klaviyo Inc",            "sector": "Information Technology",  "hq_city": "Boston",     "hq_state": "MA", "east_coast": True, "sw_score": 9, "sp500": False, "notes": "Marketing automation SaaS"},
    {"name": "Toast Inc",              "sector": "Information Technology",  "hq_city": "Boston",     "hq_state": "MA", "east_coast": True, "sw_score": 8, "sp500": False, "notes": "Restaurant tech platform"},
    {"name": "Rapid7 Inc",             "sector": "Information Technology",  "hq_city": "Boston",     "hq_state": "MA", "east_coast": True, "sw_score": 8, "sp500": False, "notes": "Cybersecurity"},
    {"name": "Carbon Black (VMware)",  "sector": "Information Technology",  "hq_city": "Waltham",    "hq_state": "MA", "east_coast": True, "sw_score": 8, "sp500": False, "notes": "Cybersecurity"},
    {"name": "Athenahealth",           "sector": "Health Care Technology",  "hq_city": "Watertown",  "hq_state": "MA", "east_coast": True, "sw_score": 7, "sp500": False, "notes": "Healthcare IT"},
    {"name": "Chewy Inc",              "sector": "Consumer Discretionary",  "hq_city": "Dania Beach","hq_state": "FL", "east_coast": True, "sw_score": 7, "sp500": False, "notes": "E-commerce; large tech team"},
    # DC / VA / MD (DMV tech corridor)
    {"name": "Booz Allen Hamilton",    "sector": "Industrials / Technology","hq_city": "McLean",     "hq_state": "VA", "east_coast": True, "sw_score": 8, "sp500": True,  "notes": "Gov't tech consulting; huge SWE demand"},
    {"name": "SAIC",                   "sector": "Industrials / Technology","hq_city": "Reston",     "hq_state": "VA", "east_coast": True, "sw_score": 7, "sp500": False, "notes": "Gov't IT/defense tech"},
    {"name": "Leidos Holdings",        "sector": "Industrials",             "hq_city": "Reston",     "hq_state": "VA", "east_coast": True, "sw_score": 7, "sp500": True,  "notes": "Defense & tech services"},
    {"name": "Capital One Financial",  "sector": "Financials",              "hq_city": "McLean",     "hq_state": "VA", "east_coast": True, "sw_score": 9, "sp500": True,  "notes": "Tech-first bank; top SWE employer"},
    {"name": "Neustar Inc",            "sector": "Information Technology",  "hq_city": "Sterling",   "hq_state": "VA", "east_coast": True, "sw_score": 7, "sp500": False, "notes": "Data analytics"},
    {"name": "Appian Corp",            "sector": "Information Technology",  "hq_city": "McLean",     "hq_state": "VA", "east_coast": True, "sw_score": 8, "sp500": False, "notes": "Low-code platform"},
    {"name": "Peraton",                "sector": "Industrials / Technology","hq_city": "Reston",     "hq_state": "VA", "east_coast": True, "sw_score": 7, "sp500": False, "notes": "Gov't tech"},
    # NC / GA / FL
    {"name": "Red Hat (IBM)",          "sector": "Information Technology",  "hq_city": "Raleigh",    "hq_state": "NC", "east_coast": True, "sw_score": 9, "sp500": False, "notes": "Open-source software; part of IBM"},
    {"name": "Lenovo (US HQ)",         "sector": "Information Technology",  "hq_city": "Morrisville","hq_state": "NC", "east_coast": True, "sw_score": 7, "sp500": False, "notes": "Hardware+software"},
    {"name": "SAS Institute",          "sector": "Information Technology",  "hq_city": "Cary",       "hq_state": "NC", "east_coast": True, "sw_score": 8, "sp500": False, "notes": "Analytics software"},
    {"name": "NCR Corp",               "sector": "Information Technology",  "hq_city": "Atlanta",    "hq_state": "GA", "east_coast": True, "sw_score": 8, "sp500": False, "notes": "Fintech / POS software"},
    {"name": "Global Payments Inc",    "sector": "Information Technology",  "hq_city": "Atlanta",    "hq_state": "GA", "east_coast": True, "sw_score": 8, "sp500": True,  "notes": "Payments technology"},
    {"name": "Damballa (Forcepoint)",  "sector": "Information Technology",  "hq_city": "Atlanta",    "hq_state": "GA", "east_coast": True, "sw_score": 7, "sp500": False, "notes": "Cybersecurity"},
    {"name": "Magic Leap",             "sector": "Information Technology",  "hq_city": "Plantation", "hq_state": "FL", "east_coast": True, "sw_score": 8, "sp500": False, "notes": "AR/VR hardware+software"},
    {"name": "Ultimate Kronos Group (UKG)", "sector": "Information Technology", "hq_city": "Weston", "hq_state": "FL", "east_coast": True, "sw_score": 8, "sp500": False, "notes": "HR/workforce SaaS"},
    # PA / NJ
    {"name": "Comcast / NBCUniversal", "sector": "Communication Services",  "hq_city": "Philadelphia","hq_state": "PA", "east_coast": True, "sw_score": 8, "sp500": True,  "notes": "Media+tech; large SWE org"},
    {"name": "SAP (US East HQ)",       "sector": "Information Technology",  "hq_city": "Newtown Square","hq_state": "PA", "east_coast": True, "sw_score": 8, "sp500": False, "notes": "ERP software"},
    {"name": "Conduent Inc",           "sector": "Information Technology",  "hq_city": "Florham Park","hq_state": "NJ", "east_coast": True, "sw_score": 7, "sp500": False, "notes": "Business process tech"},
    # Remote-first but strong East Coast presence
    {"name": "GitLab Inc",             "sector": "Information Technology",  "hq_city": "Remote",     "hq_state": "N/A","east_coast": False, "sw_score": 9, "sp500": False, "notes": "DevOps platform; remote-first, hires EC"},
    {"name": "HashiCorp Inc",          "sector": "Information Technology",  "hq_city": "Remote",     "hq_state": "N/A","east_coast": False, "sw_score": 9, "sp500": False, "notes": "DevOps tools (Terraform/Vault)"},
    {"name": "Stripe Inc",             "sector": "Financials / Technology", "hq_city": "Remote",     "hq_state": "N/A","east_coast": False, "sw_score": 10,"sp500": False, "notes": "Payments infra; hires globally/EC"},
]


def fetch_sp500() -> pd.DataFrame:
    print("Fetching S&P 500 from Wikipedia ...")
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    try:
        tables = pd.read_html(url, attrs={"id": "constituents"})
        df = tables[0]
    except Exception as e:
        print(f"  Failed: {e}. Trying fallback ...")
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers, timeout=20)
        tables = pd.read_html(io.StringIO(r.text))
        df = tables[0]

    df.columns = [c.strip() for c in df.columns]
    return df


def parse_state(hq_str: str) -> str:
    if not isinstance(hq_str, str):
        return ""
    # Expect "City, State" or "City, State, Country"
    parts = [p.strip() for p in hq_str.split(",")]
    state = parts[1] if len(parts) >= 2 else ""
    # Normalize: some entries say full name e.g. "New York"
    STATE_MAP = {
        "New York": "NY", "California": "CA", "Texas": "TX",
        "Massachusetts": "MA", "Virginia": "VA", "Georgia": "GA",
        "Florida": "FL", "Illinois": "IL", "Pennsylvania": "PA",
        "North Carolina": "NC", "Ohio": "OH", "Washington": "WA",
        "New Jersey": "NJ", "Minnesota": "MN", "Connecticut": "CT",
        "Maryland": "MD", "Colorado": "CO", "Missouri": "MO",
        "Michigan": "MI", "Tennessee": "TN", "Indiana": "IN",
    }
    return STATE_MAP.get(state.strip(), state.strip().upper()[:2])


def build_sp500_records(df: pd.DataFrame) -> list[dict]:
    records = []
    hq_col   = next((c for c in df.columns if "headquarter" in c.lower() or "location" in c.lower()), None)
    sec_col  = next((c for c in df.columns if "sector" in c.lower()), "GICS Sector")
    name_col = next((c for c in df.columns if "security" in c.lower() or "name" in c.lower()), "Security")

    for _, row in df.iterrows():
        name     = str(row.get(name_col, "")).strip()
        sector   = str(row.get(sec_col, "")).strip()
        hq_raw   = str(row.get(hq_col, "")) if hq_col else ""
        state    = parse_state(hq_raw)
        city     = hq_raw.split(",")[0].strip() if "," in hq_raw else hq_raw
        ec       = state in EAST_COAST_STATES
        score    = SECTOR_SCORE.get(sector, 3)
        if name in BOOSTED:
            score = min(score + 2, 10)

        records.append({
            "name":       name,
            "ticker":     str(row.get("Symbol", "")).strip(),
            "sector":     sector,
            "hq_city":    city,
            "hq_state":   state,
            "east_coast": ec,
            "sw_score":   score,
            "sp500":      True,
            "notes":      "",
        })
    return records


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # S&P 500
    df = fetch_sp500()
    sp500_records = build_sp500_records(df)
    print(f"  {len(sp500_records)} S&P 500 companies parsed")

    # Merge with extra curated list (deduplicate by name)
    existing_names = {r["name"].lower() for r in sp500_records}
    added = 0
    for extra in EXTRA_COMPANIES:
        if extra["name"].lower() not in existing_names:
            if "ticker" not in extra:
                extra["ticker"] = ""
            sp500_records.append(extra)
            existing_names.add(extra["name"].lower())
            added += 1
    print(f"  {added} curated non-S&P companies added")

    all_companies = sp500_records

    # Stats
    ec_sw = [c for c in all_companies if c["east_coast"] and c["sw_score"] >= 7]
    all_sw = [c for c in all_companies if c["sw_score"] >= 6]
    print(f"\n  Total companies     : {len(all_companies)}")
    print(f"  SW-relevant (≥6)    : {len(all_sw)}")
    print(f"  East Coast SW (≥7)  : {len(ec_sw)}")

    # Sort: East Coast first, then by sw_score desc
    all_companies.sort(key=lambda c: (not c["east_coast"], -c["sw_score"], c["name"]))

    # Save JSON
    out = {
        "meta": {
            "total":              len(all_companies),
            "east_coast_sw_7plus": len(ec_sw),
            "sw_relevant_6plus":  len(all_sw),
        },
        "companies": all_companies,
    }
    JSON_OUT.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\n  Saved → {JSON_OUT}")

    # Save CSV
    pd.DataFrame(all_companies).to_csv(CSV_OUT, index=False)
    print(f"  Saved → {CSV_OUT}")

    # Print East Coast top targets
    print("\n── Top East Coast SW targets (score ≥ 8) ──────────────────────")
    top = sorted(ec_sw, key=lambda c: -c["sw_score"])
    top8 = [c for c in top if c["sw_score"] >= 8]
    for c in top8[:30]:
        print(f"  [{c['hq_state']:2}] {c['name']:<40} score={c['sw_score']}  {c['sector']}")


if __name__ == "__main__":
    main()
