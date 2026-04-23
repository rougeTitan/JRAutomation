# Job Targets

Company list for targeted SW job search, biased toward East Coast USA.

## Files

| File | Description |
|------|-------------|
| `fetch_companies.py` | Scrapes S&P 500 + curated extras → builds master list |
| `companies.json` | Full list (545 companies) with metadata |
| `companies.csv`  | Same data, spreadsheet-friendly |

## Data Schema

```json
{
  "name":       "Capital One Financial",
  "ticker":     "COF",
  "sector":     "Financials",
  "hq_city":    "McLean",
  "hq_state":   "VA",
  "east_coast": true,
  "sw_score":   9,
  "sp500":      true,
  "notes":      "Tech-first bank; top SWE employer"
}
```

### `sw_score` (1–10)
Software hiring relevance. Derived from GICS sector + known-hyper-hirer boost.

| Score | Meaning |
|-------|---------|
| 9–10  | Core tech / fintech / quant — extremely high SWE demand |
| 7–8   | Strong tech function within non-tech company |
| 5–6   | Moderate tech hiring |
| ≤4    | Primarily non-tech, limited SWE roles |

## Quick Filters (Python)

```python
import json
data = json.load(open("job_targets/companies.json", encoding="utf-8"))["companies"]

# East Coast, score ≥ 8
top = [c for c in data if c["east_coast"] and c["sw_score"] >= 8]

# By state
ny = [c for c in data if c["hq_state"] == "NY" and c["sw_score"] >= 7]
```

## Stats (current run)
- **545** total companies
- **320** SW-relevant (score ≥ 6)
- **112** East Coast SW targets (score ≥ 7)

## Automation Pipeline  — No API Key Required

### Step 1 — Scrape jobs (run once, or daily)

**Sources used (zero registration):**
| Source | How | Full JD? | Jobs found |
|--------|-----|----------|------------|
| Greenhouse ATS | Public JSON API | Yes | ~1400 |
| Lever ATS | Public JSON API | Yes | ~100 |
| LinkedIn | Guest HTML search | Title only | varies |

```powershell
# All sources (recommended)
python job_targets/scrape_jobs.py

# Greenhouse only (fastest, best descriptions)
python job_targets/scrape_jobs.py --source greenhouse

# LinkedIn only (broader coverage, title/company only)
python job_targets/scrape_jobs.py --source linkedin --states NY MA VA --roles "software engineer" "backend engineer"

# Target only high-value companies
python job_targets/scrape_jobs.py --min-score 8
```
Saves → `jobs.json`  (idempotent — re-running skips duplicates)

### Step 2 — Match & rank against your resume
```powershell
python job_targets/match_jobs.py --resume path/to/your_resume.pdf

# Filter options
python job_targets/match_jobs.py --resume resume.pdf --top 30 --target-only
python job_targets/match_jobs.py --resume resume.pdf --state NY --min-match 25
```
Prints ranked table. Saves → `ranked_jobs.json`

### Composite Score Formula
`composite = (match_pct × 0.7) + (sw_score × 3.0)`

High match % + high-value company = top priority.

### Adding More Companies
To add a company: find their Greenhouse board slug at  
`https://boards.greenhouse.io/{slug}` or Lever at `https://jobs.lever.co/{slug}`  
then add to `GREENHOUSE_SLUGS` / `LEVER_SLUGS` in `scrape_jobs.py`.
