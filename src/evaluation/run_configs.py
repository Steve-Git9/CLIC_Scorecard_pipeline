"""Run the extraction configurations on evaluation documents and log what each run cost.

    python -m src.evaluation.run_configs --pilot                      # seeded random document, all configurations
    python -m src.evaluation.run_configs --document <document> --configs B C --out evaluation/runs

Each configuration writes its usual files under <out>/<configuration>/ (<document>_<UTC>.json,
.run.json, .replies.json, ...). The runner adds an "evaluation" block to the .run.json with:
    calls         every model call, successful or failed, with every attempt (retries) and the
                  provider's usage fields: input, output, reasoning and image tokens
    tokens        those token counts summed over all calls of the run, failed calls included
    preparation   the preparation steps outside the configuration's own function: the Docling
                  conversion (taken from data/markdown/<document>.conversion.json, where it was
                  timed once per document) or the native text extraction (timed here)
    end_to_end_seconds  wall clock from PDF file to final JSON, preparation included
    conversion_call     for the free form configurations: there is none, the free form reply is
                        converted to JSON locally in Python, so it uses no tokens
The targeted configurations run without the page map cache, so page location is always timed.
"""

from __future__ import annotations

import argparse
import json
import logging
import random
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from Second_step_CLICpipeline.clic_extract.backends import (
    BackendError,
    get_token,
    load_arms,
    record_calls,
    verify_token,
)
from Second_step_CLICpipeline.clic_extract.freeform import run_one_freeform
from Second_step_CLICpipeline.clic_extract.multimodal import (
    DEFAULT_BATCH_OVERLAP,
    DEFAULT_BATCH_SIZE,
    extract_native_text,
    run_one_combined,
    run_one_multimodal,
)
from Second_step_CLICpipeline.clic_extract.run_extract import run_one
from Second_step_CLICpipeline.clic_extract.targeted import run_one_targeted
from src.evaluation.pricing import load_prices, run_cost
from src.pipeline.config import Config, configure_logging, load_config

logger = logging.getLogger("pipeline.evaluation.run")

CONFIGURATIONS = [
    "B", "C", "D", "freeform_B", "freeform_light",
    "multimodal_strict", "multimodal_open",
    "multimodal_combined_qwen_vl", "multimodal_combined_llama4_maverick",
    "targeted_text", "targeted_multimodal",
]
MARKDOWN_INPUT = {"B", "C", "D", "freeform_B", "freeform_light"}
FREE_FORM = {"freeform_B", "freeform_light"}
PILOT_SEED = 20261023


def choose_document(documents: list[str], seed: int) -> str:
    return random.Random(seed).choice(sorted(documents))


def _sum(calls: list[dict], key: str) -> int | None:
    values = [c[key] for c in calls if c.get(key) is not None]
    return sum(values) if values else None


def summarise_calls(calls: list[dict]) -> dict[str, Any]:
    return {
        "calls": len(calls),
        "failed_calls": sum(1 for c in calls if not c["ok"]),
        "attempts": sum(len(c["attempts"]) for c in calls),
        "retries": sum(max(len(c["attempts"]) - 1, 0) for c in calls),
        "tokens": {key: _sum(calls, key) for key in
                   ("prompt_tokens", "completion_tokens", "reasoning_tokens", "image_tokens", "cached_tokens")},
        "calls_reporting": {key: sum(1 for c in calls if c.get(key) is not None) for key in
                            ("prompt_tokens", "completion_tokens", "reasoning_tokens", "image_tokens")},
    }


def _execute(key: str, pdf: Path, md: Path, out_dir: Path, token: str, now: datetime,
             preparation: dict[str, Any]) -> dict:
    if key in ("B", "C", "D"):
        return run_one(key, load_arms()[key], md, out_dir, token, True, now)
    if key in FREE_FORM:
        return run_one_freeform(md, out_dir, token, now, arm_name=key)
    if key in ("multimodal_strict", "multimodal_open"):
        return run_one_multimodal(pdf, out_dir, token, now, batch_size=DEFAULT_BATCH_SIZE,
                                  overlap=DEFAULT_BATCH_OVERLAP, strict=key == "multimodal_strict")
    if key.startswith("multimodal_combined_"):
        t0 = time.perf_counter()
        native_text = extract_native_text(pdf)
        preparation["native_text_seconds"] = round(time.perf_counter() - t0, 2)
        return run_one_combined(pdf, native_text, out_dir, key.removeprefix("multimodal_combined_"), token, now)
    if key in ("targeted_text", "targeted_multimodal"):
        return run_one_targeted(pdf, out_dir, key.removeprefix("targeted_"), token, now, cache_dir=None)
    raise ValueError(f"unknown configuration {key!r}")


def run_configuration(key: str, document: str, config: Config, out_root: Path, token: str,
                      prices: dict) -> dict:
    pdf = config.paths.raw / f"{document}.pdf"
    md = config.paths.markdown / f"{document}.md"
    out_dir = out_root / key
    out_dir.mkdir(parents=True, exist_ok=True)
    preparation: dict[str, Any] = {}
    if key in MARKDOWN_INPUT:
        record = json.loads((config.paths.markdown / f"{document}.conversion.json").read_text(encoding="utf-8"))
        preparation.update(docling_conversion_seconds=record["total_seconds"],
                           docling_markdown_sha256=record["markdown_sha256"])

    now = datetime.now(timezone.utc)
    with record_calls() as calls:
        t0 = time.perf_counter()
        run = _execute(key, pdf, md, out_dir, token, now, preparation)
        wall = time.perf_counter() - t0

    run_file = out_dir / f"{document}_{now.strftime('%Y%m%dT%H%M%SZ')}.run.json"
    if not run_file.is_file():
        raise FileNotFoundError(f"{key} did not write {run_file}")
    run = json.loads(run_file.read_text(encoding="utf-8"))
    run["evaluation"] = {
        "document": document,
        "run_file": str(run_file),
        "input": "docling_markdown" if key in MARKDOWN_INPUT else "pdf",
        "preparation": preparation,
        "runner_wall_clock_seconds": round(wall, 2),
        "end_to_end_seconds": round(wall + preparation.get("docling_conversion_seconds", 0), 2),
        **summarise_calls(calls),
        "conversion_call": ({"made": False, "tokens": 0,
                             "note": "the free form reply is converted to JSON locally in Python; no model call"}
                            if key in FREE_FORM else None),
        "cost": run_cost(calls, prices),
        "call_log": calls,
    }
    run_file.write_text(json.dumps(run, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return run


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pilot", action="store_true", help="one seeded random document, every configuration")
    ap.add_argument("--seed", type=int, default=PILOT_SEED)
    ap.add_argument("--document", nargs="+", help="document stems (file names without .pdf)")
    ap.add_argument("--configs", nargs="+", default=CONFIGURATIONS, choices=CONFIGURATIONS)
    ap.add_argument("--out", type=Path, help="default evaluation/pilot with --pilot")
    ap.add_argument("--config", default="config.yaml")
    args = ap.parse_args(argv)

    config: Config = load_config(args.config)
    configure_logging(config)
    gold_dir = Path(config.settings["evaluation"]["gold"])
    available = sorted(p.stem for p in gold_dir.glob("*.json") if (config.paths.raw / f"{p.stem}.pdf").is_file())

    if args.pilot:
        documents = [choose_document(available, args.seed)]
        out_root = args.out or Path("evaluation/pilot")
        out_root.mkdir(parents=True, exist_ok=True)
        manifest = {"seed": args.seed, "method": "random.Random(seed).choice(sorted(documents))",
                    "documents": available, "chosen": documents[0], "configurations": args.configs,
                    "started_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "note": "pilot runs check the pipeline end to end; they are not part of the results"}
        (out_root / "pilot_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        logger.info("pilot document %s chosen with seed %d from %d documents", documents[0], args.seed, len(available))
    else:
        if not args.document or not args.out:
            raise SystemExit("give --document and --out, or use --pilot")
        documents, out_root = args.document, args.out

    prices = load_prices(config.settings["evaluation"]["prices"])
    load_dotenv(".env")
    try:
        token = get_token()
        verify_token(token)
    except BackendError as exc:
        raise SystemExit(f"error: {exc}")

    for document in documents:
        for key in args.configs:
            logger.info("running %s on %s", key, document)
            try:
                run = run_configuration(key, document, config, out_root, token, prices)
            except Exception as exc:  # noqa: BLE001 - one configuration failing must not stop the others
                logger.error("%s on %s crashed: %s", key, document, exc)
                continue
            ev = run["evaluation"]
            logger.info("%s on %s: %s in %.1fs end to end, %d call(s), %d failed, %d retries, tokens %s, cost %s %s",
                        key, document, run["status"], ev["end_to_end_seconds"], ev["calls"],
                        ev["failed_calls"], ev["retries"], ev["tokens"], ev["cost"]["cost_usd"],
                        ev["cost"]["problems"] or "")


if __name__ == "__main__":
    main()
