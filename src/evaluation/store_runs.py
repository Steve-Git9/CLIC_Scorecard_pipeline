"""Store extraction runs in the pipeline layer of the database (sql/schema.sql, version 2).

For every run: one extraction_run row; one extraction_call row per model call (failed calls
included) with the provider's usage object and the reply exactly as returned; one call_attempt
row per HTTP attempt; the final record's values as extracted_value rows; and every pipeline
warning, plus the final schema check, as validation_result rows. Documents, their Docling
conversions, configurations and batches are registered the first time they are seen.

Amounts stay integers: cents for proposal amounts, millionths of a US dollar for API cost.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import fitz  # pymupdf

from src.evaluation.configurations import describe


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _micros(usd: float | None) -> int | None:
    return None if usd is None else round(usd * 1_000_000)


def _ms(seconds: float | None) -> int | None:
    return None if seconds is None else round(seconds * 1000)


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def ensure_document(conn: sqlite3.Connection, pdf_path: Path) -> int:
    content_hash = file_sha256(pdf_path)
    row = conn.execute("SELECT document_id FROM document WHERE content_hash = ?", (content_hash,)).fetchone()
    if row:
        return row[0]
    with fitz.open(pdf_path) as doc:
        pages = doc.page_count
    cur = conn.execute(
        "INSERT INTO document (file_name, content_hash, page_count, storage_path, received_at, status) "
        "VALUES (?, ?, ?, ?, ?, 'converted')",
        (Path(pdf_path).name, content_hash, pages, str(pdf_path), _now()))
    return cur.lastrowid


def ensure_conversion(conn: sqlite3.Connection, document_id: int, record: dict[str, Any]) -> int:
    """The Docling conversion of a document, from its <document>.conversion.json record."""
    row = conn.execute("SELECT conversion_id FROM conversion_run WHERE document_id = ? AND markdown_path = ? "
                       "AND created_at = ?", (document_id, record["markdown_file"], record["started_utc"])).fetchone()
    if row:
        return row[0]
    cur = conn.execute(
        "INSERT INTO conversion_run (document_id, method, tool, tool_version, pages_ocr, markdown_path, "
        "duration_ms, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (document_id, "ocr" if record.get("ocr_used") else "native", record.get("tool", "docling"),
         record.get("docling_version"), record["pages"] if record.get("ocr_used") else 0,
         record["markdown_file"], _ms(record["total_seconds"]), record["started_utc"]))
    return cur.lastrowid


def ensure_model_config(conn: sqlite3.Connection, name: str, prices: dict) -> int:
    d = describe(name)
    parameters = json.dumps({k: v for k, v in d.items() if k not in ("config_name", "prompt_version")},
                            sort_keys=True)
    row = conn.execute("SELECT config_id FROM model_config WHERE config_name = ? AND prompt_version = ? "
                       "AND parameters = ?", (name, d["prompt_version"], parameters)).fetchone()
    if row:
        return row[0]
    price = prices.get((d["provider"], d["model"])) or {}

    def per_mtok(key: str) -> int | None:
        return _micros(price.get(key)) if price.get(key) is not None else None

    cur = conn.execute(
        "INSERT INTO model_config (config_name, model_name, provider, is_local, prompt_version, parameters, "
        "price_in_usd_micros_mtok, price_cached_usd_micros_mtok, price_out_usd_micros_mtok, "
        "price_retrieved_on, created_at) VALUES (?, ?, ?, 0, ?, ?, ?, ?, ?, ?, ?)",
        (name, d["model"], d["provider"], d["prompt_version"], parameters, per_mtok("input_per_million"),
         per_mtok("cached_input_per_million"), per_mtok("output_per_million"), price.get("retrieved_on"), _now()))
    return cur.lastrowid


def ensure_batch(conn: sqlite3.Connection, manifest: dict[str, Any], manifest_path: Path) -> None:
    conn.execute(
        "INSERT INTO run_batch (batch_id, run_kind, code_commit, code_dirty, prompt_versions, price_file, "
        "price_file_sha256, price_retrieved_on, manifest_path, started_at, ended_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) "
        "ON CONFLICT (batch_id) DO UPDATE SET ended_at = excluded.ended_at",
        (manifest["batch_id"], manifest["run_kind"], manifest["code"]["commit"], int(manifest["code"]["dirty"]),
         json.dumps(manifest["prompt_versions"], sort_keys=True), manifest["prices"]["file"],
         manifest["prices"]["sha256"], json.dumps(manifest["prices"]["retrieved_on"], sort_keys=True),
         str(manifest_path), manifest["started_utc"], manifest.get("ended_utc")))


def _read(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else None


def _values(final: dict[str, Any]) -> list[tuple[str, int, str, str | None]]:
    rows = []
    for section in ("proposal", "proposal_facts"):
        for field, value in (final.get(section) or {}).items():
            rows.append(("proposal", 0, field, None if value is None else str(value)))
    for i, partner in enumerate(final.get("partners") or []):
        for field, value in partner.items():
            rows.append(("participation", i, field, None if value is None else str(value)))
    return rows


def store_run(conn: sqlite3.Connection, run_file: Path, *, batch_id: str | None, run_kind: str,
              config_name: str, document_id: int, conversion_id: int | None, prices: dict,
              repetition: int | None, slot_attempt: int = 1) -> int:
    """Insert one run and everything it produced. Returns the run_id."""
    run = _read(run_file)
    ev = run.get("evaluation") or {}
    base = run_file.with_name(run_file.name[: -len(".run.json")])
    final_path = base.with_name(base.name + ".json")
    raw_path = base.with_name(base.name + ".raw.txt")
    tokens = ev.get("tokens") or {}
    config_id = ensure_model_config(conn, config_name, prices)
    if slot_attempt > 1:  # the earlier attempts of this slot no longer count
        conn.execute("UPDATE extraction_run SET is_final = 0 WHERE batch_id IS NOT DISTINCT FROM ? AND config_id IN "
                     "(SELECT config_id FROM model_config WHERE config_name = ?) AND document_id = ? "
                     "AND repetition = ?", (batch_id, config_name, document_id, repetition))
    cur = conn.execute(
        "INSERT INTO extraction_run (batch_id, document_id, conversion_id, config_id, run_kind, input_kind, "
        "repetition, slot_attempt, is_final, status, error, started_at, duration_ms, end_to_end_ms, model_ms, "
        "calls, failed_calls, http_attempts, retries, context_splits, tokens_in, tokens_out, tokens_reasoning, "
        "tokens_image, tokens_cached, cost_usd_micros, schema_valid, run_file_path, output_path, replies_path, "
        "raw_output_path) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, "
        "?, ?, ?, ?)",
        (batch_id, document_id, conversion_id, config_id, run_kind, describe(config_name)["input_kind"],
         repetition, slot_attempt, run["status"], run.get("error"), run["started_utc"],
         _ms(run.get("total_seconds")), _ms(ev.get("end_to_end_seconds")), _ms(run.get("seconds")),
         ev.get("calls"), ev.get("failed_calls"), ev.get("attempts"), ev.get("retries"),
         run.get("context_splits") or 0, tokens.get("prompt_tokens"), tokens.get("completion_tokens"),
         tokens.get("reasoning_tokens"), tokens.get("image_tokens"), tokens.get("cached_tokens"),
         _micros((ev.get("cost") or {}).get("cost_usd")), int(run["status"] == "ok" and final_path.is_file()),
         str(run_file), str(final_path) if final_path.is_file() else None,
         str(base.with_name(base.name + ".replies.json")), str(raw_path) if raw_path.is_file() else None))
    run_id = cur.lastrowid

    for index, call in enumerate(ev.get("call_log") or [], start=1):
        c = conn.execute(
            "INSERT INTO extraction_call (run_id, call_index, purpose, ok, error, model_name, provider, "
            "model_reported, response_format, request_bytes, duration_ms, prompt_tokens, completion_tokens, "
            "reasoning_tokens, image_tokens, cached_tokens, cost_usd_micros, finish_reason, usage_json, reply_text, "
            "reasoning_text) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (run_id, index, call["purpose"], int(call["ok"]), call.get("error"), call["model"], call["provider"],
             call.get("model_reported"), int(call["response_format"]), call.get("request_bytes"),
             _ms(call.get("seconds")), call.get("prompt_tokens"), call.get("completion_tokens"),
             call.get("reasoning_tokens"), call.get("image_tokens"), call.get("cached_tokens"),
             _micros(call.get("cost_usd")), call.get("finish_reason"),
             json.dumps(call["usage"]) if call.get("usage") is not None else None,
             call.get("reply"), call.get("reasoning")))
        for attempt in call.get("attempts") or []:
            conn.execute("INSERT INTO call_attempt (call_id, attempt_no, http_status, error, duration_ms) "
                         "VALUES (?, ?, ?, ?, ?)", (c.lastrowid, attempt["attempt"], attempt.get("http_status"),
                                                    attempt.get("error"), _ms(attempt.get("seconds"))))

    final = _read(final_path)
    if final:
        conn.executemany("INSERT INTO extracted_value (run_id, target_entity, item_index, field_name, value_text) "
                         "VALUES (?, ?, ?, ?, ?)", [(run_id, *row) for row in _values(final)])
    created = _now()
    conn.execute("INSERT INTO validation_result (run_id, rule_code, passed, severity, message, created_at) "
                 "VALUES (?, 'final_schema', ?, 'error', ?, ?)",
                 (run_id, int(final is not None), None if final else run.get("error"), created))
    conn.executemany("INSERT INTO validation_result (run_id, rule_code, passed, severity, message, created_at) "
                     "VALUES (?, 'pipeline_warning', 0, 'warning', ?, ?)",
                     [(run_id, w, created) for w in run.get("warnings") or []])
    return run_id
