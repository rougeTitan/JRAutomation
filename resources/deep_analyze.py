"""
deep_analyze.py  –  Comprehensive resume analysis for job-search & resume optimization.

Run:
    python resources/deep_analyze.py

Outputs (resources/insights/):
    skills_taxonomy.json      – skills by category with frequency + per-role breakdown
    resume_structure.json     – section prevalence, word count, quantification stats
    action_verbs.json         – top action verbs extracted from bullet points
    ats_keywords.json         – ranked ATS keywords per role type
    optimization_guide.json   – data-backed, actionable recommendations
"""

import re
import json
import logging
from pathlib import Path
from collections import Counter, defaultdict

logging.basicConfig(level=logging.ERROR, format="%(levelname)s %(message)s")
log = logging.getLogger(__name__)
logging.getLogger("pypdf").setLevel(logging.ERROR)
logging.getLogger("pdfminer").setLevel(logging.ERROR)

RESOURCES_DIR = Path(__file__).parent
RESUMES_DIR   = RESOURCES_DIR / "resumes"
INSIGHTS_DIR  = RESOURCES_DIR / "insights"

# ── Skills taxonomy ───────────────────────────────────────────────────────────
SKILLS: dict[str, list[tuple[str, str]]] = {
    "languages": [
        ("Python",      r"\bpython\b"),
        ("JavaScript",  r"\bjavascript\b"),
        ("TypeScript",  r"\btypescript\b"),
        ("Java",        r"\bjava\b(?!script)"),
        ("C++",         r"\bc\+\+\b"),
        ("C#",          r"\bc#\b"),
        ("Go/Golang",   r"\bgolang\b|\bgo\s+(?:lang|programming)\b"),
        ("Rust",        r"\brust\b"),
        ("Scala",       r"\bscala\b"),
        ("Kotlin",      r"\bkotlin\b"),
        ("Swift",       r"\bswift\b"),
        ("Ruby",        r"\bruby\b"),
        ("PHP",         r"\bphp\b"),
        ("Bash/Shell",  r"\bbash\b|\bshell\s*script"),
        ("R",           r"\bR\b(?=\s*(?:programming|language|,|\)))"),
    ],
    "frontend": [
        ("React",       r"\breact\.?js\b|\breact\b"),
        ("Angular",     r"\bangular\b"),
        ("Vue.js",      r"\bvue\.?js\b|\bvue\b"),
        ("Next.js",     r"\bnext\.js\b"),
        ("Svelte",      r"\bsvelte\b"),
        ("HTML",        r"\bhtml\b"),
        ("CSS",         r"\bcss\b"),
        ("Tailwind",    r"\btailwind\b"),
        ("Redux",       r"\bredux\b"),
        ("Webpack",     r"\bwebpack\b"),
        ("React Native",r"\breact\s+native\b"),
    ],
    "backend": [
        ("Node.js",       r"\bnode\.js\b|\bnodejs\b"),
        ("Django",        r"\bdjango\b"),
        ("Flask",         r"\bflask\b"),
        ("FastAPI",       r"\bfastapi\b"),
        ("Spring Boot",   r"\bspring\s*(?:boot|framework)\b"),
        ("Express",       r"\bexpress\.?js\b|\bexpress\b"),
        ("GraphQL",       r"\bgraphql\b"),
        ("REST API",      r"\brest\s*api\b|\brestful\b"),
        ("Microservices", r"\bmicroservices?\b"),
        ("gRPC",          r"\bgrpc\b"),
    ],
    "cloud": [
        ("AWS",   r"\baws\b|\bamazon web services\b"),
        ("GCP",   r"\bgcp\b|\bgoogle cloud\b"),
        ("Azure", r"\bazure\b"),
    ],
    "devops": [
        ("Docker",          r"\bdocker\b"),
        ("Kubernetes",      r"\bkubernetes\b|\bk8s\b"),
        ("Terraform",       r"\bterraform\b"),
        ("CI/CD",           r"\bci/cd\b|\bcicd\b|\bcontinuous\s+(?:integration|delivery|deployment)\b"),
        ("Jenkins",         r"\bjenkins\b"),
        ("GitHub Actions",  r"\bgithub\s+actions\b"),
        ("Ansible",         r"\bansible\b"),
        ("Linux",           r"\blinux\b"),
        ("Git",             r"\bgit\b(?!hub)"),
        ("Helm",            r"\bhelm\b"),
    ],
    "databases": [
        ("PostgreSQL",    r"\bpostgresql\b|\bpostgres\b"),
        ("MySQL",         r"\bmysql\b"),
        ("MongoDB",       r"\bmongodb\b|\bmongo\b"),
        ("Redis",         r"\bredis\b"),
        ("Elasticsearch", r"\belasticsearch\b"),
        ("SQL",           r"\bsql\b"),
        ("DynamoDB",      r"\bdynamodb\b"),
        ("Cassandra",     r"\bcassandra\b"),
        ("SQLite",        r"\bsqlite\b"),
        ("Snowflake",     r"\bsnowflake\b"),
    ],
    "ai_ml": [
        ("Machine Learning", r"\bmachine learning\b"),
        ("Deep Learning",    r"\bdeep learning\b"),
        ("PyTorch",          r"\bpytorch\b"),
        ("TensorFlow",       r"\btensorflow\b"),
        ("Scikit-learn",     r"\bscikit-?learn\b"),
        ("LLM/GenAI",        r"\bllm[s]?\b|\blarge language model\b|\bgenerative ai\b|\bgenai\b"),
        ("NLP",              r"\bnlp\b|\bnatural language processing\b"),
        ("Computer Vision",  r"\bcomputer vision\b"),
        ("OpenAI/GPT",       r"\bopenai\b|\bgpt-?[3-4o]\b|\bchatgpt\b"),
        ("Hugging Face",     r"\bhugging\s*face\b|\btransformers\b"),
        ("LangChain",        r"\blangchain\b"),
        ("RAG",              r"\brag\b|\bretrieval[- ]augmented\b"),
    ],
    "data_engineering": [
        ("Apache Spark", r"\bspark\b|\bpyspark\b"),
        ("Kafka",        r"\bkafka\b"),
        ("Airflow",      r"\bairflow\b"),
        ("Databricks",   r"\bdatabricks\b"),
        ("dbt",          r"\bdbt\b"),
        ("Hadoop",       r"\bhadoop\b"),
        ("Flink",        r"\bflink\b"),
        ("BigQuery",     r"\bbigquery\b"),
    ],
    "methodology": [
        ("Agile",        r"\bagile\b"),
        ("Scrum",        r"\bscrum\b"),
        ("Kanban",       r"\bkanban\b"),
        ("TDD",          r"\btdd\b|\btest.driven\b"),
        ("System Design",r"\bsystem design\b"),
        ("OOP",          r"\boop\b|\bobject.oriented\b"),
    ],
}

# Pre-compile all skill patterns
_SKILL_COMPILED: dict[str, list[tuple[str, re.Pattern]]] = {
    cat: [(name, re.compile(pat, re.IGNORECASE)) for name, pat in items]
    for cat, items in SKILLS.items()
}

# ── Resume sections ───────────────────────────────────────────────────────────
SECTIONS = {
    "summary":        r"\b(summary|objective|profile|about\s*me|professional\s*summary|career\s*objective)\b",
    "experience":     r"\b(experience|employment|work\s*history|professional\s*experience|work\s*experience)\b",
    "education":      r"\b(education|academic|degrees?|schooling)\b",
    "skills":         r"\b(skills|technologies|tech\s*stack|competencies|tools|expertise|proficiencies)\b",
    "projects":       r"\b(projects|personal\s*projects|portfolio|open.?source|side\s*projects)\b",
    "certifications": r"\b(certifications?|certificates?|licenses?|credentials?|accreditations?)\b",
    "awards":         r"\b(awards?|honors?|achievements?|recognition|scholarships?)\b",
    "publications":   r"\b(publications?|research|papers?|journals?)\b",
    "volunteer":      r"\b(volunteer|community\s*(?:service|involvement)|extracurricular)\b",
}
_SECTION_RE = {k: re.compile(v, re.IGNORECASE) for k, v in SECTIONS.items()}

# ── Certifications ────────────────────────────────────────────────────────────
CERTS = [
    ("AWS Certified",          r"aws\s+certified|certified\s+aws"),
    ("Google Cloud Certified", r"google\s+cloud\s+certif|gcp\s+certif"),
    ("Azure Certified",        r"azure\s+certif|az-\d{3}\b"),
    ("Kubernetes (CKA/CKAD)",  r"\bck[ad]\b|certified\s+kubernetes"),
    ("PMP",                    r"\bpmp\b|project\s+management\s+professional"),
    ("Scrum Master (CSM)",     r"certified\s+scrum\s+master|\bcsm\b(?!\w)"),
    ("CompTIA",                r"\bcomptia\b|\bsecurity\+|\bnetwork\+"),
    ("Oracle Certified",       r"oracle\s+certif|\bocp\b|\boca\b"),
]
_CERT_RE = [(n, re.compile(p, re.IGNORECASE)) for n, p in CERTS]

# ── Education levels ──────────────────────────────────────────────────────────
EDU_LEVELS = [
    ("PhD",       r"\bph\.?d\.?\b|\bdoctorate\b|\bdoctor\s+of\b"),
    ("Masters",   r"\bm\.?s\.?\b|\bmaster'?s?\b|\bm\.?sc\.?\b|\bm\.?eng\.?\b"),
    ("Bachelors", r"\bb\.?s\.?\b|\bbachelor'?s?\b|\bb\.?sc\.?\b|\bb\.?eng\.?\b|\bb\.?tech\.?\b"),
    ("Bootcamp",  r"\bbootcamp\b|\bcoding\s+school\b"),
]
_EDU_RE = [(lvl, re.compile(p, re.IGNORECASE)) for lvl, p in EDU_LEVELS]

# ── Bullet / quantification / verb ────────────────────────────────────────────
BULLET_RE = re.compile(r"^[ \t]*[•\-\*◦▪▸➢✓→]\s*([A-Z].+)", re.MULTILINE)
QUANT_RE  = re.compile(
    r"\b\d+\s*%|\$\s*\d[\d,]*|\b\d+[kmb]\b|\b\d{4,}\b|\b\d+x\b",
    re.IGNORECASE,
)
VERB_RE   = re.compile(r"^([A-Z][a-z]{2,}(?:ed|ing|es|s)?)\b")

# Common English words that aren't action verbs
VERB_STOPWORDS = {
    "the", "this", "that", "these", "those", "with", "from", "for", "and", "but",
    "nor", "not", "had", "has", "have", "was", "were", "are", "our", "his", "her",
    "its", "new", "all", "any", "both", "each", "few", "more", "most", "other",
    "such", "than", "then", "when", "where", "while", "who", "which",
    "also", "been", "being", "did", "does", "doing", "done", "got",
    "may", "can", "will", "shall", "could", "would", "should", "must",
    "using", "based", "related", "including", "following", "various", "multiple",
    "team", "company", "project", "work", "time", "years", "skills", "tools",
    "experience", "knowledge", "ability", "strong", "excellent", "good", "able",
    "responsible", "worked", "working",
}

# Role detection for per-role breakdown
ROLE_KWS = {
    "software_engineer":  ["software engineer", "software engineering", " swe "],
    "frontend":           ["front-end", "frontend", "front end"],
    "backend":            ["back-end", "backend", "back end"],
    "full_stack":         ["full-stack", "fullstack", "full stack"],
    "devops_sre":         ["devops", "site reliability", " sre "],
    "data_ml":            ["data engineer", "data scientist", "ml engineer", "machine learning engineer"],
    "software_developer": ["software developer"],
}


# ── Text extraction ───────────────────────────────────────────────────────────
def extract_pdf(path: Path) -> str:
    text = ""
    # Method 1: pdfplumber
    try:
        import pdfplumber
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                text += (page.extract_text() or "") + "\n"
    except Exception:
        pass
    if text.strip():
        return text
    # Method 2: pypdf (handles more PDF variants)
    try:
        from pypdf import PdfReader
        for page in PdfReader(str(path)).pages:
            text += (page.extract_text() or "") + "\n"
    except Exception:
        try:
            from PyPDF2 import PdfReader
            for page in PdfReader(str(path)).pages:
                text += (page.extract_text() or "") + "\n"
        except Exception:
            pass
    return text


def extract_docx(path: Path) -> str:
    try:
        from docx import Document
        return "\n".join(p.text for p in Document(str(path)).paragraphs)
    except Exception:
        try:
            import docx2txt
            return docx2txt.process(str(path)) or ""
        except Exception:
            return ""


def extract_text(path: Path) -> str:
    ext = path.suffix.lower()
    if ext == ".pdf":
        return extract_pdf(path)
    if ext in {".docx", ".doc"}:
        return extract_docx(path)
    return ""


# ── Per-resume analysis ───────────────────────────────────────────────────────
def detect_skills(text: str) -> dict[str, list[str]]:
    found: dict[str, list[str]] = {}
    for cat, patterns in _SKILL_COMPILED.items():
        hits = [name for name, pat in patterns if pat.search(text)]
        if hits:
            found[cat] = hits
    return found


def detect_sections(text: str) -> list[str]:
    lines = text.split("\n")
    found = set()
    for line in lines:
        stripped = line.strip()
        if not stripped or len(stripped) > 60:
            continue
        for section, pat in _SECTION_RE.items():
            if pat.search(stripped):
                found.add(section)
    return sorted(found)


def detect_certifications(text: str) -> list[str]:
    return [name for name, pat in _CERT_RE if pat.search(text)]


def detect_education(text: str) -> str:
    for level, pat in _EDU_RE:
        if pat.search(text):
            return level
    return "unknown"


def detect_role(text: str) -> str:
    t = text.lower()
    for role, kws in ROLE_KWS.items():
        if any(kw in t for kw in kws):
            return role
    return "general"


def extract_bullets(text: str) -> list[str]:
    return [m.group(1).strip() for m in BULLET_RE.finditer(text)]


def quantification_rate(bullets: list[str]) -> float:
    if not bullets:
        return 0.0
    quantified = sum(1 for b in bullets if QUANT_RE.search(b))
    return round(quantified / len(bullets), 3)


def extract_verbs(bullets: list[str]) -> list[str]:
    seen: set[str] = set()  # deduplicate per-resume so one doc can't dominate
    for b in bullets:
        m = VERB_RE.match(b)
        if m:
            v = m.group(1).lower()
            if v not in VERB_STOPWORDS and len(v) >= 3:
                seen.add(v)
    return list(seen)


def word_count(text: str) -> int:
    return len(text.split())


def analyze_one(path: Path) -> dict | None:
    text = extract_text(path)
    if len(text.split()) < 150:
        return None
    bullets = extract_bullets(text)
    return {
        "file":            path.name,
        "word_count":      word_count(text),
        "role":            detect_role(text),
        "education":       detect_education(text),
        "sections":        detect_sections(text),
        "skills":          detect_skills(text),
        "certifications":  detect_certifications(text),
        "bullet_count":    len(bullets),
        "quant_rate":      quantification_rate(bullets),
        "action_verbs":    extract_verbs(bullets),
    }


# ── Aggregation ───────────────────────────────────────────────────────────────
def aggregate(results: list[dict]) -> dict:
    n = len(results)

    # Skills: overall + per-category + per-role
    skill_counter: dict[str, Counter] = defaultdict(Counter)
    role_skill_counter: dict[str, dict[str, Counter]] = defaultdict(lambda: defaultdict(Counter))
    for r in results:
        role = r["role"]
        for cat, skills in r["skills"].items():
            for s in skills:
                skill_counter[cat][s] += 1
                role_skill_counter[role][cat][s] += 1

    # Sections prevalence
    section_counts: Counter = Counter()
    for r in results:
        for s in r["sections"]:
            section_counts[s] += 1
    section_prevalence = {s: round(c / n, 3) for s, c in section_counts.most_common()}

    # Action verbs
    verb_counter: Counter = Counter()
    for r in results:
        verb_counter.update(r["action_verbs"])

    # Quantification
    quant_rates = [r["quant_rate"] for r in results if r["bullet_count"] > 0]
    avg_quant = round(sum(quant_rates) / len(quant_rates), 3) if quant_rates else 0.0
    pct_with_metrics = round(sum(1 for q in quant_rates if q > 0) / len(quant_rates), 3) if quant_rates else 0.0

    # Word count
    wcs = [r["word_count"] for r in results]
    avg_wc = round(sum(wcs) / n)

    # Education distribution
    edu_dist: Counter = Counter(r["education"] for r in results)

    # Certifications
    cert_counter: Counter = Counter()
    for r in results:
        for c in r["certifications"]:
            cert_counter[c] += 1

    # Role distribution
    role_dist: Counter = Counter(r["role"] for r in results)

    # ATS keywords: top skills per role (flat list, ranked by frequency)
    ats_by_role: dict[str, list[str]] = {}
    for role, cats in role_skill_counter.items():
        combined: Counter = Counter()
        for cat_counts in cats.values():
            combined.update(cat_counts)
        ats_by_role[role] = [skill for skill, _ in combined.most_common(30)]

    # Overall top 50 skills
    all_skills: Counter = Counter()
    for cat_counter in skill_counter.values():
        all_skills.update(cat_counter)
    top_50 = [{"skill": s, "count": c, "pct": round(c / n, 3)}
              for s, c in all_skills.most_common(50)]

    return {
        "meta": {
            "total_analyzed":    n,
            "avg_word_count":    avg_wc,
            "avg_quant_rate":    avg_quant,
            "pct_with_metrics":  pct_with_metrics,
        },
        "skills_by_category": {
            cat: [{"skill": s, "count": c, "pct": round(c / n, 3)}
                  for s, c in counter.most_common()]
            for cat, counter in skill_counter.items()
        },
        "top_50_skills":     top_50,
        "section_prevalence": section_prevalence,
        "action_verbs":      verb_counter.most_common(60),
        "certifications":    cert_counter.most_common(),
        "education_dist":    dict(edu_dist.most_common()),
        "role_dist":         dict(role_dist.most_common()),
        "ats_by_role":       ats_by_role,
    }


# ── Optimization guide ────────────────────────────────────────────────────────
def build_optimization_guide(agg: dict, n: int) -> dict:
    top50 = agg["top_50_skills"]
    must_have   = [s["skill"] for s in top50 if s["pct"] >= 0.35]
    nice_to_have = [s["skill"] for s in top50 if 0.15 <= s["pct"] < 0.35]

    sections = agg["section_prevalence"]
    recommended_sections = [s for s, p in sections.items() if p >= 0.50]
    optional_sections    = [s for s, p in sections.items() if 0.25 <= p < 0.50]

    top_verbs = [v for v, _ in agg["action_verbs"][:20]]

    quant_pct = round(agg["meta"]["pct_with_metrics"] * 100)
    avg_quant = round(agg["meta"]["avg_quant_rate"] * 100)

    return {
        "summary": f"Based on analysis of {n} real software engineering resumes",
        "skills": {
            "must_have":    must_have,
            "nice_to_have": nice_to_have,
            "tip": "Skills appearing in >35% of resumes are near-mandatory for most SE roles.",
        },
        "resume_structure": {
            "recommended_sections": recommended_sections,
            "optional_sections":    optional_sections,
            "tip": f"Include all recommended sections. '{recommended_sections[0] if recommended_sections else 'experience'}' section is present in {round(sections.get(recommended_sections[0] if recommended_sections else 'experience', 0) * 100)}% of resumes.",
        },
        "bullet_points": {
            "power_verbs": top_verbs,
            "quantification": {
                "pct_resumes_with_metrics": quant_pct,
                "avg_quant_rate_per_resume": avg_quant,
                "tip": f"{quant_pct}% of resumes use quantified achievements. Aim to add metrics (%, $, numbers) to at least 50% of your bullet points.",
            },
        },
        "certifications": {
            "most_common": [c for c, _ in agg["certifications"][:5]],
            "tip": "AWS Certified and Google Cloud certifications appear most frequently. Consider pursuing one if targeting cloud roles.",
        },
        "ats_strategy": {
            "tip": "Match job description keywords with terms from the role-specific ATS list. Aim for 70%+ keyword match.",
            "by_role": {role: skills[:15] for role, skills in agg["ats_by_role"].items()},
        },
    }


# ── Output helpers ────────────────────────────────────────────────────────────
def save_json(data: dict | list, path: Path, label: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"  Saved → {path.relative_to(RESOURCES_DIR.parent)}")


def print_summary(agg: dict, guide: dict):
    meta = agg["meta"]
    n = meta["total_analyzed"]
    print()
    print("=" * 60)
    print(f"  DEEP ANALYSIS  ·  {n} parseable resumes")
    print("=" * 60)

    print("\n📊 TOP SKILLS (overall)")
    for item in agg["top_50_skills"][:15]:
        bar = "█" * int(item["pct"] * 20)
        print(f"  {item['skill']:<22} {bar:<20} {item['pct']*100:4.0f}%  ({item['count']})")

    print("\n📐 RESUME SECTION PREVALENCE")
    for sec, pct in list(agg["section_prevalence"].items())[:9]:
        bar = "█" * int(pct * 20)
        print(f"  {sec:<18} {bar:<20} {pct*100:4.0f}%")

    print("\n✍️  TOP ACTION VERBS")
    verbs_line = "  " + "  |  ".join(f"{v} ({c})" for v, c in agg["action_verbs"][:12])
    print(verbs_line)

    print(f"\n📈 QUANTIFICATION")
    print(f"  {meta['pct_with_metrics']*100:.0f}% of resumes include quantified achievements")
    print(f"  Average {meta['avg_quant_rate']*100:.0f}% of bullet points per resume have metrics")

    print(f"\n🎓 EDUCATION DISTRIBUTION")
    for lvl, cnt in agg["education_dist"].items():
        print(f"  {lvl:<12} {cnt:>4}  ({cnt/n*100:.0f}%)")

    print(f"\n🏆 CERTIFICATIONS (top 5)")
    for cert, cnt in agg["certifications"][:5]:
        print(f"  {cert:<30} {cnt}  ({cnt/n*100:.0f}%)")

    print(f"\n🎯 MUST-HAVE SKILLS (≥35% of resumes)")
    print("  " + ", ".join(guide["skills"]["must_have"]))

    print(f"\n💡 NICE-TO-HAVE SKILLS (15–35%)")
    print("  " + ", ".join(guide["skills"]["nice_to_have"][:12]))

    print(f"\n📁 Insight files saved to: resources/insights/")
    print("=" * 60)


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    files = sorted(
        list(RESUMES_DIR.rglob("*.pdf"))
        + list(RESUMES_DIR.rglob("*.docx"))
        + list(RESUMES_DIR.rglob("*.doc"))
    )
    total = len(files)
    print(f"Extracting & analyzing {total} resume files ...")

    results = []
    failed  = 0
    for i, f in enumerate(files, 1):
        if i % 100 == 0:
            print(f"  {i}/{total} processed  ({len(results)} parseable so far) ...")
        r = analyze_one(f)
        if r:
            results.append(r)
        else:
            failed += 1

    parseable = len(results)
    print(f"\nParseable: {parseable}/{total}  "
          f"({'image-based/encrypted PDFs' if failed > parseable else 'some parse failures'})\n")

    if parseable < 10:
        print("Too few parseable resumes — install pypdf (`pip install pypdf`) for better extraction.")
        return

    agg   = aggregate(results)
    guide = build_optimization_guide(agg, parseable)

    print("Saving insight files ...")
    save_json({"meta": agg["meta"],
               "by_category": agg["skills_by_category"],
               "top_50": agg["top_50_skills"]},
              INSIGHTS_DIR / "skills_taxonomy.json", "skills_taxonomy")

    save_json({"meta": agg["meta"],
               "section_prevalence": agg["section_prevalence"],
               "education_distribution": agg["education_dist"],
               "role_distribution": agg["role_dist"]},
              INSIGHTS_DIR / "resume_structure.json", "resume_structure")

    save_json({"top_verbs": agg["action_verbs"],
               "tip": "Start bullet points with strong past-tense action verbs."},
              INSIGHTS_DIR / "action_verbs.json", "action_verbs")

    save_json(agg["ats_by_role"],
              INSIGHTS_DIR / "ats_keywords.json", "ats_keywords")

    save_json(guide,
              INSIGHTS_DIR / "optimization_guide.json", "optimization_guide")

    print_summary(agg, guide)


if __name__ == "__main__":
    main()
