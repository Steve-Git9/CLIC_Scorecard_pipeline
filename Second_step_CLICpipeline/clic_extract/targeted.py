"""Targeted extraction: do the cheap, exact work locally, call the model only on the pages that matter.

    python -m clic_extract.targeted --mode text --input "input/Bygg Map_Final - Copy.pdf"
    python -m clic_extract.targeted --mode multimodal --input input
    python -m clic_extract.targeted --mode text --input input --dry-run    # steps 1-3 only, no network

Steps, each timed into run["steps"]:
    1. triage + page map   page count, outline, text per page, scans flagged; cached by SHA-256
    2. locate              keyword + structure scoring per field group; the model picks pages from the
                           page map only for groups where keywords found nothing
       identifier hints    cover page title by font size, "Acronym:" / "Call:" labels and call id
                           patterns anywhere in the document (cover.py); their pages join "proposal"
    3. tables              pymupdf table parser on the located pages, arithmetic checked (tables.py)
    4. OCR                 only on located pages that are scans, never the whole file
    5. model               one call with only the located pages' text and the parsed tables
                           (text mode), plus those pages' images (multimodal mode)
    6. postprocess         the same build_final / validate_final as every other path
    7. reconcile           partner amounts checked against the verified tables; acronym, title and
                           call identifier the model left empty are filled from unambiguous hints

Outputs, as for run_extract and multimodal, under <output>/targeted_<mode>/:
    <stem>_<UTC>.json        the extraction (same final schema)
    <stem>_<UTC>.run.json    model, tokens, cost, timings, pages sent, tables verified, warnings
    <stem>_<UTC>.trace.json  located pages with scores, parsed tables and every arithmetic check
    <stem>_<UTC>.raw.txt     the raw reply, only when the run failed
"""

from __future__ import annotations

import argparse
import base64
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import fitz  # pymupdf

from .backends import BackendError, chat, get_token, load_arms, verify_token
from .fit import is_too_large, merge_raw_dicts
from .cover import fill_identifiers, find_hints, hint_pages, hints_to_text
from .multimodal import VISION_MODEL, render_pdf_pages
from .pagemap import build_page_map, compact_page_map, locate
from .postprocess import build_final, extract_json
from .prompts import PAGE_PICK_PROMPT, TARGETED_SYSTEM_PROMPT
from .run_extract import write_replies
from .schema import RAW_SCHEMA, validate_final
from .tables import cell_cents, extract_tables, find_partner_budget, is_total_row, table_to_markdown, verify_table

GROUPS = ["proposal", "budget", "partners", "readiness"]
MODES = ("text", "multimodal")
# Text mode uses arm C (gpt-oss-120b, the project's "accuracy ceiling" text arm); multimodal mode
# uses the vision model the batched multimodal path already uses.
TEXT_ARM = "C"
MAX_PAGES_SENT = 8
MAX_IMAGES = 6
DEFAULT_CACHE_DIR = Path(__file__).resolve().parent.parent / "output" / "targeted" / "_pagemap_cache"

_ocr_engine: Any = None


def model_for(mode: str) -> dict[str, Any]:
    if mode == "text":
        return dict(load_arms()[TEXT_ARM])
    if mode == "multimodal":
        return dict(VISION_MODEL)
    raise ValueError(f"unknown mode {mode!r}, expected one of {MODES}")


def ocr_page(pdf_path: Path, page: int) -> str:
    """Local OCR (rapidocr, already installed with docling) of one 1-indexed page."""
    global _ocr_engine
    if _ocr_engine is None:
        from rapidocr import RapidOCR
        _ocr_engine = RapidOCR()
    png = render_pdf_pages(pdf_path, page_indices=[page - 1])[0]
    result = _ocr_engine(png)
    return "\n".join(getattr(result, "txts", None) or [])


def _score_key(hit: dict) -> float:
    # Pages added by an identifier hint or by the model's page picking carry no numeric score.
    score = hit.get("score")
    return -score if isinstance(score, (int, float)) else 0.0


def shortlist(located: dict[str, list[dict] | None], limit: int = MAX_PAGES_SENT) -> list[int]:
    """Best page of every group first, then the rest by score, at most `limit` pages, in page order."""
    picked: list[int] = []
    for hits in located.values():
        if hits and hits[0]["page"] not in picked:
            picked.append(hits[0]["page"])
    rest = sorted((h for hits in located.values() if hits for h in hits[1:]), key=_score_key)
    for h in rest:
        if len(picked) >= limit:
            break
        if h["page"] not in picked:
            picked.append(h["page"])
    return sorted(picked[:limit])


def prepare(pdf_path: Path, cache_dir: Path | None = DEFAULT_CACHE_DIR) -> dict[str, Any]:
    """Steps 1 to 3, all local: page map, keyword location, tables. No model, no OCR."""
    steps: dict[str, float] = {}
    t0 = time.monotonic()
    page_map = build_page_map(pdf_path, cache_dir)
    steps["page_map"] = round(time.monotonic() - t0, 2)

    t0 = time.monotonic()
    located = {g: locate(page_map, g) for g in GROUPS}
    steps["locate"] = round(time.monotonic() - t0, 2)

    t0 = time.monotonic()
    hints = find_hints(pdf_path)
    proposal_hits = located.get("proposal") or []
    known = {h["page"] for h in proposal_hits}
    for p in hint_pages(hints):
        if p not in known:
            proposal_hits.append({"page": p, "score": "hint"})
            known.add(p)
    located["proposal"] = sorted(proposal_hits, key=lambda h: h["page"])[:3] or None
    steps["identifier_hints"] = round(time.monotonic() - t0, 2)

    t0 = time.monotonic()
    table_pages = {h["page"] for g in ("budget", "partners") for h in (located.get(g) or [])}
    tables = extract_tables(pdf_path, sorted(table_pages))
    for table in tables:
        table["verification"] = verify_table(table["rows"])
    steps["tables"] = round(time.monotonic() - t0, 2)
    return {"page_map": page_map, "located": located, "tables": tables, "hints": hints, "steps": steps}


def pick_pages_with_model(page_map: dict, groups: list[str], arm: dict, token: str) -> tuple[dict[str, list[int]], dict]:
    """Fallback for groups keywords could not place: the model reads only the compact page map."""
    messages = [
        {"role": "system", "content": PAGE_PICK_PROMPT},
        {"role": "user", "content": f"Groups needed: {', '.join(groups)}\n\nPage map:\n{compact_page_map(page_map)}"},
    ]
    result = chat(arm, messages, None, token, use_extras=True)
    picked: dict[str, list[int]] = {}
    try:
        reply = extract_json(result["content"])
        pages = reply.get("pages", {}) if isinstance(reply, dict) else {}
    except (ValueError, json.JSONDecodeError):
        pages = {}
    for g in groups:
        values = pages.get(g) if isinstance(pages, dict) else None
        picked[g] = [p for p in (values or []) if isinstance(p, int) and 1 <= p <= page_map["page_count"]][:3]
    return picked, result


def _names_match(a: str, b: str) -> bool:
    a, b = a.casefold().strip(), b.casefold().strip()
    return bool(a and b) and (a == b or a in b or b in a)


def reconcile(final: dict, tables: list[dict], budget: dict | None) -> tuple[list[str], list[dict]]:
    """Check each partner amount against verified table rows. Returns (warnings, per-partner results).

    confirmed  the amount equals a cell in a verified column on that partner's table row
    filled      the model gave no amount; the partner budget table's verified cell is used instead
    mismatch    the partner has a verified row, but the amount is not on it
    unchecked   no verified table row for this partner
    """
    warnings: list[str] = []
    results: list[dict] = []
    for partner in final["partners"]:
        name, cents = partner["partner_name"], partner["requested_cents"]
        row_cells: list[int] = []
        for table in tables:
            verified_cols = [c for c, s in table["verification"]["columns"].items() if s == "verified"]
            for row in table["rows"]:
                if row and not is_total_row(row) and _names_match(name, row[0]):
                    row_cells += [v for c in verified_cols if c < len(row) and (v := cell_cents(row[c])) is not None]
        status = "unchecked"
        if cents is not None and cents in row_cells:
            status = "confirmed"
        elif cents is None and budget:
            match = next((e for e in budget["partners"] if _names_match(name, e["name"])), None)
            if match:
                partner["requested_cents"] = match["cents"]
                status = "filled"
                warnings.append(f"requested[{name}] filled from the verified table on page {budget['page']} "
                                f"({match['amount_text']!r}); the model gave no amount")
        elif cents is not None and row_cells:
            status = "mismatch"
            warnings.append(f"requested[{name}] ({cents} cents) is not on that partner's verified table row")
        results.append({"partner_name": name, "status": status})
    return warnings, results


def _page_texts(pdf_path: Path, pages: list[int], scans: set[int]) -> tuple[dict[int, str], list[int]]:
    texts, ocr_done = {}, []
    doc = fitz.open(pdf_path)
    try:
        for p in pages:
            texts[p] = doc[p - 1].get_text()
    finally:
        doc.close()
    for p in pages:
        if p in scans:
            texts[p] = ocr_page(pdf_path, p)
            ocr_done.append(p)
    return texts, ocr_done


def build_context(texts: dict[int, str], tables: list[dict], hints: dict | None = None) -> str:
    parts = [hints_to_text(hints)] if hints else []
    parts += [f"<!-- page {p} -->\n{texts[p].strip()}" for p in sorted(texts)]
    if tables:
        parts.append("PARSED TABLES (exact, from the table parser)\n\n" + "\n\n".join(table_to_markdown(t) for t in tables))
    return "\n\n".join(parts)


def build_targeted_messages(context: str, images: list[bytes]) -> list[dict]:
    text = "Extract the data from these selected pages of the document.\n\n<document_pages>\n" + context + "\n</document_pages>"
    if not images:
        return [{"role": "system", "content": TARGETED_SYSTEM_PROMPT}, {"role": "user", "content": text}]
    content: list[dict] = [{"type": "text", "text": text}]
    for png in images:
        content.append({"type": "image_url", "image_url": {"url": "data:image/png;base64," + base64.b64encode(png).decode("ascii")}})
    return [{"role": "system", "content": TARGETED_SYSTEM_PROMPT}, {"role": "user", "content": content}]


def run_one_targeted(
    pdf_path: Path,
    out_dir: Path,
    mode: str,
    token: str,
    now: datetime | None = None,
    cache_dir: Path | None = DEFAULT_CACHE_DIR,
) -> dict:
    """Run every step on one PDF and write the outputs. Never raises for a document problem:
    failures are reported in the returned run dict, as in run_extract.run_one."""
    started_monotonic = time.monotonic()
    pdf_path, out_dir = Path(pdf_path), Path(out_dir)
    now = now or datetime.now(timezone.utc)
    base = out_dir / f"{pdf_path.stem}_{now.strftime('%Y%m%dT%H%M%SZ')}"
    arm = model_for(mode)
    run: dict[str, Any] = {
        "arm": f"targeted_{mode}", "mode": mode, "model": arm["model"], "provider": arm["provider"],
        "source_file": pdf_path.name, "started_utc": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "status": "failed", "error": None, "warnings": [],
        "pages_total": 0, "pages_sent": [], "scanned_pages": [], "ocr_pages": [], "images_sent": 0,
        "located": {}, "located_by": {}, "tables_found": 0, "tables_verified": 0, "page_map_cached": False,
        "calls": 0, "seconds": 0.0, "attempts": 0, "prompt_tokens": 0, "completion_tokens": 0, "cost_usd": 0.0,
        "finish_reason": None, "model_reported": None, "steps": {},
    }
    trace: dict[str, Any] = {}
    # Only the extraction call's reply; the page picking fallback call does not extract fields.
    replies: list[str] = []

    def add_usage(result: dict) -> None:
        run["calls"] += 1
        run["seconds"] = round(run["seconds"] + result["seconds"], 2)
        run["attempts"] += result["attempts"]
        run["prompt_tokens"] += result["prompt_tokens"] or 0
        run["completion_tokens"] += result["completion_tokens"] or 0
        run["cost_usd"] = round(run["cost_usd"] + (result["cost_usd"] or 0), 6)
        run["finish_reason"] = result["finish_reason"]
        run["model_reported"] = result["model_reported"]

    def finish(error: str | None = None, raw_text: str | None = None) -> dict:
        out_dir.mkdir(parents=True, exist_ok=True)
        if error:
            run["error"] = error
        if raw_text is not None:
            base.with_suffix(".raw.txt").write_text(raw_text, encoding="utf-8")
        write_replies(base, replies, run)
        run["total_seconds"] = round(time.monotonic() - started_monotonic, 2)
        if trace:
            base.with_suffix(".trace.json").write_text(json.dumps(trace, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
            run["trace_file"] = base.with_suffix(".trace.json").name
        base.with_suffix(".run.json").write_text(json.dumps(run, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        return run

    try:
        prep = prepare(pdf_path, cache_dir)
    except Exception as exc:  # noqa: BLE001 - surfaced as a run failure, not raised
        return finish(f"could not read the PDF: {exc}")
    page_map, located, tables, hints = prep["page_map"], prep["located"], prep["tables"], prep["hints"]
    run["steps"].update(prep["steps"])
    run["pages_total"] = page_map["page_count"]
    run["page_map_cached"] = page_map.get("from_cache", False)
    run["scanned_pages"] = [p["page"] for p in page_map["pages"] if p.get("is_scan")]
    run["located_by"] = {g: "keywords" for g in GROUPS if located[g]}
    if not page_map["page_count"]:
        return finish("PDF has no pages")

    missing = [g for g in GROUPS if not located[g]]
    if missing:
        t0 = time.monotonic()
        try:
            picked, result = pick_pages_with_model(page_map, missing, arm, token)
            add_usage(result)
            for g in missing:
                if picked.get(g):
                    located[g] = [{"page": p, "score": None} for p in picked[g]]
                    run["located_by"][g] = "model"
        except BackendError as exc:
            run["warnings"].append(f"page picking fallback failed for {missing}: {exc}")
        run["steps"]["locate_model_fallback"] = round(time.monotonic() - t0, 2)
        new_table_pages = {h["page"] for g in ("budget", "partners") if g in missing for h in (located[g] or [])}
        for table in extract_tables(pdf_path, sorted(new_table_pages)):
            table["verification"] = verify_table(table["rows"])
            tables.append(table)
    run["located"] = {g: [h["page"] for h in (located[g] or [])] for g in GROUPS}
    run["tables_found"] = len(tables)
    run["tables_verified"] = sum(1 for t in tables if t["verification"]["verified"])
    budget = find_partner_budget(tables)
    trace.update({"located": located, "tables": tables, "partner_budget_table": budget, "identifier_hints": hints,
                  "page_map_sha256": page_map["sha256"]})

    pages = shortlist(located)
    run["pages_sent"] = pages
    t0 = time.monotonic()
    try:
        texts, run["ocr_pages"] = _page_texts(pdf_path, pages, set(run["scanned_pages"]))
    except Exception as exc:  # noqa: BLE001
        return finish(f"could not read or OCR the located pages: {exc}")
    run["steps"]["text_and_ocr"] = round(time.monotonic() - t0, 2)

    # Verified tables, plus every table on a budget page; other unverified tables (timelines, work
    # package grids) are already in the page text and would only bloat the request.
    budget_pages = set(run["located"]["budget"])
    image_pages = set(pages[:MAX_IMAGES]) if mode == "multimodal" else set()

    def context_for(group: list[int]) -> str:
        sent = [t for t in tables if t["page"] in group and (t["verification"]["verified"] or t["page"] in budget_pages)]
        return build_context({p: texts[p] for p in group}, sent, hints)

    # The located pages go in one call. Only if the provider rejects it as too large for the
    # model's context are the pages split into two groups, recursively, and the answers merged
    # (clic_extract.fit); with at most eight pages this is not expected to happen.
    t0 = time.monotonic()
    worklist, raws, contexts, bad = [pages], [], [], []
    run["context_splits"] = 0
    run["images_sent"] = 0
    while worklist:
        group = worklist.pop(0)
        context = context_for(group)
        images: list[bytes] = []
        if image_pages & set(group):
            images = render_pdf_pages(pdf_path, page_indices=[p - 1 for p in group if p in image_pages])
        try:
            result = chat(arm, build_targeted_messages(context, images), RAW_SCHEMA, token, use_extras=True)
        except BackendError as exc:
            if is_too_large(exc) and len(group) > 1:
                mid = len(group) // 2
                worklist[0:0] = [group[:mid], group[mid:]]
                run["context_splits"] += 1
                run["warnings"].append(f"pages {group} were too large for one request; split into {group[:mid]} "
                                       f"and {group[mid:]}")
                continue
            return finish(str(exc))
        replies.append(result["content"] or "")
        add_usage(result)
        run["images_sent"] += len(images)
        try:
            raws.append(extract_json(result["content"]))
            contexts.append(context)
        except (ValueError, json.JSONDecodeError) as exc:
            note = " (reply was cut off: raise max_tokens)" if result["finish_reason"] == "length" else ""
            bad.append((f"reply is not valid JSON: {exc}{note}", result["content"] or ""))
    run["steps"]["model"] = round(time.monotonic() - t0, 2)
    if not raws or (len(replies) == 1 and bad):
        error, raw_text = bad[0] if len(replies) == 1 else ("no part produced a valid reply", "\n\n".join(r for _, r in bad))
        return finish(error, raw_text=raw_text)
    raw = raws[0] if len(raws) == 1 else merge_raw_dicts(raws)
    context = "\n\n".join(contexts)

    final, warnings = build_final(raw, context, pdf_path.name, now)
    run["warnings"].extend(warnings)
    reconcile_warnings, reconciliation = reconcile(final, tables, budget)
    run["warnings"].extend(reconcile_warnings)
    fill_warnings, run["identifiers_filled"] = fill_identifiers(final, hints)
    run["warnings"].extend(fill_warnings)
    run["partners_confirmed_by_table"] = sum(1 for r in reconciliation if r["status"] in ("confirmed", "filled"))
    trace["reconciliation"] = reconciliation
    problems = validate_final(final)
    if problems:
        return finish("final document failed validation: " + "; ".join(problems), raw_text="\n\n".join(replies))

    out_dir.mkdir(parents=True, exist_ok=True)
    base.with_suffix(".json").write_text(json.dumps(final, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    run["status"] = "ok"
    run["output_file"] = base.with_suffix(".json").name
    return finish()


def _print_dry_run(pdf: Path, prep: dict) -> None:
    pm = prep["page_map"]
    print(f"  {pdf.name}: {pm['page_count']} pages, {sum(p['is_scan'] for p in pm['pages'])} scan(s), "
          f"outline entries {len(pm['outline'])}, page map {'from cache' if pm.get('from_cache') else 'built'}")
    for g in GROUPS:
        hits = prep["located"][g]
        where = ", ".join(f"p{h['page']} ({h['score']})" for h in hits) if hits else "not found (model would pick from the page map)"
        print(f"      {g:<10} {where}")
    print(f"      would send pages {shortlist(prep['located'])}")
    for line in hints_to_text(prep["hints"]).splitlines()[1:]:
        print(f"      hint {line[2:]}")
    for t in prep["tables"]:
        v = t["verification"]
        status = "VERIFIED" if v["verified"] else "not verified"
        print(f"      table p{t['page']}#{t['index'] + 1}: {len(t['rows'])} rows, {status} {v['columns']}")
    budget = find_partner_budget(prep["tables"])
    if budget:
        print(f"      partner budget: page {budget['page']}, column {budget['header']!r}, "
              f"{len(budget['partners'])} partners, total {budget['total_text']!r}")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--mode", choices=MODES, required=True)
    ap.add_argument("--input", required=True, help="a .pdf file or a folder of .pdf files")
    ap.add_argument("--output", default="output")
    ap.add_argument("--dry-run", action="store_true", help="steps 1 to 3 only (page map, locate, tables); no network, no token")
    args = ap.parse_args(argv)

    path = Path(args.input)
    files = [path] if path.is_file() else sorted(path.glob("*.pdf"))
    if not files:
        raise SystemExit(f"no .pdf files found in {args.input}")

    if args.dry_run:
        for pdf in files:
            _print_dry_run(pdf, prepare(pdf))
        return

    try:
        token = get_token()
        verify_token(token)
    except BackendError as exc:
        raise SystemExit(f"error: {exc}")

    out_dir = Path(args.output) / f"targeted_{args.mode}"
    failures = 0
    for pdf in files:
        run = run_one_targeted(pdf, out_dir, args.mode, token, datetime.now(timezone.utc))
        if run["status"] == "ok":
            print(f"  {pdf.name}: ok  pages {run['pages_sent']} of {run['pages_total']}  {run['seconds']}s  "
                  f"{run['prompt_tokens']}+{run['completion_tokens']} tokens  ${run['cost_usd']}  "
                  f"{run['tables_verified']}/{run['tables_found']} tables verified  {len(run['warnings'])} warning(s)")
            for w in run["warnings"]:
                print(f"      ! {w}")
        else:
            failures += 1
            print(f"  {pdf.name}: FAILED  {run['error']}")
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
