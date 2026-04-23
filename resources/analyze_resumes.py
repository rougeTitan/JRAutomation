#!/usr/bin/env python3
"""
Analyze collected resumes: extract text, detect experience level, position, and
top technologies. Outputs analysis_report.json + console summary.

Requires (already in ats_resume_optimizer/backend/requirements.txt):
    pdfplumber       — PDF text extraction
    python-docx      — DOCX text extraction

Usage:
    python analyze_resumes.py
    python analyze_resumes.py --resumes-dir resources/resumes
"""

import re
import json
import logging
import argparse
from pathlib import Path
from collections import Counter
from functools import lru_cache

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
log = logging.getLogger(__name__)

RESOURCES_DIR = Path(__file__).parent
RESUMES_DIR   = RESOURCES_DIR / "resumes"
REPORT_FILE   = RESOURCES_DIR / "analysis_report.json"

# ── Experience level keywords (whole-phrase, not substrings) ─────────────────
LEVELS = {
    "intern":    ["intern ", "internship", "co-op", "coop"],
    "junior":    ["junior ", " jr.", "entry level", "entry-level", "new grad",
                   "associate software", "associate engineer"],
    "mid":        ["mid-level", "mid level", "intermediate engineer"],
    "senior":     ["senior software", "senior engineer", "sr. software",
                   "sr. engineer", "senior developer", "senior data"],
    "staff":      ["staff engineer", "staff software", "staff swe"],
    "principal":  ["principal engineer", "principal software", "principal swe"],
    "manager":    ["engineering manager", "software manager", "tech lead",
                   "team lead", "development manager"],
    "director":   ["director of engineering", "vp of engineering",
                   "vp engineering", "head of engineering", " cto "],
}

# ── Position type keywords ────────────────────────────────────────────────────
POSITIONS = {
    "software_engineer":   ["software engineer", "software engineering", "swe"],
    "software_developer":  ["software developer", "software development"],
    "software_architect":  ["software architect", "solutions architect",
                            "technical architect", "enterprise architect"],
    "engineering_manager": ["engineering manager", "software manager",
                            "tech lead", "team lead", "director of eng"],
    "full_stack":          ["full stack", "full-stack"],
    "frontend":            ["front-end", "frontend", "front end"],
    "backend":             ["back-end", "backend", "back end"],
    "devops_sre":          ["devops", "site reliability", "sre", "platform engineer"],
    "data_ml":             ["data engineer", "data scientist", "machine learning engineer",
                            "ml engineer", "ai engineer"],
}

# ── Technology keywords ───────────────────────────────────────────────────────
# Each entry: (display_name, regex_pattern)
# Patterns use \b word boundaries; special chars escaped as needed.
TECHNOLOGIES: list[tuple[str, str]] = [
    # Languages
    ("python",      r"\bpython\b"),
    ("java",        r"\bjava\b(?!script)"),   # not javascript
    ("javascript",  r"\bjavascript\b"),
    ("typescript",  r"\btypescript\b"),
    ("c++",         r"\bc\+\+\b"),
    ("c#",          r"\bc#\b"),
    ("golang",      r"\bgolang\b|\bgo\s+(?:lang|programming|developer|engineer)\b"),
    ("rust",        r"\brust\b"),
    ("scala",       r"\bscala\b"),
    ("kotlin",      r"\bkotlin\b"),
    ("swift",       r"\bswift\b"),
    ("ruby",        r"\bruby\b"),
    ("php",         r"\bphp\b"),
    ("bash",        r"\bbash\b"),
    ("r-lang",      r"\bR\b(?=\s*(?:programming|language|\())"),
    # Frontend
    ("react",       r"\breact\.?js\b|\breact\b"),
    ("angular",     r"\bangular\b"),
    ("vue",         r"\bvue\.?js\b|\bvue\b"),
    ("next.js",     r"\bnext\.js\b"),
    ("svelte",      r"\bsvelte\b"),
    ("html",        r"\bhtml\b"),
    ("css",         r"\bcss\b"),
    ("tailwind",    r"\btailwind\b"),
    ("webpack",     r"\bwebpack\b"),
    # Backend
    ("node.js",     r"\bnode\.js\b|\bnodejs\b"),
    ("django",      r"\bdjango\b"),
    ("flask",       r"\bflask\b"),
    ("fastapi",     r"\bfastapi\b"),
    ("spring",      r"\bspring\s*(?:boot|framework|mvc)?\b"),
    ("rails",       r"\bruby on rails\b|\brails\b"),
    ("graphql",     r"\bgraphql\b"),
    ("grpc",        r"\bgrpc\b"),
    ("rest api",    r"\brest\s*api\b|\brestful\b"),
    ("microservices",r"\bmicroservices?\b"),
    # Cloud & DevOps
    ("aws",         r"\baws\b|\bamazon web services\b"),
    ("gcp",         r"\bgcp\b|\bgoogle cloud\b"),
    ("azure",       r"\bazure\b"),
    ("kubernetes",  r"\bkubernetes\b|\bk8s\b"),
    ("docker",      r"\bdocker\b"),
    ("terraform",   r"\bterraform\b"),
    ("ansible",     r"\bansible\b"),
    ("ci/cd",       r"\bci/cd\b|\bcicd\b"),
    ("jenkins",     r"\bjenkins\b"),
    ("github actions",r"\bgithub actions\b"),
    ("linux",       r"\blinux\b"),
    # Databases
    ("postgresql",  r"\bpostgresql\b|\bpostgres\b"),
    ("mysql",       r"\bmysql\b"),
    ("mongodb",     r"\bmongodb\b|\bmongo\b"),
    ("redis",       r"\bredis\b"),
    ("elasticsearch",r"\belasticsearch\b"),
    ("cassandra",   r"\bcassandra\b"),
    ("dynamodb",    r"\bdynamodb\b"),
    ("sql",         r"\bsql\b"),
    # AI / ML
    ("machine learning",r"\bmachine learning\b"),
    ("deep learning",   r"\bdeep learning\b"),
    ("pytorch",     r"\bpytorch\b"),
    ("tensorflow",  r"\btensorflow\b"),
    ("keras",       r"\bkeras\b"),
    ("llm",         r"\bllm[s]?\b|\blarge language model\b"),
    ("nlp",         r"\bnlp\b|\bnatural language processing\b"),
    ("computer vision",r"\bcomputer vision\b"),
    ("scikit-learn",r"\bscikit-?learn\b"),
    # Data
    ("spark",       r"\bapache spark\b|\bpyspark\b|\bspark\b"),
    ("kafka",       r"\bkafka\b"),
    ("airflow",     r"\bairflow\b"),
    ("databricks",  r"\bdatabricks\b"),
    # Other
    ("git",         r"\bgit\b(?!hub)"),    # not github
    ("agile",       r"\bagile\b"),
    ("scrum",       r"\bscrum\b"),
]

# Pre-compile all patterns once
_TECH_PATTERNS: list[tuple[str, re.Pattern]] = [
    (name, re.compile(pat, re.IGNORECASE)) for name, pat in TECHNOLOGIES
]

# YOE pattern: "8+ years", "5 years of experience", "3 yrs"
YOE_RE = re.compile(
    r"(\d{1,2})\s*\+?\s*(?:years?|yrs?)(?:\s+of)?\s*(?:experience|exp\.?)?",
    re.IGNORECASE,
)


# ── Text extraction ───────────────────────────────────────────────────────────
def extract_pdf(path: Path) -> str:
    try:
        import pdfplumber
        with pdfplumber.open(str(path)) as pdf:
            return " ".join(page.extract_text() or "" for page in pdf.pages)
    except ImportError:
        log.warning("pdfplumber not installed. Install: pip install pdfplumber")
        return ""
    except Exception as e:
        log.debug(f"PDF extract error {path.name}: {e}")
        return ""


def extract_docx(path: Path) -> str:
    try:
        from docx import Document
        return " ".join(p.text for p in Document(str(path)).paragraphs)
    except ImportError:
        log.warning("python-docx not installed. Install: pip install python-docx")
        return ""
    except Exception as e:
        log.debug(f"DOCX extract error {path.name}: {e}")
        return ""


def extract_text(path: Path) -> str:
    ext = path.suffix.lower()
    if ext == ".pdf":
        return extract_pdf(path)
    if ext in {".docx", ".doc"}:
        return extract_docx(path)
    return ""


# ── Detection helpers ─────────────────────────────────────────────────────────
def detect_yoe(text: str) -> int | None:
    """Return max years-of-experience number found in text, or None."""
    matches = YOE_RE.findall(text)
    return max(int(y) for y in matches) if matches else None


def detect_level(text: str) -> str:
    t   = text.lower()
    yoe = detect_yoe(t)
    if yoe is not None:
        if yoe >= 15: return "senior/staff"
        if yoe >= 8:  return "senior"
        if yoe >= 5:  return "mid-senior"
        if yoe >= 3:  return "mid"
        if yoe >= 1:  return "junior"
        return "intern"
    for level, kws in LEVELS.items():
        if any(kw in t for kw in kws):
            return level
    return "unknown"


def detect_position(text: str) -> str:
    t = text.lower()
    for pos, kws in POSITIONS.items():
        if any(kw in t for kw in kws):
            return pos
    return "general_software"


def detect_techs(text: str) -> list[str]:
    return [name for name, pat in _TECH_PATTERNS if pat.search(text)]


# ── Main analysis ─────────────────────────────────────────────────────────────
def analyze(resumes_dir: Path = RESUMES_DIR, report_file: Path = REPORT_FILE) -> dict:
    if not resumes_dir.exists():
        print("No resumes directory found. Run collect_resumes.py first.")
        return {}

    files = sorted(
        list(resumes_dir.rglob("*.pdf"))
        + list(resumes_dir.rglob("*.docx"))
        + list(resumes_dir.rglob("*.doc"))
    )

    if not files:
        print(f"No resume files found in {resumes_dir}")
        return {}

    print(f"Analyzing {len(files)} resumes …")

    results    = []
    ext_counts = Counter()
    lvl_counts = Counter()
    pos_counts = Counter()
    tch_counts = Counter()

    for i, fpath in enumerate(files, 1):
        if i % 25 == 0:
            print(f"  {i}/{len(files)} …")

        ext  = fpath.suffix.lower()
        text = extract_text(fpath)
        lvl  = detect_level(text)   if text else "unknown"
        pos  = detect_position(text) if text else "unknown"
        techs = detect_techs(text)  if text else []
        yoe  = detect_yoe(text.lower()) if text else None

        ext_counts[ext] += 1
        lvl_counts[lvl] += 1
        pos_counts[pos] += 1
        for t in techs:
            tch_counts[t] += 1

        results.append({
            "file":         fpath.name,
            "path":         str(fpath.relative_to(RESOURCES_DIR)),
            "ext":          ext,
            "level":        lvl,
            "position":     pos,
            "technologies": techs,
            "yoe":          yoe,
            "text_chars":   len(text),
            "parseable":    bool(text),
        })

    report = {
        "summary": {
            "total_resumes":    len(files),
            "parseable":        sum(1 for r in results if r["parseable"]),
            "by_extension":     dict(ext_counts.most_common()),
            "by_level":         dict(lvl_counts.most_common()),
            "by_position":      dict(pos_counts.most_common()),
            "top_technologies": dict(tch_counts.most_common(25)),
        },
        "resumes": results,
    }

    report_file.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    s = report["summary"]
    print(f"\n{'='*55}")
    print(f"Total resumes   : {s['total_resumes']}")
    print(f"Parseable       : {s['parseable']}")
    print(f"By extension    : {s['by_extension']}")
    print(f"By level        : {s['by_level']}")
    print(f"By position     : {s['by_position']}")
    print(f"Top 10 techs    : {dict(tch_counts.most_common(10))}")
    print(f"\nFull report  →  {report_file}")
    return report


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Analyze collected resumes")
    p.add_argument("--resumes-dir", type=Path, default=RESUMES_DIR,
                   help="Directory containing resume files (default: resources/resumes)")
    p.add_argument("--report-file", type=Path, default=REPORT_FILE,
                   help="Output JSON report path (default: resources/analysis_report.json)")
    args = p.parse_args()
    analyze(args.resumes_dir, args.report_file)
