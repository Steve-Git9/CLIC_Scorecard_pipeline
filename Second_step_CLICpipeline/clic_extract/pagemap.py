"""Triage, page map and page location for the targeted pipeline - all local, no model calls.

triage() reads the page count, the outline (bookmarks) and how much embedded text each page
has; a page with almost no text but an embedded picture is a scan and needs OCR later.
build_page_map() keeps, per page, only the first few lines and the keyword hits - for a long
proposal that is a few thousand tokens instead of the whole text, small enough to show a model
if keyword location fails. The map is cached by the PDF's SHA-256, so a second run on the same
document skips this work entirely. locate() scores every page against a field group's keywords
plus structural cues (outline entries, page headers, detected tables) and keeps the top pages.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

import fitz  # pymupdf

PAGE_MAP_VERSION = 1
# Same threshold as config.yaml's conversion.ocr_min_chars_per_page and
# src/pipeline/convert._needs_ocr: below this a page has no usable text layer.
SCAN_MAX_CHARS = 100
HEADER_LINES = 3
HEADER_LINE_CHARS = 120

KEYWORDS: dict[str, list[str]] = {
    "proposal": ["title", "acronym", "call", "topic", "submission", "deadline", "project plan", "proposal"],
    "budget": ["budget", "total costs", "total cost", "personnel", "requested", "grant", "funding applied",
               "funding", "eur", "€", "total"],
    "partners": ["partner", "consortium", "beneficiary", "participant", "coordinator", "research institute",
                 "companies"],
    "readiness": ["trl", "technology readiness", "mcrl", "market readiness", "readiness level"],
}
# Groups whose answer normally sits in a table: a detected table on the page is a strong cue.
TABLE_GROUPS = {"budget", "partners"}
# The cover pages carry acronym, title, call and date in nearly every proposal.
COVER_PAGES = {1: 3.0, 2: 1.5}


def _keyword_pattern(keyword: str) -> re.Pattern:
    if keyword.isalpha() and len(keyword) <= 4:  # short words like "trl", "eur", "call" need word bounds
        return re.compile(rf"\b{re.escape(keyword)}\b", re.IGNORECASE)
    return re.compile(re.escape(keyword), re.IGNORECASE)


_PATTERNS = {group: {k: _keyword_pattern(k) for k in words} for group, words in KEYWORDS.items()}


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def keyword_hits(text: str) -> dict[str, dict[str, int]]:
    """{group: {keyword: count}}, only keywords that occur at least once."""
    hits: dict[str, dict[str, int]] = {}
    for group, patterns in _PATTERNS.items():
        found = {k: len(p.findall(text)) for k, p in patterns.items()}
        found = {k: n for k, n in found.items() if n}
        if found:
            hits[group] = found
    return hits


def triage(pdf_path: Path) -> dict[str, Any]:
    """Page count, outline and per-page text size, with scans flagged. Seconds, no OCR."""
    doc = fitz.open(pdf_path)
    try:
        pages = []
        for i, page in enumerate(doc):
            chars = len(page.get_text().strip())
            has_images = bool(page.get_images())
            pages.append({"page": i + 1, "chars": chars, "has_images": has_images,
                          "is_scan": chars < SCAN_MAX_CHARS and has_images})
        outline = [{"level": lvl, "title": title, "page": pno} for lvl, title, pno in doc.get_toc()]
        return {"page_count": doc.page_count, "outline": outline, "pages": pages}
    finally:
        doc.close()


def _header_lines(text: str) -> list[str]:
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    return [ln[:HEADER_LINE_CHARS] for ln in lines[:HEADER_LINES]]


def build_page_map(pdf_path: Path, cache_dir: Path | None = None) -> dict[str, Any]:
    """Triage plus, per page, header lines, keyword hits and detected table count.

    Cached at cache_dir/<sha256>.json when cache_dir is given. The returned dict has
    "from_cache": True when it was read back rather than built.
    """
    pdf_path = Path(pdf_path)
    sha = file_sha256(pdf_path)
    cache_path = Path(cache_dir) / f"{sha}.json" if cache_dir else None
    if cache_path and cache_path.exists():
        try:
            cached = json.loads(cache_path.read_text(encoding="utf-8"))
            if cached.get("version") == PAGE_MAP_VERSION:
                cached["from_cache"] = True
                return cached
        except json.JSONDecodeError:
            pass

    info = triage(pdf_path)
    doc = fitz.open(pdf_path)
    try:
        for entry, page in zip(info["pages"], doc):
            text = page.get_text()
            entry["header"] = _header_lines(text)
            entry["hits"] = keyword_hits(text)
            entry["table_count"] = len(page.find_tables().tables) if not entry["is_scan"] else 0
    finally:
        doc.close()

    page_map = {"version": PAGE_MAP_VERSION, "sha256": sha, "source_file": pdf_path.name, **info}
    if cache_path:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(json.dumps(page_map, indent=1, ensure_ascii=False), encoding="utf-8")
    page_map["from_cache"] = False
    return page_map


def score_page(entry: dict[str, Any], group: str, outline_pages: set[int]) -> float:
    hits = entry.get("hits", {}).get(group, {})
    # Distinct keywords count more than repetitions of one word.
    score = len(hits) * 2.0 + min(sum(hits.values()), 20) * 0.25
    if not hits and group != "proposal":
        return 0.0
    header = " ".join(entry.get("header", []))
    if any(p.search(header) for p in _PATTERNS[group].values()):
        score += 3.0
    if entry["page"] in outline_pages:
        score += 3.0
    if group in TABLE_GROUPS and entry.get("table_count"):
        score += 4.0
    if group == "proposal":
        score += COVER_PAGES.get(entry["page"], 0.0)
    return round(score, 2)


def locate(page_map: dict[str, Any], group: str, k: int = 3) -> list[dict[str, Any]] | None:
    """Top 1 to k pages for a field group, best first, or None if nothing scores at all.

    Pages scoring under half of the best page are dropped, so a clear winner is sent alone.
    """
    outline_pages = {
        o["page"] for o in page_map.get("outline", [])
        if any(p.search(o["title"]) for p in _PATTERNS[group].values())
    }
    scored = [{"page": e["page"], "score": score_page(e, group, outline_pages)} for e in page_map["pages"]]
    scored = [s for s in scored if s["score"] > 0]
    if not scored:
        return None
    scored.sort(key=lambda s: (-s["score"], s["page"]))
    best = scored[0]["score"]
    return [s for s in scored[:k] if s["score"] >= best / 2]


def compact_page_map(page_map: dict[str, Any]) -> str:
    """The page map as short text lines, for the model's page-picking fallback."""
    lines = []
    for e in page_map["pages"]:
        hits = ", ".join(f"{g}:{'/'.join(sorted(h))}" for g, h in e.get("hits", {}).items())
        header = " | ".join(e.get("header", []))
        flags = (" [scan]" if e.get("is_scan") else "") + (f" [{e['table_count']} table(s)]" if e.get("table_count") else "")
        lines.append(f"p{e['page']}{flags}: {header} || {hits}")
    return "\n".join(lines)
