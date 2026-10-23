"""Direct PDF -> JSON extraction using a vision-capable model, bypassing Markdown conversion.

The PDF's pages are rendered to images and sent in batches (not all in one call - a
single request with every page tipped real multi-page documents over the router's
request-size limit, HTTP 413, even after lowering image resolution). Each batch
produces its own partial extraction; merge_raw_dicts combines them before the shared
Markdown-pipeline logic (clic_extract.schema / .postprocess / .prompts) runs once on
the combined result, so results stay directly comparable and flow into the same
review/approve/save step in app/viewer.py.

Grounding checks (does this value appear verbatim in the source text?) are skipped for
this path: there is no text version of the document, only images - see
postprocess.build_final's document_text=None handling.
"""

from __future__ import annotations

import base64
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import fitz  # pymupdf

from .backends import BackendError, chat
from .fit import is_too_large, merge_raw_dicts, split_text
from .postprocess import build_final, extract_json
from .prompts import COMBINED_VISION_SYSTEM_PROMPT, OPEN_VISION_SYSTEM_PROMPT, VISION_SYSTEM_PROMPT
from .run_extract import write_replies
from .schema import RAW_SCHEMA, validate_final

# Used for the "open" path (strict=False): no response_format constraint, so the model
# can reason in prose before writing JSON. That reasoning needs real room, on top of the
# JSON itself, hence the higher ceiling than the strict arms' 3000.
OPEN_MAX_TOKENS = 6000

# Changed 2026-10-12: DeepSeek-V4.1-Flash (picked 2026-10-11) correctly read only 1 of
# 30 partner amounts on a real document, even after fixing resolution and batch-boundary
# table splits. "Flash" is that model's fast/cheap tier, not its strongest. Switched to
# Qwen's largest vision-language model on the router instead: a dedicated VL line (tuned
# for document/image understanding specifically), not a general-purpose multimodal model
# where vision is secondary. Confirmed live, structured-output supported. See
# PIPELINE_SUMMARY.md section 12.
VISION_MODEL: dict[str, Any] = {
    "model": "Qwen/Qwen3-VL-235B-A22B-Instruct",
    "provider": "deepinfra",
    "role": "multimodal, direct from PDF",
    "max_tokens": 3000,
    "context_length": 262_144,
    "input_per_m": 0.20,
    "output_per_m": 0.88,
}

DEFAULT_BATCH_SIZE = 10
DEFAULT_BATCH_OVERLAP = 1

# "Combined" path (see build_combined_messages / run_one_combined): one request carries the
# document's text AND every page image together, the way a general-purpose provider's own chat
# interface receives a PDF - no batching, no merge step. Two models, picked from the HF router's
# live model list (architecture.input_modalities includes "image") on 2026-10-14:
#   qwen_vl        - the same model already used by the batched path above, for continuity.
#   llama4_maverick - the strongest vision-capable model with known pricing found on the router;
#                     1,048,576-token context (by far the largest available), a large MoE model
#                     widely regarded as one of the closer open alternatives to the proprietary
#                     frontier models (GPT-4o/Claude/Gemini class), though not reaching their
#                     benchmarked accuracy. Does not support strict structured output on this
#                     router, so both models use the same unconstrained, reason-then-JSON prompt
#                     for a fair comparison between them.
COMBINED_MODELS: dict[str, dict[str, Any]] = {
    "qwen_vl": {
        "model": "Qwen/Qwen3-VL-235B-A22B-Instruct",
        "provider": "deepinfra",
        "label": "Qwen3-VL-235B-A22B (already used in the batched multimodal path)",
        "max_tokens": OPEN_MAX_TOKENS,
        "context_length": 262_144,
        "input_per_m": 0.20,
        "output_per_m": 0.88,
    },
    "llama4_maverick": {
        "model": "meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8",
        "provider": "novita",
        "label": "Llama 4 Maverick (large MoE, the closest capability available here to a frontier model)",
        "max_tokens": OPEN_MAX_TOKENS,
        "context_length": 1_048_576,
        "input_per_m": 0.27,
        "output_per_m": 0.85,
    },
}


def render_pdf_pages(pdf_path: Path, zoom: float = 2.0, page_indices: list[int] | None = None) -> list[bytes]:
    """Render PDF pages to PNG bytes, in page order. page_indices=None renders every page
    (0-indexed); a list renders only those pages - see pages_needing_visual_check.

    zoom=2.0 (~144 DPI): zoom=1.0 (~72 DPI) was tried first to shrink the request that
    was tripping HTTP 413, but a real run at that resolution correctly read only 1 of
    30 partner amounts - the model could read some small table text, not reliably.
    Batching (see chunk_pages) turned out to be what actually fixes request size, which
    freed up room to raise resolution back up for legibility. PNG was kept over JPEG:
    for this flat-background, high-contrast text content, PNG's lossless compression
    measured smaller than JPEG's lossy compression at every zoom level tried.
    """
    images = []
    doc = fitz.open(pdf_path)
    try:
        matrix = fitz.Matrix(zoom, zoom)
        indices = range(doc.page_count) if page_indices is None else page_indices
        for i in indices:
            pix = doc[i].get_pixmap(matrix=matrix)
            images.append(pix.tobytes("png"))
    finally:
        doc.close()
    return images


def pages_needing_visual_check(pdf_path: Path) -> list[int]:
    """0-indexed pages likely to contain a table, chart or other visual content that plain
    text extraction would not reliably capture - detected cheaply via pymupdf, no model calls.

    A page qualifies if it has at least one embedded raster image (a photo, a scanned stamp, a
    chart saved as a picture - text extraction cannot see inside these at all) or page.find_tables()
    detects a real table. find_tables() (pymupdf's own table-structure detector, not a count-based
    guess) was chosen over a cheaper proxy - counting vector drawing primitives - after that proxy
    was tried on a real 38-page proposal and flagged nearly every content page (80-336 "drawings"
    each), because ordinary document formatting (bullet points, underlines, section-divider rules)
    produces plenty of small vector shapes with no table anywhere nearby; it cannot tell a real
    table from a bulleted list. find_tables() needs actual text arranged in a grid, not just drawn
    lines, so it does not fire on decorative formatting. On that same real document it agreed with
    the drawing-count proxy's result (30 of 38 pages) - this document genuinely has tables spread
    across most of its content pages - but it will not be fooled on a document that merely looks
    busy. It costs real time (6.2s on that 38-page document, all pages) - still negligible next to
    rendering and the model calls themselves, and nothing close to docling's 278-318s.

    Used by run_one_combined to render and send images only for these pages instead of every page
    - the request's image payload (the dominant cost behind HTTP 413, see run_one_combined's
    docstring) scales with how many pages actually need visual reading, not with document length.
    A document with no qualifying pages sends no images at all: a single fast text-only call,
    since there is nothing for the images to add in that case.
    """
    doc = fitz.open(pdf_path)
    try:
        return [i for i, page in enumerate(doc) if page.get_images() or page.find_tables().tables]
    finally:
        doc.close()


def extract_native_text(pdf_path: Path) -> str:
    """Plain embedded-text extraction, page by page - no OCR, no layout model, no docling at
    all. Near-instant (milliseconds) regardless of document length, unlike docling's layout and
    table-structure analysis, which measured 278-318s on a real 38-page proposal even with OCR
    correctly skipped.

    Deliberately used instead of docling for the combined path (see run_one_combined): the model
    receives the real page images in the same request anyway, so it can read a table directly
    from the image even though this plain extraction does not preserve table layout the way
    docling's markdown export does. That trade - a text component with no table structure, for a
    text component that costs nothing - is the right one here specifically because the images
    are already doing the table-reading work. This mirrors the comparison this path was built to
    be closer to: a general-purpose chat interface's own PDF handling pulls out the embedded text
    layer directly, the same cheap way, rather than running its own layout analysis locally.
    """
    doc = fitz.open(pdf_path)
    try:
        return "\n\n".join(f"<!-- page {i + 1} -->\n\n{page.get_text()}" for i, page in enumerate(doc))
    finally:
        doc.close()


def chunk_pages(
    page_images: list[bytes], batch_size: int, overlap: int = 0
) -> list[list[bytes]]:
    """Split pages into batches, each one overlapping the previous by `overlap` pages.

    Plain non-overlapping chunks can cut a table that spans a page boundary in half:
    one batch sees the header row, the next sees only continuation rows with no header
    to anchor them to, and the model can mention names without matching amounts to
    either. A 1-page overlap means any table spanning two adjacent pages is fully
    visible within at least one batch.
    """
    if batch_size < 1:
        raise ValueError("batch_size must be at least 1")
    if overlap < 0:
        raise ValueError("overlap must be >= 0")
    if overlap >= batch_size:
        raise ValueError("overlap must be smaller than batch_size")

    step = batch_size - overlap
    n = len(page_images)
    batches = []
    i = 0
    while i < n:
        batches.append(page_images[i:i + batch_size])
        if i + batch_size >= n:
            break
        i += step
    return batches


def build_multimodal_messages(page_images: list[bytes], strict: bool = True) -> list[dict]:
    """Same field definitions as the Markdown pipeline; the document is page images, not text.

    strict=True: the usual prompt, paired with a strict response_format at the API level.
    strict=False: the "open" prompt, which invites reasoning in prose before the final JSON
    block - paired with no response_format constraint at all (see run_one_multimodal).
    """
    content: list[dict] = [
        {"type": "text", "text": "Extract the data from this document. Each image is one page, in order."}
    ]
    for png_bytes in page_images:
        b64 = base64.b64encode(png_bytes).decode("ascii")
        content.append({"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}})
    system_prompt = VISION_SYSTEM_PROMPT if strict else OPEN_VISION_SYSTEM_PROMPT
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": content},
    ]


# merge_raw_dicts now lives in clic_extract.fit (shared with the text paths) and is imported above.


def run_one_multimodal(
    pdf_path: Path,
    out_dir: Path,
    token: str,
    now: datetime | None = None,
    batch_size: int = DEFAULT_BATCH_SIZE,
    overlap: int = DEFAULT_BATCH_OVERLAP,
    strict: bool = True,
) -> dict:
    """Render pdf_path's pages, extract batch by batch via VISION_MODEL, merge, validate,
    and write outputs.

    strict=True: the usual path - response_format enforces RAW_SCHEMA at decoding time.
    strict=False: the "open" path - no response_format at all (schema=None), paired with
    OPEN_VISION_SYSTEM_PROMPT, which invites working through the table in prose before
    the final JSON block. Tries whether the strict constraint itself, not the model, is
    what is costing accuracy on a given document - see PIPELINE_SUMMARY.md section 12.

    Mirrors run_extract.run_one's file conventions (<stem>_<UTC>.json / .run.json /
    .raw.txt) so both pipelines' outputs sit side by side and are told apart only by arm.
    One batch failing (bad reply, network error) does not fail the whole run - it is
    recorded as a warning and the remaining batches still contribute. A batch that fails
    specifically with HTTP 413 (request too large) is split in half and each half retried
    instead of abandoned outright - on a real document, the very first batch hit 413 and was
    simply dropped every run, silently missing from every result, until this was added.
    """
    # "seconds" (accumulated below, one chat() call per batch) times only the model calls.
    # "total_seconds" is true wall-clock time for this whole function - rendering every page
    # to an image, chunking into batches, every call, and merging - the part "seconds" alone
    # leaves out. Neither one includes converting a PDF to Markdown, since this path never
    # does that at all (see this function's own docstring: no Markdown conversion step).
    started_monotonic = time.monotonic()
    pdf_path = Path(pdf_path)
    now = now or datetime.now(timezone.utc)
    stamp = now.strftime("%Y%m%dT%H%M%SZ")
    base = out_dir / f"{pdf_path.stem}_{stamp}"
    arm = dict(VISION_MODEL) if strict else {**VISION_MODEL, "max_tokens": OPEN_MAX_TOKENS}
    run: dict[str, Any] = {
        "arm": "multimodal_strict" if strict else "multimodal_open",
        "strict": strict,
        "model": arm["model"],
        "provider": arm["provider"],
        "source_file": pdf_path.name,
        "started_utc": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "status": "failed",
        "error": None,
        "warnings": [],
        "batch_size": batch_size,
        "overlap": overlap,
        "batches": 0,
        "seconds": 0.0,
        "attempts": 0,
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "cost_usd": 0.0,
        "finish_reason": None,
        "model_reported": None,
    }
    replies: list[str] = []

    def finish(error: str | None = None, raw_text: str | None = None) -> dict:
        if error:
            run["error"] = error
        if raw_text is not None:
            base.with_suffix(".raw.txt").write_text(raw_text, encoding="utf-8")
        write_replies(base, replies, run)
        run["total_seconds"] = round(time.monotonic() - started_monotonic, 2)
        base.with_suffix(".run.json").write_text(json.dumps(run, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        return run

    try:
        page_images = render_pdf_pages(pdf_path)
    except Exception as exc:  # noqa: BLE001 - surfaced to the user as a run failure, not raised
        return finish(f"could not render PDF pages: {exc}")

    if not page_images:
        return finish("PDF has no pages")

    batches = chunk_pages(page_images, batch_size, overlap)
    run["batches"] = len(batches)

    raw_results: list[dict] = []
    raw_texts: list[str] = []
    schema = RAW_SCHEMA if strict else None
    # A batch that hits HTTP 413 (request too large - a transport-layer byte limit, unrelated
    # to the model's own context window) is split in half and each half retried on its own,
    # rather than abandoned outright - see run_one_combined's docstring for the full reasoning.
    # Abandoning it silently (the previous behaviour here) meant that batch's pages never
    # contributed anything to the final result at all, every time, on a real document that
    # happened to trip the limit on its first batch.
    worklist: list[list[bytes]] = list(batches)
    while worklist:
        batch = worklist.pop(0)
        messages = build_multimodal_messages(batch, strict=strict)
        try:
            result = chat(arm, messages, schema, token, use_extras=True)
        except BackendError as exc:
            if is_too_large(exc) and len(batch) > 1:
                mid = len(batch) // 2
                worklist.insert(0, batch[mid:])
                worklist.insert(0, batch[:mid])
                reason = "413" if "413" in str(exc) else "context length"
                run["warnings"].append(
                    f"a {len(batch)}-page batch was too large ({reason}); split into "
                    f"{mid} and {len(batch) - mid} pages and retrying"
                )
            else:
                run["warnings"].append(f"a {len(batch)}-page batch failed: {exc}")
            continue

        replies.append(result["content"] or "")
        run["seconds"] = round(run["seconds"] + result["seconds"], 2)
        run["attempts"] += result["attempts"]
        run["prompt_tokens"] += result["prompt_tokens"] or 0
        run["completion_tokens"] += result["completion_tokens"] or 0
        run["cost_usd"] = round(run["cost_usd"] + (result["cost_usd"] or 0), 6)
        run["finish_reason"] = result["finish_reason"]
        run["model_reported"] = result["model_reported"]
        if result["finish_reason"] == "length":
            run["warnings"].append(f"a {len(batch)}-page batch's reply was cut off (raise max_tokens)")

        try:
            raw = extract_json(result["content"])
        except (ValueError, json.JSONDecodeError) as exc:
            run["warnings"].append(f"a {len(batch)}-page batch's reply is not valid JSON: {exc}")
            raw_texts.append(f"=== batch of {len(batch)} page(s) ===\n{result['content'] or ''}")
            continue

        raw_results.append(raw)

    combined_raw_text = "\n\n".join(raw_texts) if raw_texts else None
    if not raw_results:
        return finish("no batch produced a valid reply", raw_text=combined_raw_text)

    merged_raw = merge_raw_dicts(raw_results)
    final, warnings = build_final(merged_raw, None, pdf_path.name, now)
    run["warnings"].extend(warnings)
    problems = validate_final(final)
    if problems:
        return finish("final document failed validation: " + "; ".join(problems), raw_text=combined_raw_text)

    base.with_suffix(".json").write_text(json.dumps(final, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    run["status"] = "ok"
    run["output_file"] = base.with_suffix(".json").name
    return finish()


def build_combined_messages(document_text: str, page_images: list[bytes]) -> list[dict]:
    """One user turn carrying the document's full text plus one batch's page images, in page
    order. Called once per batch by run_one_combined - document_text is the same on every call,
    only page_images changes, so every batch still gets the full text alongside its own images."""
    content: list[dict] = [
        {
            "type": "text",
            "text": (
                "Here is the document's text, extracted with layout analysis:\n\n"
                "<document_text>\n" + document_text + "\n</document_text>\n\n"
                "Below are the same document's pages rendered as images, in page order. Use the "
                "text as your primary source, and check the images directly for anything the text "
                "extraction may have missed or gotten wrong."
            ),
        }
    ]
    for png_bytes in page_images:
        b64 = base64.b64encode(png_bytes).decode("ascii")
        content.append({"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}})
    return [
        {"role": "system", "content": COMBINED_VISION_SYSTEM_PROMPT},
        {"role": "user", "content": content},
    ]


def run_one_combined(
    pdf_path: Path,
    document_text: str,
    out_dir: Path,
    model_key: str,
    token: str,
    now: datetime | None = None,
    batch_size: int = DEFAULT_BATCH_SIZE,
    overlap: int = DEFAULT_BATCH_OVERLAP,
) -> dict:
    """Text-and-images-together extraction, batched automatically and transparently.

    Images are sent only for pages pages_needing_visual_check flags as likely containing a
    table, chart or other visual content - not every page. A document with no qualifying pages
    gets a single text-only call; the images (the dominant cost behind HTTP 413, see below, and
    the dominant cost in tokens/pricing) scale with how much of the document is actually visual,
    not with page count.

    `document_text` is expected to come from extract_native_text, not docling: docling's layout
    and table-structure analysis measured 278-318s on a real 38-page proposal even with OCR
    correctly skipped, which made this path take 7-9 minutes end to end for no real benefit -
    the model sees the actual page images in the same request anyway, so a nicely table-
    structured text component is not worth minutes of local preprocessing here. This also
    matches the comparison this path was built against more closely: a general-purpose chat
    interface's own PDF handling pulls the embedded text layer out directly and cheaply, it does
    not run its own local layout-analysis model first.

    A single request carrying the full document's text plus every page image reliably hit a
    provider's inbound request-size limit (HTTP 413) on real multi-page proposals. This is a
    transport-layer byte limit the provider's gateway enforces before the request even reaches
    the model, completely independent of the model's own context window - Llama 4 Maverick's
    1,048,576-token context does not help here, since a 413 happens before any tokens are
    counted at all. Starting at batch_size=10/overlap=1 (same as run_one_multimodal, the proven
    images-only path - most batches have no size problem at all, since images, not the resent
    text, dominate request bytes); a batch that still gets a 413 is split in half and each half
    retried on its own (recursively, if a half is still too large), rather than shrinking every
    batch up front - a real run that hit 413 on 2 of 5 batches at batch_size=10 would otherwise
    have had its other 3, already-fine batches needlessly fragmented into more, smaller, more
    expensive calls for no reason. Grounding checks in build_final still run normally, since
    real text is available either way. The user never sees or sets any of this.

    Outputs follow the same <stem>_<UTC>.json / .run.json / .raw.txt convention as run_one and
    run_one_multimodal, so this path plugs into the same review/approve/save flow unmodified.

    "seconds" (accumulated below, one chat() call per batch) times only the model calls.
    "total_seconds" is true wall-clock time for this whole function - pages_needing_visual_check
    (table detection), rendering the flagged pages, chunking, every call, and merging. Neither
    one includes extracting `document_text` itself, since that happens before this function is
    called and is shared across both combined models if both are run on the same document.
    """
    started_monotonic = time.monotonic()
    pdf_path = Path(pdf_path)
    now = now or datetime.now(timezone.utc)
    stamp = now.strftime("%Y%m%dT%H%M%SZ")
    base = out_dir / f"{pdf_path.stem}_{stamp}"
    arm = dict(COMBINED_MODELS[model_key])
    run: dict[str, Any] = {
        "arm": f"multimodal_combined_{model_key}",
        "model": arm["model"],
        "provider": arm["provider"],
        "source_file": pdf_path.with_suffix(".md").name,
        "started_utc": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "status": "failed",
        "error": None,
        "warnings": [],
        "batch_size": batch_size,
        "overlap": overlap,
        "pages_total": 0,
        "pages_with_images": 0,
        "batches": 0,
        "calls": 0,
        "seconds": 0.0,
        "attempts": 0,
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "cost_usd": 0.0,
        "finish_reason": None,
        "model_reported": None,
    }
    replies: list[str] = []

    def finish(error: str | None = None, raw_text: str | None = None) -> dict:
        if error:
            run["error"] = error
        if raw_text is not None:
            base.with_suffix(".raw.txt").write_text(raw_text, encoding="utf-8")
        write_replies(base, replies, run)
        run["total_seconds"] = round(time.monotonic() - started_monotonic, 2)
        base.with_suffix(".run.json").write_text(json.dumps(run, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        return run

    try:
        probe = fitz.open(pdf_path)
        total_pages = probe.page_count
        probe.close()
    except Exception as exc:  # noqa: BLE001 - surfaced as a run failure, not raised
        return finish(f"could not open PDF: {exc}")
    if total_pages == 0:
        return finish("PDF has no pages")
    run["pages_total"] = total_pages

    try:
        flagged_pages = pages_needing_visual_check(pdf_path)
    except Exception as exc:  # noqa: BLE001
        return finish(f"could not inspect PDF pages: {exc}")
    run["pages_with_images"] = len(flagged_pages)

    try:
        page_images = render_pdf_pages(pdf_path, page_indices=flagged_pages) if flagged_pages else []
    except Exception as exc:  # noqa: BLE001
        return finish(f"could not render PDF pages: {exc}")

    # No page needs visual reading at all: one fast, text-only call instead of forcing an
    # empty image batch through the usual rendering path for no reason.
    batches = chunk_pages(page_images, batch_size, overlap) if page_images else [[]]
    run["batches"] = len(batches)

    raw_results: list[dict] = []
    raw_texts: list[str] = []
    # Each work item is (text, images). A request rejected as too large is split: first its images
    # in half; once a single image is left, the text itself in half (clic_extract.fit.split_text),
    # each half keeping that image. A document that fits is never split.
    worklist: list[tuple[str, list[bytes]]] = [(document_text, b) for b in batches]
    run["context_splits"] = 0
    while worklist:
        text_part, batch = worklist.pop(0)
        messages = build_combined_messages(text_part, batch)
        try:
            result = chat(arm, messages, None, token, use_extras=True)
        except BackendError as exc:
            reason = "413" if "413" in str(exc) else "context length"
            halves = split_text(text_part) if is_too_large(exc) and len(batch) <= 1 else None
            if is_too_large(exc) and len(batch) > 1:
                mid = len(batch) // 2
                worklist[0:0] = [(text_part, batch[:mid]), (text_part, batch[mid:])]
                run["warnings"].append(
                    f"a {len(batch)}-page batch was too large ({reason}); split into "
                    f"{mid} and {len(batch) - mid} pages and retrying"
                )
            elif halves is not None:
                worklist[0:0] = [(halves[0], batch), (halves[1], batch)]
                run["context_splits"] += 1
                run["warnings"].append(
                    f"a request with {len(batch)} page image(s) and {len(text_part)} characters of text was too "
                    f"large ({reason}); text split into {len(halves[0])} and {len(halves[1])} characters"
                )
            else:
                run["warnings"].append(f"a {len(batch)}-page batch failed: {exc}")
            continue

        replies.append(result["content"] or "")
        run["calls"] += 1
        run["seconds"] = round(run["seconds"] + result["seconds"], 2)
        run["attempts"] += result["attempts"]
        run["prompt_tokens"] += result["prompt_tokens"] or 0
        run["completion_tokens"] += result["completion_tokens"] or 0
        run["cost_usd"] = round(run["cost_usd"] + (result["cost_usd"] or 0), 6)
        run["finish_reason"] = result["finish_reason"]
        run["model_reported"] = result["model_reported"]
        if result["finish_reason"] == "length":
            run["warnings"].append(f"a {len(batch)}-page batch's reply was cut off (raise max_tokens)")

        try:
            raw = extract_json(result["content"])
        except (ValueError, json.JSONDecodeError) as exc:
            run["warnings"].append(f"a {len(batch)}-page batch's reply is not valid JSON: {exc}")
            raw_texts.append(f"=== batch of {len(batch)} page(s) ===\n{result['content'] or ''}")
            continue

        raw_results.append(raw)

    combined_raw_text = "\n\n".join(raw_texts) if raw_texts else None
    if not raw_results:
        return finish("no batch produced a valid reply", raw_text=combined_raw_text)

    merged_raw = merge_raw_dicts(raw_results)
    final, warnings = build_final(merged_raw, document_text, pdf_path.name, now)
    run["warnings"].extend(warnings)
    problems = validate_final(final)
    if problems:
        return finish("final document failed validation: " + "; ".join(problems), raw_text=combined_raw_text)

    base.with_suffix(".json").write_text(json.dumps(final, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    run["status"] = "ok"
    run["output_file"] = base.with_suffix(".json").name
    return finish()
