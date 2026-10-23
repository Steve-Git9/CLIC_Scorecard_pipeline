"""Tests for the pipeline layer version 2, storing runs, and the batch runner's rules.
FICTIONAL TEST DATA ONLY: documents, partners, amounts and replies below are invented."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from src.evaluation import run_batch
from src.evaluation.configurations import CONFIGURATIONS, describe, prompt_versions
from src.evaluation.run_batch import interleaved_schedule, transient_failure
from src.evaluation.store_runs import ensure_conversion, ensure_document, store_run
from src.pipeline.db import get_connection, init_db, migrate_pipeline_v2

FINAL = {
    "proposal": {"proposal_acronym": "FICTO", "proposal_title": "Fictional Test Initiative",
                 "call_identifier": None, "submission_date": "2099-03-15"},
    "proposal_facts": {"requested_total_cents": 300_000_000, "trl_start": 3, "trl_target": 6,
                       "mcrl_start": None, "mcrl_target": None},
    "partners": [{"partner_name": "Imaginary Labs Oy", "requested_cents": 100_000_000},
                 {"partner_name": "Nowhere University", "requested_cents": 200_000_000}],
    "metadata": {"extraction_timestamp": "2099-01-01T00:00:00Z", "source_file": "FICTO.md"},
}


def _call(ok: bool, statuses: list[int | None], reply: str | None = None) -> dict:
    return {"purpose": "extraction", "model": "Qwen/Qwen3.5-9B", "provider": "deepinfra", "response_format": True,
            "request_bytes": 1234, "ok": ok, "error": None if ok else "HTTP 503: fictional outage",
            "attempts": [{"attempt": i + 1, "http_status": s, "error": None if s == 200 else "x", "seconds": 0.5}
                         for i, s in enumerate(statuses)],
            "usage": {"prompt_tokens": 1000, "completion_tokens": 50} if ok else None,
            "prompt_tokens": 1000 if ok else None, "completion_tokens": 50 if ok else None,
            "reasoning_tokens": None, "image_tokens": None, "cached_tokens": None, "seconds": 1.2,
            "finish_reason": "stop" if ok else None, "model_reported": "fictional", "reply": reply,
            "reasoning": None, "cost_usd": 0.00010750 if ok else 0.0}


def write_run(folder: Path, stamp: str, status: str = "ok", warnings: list[str] | None = None) -> Path:
    folder.mkdir(parents=True, exist_ok=True)
    base = folder / f"FICTO_{stamp}"
    calls = [_call(False, [503, 503, 503, 503]), _call(True, [503, 200], reply=json.dumps({"x": 1}))]
    run = {"arm": "B", "status": status, "error": None if status == "ok" else "reply is not valid JSON",
           "warnings": warnings or [], "started_utc": "2099-01-01T00:00:00Z", "seconds": 1.2, "total_seconds": 2.0,
           "context_splits": 0,
           "evaluation": {"end_to_end_seconds": 3.5, "calls": 2, "failed_calls": 1, "attempts": 6, "retries": 4,
                          "tokens": {"prompt_tokens": 1000, "completion_tokens": 50},
                          "cost": {"cost_usd": 0.0001075}, "call_log": calls}}
    (base.parent / (base.name + ".run.json")).write_text(json.dumps(run), encoding="utf-8")
    if status == "ok":
        (base.parent / (base.name + ".json")).write_text(json.dumps(FINAL), encoding="utf-8")
    return base.parent / (base.name + ".run.json")


@pytest.fixture
def db(test_config):
    init_db(test_config)
    conn = get_connection(test_config)
    yield conn
    conn.close()


def test_schema_has_the_version_2_tables(db):
    tables = {r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}
    assert {"run_batch", "model_config", "extraction_run", "extraction_call", "call_attempt"} <= tables


def test_migration_recreates_empty_tables_and_refuses_tables_with_rows(test_config, db, fictional_pdf):
    migrate_pipeline_v2(test_config)
    doc = ensure_document(db, fictional_pdf)
    store_run(db, write_run(fictional_pdf.parent / "B", "20990101T000000Z"), batch_id=None, run_kind="evaluation",
              config_name="B", document_id=doc, conversion_id=None, prices={}, repetition=1)
    db.commit()
    with pytest.raises(RuntimeError, match="holds rows"):
        migrate_pipeline_v2(test_config)
    assert db.execute("SELECT COUNT(*) FROM extraction_run").fetchone()[0] == 1


def test_store_run_keeps_calls_attempts_raw_replies_values_and_warnings(db, fictional_pdf):
    doc = ensure_document(db, fictional_pdf)
    assert ensure_document(db, fictional_pdf) == doc  # registered once
    conv = ensure_conversion(db, doc, {"markdown_file": "data/markdown/FICTO.md", "started_utc": "2099-01-01T00:00:00Z",
                                       "ocr_used": False, "pages": 3, "total_seconds": 12.5,
                                       "docling_version": "0.0.0"})
    prices = {("deepinfra", "Qwen/Qwen3.5-9B"): {"input_per_million": 0.10, "cached_input_per_million": None,
                                                  "output_per_million": 0.15, "retrieved_on": "2099-01-01",
                                                  "status": "verified"}}
    run_id = store_run(db, write_run(fictional_pdf.parent / "B", "20990101T000000Z", warnings=["fictional warning"]),
                       batch_id=None, run_kind="evaluation", config_name="B", document_id=doc,
                       conversion_id=conv, prices=prices, repetition=1)
    run = db.execute("SELECT * FROM extraction_run WHERE run_id = ?", (run_id,)).fetchone()
    assert (run["status"], run["schema_valid"], run["input_kind"], run["retries"]) == ("ok", 1, "markdown", 4)
    assert (run["end_to_end_ms"], run["cost_usd_micros"], run["tokens_in"]) == (3500, 108, 1000)
    calls = db.execute("SELECT * FROM extraction_call WHERE run_id = ? ORDER BY call_index", (run_id,)).fetchall()
    assert [c["ok"] for c in calls] == [0, 1]
    assert calls[1]["reply_text"] == '{"x": 1}' and json.loads(calls[1]["usage_json"])["prompt_tokens"] == 1000
    attempts = db.execute("SELECT http_status FROM call_attempt ORDER BY attempt_id").fetchall()
    assert [a[0] for a in attempts] == [503, 503, 503, 503, 503, 200]
    values = dict(((r[0], r[1], r[2]), r[3]) for r in db.execute(
        "SELECT target_entity, item_index, field_name, value_text FROM extracted_value WHERE run_id = ?", (run_id,)))
    assert values[("proposal", 0, "requested_total_cents")] == "300000000"
    assert values[("participation", 1, "partner_name")] == "Nowhere University"
    assert values[("proposal", 0, "call_identifier")] is None
    rules = [r[0] for r in db.execute("SELECT rule_code FROM validation_result WHERE run_id = ?", (run_id,))]
    assert sorted(rules) == ["final_schema", "pipeline_warning"]
    config = db.execute("SELECT * FROM model_config").fetchone()
    assert (config["config_name"], config["price_in_usd_micros_mtok"], config["price_out_usd_micros_mtok"]) \
        == ("B", 100_000, 150_000)
    assert config["prompt_version"] == describe("B")["prompt_version"]


def test_repeated_slot_supersedes_the_earlier_attempt(db, fictional_pdf):
    doc = ensure_document(db, fictional_pdf)
    first = store_run(db, write_run(fictional_pdf.parent / "B", "20990101T000000Z", status="failed"),
                      batch_id=None, run_kind="evaluation", config_name="B", document_id=doc, conversion_id=None,
                      prices={}, repetition=2)
    second = store_run(db, write_run(fictional_pdf.parent / "B", "20990101T000500Z"), batch_id=None,
                       run_kind="evaluation", config_name="B", document_id=doc, conversion_id=None, prices={},
                       repetition=2, slot_attempt=2)
    finals = dict(db.execute("SELECT run_id, is_final FROM extraction_run").fetchall())
    assert finals == {first: 0, second: 1}
    assert db.execute("SELECT schema_valid FROM extraction_run WHERE run_id = ?", (first,)).fetchone()[0] == 0


def test_provider_failures_are_recognised_and_content_failures_are_not():
    assert transient_failure({"status": "failed", "error": "HTTP 503: down"}) == "HTTP 503: down"
    assert transient_failure({"status": "failed", "error": "network error: timed out"})
    ok_with_failed_batch = {"status": "ok", "evaluation": {"call_log": [{"ok": False, "error": "HTTP 429: slow down"}]}}
    assert transient_failure(ok_with_failed_batch) == "HTTP 429: slow down"
    assert transient_failure({"status": "failed", "error": "reply is not valid JSON"}) is None
    assert transient_failure({"status": "failed", "error": "HTTP 400: bad request"}) is None
    assert transient_failure({"status": "ok", "evaluation": {"call_log": [{"ok": True}]}}) is None


def test_schedule_interleaves_configurations_and_keeps_repetitions_apart():
    schedule = interleaved_schedule(CONFIGURATIONS, ["FICTA", "FICTB"], 3, "fictional-seed")
    assert len(schedule) == 66
    for rep in (1, 2, 3):
        block = schedule[(rep - 1) * 22: rep * 22]
        assert {s["repetition"] for s in block} == {rep}
        assert sorted((s["configuration"], s["document"]) for s in block) == \
            sorted((c, d) for c in CONFIGURATIONS for d in ("FICTA", "FICTB"))
    first = [s["configuration"] for s in schedule[:22]]
    assert first != sorted(first, key=CONFIGURATIONS.index)  # not one configuration after another
    assert schedule == interleaved_schedule(CONFIGURATIONS, ["FICTA", "FICTB"], 3, "fictional-seed")


def test_every_configuration_is_described_with_a_prompt_version():
    versions = prompt_versions()
    assert len(versions["SYSTEM_PROMPT"]) == 64 and "RAW_SCHEMA" in versions
    described = {c: describe(c) for c in CONFIGURATIONS}
    assert len({d["prompt_version"] for d in described.values()}) >= 6
    assert described["freeform_B"]["model"] == described["B"]["model"]
    assert described["targeted_text"]["model"] == described["C"]["model"]


def test_batch_refuses_uncommitted_code(monkeypatch, test_config, tmp_path):
    monkeypatch.setattr(run_batch, "code_version",
                        lambda: {"commit": "abc", "dirty": True, "uncommitted_changes": [" M src/x.py"]})
    with pytest.raises(SystemExit, match="uncommitted changes"):
        run_batch.main(["--new", "--next", "2", "--config", str(tmp_path / "config.yaml")])


def test_a_chunk_runs_every_slot_requeues_provider_failures_and_stores_everything(
        monkeypatch, test_config, db, fictional_pdf, tmp_path):
    test_config.paths.raw.mkdir(parents=True)
    test_config.paths.markdown.mkdir(parents=True)
    for doc in ("FICTA", "FICTB"):
        (test_config.paths.raw / f"{doc}.pdf").write_bytes(fictional_pdf.read_bytes())
        (test_config.paths.markdown / f"{doc}.conversion.json").write_text(json.dumps(
            {"markdown_file": f"md/{doc}.md", "started_utc": "2099-01-01T00:00:00Z", "ocr_used": False,
             "pages": 3, "total_seconds": 1.0, "docling_version": "0.0.0"}), encoding="utf-8")
    # FICTA.pdf and FICTB.pdf are identical bytes, so they register as one document; give B its own bytes
    (test_config.paths.raw / "FICTB.pdf").write_bytes(fictional_pdf.read_bytes() + b"\n%fictional")
    monkeypatch.setattr(run_batch, "REQUEUE_DELAY_SECONDS", 0)
    seen: list[tuple[str, str]] = []

    def fake_run_configuration(key, document, config, out_root, token, prices):
        seen.append((key, document))
        stamp = f"20990101T{len(seen):06d}Z"
        run_file = write_run(out_root / key, stamp)
        run = json.loads(run_file.read_text(encoding="utf-8"))
        provider_down = key == "C" and document == "FICTA" and seen.count(("C", "FICTA")) == 1
        run["status"] = "failed" if provider_down else "ok"
        run["error"] = "HTTP 503: fictional outage" if provider_down else None
        if not provider_down:  # a clean run: only the successful call
            run["evaluation"]["call_log"] = [c for c in run["evaluation"]["call_log"] if c["ok"]]
        run["evaluation"]["run_file"] = str(run_file)
        run_file.write_text(json.dumps(run), encoding="utf-8")
        return run

    monkeypatch.setattr(run_batch, "run_configuration", fake_run_configuration)
    manifest_path = tmp_path / "batch_x" / "manifest.json"
    manifest_path.parent.mkdir()
    manifest = run_batch.new_manifest("batch_x", ["FICTA", "FICTB"], 3,
                                      {"commit": "abc1234", "dirty": False, "uncommitted_changes": []},
                                      {"file": "p.csv", "sha256": "0" * 64, "retrieved_on": {}, "status": {}})
    run_batch.ensure_batch(db, manifest, manifest_path)
    chunk = run_batch.run_chunk(manifest, manifest_path, ["FICTA", "FICTB"], test_config, "hf_fake", {}, db)

    assert len(seen) == 66 + 1  # C on FICTA hit a provider failure once and was repeated later
    assert len(chunk["runs"]) == 67
    assert sum(1 for r in chunk["runs"] if r.get("repeated_later")) == 1
    stored = db.execute("SELECT COUNT(*), SUM(is_final) FROM extraction_run WHERE batch_id = 'batch_x'").fetchone()
    assert tuple(stored) == (67, 66)
    assert db.execute("SELECT COUNT(*) FROM document").fetchone()[0] == 2
    assert db.execute("SELECT COUNT(DISTINCT config_id) FROM extraction_run").fetchone()[0] == 11
    saved = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert saved["chunks"][0]["ended_utc"] and saved["code"]["commit"] == "abc1234"
    assert db.execute("SELECT ended_at FROM run_batch WHERE batch_id = 'batch_x'").fetchone()[0]
