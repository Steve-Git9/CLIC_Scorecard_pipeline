"""Run a batch of extraction runs: every configuration, chosen documents, several repetitions.

    python -m src.evaluation.run_batch --new --next 2           # start a batch, first two documents
    python -m src.evaluation.run_batch --batch <id> --next 2    # the next two documents of that batch
    python -m src.evaluation.run_batch --batch <id> --documents ABC DEF

Results go to evaluation/runs/<batch id>/<configuration>/ and are never overwritten: a batch id
is new for every batch and every run file carries its UTC start time. The manifest
(evaluation/runs/<batch id>/manifest.json) records the code version (git commit, refused if the
working tree has uncommitted changes), the SHA 256 of every prompt and of the schema, the price
file with its digest and retrieval dates, the document order, and per chunk of documents the
interleaved schedule, the start and end time and every run, retries included.

Interleaving: within a chunk, each repetition runs every configuration and document pair in a
seeded random order, so a provider incident spreads over all configurations instead of hitting
one. Retries: each model call is retried with backoff inside the client (every attempt is
logged); a run that a provider failure still affected (a failed run, or a failed call, with
HTTP 408, 429 or 5xx, a network error or an unexpected response) is run again later, at most
three attempts per slot, and every attempt is kept and stored. Every run is stored in the
pipeline layer of the database as soon as it ends.
"""

from __future__ import annotations

import argparse
import json
import logging
import random
import re
import subprocess
import time
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from Second_step_CLICpipeline.clic_extract.backends import BackendError, get_token, verify_token
from src.evaluation.configurations import CONFIGURATIONS, describe, prompt_versions
from src.evaluation.pricing import load_prices
from src.evaluation.run_configs import run_configuration
from src.evaluation.store_runs import ensure_batch, ensure_conversion, ensure_document, file_sha256, store_run
from src.pipeline.config import Config, configure_logging, load_config
from src.pipeline.db import get_connection

logger = logging.getLogger("pipeline.evaluation.batch")

RUNS_ROOT = Path("evaluation/runs")
MAX_SLOT_ATTEMPTS = 3
REQUEUE_DELAY_SECONDS = 60
DOCUMENT_ORDER_SEED = 20261024
_TRANSIENT = re.compile(r"^(HTTP (408|429|5\d\d)\b|network error|unexpected response shape)")


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def code_version() -> dict[str, Any]:
    def git(*args: str) -> str:
        return subprocess.run(["git", *args], capture_output=True, text=True, check=True).stdout.strip()
    changes = [line for line in git("status", "--porcelain").splitlines() if line]
    return {"commit": git("rev-parse", "HEAD"), "dirty": bool(changes), "uncommitted_changes": changes}


def transient_failure(run: dict[str, Any]) -> str | None:
    """The provider failure that affected a run, if any; None when the run was not affected."""
    if run.get("status") == "failed" and _TRANSIENT.match(run.get("error") or ""):
        return run["error"]
    for call in (run.get("evaluation") or {}).get("call_log") or []:
        if not call["ok"] and _TRANSIENT.match(call.get("error") or ""):
            return call["error"]
    return None


def interleaved_schedule(configs: list[str], documents: list[str], repetitions: int, seed: str) -> list[dict]:
    schedule = []
    for rep in range(1, repetitions + 1):
        pairs = [(c, d) for c in configs for d in documents]
        random.Random(f"{seed}/{rep}").shuffle(pairs)
        schedule += [{"configuration": c, "document": d, "repetition": rep} for c, d in pairs]
    return schedule


def price_record(path: Path, prices: dict, configs: list[str]) -> dict[str, Any]:
    used = {(describe(c)["provider"], describe(c)["model"]) for c in configs}
    return {"file": str(path), "sha256": file_sha256(path),
            "retrieved_on": {f"{p} / {m}": (prices.get((p, m)) or {}).get("retrieved_on") for p, m in sorted(used)},
            "status": {f"{p} / {m}": (prices.get((p, m)) or {}).get("status") for p, m in sorted(used)}}


def write_manifest(path: Path, manifest: dict) -> None:
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    tmp.replace(path)


def new_manifest(batch_id: str, documents: list[str], repetitions: int, code: dict, prices: dict) -> dict:
    order = sorted(documents)
    random.Random(DOCUMENT_ORDER_SEED).shuffle(order)
    return {
        "batch_id": batch_id, "run_kind": "evaluation", "started_utc": _utc(), "ended_utc": None,
        "code": code, "prompt_versions": prompt_versions(), "prices": prices,
        "configurations": {c: describe(c) for c in CONFIGURATIONS},
        "repetitions": repetitions, "max_slot_attempts": MAX_SLOT_ATTEMPTS,
        "document_order": {"seed": DOCUMENT_ORDER_SEED, "method": "random.Random(seed).shuffle(sorted(documents))",
                           "order": order},
        "chunks": [],
    }


def run_chunk(manifest: dict, manifest_path: Path, documents: list[str], config: Config, token: str,
              prices: dict, conn) -> dict:
    batch_dir = manifest_path.parent
    chunk = {"index": len(manifest["chunks"]) + 1, "documents": documents, "code_commit": manifest["code"]["commit"],
             "started_utc": _utc(), "ended_utc": None, "runs": []}
    seed = f"{manifest['batch_id']}/chunk{chunk['index']}"
    chunk["schedule_seed"] = seed
    chunk["schedule"] = interleaved_schedule(CONFIGURATIONS, documents, manifest["repetitions"], seed)
    manifest["chunks"].append(chunk)
    write_manifest(manifest_path, manifest)

    doc_ids = {d: ensure_document(conn, config.paths.raw / f"{d}.pdf") for d in documents}
    conversions = {}
    for d in documents:
        record = json.loads((config.paths.markdown / f"{d}.conversion.json").read_text(encoding="utf-8"))
        conversions[d] = ensure_conversion(conn, doc_ids[d], record)
    conn.commit()

    queue = deque({**slot, "slot_attempt": 1, "not_before": 0.0} for slot in chunk["schedule"])
    total = len(queue)
    done = 0
    while queue:
        slot = queue.popleft()
        wait = slot["not_before"] - time.monotonic()
        if wait > 0:
            if any(s["not_before"] <= time.monotonic() for s in queue):
                queue.append(slot)
                continue
            time.sleep(wait)
        key, doc, rep, attempt = slot["configuration"], slot["document"], slot["repetition"], slot["slot_attempt"]
        entry = {"configuration": key, "document": doc, "repetition": rep, "slot_attempt": attempt,
                 "started_utc": _utc()}
        try:
            run = run_configuration(key, doc, config, batch_dir, token, prices)
        except Exception as exc:  # noqa: BLE001 - recorded, the batch goes on
            entry.update(status="crashed", error=str(exc))
            logger.error("%s on %s rep %d attempt %d crashed: %s", key, doc, rep, attempt, exc)
            chunk["runs"].append(entry)
            write_manifest(manifest_path, manifest)
            continue
        run_file = Path(run["evaluation"]["run_file"])
        provider_failure = transient_failure(run)
        run_id = store_run(conn, run_file, batch_id=manifest["batch_id"], run_kind=manifest["run_kind"],
                           config_name=key, document_id=doc_ids[doc],
                           conversion_id=conversions[doc] if describe(key)["input_kind"] == "markdown" else None,
                           prices=prices, repetition=rep, slot_attempt=attempt)
        conn.commit()
        repeat = provider_failure is not None and attempt < MAX_SLOT_ATTEMPTS
        entry.update(status=run["status"], run_file=str(run_file), run_id=run_id,
                     end_to_end_seconds=run["evaluation"]["end_to_end_seconds"],
                     retries=run["evaluation"]["retries"], failed_calls=run["evaluation"]["failed_calls"],
                     provider_failure=provider_failure, repeated_later=repeat)
        chunk["runs"].append(entry)
        write_manifest(manifest_path, manifest)
        if repeat:
            queue.append({**slot, "slot_attempt": attempt + 1,
                          "not_before": time.monotonic() + REQUEUE_DELAY_SECONDS})
        else:
            done += 1
        logger.info("[%d/%d] %s on %s rep %d: %s, %.1fs, %d retries%s", done, total, key, doc, rep, run["status"],
                    run["evaluation"]["end_to_end_seconds"], run["evaluation"]["retries"],
                    f", provider failure, repeated later: {provider_failure}" if repeat else "")

    chunk["ended_utc"] = manifest["ended_utc"] = _utc()
    write_manifest(manifest_path, manifest)
    ensure_batch(conn, manifest, manifest_path)
    conn.commit()
    return chunk


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    group = ap.add_mutually_exclusive_group(required=True)
    group.add_argument("--new", action="store_true", help="start a new batch")
    group.add_argument("--batch", help="continue this batch id")
    which = ap.add_mutually_exclusive_group(required=True)
    which.add_argument("--next", type=int, help="the next N documents of the batch's document order")
    which.add_argument("--documents", nargs="+")
    ap.add_argument("--repetitions", type=int, default=3)
    ap.add_argument("--config", default="config.yaml")
    ap.add_argument("--allow-dirty", action="store_true", help="run on uncommitted code (recorded as dirty)")
    args = ap.parse_args(argv)

    config: Config = load_config(args.config)
    configure_logging(config)
    code = code_version()
    if code["dirty"] and not args.allow_dirty:
        raise SystemExit("the working tree has uncommitted changes; commit and push first:\n  "
                         + "\n  ".join(code["uncommitted_changes"]))
    gold_dir = Path(config.settings["evaluation"]["gold"])
    available = sorted(p.stem for p in gold_dir.glob("*.json") if (config.paths.raw / f"{p.stem}.pdf").is_file())
    price_path = Path(config.settings["evaluation"]["prices"])
    prices = load_prices(price_path)

    if args.new:
        batch_id = "batch_" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        manifest_path = RUNS_ROOT / batch_id / "manifest.json"
        if manifest_path.parent.exists():
            raise SystemExit(f"{manifest_path.parent} already exists")
        manifest_path.parent.mkdir(parents=True)
        manifest = new_manifest(batch_id, available, args.repetitions, code,
                                price_record(price_path, prices, CONFIGURATIONS))
    else:
        manifest_path = RUNS_ROOT / args.batch / "manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if code["commit"] != manifest["code"]["commit"]:
            raise SystemExit(f"code is at {code['commit']}, the batch was started at {manifest['code']['commit']}; "
                             "a batch must not mix code versions")
        if file_sha256(price_path) != manifest["prices"]["sha256"]:
            raise SystemExit("the price file changed since the batch started")

    done = {d for c in manifest["chunks"] for d in c["documents"] if c.get("ended_utc")}
    if args.documents:
        documents = args.documents
        unknown = [d for d in documents if d not in available]
        if unknown:
            raise SystemExit(f"no PDF and gold set for {unknown}")
    else:
        documents = [d for d in manifest["document_order"]["order"] if d not in done][: args.next]
    if not documents:
        raise SystemExit("every document of this batch has been run")

    load_dotenv(".env")
    try:
        token = get_token()
        verify_token(token)
    except BackendError as exc:
        raise SystemExit(f"error: {exc}")

    conn = get_connection(config)
    try:
        ensure_batch(conn, manifest, manifest_path)
        conn.commit()
        write_manifest(manifest_path, manifest)
        logger.info("batch %s at commit %s: documents %s, %d repetitions", manifest["batch_id"],
                    code["commit"][:7], documents, manifest["repetitions"])
        chunk = run_chunk(manifest, manifest_path, documents, config, token, prices, conn)
    finally:
        conn.close()
    remaining = [d for d in manifest["document_order"]["order"]
                 if d not in {x for c in manifest["chunks"] for x in c["documents"]}]
    failed = sum(1 for r in chunk["runs"] if r["status"] != "ok" and not r.get("repeated_later"))
    logger.info("chunk %d done: %d runs recorded, %d not ok; remaining documents: %s",
                chunk["index"], len(chunk["runs"]), failed, remaining or "none")


if __name__ == "__main__":
    main()
