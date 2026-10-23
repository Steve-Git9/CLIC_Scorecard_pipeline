"""Identifier hints for the targeted pipeline: acronym, title and call identifier, found locally.

Free and deterministic, like pagemap.py and tables.py:
    cover text   the largest text on the cover page (font size from pymupdf), which is where nearly
                 every proposal prints its title and acronym
    labels       lines such as "Acronym: X", "Project title: Y", "Call: Z", "Topic identifier: Z"
                 anywhere in the document
    call ids     tokens shaped like a call or topic identifier (for example HORIZON-CL5-2026-D3-01:
                 at least three dash separated parts, one of them a year)

The hints are shown to the model next to the located pages, and fill_identifiers() fills a field the
model left empty from a hint, always with a warning recording where the value came from.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import fitz  # pymupdf

# Cover lines that are never the title: classification stamps, document type, contents headings.
_BOILERPLATE = re.compile(
    r"(?i)^(table of contents|contents|confidential|luottamuksellinen|public|draft|abstract|summary|"
    r"ai disclaimer|project plan\b.*|proposal\b.*|part [ab]\b.*|annex\b.*|page \d+)$"
)
_LABELS = {
    "acronym": re.compile(r"(?im)^[ \t]*(?:project[ \t]+|proposal[ \t]+)?acronym[ \t]*[:\-–][ \t]*(\S.{0,60}?)[ \t]*$"),
    "title": re.compile(r"(?im)^[ \t]*(?:project[ \t]+|proposal[ \t]+|full[ \t]+)*title[ \t]*[:\-–][ \t]*(\S.{3,200}?)[ \t]*$"),
    "call": re.compile(r"(?im)^[ \t]*(?:call|topic)(?:[ \t]+(?:identifier|id|number|code|reference))?[ \t]*[:\-–][ \t]*(\S.{1,80}?)[ \t]*$"),
}
_CALL_ID = re.compile(r"\b[A-Z][A-Z0-9]+(?:-[A-Z0-9]+){2,}\b")
_YEAR = re.compile(r"^(19|20)\d{2}$")
_ACRONYM_TOKEN = re.compile(r"^(?:[A-Z][A-Za-z0-9]*[A-Z][A-Za-z0-9]*|[A-Z0-9]{2,12})$")


def _cover_lines(page: fitz.Page) -> list[dict[str, Any]]:
    """Text lines of one page with their largest font size and vertical position."""
    lines = []
    for block in page.get_text("dict")["blocks"]:
        for line in block.get("lines", []):
            text = " ".join(s["text"].strip() for s in line["spans"] if s["text"].strip())
            if text:
                lines.append({"text": " ".join(text.split()), "size": max(s["size"] for s in line["spans"]),
                              "y": line["bbox"][1]})
    return lines


def cover_title(pdf_path: Path) -> tuple[str | None, int | None]:
    """The largest text on page 1 (page 2 if page 1 has none), lines in reading order, boilerplate dropped."""
    doc = fitz.open(pdf_path)
    try:
        for pno in range(min(2, doc.page_count)):
            lines = [ln for ln in _cover_lines(doc[pno]) if not _BOILERPLATE.match(ln["text"]) and len(ln["text"]) > 1]
            if not lines:
                continue
            top = max(ln["size"] for ln in lines)
            title_lines = sorted((ln for ln in lines if ln["size"] >= 0.9 * top), key=lambda ln: ln["y"])
            title = " ".join(ln["text"] for ln in title_lines)[:250].strip()
            if title:
                return title, pno + 1
    finally:
        doc.close()
    return None, None


def acronym_candidates(title: str | None) -> list[str]:
    """Short capitalised tokens in the cover title (for example "FiCTo"); a cover name of three words
    or fewer with no such token is itself the candidate (for example "Fiction Map")."""
    if not title:
        return []
    tokens = [t.strip(".,:;()[]") for t in title.split()]
    found = [t for t in tokens if _ACRONYM_TOKEN.match(t) and not _YEAR.match(t)]
    if found:
        return list(dict.fromkeys(found))
    return [title] if len(tokens) <= 3 else []


def find_hints(pdf_path: Path) -> dict[str, Any]:
    title, title_page = cover_title(pdf_path)
    labelled: dict[str, list[dict[str, Any]]] = {k: [] for k in _LABELS}
    call_ids: dict[str, int] = {}
    doc = fitz.open(pdf_path)
    try:
        for pno, page in enumerate(doc, start=1):
            text = page.get_text()
            for field, pattern in _LABELS.items():
                for m in pattern.finditer(text):
                    labelled[field].append({"page": pno, "value": m.group(1).strip()})
            for m in _CALL_ID.finditer(text):
                if any(_YEAR.match(part) for part in m.group(0).split("-")):
                    call_ids.setdefault(m.group(0), pno)
    finally:
        doc.close()
    return {
        "cover_title": title, "cover_page": title_page,
        "acronym_candidates": acronym_candidates(title),
        "labelled": labelled,
        "call_ids": [{"id": cid, "page": p} for cid, p in call_ids.items()],
    }


def hint_pages(hints: dict[str, Any]) -> list[int]:
    """Pages where a labelled identifier or a call id pattern was found, in page order."""
    pages = {h["page"] for items in hints["labelled"].values() for h in items}
    pages |= {c["page"] for c in hints["call_ids"]}
    if hints.get("cover_page"):
        pages.add(hints["cover_page"])
    return sorted(pages)


def hints_to_text(hints: dict[str, Any]) -> str:
    lines = ["IDENTIFIER HINTS (found locally, without a model; check them against the pages)"]
    if hints["cover_title"]:
        lines.append(f"- Largest text on the cover (page {hints['cover_page']}): {hints['cover_title']!r}")
    if hints["acronym_candidates"]:
        lines.append(f"- Acronym candidates from the cover: {', '.join(repr(a) for a in hints['acronym_candidates'])}")
    for field, items in hints["labelled"].items():
        for h in items[:3]:
            lines.append(f"- Labelled {field} on page {h['page']}: {h['value']!r}")
    for c in hints["call_ids"][:5]:
        lines.append(f"- Call or topic identifier pattern on page {c['page']}: {c['id']!r}")
    if len(lines) == 1:
        lines.append("- none found")
    return "\n".join(lines)


def _unique(values: list[str]) -> str | None:
    distinct = list(dict.fromkeys(v for v in values if v))
    return distinct[0] if len(distinct) == 1 else None


def fill_identifiers(final: dict[str, Any], hints: dict[str, Any]) -> tuple[list[str], dict[str, str]]:
    """Fill proposal fields the model left null from unambiguous hints. Returns (warnings, {field: source})."""
    proposal = final["proposal"]
    warnings: list[str] = []
    filled: dict[str, str] = {}

    def fill(field: str, value: str | None, source: str) -> None:
        if value and proposal.get(field) is None:
            proposal[field] = value
            filled[field] = source
            warnings.append(f"proposal.{field} filled from {source} ({value!r}); the model gave none")

    labelled = hints["labelled"]
    fill("proposal_acronym", _unique([h["value"] for h in labelled["acronym"]]), "an 'Acronym:' label")
    if len(hints["acronym_candidates"]) == 1:
        fill("proposal_acronym", hints["acronym_candidates"][0], f"the cover page (page {hints['cover_page']})")
    fill("proposal_title", _unique([h["value"] for h in labelled["title"]]), "a 'Title:' label")
    fill("proposal_title", hints["cover_title"], f"the largest text on the cover page (page {hints['cover_page']})")
    labelled_calls = [h["value"] for h in labelled["call"] if _CALL_ID.search(h["value"])]
    fill("call_identifier", _unique(labelled_calls), "a 'Call:' or 'Topic:' label")
    fill("call_identifier", _unique([c["id"] for c in hints["call_ids"]]), "the only call identifier pattern in the document")
    return warnings, filled
