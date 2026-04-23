"""
match_jobs.py  –  Score & rank scraped JDs against your resume.

Run:
  python job_targets/match_jobs.py --resume path/to/resume.pdf
  python job_targets/match_jobs.py --resume path/to/resume.pdf --top 20 --min-score 7
  python job_targets/match_jobs.py --resume path/to/resume.pdf --state NY --role "software engineer"
"""

import re
import json
import argparse
from pathlib import Path
from collections import Counter

OUT_DIR   = Path(__file__).parent
JOBS_FILE = OUT_DIR / "jobs.json"
RANKED_FILE = OUT_DIR / "ranked_jobs.json"

# ── Stopwords ─────────────────────────────────────────────────────────────────
STOPWORDS = {
    "a","an","the","and","or","but","in","on","at","to","for","of","with",
    "by","from","is","are","was","were","be","been","being","have","has",
    "had","do","does","did","will","would","could","should","may","might",
    "must","shall","can","not","no","nor","so","yet","both","either",
    "each","few","more","most","other","some","such","than","then","when",
    "where","while","who","which","what","this","that","these","those",
    "we","our","us","you","your","they","their","them","he","she","it",
    "his","her","its","i","my","me","myself","yourself","themselves",
    "also","just","only","very","well","as","if","about","up","out",
    "any","all","both","through","during","before","after","above","below",
    "between","into","through","during","including","without","within",
    "following","across","behind","beyond","plus","except","but","how",
    "however","therefore","thus","hence","otherwise","accordingly",
    "work","working","job","role","position","team","company","experience",
    "year","years","ability","strong","excellent","good","required",
    "responsibilities","requirements","qualifications","preferred",
    "please","apply","opportunity","looking","seeking","join","help",
    "new","use","using","used","build","building","built","make","making",
}

# Tech terms that should count extra (weight boost)
TECH_BOOST_TERMS = {
    "python","javascript","typescript","java","golang","rust","scala","kotlin",
    "react","angular","vue","nextjs","nodejs","django","flask","fastapi","spring",
    "aws","gcp","azure","kubernetes","docker","terraform","ci/cd","linux",
    "postgresql","mysql","mongodb","redis","elasticsearch","sql","dynamodb",
    "machine learning","deep learning","pytorch","tensorflow","llm","nlp","mlops",
    "microservices","graphql","grpc","kafka","spark","airflow","databricks",
    "git","agile","scrum","system design","distributed systems","api",
    "backend","frontend","fullstack","devops","sre","cloud","data engineering",
    "software engineer","senior","staff","principal","architect","lead",
}


# ── Resume text extraction ────────────────────────────────────────────────────
def extract_resume(path: Path) -> str:
    ext = path.suffix.lower()
    if ext == ".pdf":
        try:
            import pdfplumber
            with pdfplumber.open(path) as pdf:
                return "\n".join(p.extract_text() or "" for p in pdf.pages)
        except Exception:
            pass
        try:
            from pypdf import PdfReader
            return "\n".join(pg.extract_text() or "" for pg in PdfReader(str(path)).pages)
        except Exception:
            return ""
    if ext in {".docx", ".doc"}:
        try:
            from docx import Document
            return "\n".join(p.text for p in Document(str(path)).paragraphs)
        except Exception:
            try:
                import docx2txt
                return docx2txt.process(str(path)) or ""
            except Exception:
                return ""
    if ext == ".txt":
        return path.read_text(encoding="utf-8", errors="ignore")
    return ""


# ── Keyword extraction ────────────────────────────────────────────────────────
def tokenize(text: str) -> list[str]:
    text = text.lower()
    # Keep multi-word tech phrases intact
    multi = [
        "machine learning", "deep learning", "natural language processing",
        "computer vision", "system design", "distributed systems",
        "software engineer", "data engineering", "site reliability",
        "full stack", "full-stack", "ci/cd", "rest api", "restful api",
        "object oriented", "object-oriented", "test driven",
    ]
    tokens = []
    consumed = set()
    for phrase in multi:
        if phrase in text:
            tokens.append(phrase.replace(" ", "_").replace("-", "_"))
            text = text.replace(phrase, " ")

    words = re.findall(r"[a-z][a-z0-9#+./\-]{1,30}", text)
    tokens += [w for w in words if w not in STOPWORDS and len(w) > 2]
    return tokens


def keyword_counter(text: str) -> Counter:
    return Counter(tokenize(text))


def resume_term_set(resume_text: str) -> set[str]:
    return set(tokenize(resume_text))


# ── Scoring ───────────────────────────────────────────────────────────────────
def score_jd(jd_text: str, resume_terms: set[str]) -> dict:
    jd_counter = keyword_counter(jd_text)
    if not jd_counter:
        return {"match_pct": 0.0, "matched": [], "missing": [], "jd_term_count": 0}

    # Weight: tech terms count 2x
    total_weight  = 0.0
    matched_weight = 0.0
    matched_terms = []
    missing_terms = []

    for term, freq in jd_counter.most_common(80):
        w = 2.0 if any(t in term for t in TECH_BOOST_TERMS) else 1.0
        w *= min(freq, 3)  # cap freq weight at 3
        total_weight += w
        if term in resume_terms:
            matched_weight += w
            matched_terms.append(term)
        else:
            missing_terms.append(term)

    match_pct = round((matched_weight / total_weight) * 100, 1) if total_weight else 0.0

    return {
        "match_pct":      match_pct,
        "matched":        matched_terms[:20],
        "missing_top10":  missing_terms[:10],
        "jd_term_count":  len(jd_counter),
    }


def composite_score(match_pct: float, sw_score: int) -> float:
    return round((match_pct * 0.7) + (sw_score * 3.0), 2)


# ── Output ────────────────────────────────────────────────────────────────────
def print_table(ranked: list[dict], top_n: int = 20):
    print()
    print("=" * 90)
    print(f"  TOP {min(top_n, len(ranked))} JOB MATCHES")
    print("=" * 90)
    print(f"  {'#':<3} {'Match':>5}  {'CS':>5}  {'SW':>3}  {'Company':<30} {'Title':<35} {'Loc'}")
    print("  " + "-" * 87)
    for i, j in enumerate(ranked[:top_n], 1):
        loc = j.get("location", "")[:15]
        co  = (j.get("matched_company") or j.get("company", ""))[:29]
        title = j.get("title", "")[:34]
        print(f"  {i:<3} {j['match_pct']:>4.0f}%  {j['composite']:>5.1f}  {j['sw_score']:>3}  "
              f"{co:<30} {title:<35} {loc}")
    print()

    if ranked:
        top = ranked[0]
        print(f"  Best match: {top.get('matched_company') or top.get('company')} — {top.get('title')}")
        print(f"  Match: {top['match_pct']}%  |  Missing keywords: {', '.join(top.get('missing_top10', [])[:6])}")
        print(f"  URL: {top.get('url','')}")
    print("=" * 90)


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--resume",    required=True, help="Path to your resume (PDF/DOCX/TXT)")
    ap.add_argument("--top",       type=int, default=25, help="Top N to show (default 25)")
    ap.add_argument("--min-match", type=float, default=0.0, help="Min match % filter")
    ap.add_argument("--state",     help="Filter by state code e.g. NY")
    ap.add_argument("--role",      help="Filter title contains substring")
    ap.add_argument("--target-only", action="store_true",
                    help="Only show jobs from matched target companies")
    args = ap.parse_args()

    # Load resume
    resume_path = Path(args.resume)
    if not resume_path.exists():
        print(f"Resume not found: {resume_path}")
        return
    print(f"Loading resume: {resume_path.name} ...")
    resume_text = extract_resume(resume_path)
    if len(resume_text.split()) < 50:
        print("Could not extract resume text. Is it a text-based PDF (not scanned)?")
        return
    resume_terms = resume_term_set(resume_text)
    print(f"  Resume terms extracted: {len(resume_terms)}")

    # Load jobs
    if not JOBS_FILE.exists():
        print("jobs.json not found. Run scrape_jobs.py first.")
        return
    data = json.loads(JOBS_FILE.read_text(encoding="utf-8"))
    jobs = list(data["jobs"].values())
    print(f"Loaded {len(jobs)} jobs from jobs.json")

    # Apply filters
    if args.state:
        jobs = [j for j in jobs if args.state.upper() in j.get("location", "").upper()]
    if args.role:
        jobs = [j for j in jobs if args.role.lower() in j.get("title", "").lower()]
    if args.target_only:
        jobs = [j for j in jobs if j.get("matched_company")]
    print(f"  After filters: {len(jobs)} jobs")

    if not jobs:
        print("No jobs match filters.")
        return

    # Score
    print("Scoring ...")
    ranked = []
    for j in jobs:
        jd_text = f"{j.get('title','')} {j.get('description','')}"
        result  = score_jd(jd_text, resume_terms)
        if result["match_pct"] < args.min_match:
            continue
        ranked.append({
            **j,
            "match_pct":      result["match_pct"],
            "matched_terms":  result["matched"],
            "missing_top10":  result["missing_top10"],
            "composite":      composite_score(result["match_pct"], j.get("sw_score", 5)),
        })

    ranked.sort(key=lambda x: -x["composite"])

    # Save
    RANKED_FILE.write_text(
        json.dumps({"meta": {"total_scored": len(ranked), "resume": str(resume_path)},
                    "jobs": ranked}, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

    print_table(ranked, args.top)
    print(f"  Full ranked list → {RANKED_FILE}")


if __name__ == "__main__":
    main()
