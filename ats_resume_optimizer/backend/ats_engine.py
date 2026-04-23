import re
import string
from dataclasses import dataclass, field
from typing import List, Set

import nltk
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer
from nltk.tokenize import RegexpTokenizer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Download NLTK data once on import
def _ensure_nltk():
    for resource, category in [
        ("stopwords", "corpora"),
    ]:
        try:
            nltk.data.find(f"{category}/{resource}")
        except LookupError:
            nltk.download(resource, quiet=True)

_ensure_nltk()

_TOKENIZER = RegexpTokenizer(r"[a-zA-Z]+")

_STEMMER = PorterStemmer()
_STOP_WORDS: Set[str] = set(stopwords.words("english"))

# Common ATS boilerplate to strip from JD/resume so they don't inflate scores
_BOILERPLATE = {
    "experience", "experiences", "responsibilities", "qualifications", "requirements",
    "skills", "ability", "knowledge", "work", "team", "role", "position",
    "job", "company", "apply", "please", "equal", "opportunity", "employer",
    "looking", "seeking", "strong", "excellent", "good", "including",
    "preferred", "required", "minimum", "years", "degree", "bachelor",
    "master", "plus", "bonus", "salary", "benefit", "submit",
    # generic filler that pollutes missing-keyword lists
    "familiarity", "understanding", "concepts", "concept", "practices",
    "practice", "tools", "tool", "systems", "system", "solutions", "solution",
    "platform", "platforms", "environment", "environments", "technologies",
    "technology", "similar", "related", "relevant", "demonstrated",
    "proven", "ability", "hands", "working", "using", "use", "build",
    "building", "develop", "developing", "develop", "design", "designing",
    "manage", "managing", "support", "supporting", "maintain", "maintaining",
    "implement", "implementing", "ensure", "ensuring", "provide", "providing",
    "create", "creating", "define", "defining", "drive", "driving",
    "collaborate", "collaborating", "communicate", "communicating",
    "ownership", "mindset", "passion", "passionate", "motivated", "motivation",
    "self", "starter", "detail", "oriented", "organized", "proactive",
    "collaborative", "fast", "paced", "startup", "enterprise", "global",
    "cross", "functional", "stakeholder", "stakeholders",
}


@dataclass
class ATSReport:
    keyword_score: float
    semantic_score: float
    overall_score: float
    verdict: str
    matched_keywords: List[str]
    missing_keywords: List[str]
    jd_keyword_count: int
    resume_keyword_count: int
    section_scores: dict = field(default_factory=dict)


def _clean_text(text: str) -> str:
    text = text.lower()
    text = re.sub(r"http\S+|www\S+", " ", text)
    text = text.translate(str.maketrans(string.punctuation, " " * len(string.punctuation)))
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _tokenize_and_stem(text: str) -> List[str]:
    tokens = _TOKENIZER.tokenize(_clean_text(text))
    return [
        _STEMMER.stem(t)
        for t in tokens
        if t not in _STOP_WORDS and t not in _BOILERPLATE and len(t) > 2
    ]


def _extract_keywords(text: str) -> Set[str]:
    return set(_tokenize_and_stem(text))


def _semantic_score(resume_text: str, jd_text: str) -> float:
    vectorizer = TfidfVectorizer(
        stop_words="english",
        ngram_range=(1, 3),
        sublinear_tf=True,
        min_df=1,
    )
    try:
        tfidf = vectorizer.fit_transform([_clean_text(resume_text), _clean_text(jd_text)])
        raw = float(cosine_similarity(tfidf[0:1], tfidf[1:2])[0][0])
        # TF-IDF cosine on short docs naturally low; scale up, cap at 100
        scaled = min(raw * 4.0, 1.0)
        return round(scaled * 100, 2)
    except Exception:
        return 0.0


def _extract_named_keywords(text: str) -> List[str]:
    """Extract meaningful multi-word skills/tools from raw text (no stemming)."""
    text_lower = _clean_text(text)
    tokens = _TOKENIZER.tokenize(text_lower)
    keywords = []
    for t in tokens:
        if (
            t not in _STOP_WORDS
            and t not in _BOILERPLATE
            and _STEMMER.stem(t) not in {_STEMMER.stem(b) for b in _BOILERPLATE}
            and len(t) > 2
        ):
            keywords.append(t)
    # deduplicate preserving order
    seen = set()
    result = []
    for k in keywords:
        if k not in seen:
            seen.add(k)
            result.append(k)
    return result


def _verdict(score: float) -> str:
    if score >= 75:
        return "🚀 Strong Match – Interview Likely"
    elif score >= 50:
        return "⚠️ Moderate Match – Needs Improvement"
    else:
        return "🗑️ Weak Match – High Rejection Risk"


def analyze(resume_text: str, jd_text: str) -> ATSReport:
    resume_kw = _extract_keywords(resume_text)
    jd_kw = _extract_keywords(jd_text)

    matched_stems = resume_kw & jd_kw
    missing_stems = jd_kw - resume_kw

    # Map stems back to raw readable words from JD
    jd_raw_kw = _extract_named_keywords(jd_text)
    resume_raw_kw = _extract_named_keywords(resume_text)

    # Build stem→word maps
    jd_stem_to_word = {_STEMMER.stem(w): w for w in jd_raw_kw}
    resume_stem_to_word = {_STEMMER.stem(w): w for w in resume_raw_kw}

    matched_words = sorted({
        jd_stem_to_word.get(s, resume_stem_to_word.get(s, s))
        for s in matched_stems
    })
    missing_words = sorted({
        jd_stem_to_word.get(s, s) for s in missing_stems
    })

    keyword_score = round(len(matched_stems) / max(len(jd_kw), 1) * 100, 2)
    semantic = _semantic_score(resume_text, jd_text)
    overall = round(keyword_score * 0.65 + semantic * 0.35, 2)

    return ATSReport(
        keyword_score=keyword_score,
        semantic_score=semantic,
        overall_score=overall,
        verdict=_verdict(overall),
        matched_keywords=matched_words[:50],
        missing_keywords=missing_words[:50],
        jd_keyword_count=len(jd_kw),
        resume_keyword_count=len(resume_kw),
    )
