"""
scrape_jobs.py  –  Fetch SW job listings. NO API KEY required.

Sources (in order):
  1. Greenhouse ATS public API  – JSON, no auth, many mid/large tech cos
  2. Lever ATS public API       – JSON, no auth
  3. LinkedIn guest search      – HTML scrape, no login

Run:
  python job_targets/scrape_jobs.py
  python job_targets/scrape_jobs.py --source greenhouse
  python job_targets/scrape_jobs.py --source linkedin --roles "software engineer"
  python job_targets/scrape_jobs.py --states NY MA VA --min-score 8
"""

import json
import time
import hashlib
import logging
import argparse
import re
from pathlib import Path
from datetime import datetime, timezone
from difflib import SequenceMatcher

import requests
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

OUT_DIR        = Path(__file__).parent
JOBS_FILE      = OUT_DIR / "jobs.json"
COMPANIES_FILE = OUT_DIR / "companies.json"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}

DEFAULT_ROLES = [
    "software engineer",
    "backend engineer",
    "frontend engineer",
    "full stack engineer",
    "software developer",
    "staff engineer",
    "platform engineer",
    "devops engineer",
    "data engineer",
    "machine learning engineer",
]

EC_METROS = {
    "NY": "New York, NY",
    "MA": "Boston, MA",
    "VA": "Arlington, VA",
    "MD": "Bethesda, MD",
    "PA": "Philadelphia, PA",
    "NC": "Raleigh, NC",
    "GA": "Atlanta, GA",
    "FL": "Miami, FL",
    "NJ": "Newark, NJ",
    "CT": "Hartford, CT",
    "DC": "Washington, DC",
}

# ── Greenhouse ATS company slugs (public API, no auth) ────────────────────────
# Format: company display name → greenhouse board token
GREENHOUSE_SLUGS: dict[str, str] = {
    # ── Verified working slugs ─────────────────────────────────────────────
    "HubSpot Inc":             "hubspot",
    "Klaviyo Inc":             "klaviyo",
    "Appian Corp":             "appian",
    "MongoDB Inc":             "mongodb",
    "Datadog Inc":             "datadog",       # fixed: was datadoghq
    "Squarespace Inc":         "squarespace",
    "Coinbase":                "coinbase",
    "GitLab Inc":              "gitlab",
    "Peloton Interactive":     "peloton",
    "Discord":                 "discord",
    "Robinhood":               "robinhood",
    "Checkr":                  "checkr",
    "Brex":                    "brex",
    "Twilio Inc":              "twilio",
    "SeatGeek":                "seatgeek",
    "Betterment":              "betterment",
    "Recorded Future":         "recordedfuture",
    "Formlabs":                "formlabs",
    "SimpliSafe":              "simplisafe",
    "Brightcove":              "brightcove",
    "Toast Inc":               "toast",
    "Rapid7 Inc":              "rapid7inc",
    "Etsy Inc":                "etsyinc",
    "Wayfair Inc":             "wayfairtech",
    "Ultimate Kronos Group (UKG)": "ultimatesoftware",
    "Global Payments Inc":     "globalpaymentsinc",
    # ── More East Coast tech companies on Greenhouse ───────────────────────
    "BambooHR":                "bamboohr",
    "Duo Security":            "duo",
    "Elastic":                 "elastic",
    "Figma":                   "figma",
    "Benchling":               "benchling",
    "Spring Health":           "springhealth",
    "Navan":                   "tripactions",
    "Rippling":                "rippling",
    "Coalition Inc":           "coalitioninc",
    "Octane":                  "octane",
    "Oscar Health":            "oscar",
    "Ro Health":               "ro",
    "Gemini Trust":            "gemini",
    "Wealthfront":             "wealthfront",
    "Pendo":                   "pendo",
    "Namely":                  "namely",
    "Justworks":               "justworks",
    "Cityblock Health":        "cityblock",
    "Viz.ai":                  "vizai",
    "Noom":                    "noom",
}

# Lever ATS slugs (public API, no auth)
LEVER_SLUGS: dict[str, str] = {
    "HashiCorp Inc":           "hashicorp",
    "Affirm":                  "affirm",
    "Plaid":                   "plaid",
    "Airtable":                "airtable",
    "Gusto":                   "gusto",
    "Benchling":               "benchling",
    "Carta":                   "carta",
    "Navan":                   "navan",
    "Figma":                   "figma",
    "Lob":                     "lob",
    "Verkada":                 "verkada",
    "OpenAI":                  "openai",
    "Scale AI":                "scaleai",
    "Weights & Biases":        "wandb",
    "Palantir Technologies":   "palantir",
    "Cloudflare Inc":          "cloudflare",
    "Samsara":                 "samsara",
}


# ── Helpers ───────────────────────────────────────────────────────────────────
def make_id(title: str, company: str, url: str) -> str:
    return hashlib.md5(f"{title}{company}{url}".encode()).hexdigest()[:12]


def fuzzy_match(a: str, b: str) -> float:
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def match_company(job_co: str, target_names: list[str], threshold: float = 0.70) -> str | None:
    best, best_name = 0.0, None
    for name in target_names:
        s = fuzzy_match(job_co, name)
        if s > best:
            best, best_name = s, name
    return best_name if best >= threshold else None


def clean_html(html_str: str) -> str:
    return re.sub(r"<[^>]+>", " ", html_str or "").strip()


# ── Greenhouse API (public, no auth) ─────────────────────────────────────────
def fetch_greenhouse(slug: str, company_name: str) -> list[dict]:
    url = f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true"
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        r.raise_for_status()
        jobs_raw = r.json().get("jobs", [])
    except Exception as e:
        log.warning(f"  Greenhouse [{slug}] failed: {e}")
        return []

    jobs = []
    for raw in jobs_raw:
        title = raw.get("title", "")
        loc   = (raw.get("location") or {}).get("name", "")
        desc  = clean_html(raw.get("content", ""))
        jurl  = raw.get("absolute_url", "")
        jobs.append({
            "id":          make_id(title, company_name, jurl),
            "title":       title,
            "company":     company_name,
            "location":    loc,
            "description": desc,
            "url":         jurl,
            "posted":      raw.get("updated_at", ""),
            "source":      "greenhouse",
            "fetched_at":  datetime.now(timezone.utc).isoformat(),
        })
    return jobs


# ── Lever API (public, no auth) ───────────────────────────────────────────────
def fetch_lever(slug: str, company_name: str) -> list[dict]:
    url = f"https://api.lever.co/v0/postings/{slug}?mode=json&limit=100"
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        r.raise_for_status()
        postings = r.json()
    except Exception as e:
        log.warning(f"  Lever [{slug}] failed: {e}")
        return []

    jobs = []
    for raw in postings:
        title = raw.get("text", "")
        loc   = (raw.get("categories") or {}).get("location", "")
        lists = raw.get("lists", [])
        desc  = " ".join(
            clean_html(item.get("content", ""))
            for item in lists
        )
        desc += " " + clean_html(raw.get("descriptionPlain", ""))
        jurl  = raw.get("hostedUrl", "")
        jobs.append({
            "id":          make_id(title, company_name, jurl),
            "title":       title,
            "company":     company_name,
            "location":    loc,
            "description": desc.strip(),
            "url":         jurl,
            "posted":      "",
            "source":      "lever",
            "fetched_at":  datetime.now(timezone.utc).isoformat(),
        })
    return jobs


# ── LinkedIn guest search (no login) ─────────────────────────────────────────
LI_SEARCH = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"

def fetch_linkedin(role: str, location: str, start: int = 0) -> list[dict]:
    params = {
        "keywords": role,
        "location": location,
        "start":    start,
        "f_TPR":    "r2592000",  # last 30 days
    }
    try:
        r = requests.get(LI_SEARCH, params=params, headers=HEADERS, timeout=15)
        if r.status_code == 429:
            log.warning("  LinkedIn rate-limited. Sleeping 30s ...")
            time.sleep(30)
            return []
        r.raise_for_status()
    except Exception as e:
        log.warning(f"  LinkedIn [{role}/{location}] failed: {e}")
        return []

    soup  = BeautifulSoup(r.text, "html.parser")
    cards = soup.find_all("li")
    jobs  = []

    for card in cards:
        title_el = card.find("h3", {"class": re.compile("title", re.I)}) \
                   or card.find("span", {"class": re.compile("title", re.I)})
        co_el    = card.find("h4") or card.find("a", {"class": re.compile("company", re.I)})
        loc_el   = card.find("span", {"class": re.compile("location|subtitle", re.I)})
        link_el  = card.find("a", href=True)

        title   = title_el.get_text(strip=True) if title_el else ""
        company = co_el.get_text(strip=True)    if co_el    else ""
        loc     = loc_el.get_text(strip=True)   if loc_el   else location
        url     = link_el["href"].split("?")[0]  if link_el  else ""

        if not title:
            continue

        jobs.append({
            "id":          make_id(title, company, url),
            "title":       title,
            "company":     company,
            "location":    loc,
            "description": "",  # LinkedIn requires follow-up request for full JD
            "url":         url,
            "posted":      "",
            "source":      "linkedin",
            "fetched_at":  datetime.now(timezone.utc).isoformat(),
        })

    return jobs


# ── Metadata ──────────────────────────────────────────────────────────────────
def load_jobs() -> dict:
    if JOBS_FILE.exists():
        return json.loads(JOBS_FILE.read_text(encoding="utf-8"))
    return {"jobs": {}, "stats": {"total": 0, "by_source": {}}}


def save_jobs(data: dict):
    JOBS_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def ingest(jobs: list[dict], data: dict, seen: set,
           target_cos: dict, target_names: list) -> int:
    added = 0
    for j in jobs:
        if j["id"] in seen:
            continue
        matched = match_company(j["company"], target_names)
        j["matched_company"] = matched
        j["sw_score"] = target_cos[matched]["sw_score"] if matched else 5
        j["company_sector"] = target_cos[matched].get("sector", "") if matched else ""

        data["jobs"][j["id"]] = j
        seen.add(j["id"])
        src = j.get("source", "unknown")
        data["stats"]["by_source"][src] = data["stats"]["by_source"].get(src, 0) + 1
        data["stats"]["total"] = len(data["jobs"])
        added += 1
    return added


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source",    choices=["all", "greenhouse", "lever", "linkedin"],
                    default="all")
    ap.add_argument("--roles",     nargs="+", default=DEFAULT_ROLES[:5])
    ap.add_argument("--states",    nargs="+", default=["NY", "MA", "VA", "NC", "GA"])
    ap.add_argument("--min-score", type=int,  default=7)
    ap.add_argument("--li-pages",  type=int,  default=3,
                    help="LinkedIn result pages (25 results each)")
    args = ap.parse_args()

    if not COMPANIES_FILE.exists():
        log.error("companies.json not found. Run fetch_companies.py first.")
        return

    co_data     = json.loads(COMPANIES_FILE.read_text(encoding="utf-8"))
    target_cos  = {c["name"]: c for c in co_data["companies"]
                   if c.get("sw_score", 0) >= args.min_score}
    target_names = list(target_cos.keys())
    log.info(f"Targeting {len(target_names)} companies (sw_score ≥ {args.min_score})")

    data  = load_jobs()
    seen  = set(data["jobs"].keys())
    total_added = 0

    # ── Greenhouse ────────────────────────────────────────────────────────────
    if args.source in ("all", "greenhouse"):
        log.info("\n[Greenhouse] Fetching from known company boards ...")
        for co_name, slug in GREENHOUSE_SLUGS.items():
            if co_name not in target_cos and args.min_score > 0:
                continue
            log.info(f"  {co_name} ...")
            jobs = fetch_greenhouse(slug, co_name)
            sw_jobs = [j for j in jobs
                       if any(kw in j["title"].lower()
                              for kw in ["software", "engineer", "developer",
                                         "backend", "frontend", "platform",
                                         "devops", "data", "machine learning",
                                         "architect", "sre", "infrastructure"])]
            n = ingest(sw_jobs, data, seen, target_cos, target_names)
            if n:
                log.info(f"    +{n} SW jobs")
            time.sleep(0.8)

    # ── Lever ─────────────────────────────────────────────────────────────────
    if args.source in ("all", "lever"):
        log.info("\n[Lever] Fetching from known company boards ...")
        for co_name, slug in LEVER_SLUGS.items():
            log.info(f"  {co_name} ...")
            jobs = fetch_lever(slug, co_name)
            sw_jobs = [j for j in jobs
                       if any(kw in j["title"].lower()
                              for kw in ["software", "engineer", "developer",
                                         "backend", "frontend", "platform",
                                         "devops", "data", "machine learning",
                                         "architect", "sre", "infrastructure"])]
            n = ingest(sw_jobs, data, seen, target_cos, target_names)
            if n:
                log.info(f"    +{n} SW jobs")
            time.sleep(0.8)

    # ── LinkedIn ──────────────────────────────────────────────────────────────
    if args.source in ("all", "linkedin"):
        log.info("\n[LinkedIn] Searching by role + location ...")
        metros = {s: EC_METROS[s] for s in args.states if s in EC_METROS}
        for role in args.roles:
            for state, metro in metros.items():
                log.info(f"  [{state}] {role} ...")
                for page in range(args.li_pages):
                    jobs = fetch_linkedin(role, metro, start=page * 25)
                    n = ingest(jobs, data, seen, target_cos, target_names)
                    total_added += n
                    if not jobs:
                        break
                    time.sleep(2.5)
                time.sleep(1.0)

    save_jobs(data)

    total     = len(data["jobs"])
    matched   = sum(1 for j in data["jobs"].values() if j.get("matched_company"))
    by_source = data["stats"].get("by_source", {})
    log.info(f"\nTotal jobs stored : {total}")
    log.info(f"Matched to targets: {matched}")
    log.info(f"By source         : {by_source}")
    log.info(f"Saved → {JOBS_FILE}")


if __name__ == "__main__":
    main()
