"""Table extraction and arithmetic verification for the targeted pipeline - local, exact.

Tables are read with pymupdf's own table detector (page.find_tables), already a dependency and
already used by multimodal.pages_needing_visual_check; pdfplumber would add a dependency for the
same job. Amounts are parsed with postprocess.parse_amount_to_cents, the same parser every other
path uses, so "123 456", "€ 590,625.00" and "1 234 567" all mean the same thing everywhere.

verify_table checks the arithmetic: each numeric column's rows add up to its totals row, and a
row-total column equals the sum of the other amount columns on that row. A column whose checks all
pass is a strong sign the extraction is correct - better evidence than any model's confidence.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import fitz  # pymupdf

from .postprocess import parse_amount_to_cents

_TOTAL = re.compile(r"^\s*(grand\s+)?(total|tot|sum|yhteensä|summa)\b", re.IGNORECASE)
_AMOUNT_HEADER = re.compile(r"(?i)request|grant|funding applied|applied|€|\beur\b|budget|cost")
_REQUESTED_HEADER = re.compile(r"(?i)request|grant|funding applied")


def _cell(value: Any) -> str:
    return " ".join(str(value).split()) if value is not None else ""


def cell_cents(text: str) -> int | None:
    """Cents for an amount cell, or None for blanks, percentages and anything not a clean number."""
    text = _cell(text)
    if not text or "%" in text or not re.search(r"\d", text):
        return None
    cents, warning = parse_amount_to_cents(text)
    return None if warning else cents


def is_total_row(row: list[str]) -> bool:
    return bool(row) and bool(_TOTAL.match(_cell(row[0])))


def extract_tables(pdf_path: Path, pages: list[int]) -> list[dict[str, Any]]:
    """Every table pymupdf detects on the given 1-indexed pages, as plain text cells."""
    tables = []
    doc = fitz.open(pdf_path)
    try:
        for pno in sorted(set(pages)):
            if not 1 <= pno <= doc.page_count:
                continue
            for index, table in enumerate(doc[pno - 1].find_tables().tables):
                rows = [[_cell(c) for c in row] for row in table.extract()]
                if rows:
                    tables.append({"page": pno, "index": index, "rows": rows})
    finally:
        doc.close()
    return tables


def verify_table(rows: list[list[str]]) -> dict[str, Any]:
    """Arithmetic checks for one table.

    Column checks: in each column, the numeric cells since the previous totals row (or section
    heading, a row with text in the first cell and nothing else) must add up to the next totals
    row's cell. Row checks: if a column's header says "total", every ordinary row's cell in that
    column must equal the sum of the row's other amount cells.

    Returns {"checks": [...], "columns": {col: "verified" | "partial" | "failed"}, "verified": bool}.
    A column is "verified" only if every check on it passed; the table is verified if at least one
    column is.
    """
    checks: list[dict[str, Any]] = []
    width = max((len(r) for r in rows), default=0)
    header = rows[0] if rows else []

    for col in range(1, width):
        segment: list[int] = []
        for r, row in enumerate(rows):
            value = cell_cents(row[col]) if col < len(row) else None
            if is_total_row(row):
                if value is not None and segment:
                    found = sum(segment)
                    checks.append({"kind": "column", "column": col, "row": r, "expected": value,
                                   "found": found, "ok": found == value})
                segment = []
            elif _cell(row[0]) and all(not _cell(c) for c in row[1:]):
                segment = []  # section heading
            elif value is not None:
                segment.append(value)

    total_cols = [c for c in range(1, width) if c < len(header) and _TOTAL.match(_cell(header[c]))]
    for tc in total_cols:
        for r, row in enumerate(rows[1:], start=1):
            if is_total_row(row) or tc >= len(row):
                continue
            expected = cell_cents(row[tc])
            parts = [cell_cents(row[c]) for c in range(1, len(row)) if c != tc]
            parts = [p for p in parts if p is not None]
            if expected is not None and len(parts) >= 1:
                checks.append({"kind": "row", "column": tc, "row": r, "expected": expected,
                               "found": sum(parts), "ok": sum(parts) == expected})

    columns: dict[int, str] = {}
    for col in sorted({c["column"] for c in checks if c["kind"] == "column"}):
        results = [c["ok"] for c in checks if c["column"] == col and c["kind"] == "column"]
        columns[col] = "verified" if all(results) else ("partial" if any(results) else "failed")
    return {"checks": checks, "columns": columns, "verified": "verified" in columns.values()}


def find_partner_budget(tables: list[dict[str, Any]]) -> dict[str, Any] | None:
    """The table most likely to be the per-partner budget: a name column plus a verified amount
    column, preferring headers that say requested / grant / funding applied. None if no table
    has a verified amount column."""
    best, best_score = None, -1.0
    for table in tables:
        rows = table["rows"]
        verification = table.get("verification") or verify_table(rows)
        header = rows[0] if rows else []
        for col, status in verification["columns"].items():
            if status != "verified":
                continue
            entries = []
            for row in rows[1:]:
                if is_total_row(row) or col >= len(row):
                    continue
                name, cents = _cell(row[0]), cell_cents(row[col])
                if name and cents is not None and not re.fullmatch(r"[\d\s.,]+", name):
                    entries.append({"name": name, "amount_text": _cell(row[col]), "cents": cents})
            if len(entries) < 2:
                continue
            head = _cell(header[col]) if col < len(header) else ""
            score = len(entries) + (10 if _REQUESTED_HEADER.search(head) else 0) \
                + (3 if _AMOUNT_HEADER.search(head) else 0)
            if score > best_score:
                total_row = next((r for r in rows if is_total_row(r) and col < len(r) and cell_cents(r[col])), None)
                best_score = score
                best = {"page": table["page"], "index": table["index"], "column": col, "header": head,
                        "partners": entries, "total_text": _cell(total_row[col]) if total_row else None}
    return best


def table_to_markdown(table: dict[str, Any]) -> str:
    """A parsed table as a Markdown table, labelled with its page and verification status."""
    rows = table["rows"]
    verification = table.get("verification") or verify_table(rows)
    verified_cols = [c for c, s in verification["columns"].items() if s == "verified"]
    if verified_cols:
        status = "VERIFIED (columns " + ", ".join(str(c + 1) for c in verified_cols) + " add up to their totals row)"
    else:
        status = "NOT VERIFIED (no column adds up to a totals row)"
    width = max(len(r) for r in rows)
    lines = [f"Table {table['index'] + 1} on page {table['page']}: {status}"]
    for i, row in enumerate(rows):
        cells = [c.replace("|", "/") for c in row] + [""] * (width - len(row))
        lines.append("| " + " | ".join(cells) + " |")
        if i == 0:
            lines.append("|" + " --- |" * width)
    return "\n".join(lines)
