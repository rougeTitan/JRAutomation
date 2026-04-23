#!/usr/bin/env python3
"""
Collect publicly available software engineering resumes from GitHub.
People intentionally publish their resumes in public GitHub repos.

Two strategies:
  1. Code Search  — filename-based search (filename:resume.pdf etc.)
  2. Repo Search  — crawl repos tagged with resume-related topics

NOTE: LinkedIn/Indeed NOT included — scraping violates their ToS.
      For curated public datasets, see README.md.

Usage:
    python collect_resumes.py                   # both strategies, defaults
    python collect_resumes.py --max-per-query 50
    python collect_resumes.py --code-search     # only strategy 1
    python collect_resumes.py --repo-search     # only strategy 2

Set GITHUB_TOKEN env var for 30x better rate limits:
    $env:GITHUB_TOKEN = "ghp_your_token_here"   (PowerShell)
    export GITHUB_TOKEN="ghp_your_token_here"   (bash)
"""

import os
import re
import time
import json
import logging
import argparse
from pathlib import Path
from datetime import datetime, timezone

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

# ── Config ───────────────────────────────────────────────────────────────────
RESOURCES_DIR = Path(__file__).parent
RESUMES_DIR   = RESOURCES_DIR / "resumes"
META_FILE     = RESOURCES_DIR / "metadata.json"
VALID_EXTS    = {".pdf", ".docx", ".doc"}
MAX_FILE_BYTES  = 5 * 1024 * 1024  # 5 MB — resumes are never this large
TOTAL_CAP       = 1000              # stop collecting once we reach this count

# Filename substrings that indicate low-quality / non-real resumes
SKIP_FILENAME_TOKENS = {
    "dummy", "placeholder", "sample", "template", "blank", "example",
    "fake", "mock", "test", "demo", "lorem", "ipsum",
    "jane_doe", "jane doe", "john_doe", "john doe",
    "user0", "user1", "user2", "user3", "user4", "user5",
    "user6", "user7", "user8", "user9",
    "candidate", "applicant",
}

# Path segments that indicate non-resume content
SKIP_PATH_SEGMENTS = {
    'books', 'book', 'ppt', 'slides', 'tutorial', 'tutorials',
    'cheat', 'cheatsheet', 'cheat sheets', 'reference',
    'docs', 'documentation', 'test', 'tests', 'testdata',
    'node_modules', 'vendor', 'dist', 'build', 'assets/images',
}

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
GH_HEADERS = {
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}
if GITHUB_TOKEN:
    GH_HEADERS["Authorization"] = f"Bearer {GITHUB_TOKEN}"
    SEARCH_DELAY = 3
else:
    log.warning(
        "GITHUB_TOKEN not set — limited to ~10 searches/min. "
        "Set it for 30x better throughput: $env:GITHUB_TOKEN='ghp_...'"
    )
    SEARCH_DELAY = 8

# ── Filename-based code search queries ───────────────────────────────────────
CODE_QUERIES = [
    "filename:resume.pdf",
    "filename:resume.docx",
    "filename:CV.pdf",
    "filename:cv.pdf",
    "filename:software-engineer-resume.pdf",
    "filename:swe-resume.pdf",
    "filename:engineer-resume.pdf",
    "filename:developer-resume.pdf",
    "filename:senior-engineer-resume.pdf",
    "filename:architect-resume.pdf",
    "filename:manager-resume.pdf",
    "filename:tech-lead-resume.pdf",
    "filename:resume extension:pdf",
    "filename:resume extension:docx",
]

# ── Repo topics to crawl for resume files ────────────────────────────────────
REPO_TOPICS = [
    "resume",
    "resume-template",
    "software-engineer-resume",
    "cv-template",
]


# ── Metadata helpers ─────────────────────────────────────────────────────────
def load_meta() -> dict:
    if META_FILE.exists():
        return json.loads(META_FILE.read_text(encoding="utf-8"))
    return {
        "downloaded": {},
        "skipped": [],
        "stats": {"total": 0, "by_ext": {}},
    }


def save_meta(m: dict):
    META_FILE.write_text(json.dumps(m, indent=2, ensure_ascii=False), encoding="utf-8")


# ── GitHub API helpers ───────────────────────────────────────────────────────
def gh_get(url: str, params: dict = None) -> dict:
    r = requests.get(url, headers=GH_HEADERS, params=params, timeout=30)
    r.raise_for_status()
    remaining = int(r.headers.get("X-RateLimit-Remaining", 99))
    if remaining < 5:
        reset_ts = int(r.headers.get("X-RateLimit-Reset", time.time() + 65))
        wait     = max(0, reset_ts - time.time()) + 2
        log.warning(f"Rate limit low ({remaining} left). Sleeping {wait:.0f}s …")
        time.sleep(wait)
    return r.json()


def html_to_raw(html_url: str) -> str:
    """Convert GitHub blob URL to raw.githubusercontent.com download URL."""
    return (
        html_url
        .replace("github.com", "raw.githubusercontent.com")
        .replace("/blob/", "/")
    )


def is_resume_path(path: str) -> bool:
    """Return False if path strongly suggests non-resume content."""
    parts = {p.lower() for p in Path(path).parts}
    return not (parts & SKIP_PATH_SEGMENTS)


def is_quality_filename(filename: str) -> bool:
    """Return False if filename is clearly a placeholder/template, not a real person's resume."""
    name_lower = filename.lower()
    return not any(tok in name_lower for tok in SKIP_FILENAME_TOKENS)


def download_file(url: str, dest: Path, max_bytes: int = MAX_FILE_BYTES) -> bool:
    try:
        r = requests.get(url, headers=GH_HEADERS, timeout=30, stream=True)
        r.raise_for_status()
        # Check Content-Length before writing
        cl = int(r.headers.get("Content-Length", 0))
        if cl > max_bytes:
            log.debug(f"Skipping {url} — too large ({cl/1024/1024:.1f} MB)")
            return False
        dest.parent.mkdir(parents=True, exist_ok=True)
        data = b"".join(r.iter_content(chunk_size=65536))
        if len(data) > max_bytes:
            log.debug(f"Skipping {url} — content too large ({len(data)/1024/1024:.1f} MB)")
            return False
        dest.write_bytes(data)
        return True
    except Exception as e:
        log.debug(f"Download failed {url}: {e}")
        return False


def record_download(meta: dict, html_url: str, dest: Path, repo: str, name: str, ext: str):
    meta["downloaded"][html_url] = {
        "file": str(dest.relative_to(RESOURCES_DIR)),
        "repo": repo,
        "name": name,
        "ext":  ext,
        "ts":   datetime.now(timezone.utc).isoformat(),
    }
    meta["stats"]["total"] += 1
    meta["stats"]["by_ext"][ext] = meta["stats"]["by_ext"].get(ext, 0) + 1


def dest_path(ext: str, repo_full_name: str, filename: str) -> Path:
    repo_str = repo_full_name.replace("/", "__")
    return RESUMES_DIR / ext.lstrip(".") / f"{repo_str}__{filename}"


# ── Strategy 1: GitHub Code Search ───────────────────────────────────────────
def collect_code_search(meta: dict, max_per_query: int):
    """Search for resume files by filename across all public repos."""
    seen = set(meta["downloaded"]) | set(meta["skipped"])

    for query in CODE_QUERIES:
        log.info(f"\n[CodeSearch] {query!r}")
        count = 0

        for page in range(1, 11):           # max 10 pages = 1000 results per query
            if count >= max_per_query:
                break
            try:
                data  = gh_get("https://api.github.com/search/code",
                                {"q": query, "per_page": 100, "page": page})
            except requests.HTTPError as e:
                if e.response is not None and e.response.status_code == 401:
                    log.warning("  Code Search requires GITHUB_TOKEN. Set $env:GITHUB_TOKEN and re-run.")
                    return
                log.warning(f"  Search error (page {page}): {e}")
                break

            items = data.get("items", [])
            if not items:
                break

            for item in items:
                if count >= max_per_query:
                    break
                html_url = item["html_url"]
                if html_url in seen:
                    continue

                name = item["name"]
                ext  = Path(name).suffix.lower()
                if ext not in VALID_EXTS:
                    meta["skipped"].append(html_url)
                    seen.add(html_url)
                    continue
                if not is_resume_path(item["path"]) or not is_quality_filename(name):
                    meta["skipped"].append(html_url)
                    seen.add(html_url)
                    continue
                if meta["stats"]["total"] >= TOTAL_CAP:
                    log.info(f"  Reached total cap of {TOTAL_CAP}. Stopping.")
                    save_meta(meta)
                    return

                repo = item["repository"]["full_name"]
                dest = dest_path(ext, repo, name)

                if dest.exists():
                    record_download(meta, html_url, dest, repo, name, ext)
                    seen.add(html_url)
                    continue

                raw_url = html_to_raw(html_url)
                log.info(f"  ↓ {repo} / {name}")
                if download_file(raw_url, dest):
                    record_download(meta, html_url, dest, repo, name, ext)
                    count += 1
                else:
                    meta["skipped"].append(html_url)
                seen.add(html_url)
                time.sleep(0.4)

            save_meta(meta)
            time.sleep(SEARCH_DELAY)

        log.info(f"  → {count} new downloads from this query")


# ── Strategy 2: Repo Topic Search + file tree crawl ──────────────────────────
def collect_repo_topics(meta: dict, max_repos: int):
    """Find repos tagged with resume topics, then download all PDF/DOCX files."""
    seen = set(meta["downloaded"]) | set(meta["skipped"])

    for topic in REPO_TOPICS:
        log.info(f"\n[RepoTopic] {topic!r}")
        try:
            data = gh_get("https://api.github.com/search/repositories",
                           {"q": f"topic:{topic}", "sort": "stars",
                            "per_page": min(max_repos, 100)})
        except requests.HTTPError as e:
            log.warning(f"  Repo search error: {e}")
            continue

        for repo_obj in data.get("items", []):
            full_name      = repo_obj["full_name"]
            default_branch = repo_obj.get("default_branch", "main")
            log.info(f"  Crawling {full_name}")

            try:
                tree_data = gh_get(
                    f"https://api.github.com/repos/{full_name}/git/trees/{default_branch}",
                    {"recursive": "1"},
                )
            except requests.HTTPError as e:
                log.debug(f"  Tree error {full_name}: {e}")
                continue

            for node in tree_data.get("tree", []):
                path = node.get("path", "")
                ext  = Path(path).suffix.lower()
                if ext not in VALID_EXTS:
                    continue
                if not is_resume_path(path):
                    continue
                if node.get("size", 0) > MAX_FILE_BYTES:
                    log.debug(f"  Skipping large file: {path} ({node.get('size',0)/1024/1024:.1f} MB)")
                    continue

                name = Path(path).name
                if not is_quality_filename(name):
                    continue
                if meta["stats"]["total"] >= TOTAL_CAP:
                    log.info(f"  Reached total cap of {TOTAL_CAP}. Stopping.")
                    save_meta(meta)
                    return
                html_url = f"https://github.com/{full_name}/blob/{default_branch}/{path}"
                raw_url  = (
                    f"https://raw.githubusercontent.com/{full_name}"
                    f"/{default_branch}/{path}"
                )

                if html_url in seen:
                    continue

                dest = dest_path(ext, full_name, name)
                log.info(f"    ↓ {path}")
                if download_file(raw_url, dest):
                    record_download(meta, html_url, dest, full_name, name, ext)
                else:
                    meta["skipped"].append(html_url)
                seen.add(html_url)
                save_meta(meta)
                time.sleep(0.4)

            time.sleep(1)


# ── Entry point ───────────────────────────────────────────────────────────────
def main():
    p = argparse.ArgumentParser(
        description="Collect public software engineering resumes from GitHub"
    )
    p.add_argument("--max-per-query", type=int, default=100,
                   help="Max downloads per code-search query (default: 100)")
    p.add_argument("--max-repos",     type=int, default=30,
                   help="Max repos to crawl via topic search (default: 30)")
    p.add_argument("--code-search",   action="store_true",
                   help="Run code-search strategy only")
    p.add_argument("--repo-search",   action="store_true",
                   help="Run repo-topic strategy only")
    args = p.parse_args()

    both = not args.code_search and not args.repo_search

    RESUMES_DIR.mkdir(parents=True, exist_ok=True)
    meta = load_meta()

    if both or args.code_search:
        collect_code_search(meta, args.max_per_query)
    if both or args.repo_search:
        collect_repo_topics(meta, args.max_repos)

    save_meta(meta)
    log.info(
        f"\nDone. Total collected: {meta['stats']['total']} | "
        f"By ext: {meta['stats']['by_ext']}"
    )


if __name__ == "__main__":
    main()
