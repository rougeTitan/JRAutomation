Yes # Resume Research Resources

Public software engineering resumes collected for ATS/resume improvement research.
Feeds data into the resume optimizer pipeline at `ats_resume_optimizer/`.

## Directory Structure

```
resources/
├── collect_resumes.py      ← download resumes from public GitHub repos
├── analyze_resumes.py      ← extract text, detect level/position/tech
├── metadata.json           ← download tracking (auto-generated)
├── analysis_report.json    ← analysis output (auto-generated)
└── resumes/
    ├── pdf/                ← downloaded PDF resumes
    └── docx/               ← downloaded DOCX resumes
```

---

## Step 1 — Set GitHub Token (highly recommended)

Without a token: ~10 searches/min, 60 API calls/hr  
With a token: 30 searches/min, 5000 API calls/hr

```powershell
# PowerShell
$env:GITHUB_TOKEN = "ghp_your_token_here"
```

```bash
# bash / WSL
export GITHUB_TOKEN="ghp_your_token_here"
```

Get a free token (no special scopes needed) at: https://github.com/settings/tokens

---

## Step 2 — Collect Resumes

```bash
# Run from repo root
python resources/collect_resumes.py

# Options
python resources/collect_resumes.py --max-per-query 200   # more per search query
python resources/collect_resumes.py --max-repos 50        # more repos to crawl
python resources/collect_resumes.py --code-search          # only filename search
python resources/collect_resumes.py --repo-search          # only repo topic crawl
```

**Collection is fully idempotent** — re-running skips already-downloaded files.
Progress is saved to `metadata.json` after each download.

---

## Step 3 — Analyze

```bash
python resources/analyze_resumes.py
```

Outputs `analysis_report.json` with:
- Counts by extension, experience level, position type
- Top 25 technologies detected across the corpus
- Per-resume metadata (level, position, techs, years-of-experience, parseability)

Requires `pdfplumber` + `python-docx` (already in `ats_resume_optimizer/backend/requirements.txt`).

---

## Additional Public Datasets (Manual Download)

Curated datasets to significantly expand the corpus.  
Download and place files into `resources/resumes/pdf/` or `resources/resumes/docx/`.

| Dataset | URL | Format | Count |
|---------|-----|--------|-------|
| Resume Dataset | https://www.kaggle.com/datasets/snehaanbhawal/resume-dataset | CSV + PDFs | 2,400+ |
| Resume Entities for NER | https://www.kaggle.com/datasets/dataturks/resume-entities-for-ner | JSON | 220 |
| Resume Dataset v2 | https://www.kaggle.com/datasets/jithinjagadeesh/resume-dataset | CSV | 960+ |
| Live Career Resume Samples | https://www.livecareer.com/resume-search | HTML/PDF | public |
| GitHub Resume Collections | https://github.com/topics/resume | Various | varies |

---

## Data Sources & Legal Notes

| Source | Status | Reason |
|--------|--------|--------|
| **GitHub public repos** | ✅ Used | People intentionally publish resumes in public repos |
| **Kaggle datasets** | ✅ Manual download | Publicly licensed datasets |
| **LinkedIn** | ❌ Not included | Scraping explicitly violates LinkedIn ToS (Section 8.2) |
| **Indeed** | ❌ Not included | Scraping violates Indeed ToS and robots.txt |

---

## Output: analysis_report.json Schema

```json
{
  "summary": {
    "total_resumes": 500,
    "parseable": 480,
    "by_extension": { ".pdf": 400, ".docx": 100 },
    "by_level": { "senior": 120, "junior": 80, "mid": 60, ... },
    "by_position": { "software_engineer": 200, ... },
    "top_technologies": { "python": 180, "react": 150, ... }
  },
  "resumes": [
    {
      "file": "user__repo__resume.pdf",
      "path": "resumes/pdf/user__repo__resume.pdf",
      "ext": ".pdf",
      "level": "senior",
      "position": "software_engineer",
      "technologies": ["python", "aws", "docker"],
      "yoe": 7,
      "text_chars": 4200,
      "parseable": true
    }
  ]
}
```
