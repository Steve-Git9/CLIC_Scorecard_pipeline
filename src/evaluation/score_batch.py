"""Score every final run of a batch against the gold sets and write the results (Phase 4).

    python -m src.evaluation.score_batch --batch batch_20261030T105636Z

Only the final attempt of each slot is scored and reported (`is_final` in the database);
superseded attempts stay in the database and the run folder as the raw record but appear in no
output, total or report (author's decision of 31 October 2026). Each scored run gets a
<run>.score.json next to its run file. The results go to evaluation/results/<batch>/:

    results_per_run.csv             one row per final run
    configuration_summary.csv       means and ranges per configuration, consistency, over
                                    inclusion, cost per document, cost of pass
    contrast_table.csv              the planned contrasts, per document and as a mean
    error_log.csv, extras_log.csv   every error and every extra partner
    frontier_plot.png               field accuracy against cost per document
    spot_check.md                   two runs per configuration for a manual check of the scorer
    review_list.csv                 every unsure partner name (half scores)
    review_decisions_template.csv   each distinct document and unsure name once, to decide
    report.md                       the readable report
    document_codes.csv              the key from document codes to names
    scoring_manifest.json           scorer commit, inputs and their digests, counts
    shareable/                      copies without names, values or amounts, documents coded

Decisions on unsure names: fill in a copy of the template as review_decisions.csv in the same
folder (decision `gold:<gold partner name>`, `supported_extra` or `unsupported_extra`) and run
the scorer again; no model is called. The scorer refuses to run on uncommitted code unless
--allow-dirty is given, and the manifest records the commit either way.
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.evaluation import batch_report as report
from src.evaluation import batch_tables as tables
from src.evaluation.partners import DECISIONS, normalise_name
from src.evaluation.run_batch import code_version
from src.evaluation.score_runs import score_run_file
from src.evaluation.store_runs import file_sha256
from src.pipeline.config import Config, configure_logging, load_config
from src.pipeline.db import get_connection

logger = logging.getLogger("pipeline.evaluation.score")

RESULTS_ROOT = Path("evaluation/results")
DECISIONS_FILE = "review_decisions.csv"

_FINAL_RUNS = """
SELECT m.config_name, d.file_name, r.repetition, r.status, r.run_file_path, r.cost_usd_micros,
       r.end_to_end_ms, r.tokens_in, r.tokens_out, r.tokens_reasoning, r.tokens_cached, r.tokens_image,
       r.started_at
FROM extraction_run r
JOIN model_config m ON m.config_id = r.config_id
JOIN document d ON d.document_id = r.document_id
WHERE r.batch_id = ? AND r.is_final = 1
ORDER BY m.config_name, d.file_name, r.repetition
"""


def load_decisions(path: Path) -> dict[str, dict[str, tuple]]:
    """document -> normalised partner name -> decision, from the author's decisions file."""
    if not path.is_file():
        return {}
    decisions: dict[str, dict[str, tuple]] = {}
    with path.open(encoding="utf-8", newline="") as f:
        for line, row in enumerate(csv.DictReader(f), start=2):
            text = (row.get("decision") or "").strip()
            if not text:
                continue
            kind, _, name = text.partition(":")
            kind = kind.strip()
            if kind not in DECISIONS or (kind == "gold") != bool(name.strip()):
                raise SystemExit(f"{path}, line {line}: decision {text!r} must be gold:<gold partner name>, "
                                 "supported_extra or unsupported_extra")
            decision = ("gold", name.strip()) if kind == "gold" else (kind,)
            decisions.setdefault(row["document"], {})[normalise_name(row["partner_name"])] = decision
    return decisions


def final_runs(conn, batch_id: str) -> list[dict[str, Any]]:
    out = []
    for (config, file_name, rep, status, run_file, cost, e2e, t_in, t_out, t_reason, t_cached, t_image,
         started) in conn.execute(_FINAL_RUNS, (batch_id,)):
        out.append({"configuration": config, "document": Path(file_name).stem, "repetition": rep,
                    "status": status, "run_file": run_file, "cost_usd": (cost or 0) / 1e6,
                    "end_to_end_seconds": (e2e or 0) / 1000,
                    "tokens": {"input": t_in, "output": t_out, "reasoning": t_reason, "cached": t_cached,
                               "image": t_image},
                    "started_utc": started})
    return out


def score_all(runs: list[dict[str, Any]], settings: dict, decisions: dict) -> None:
    for run in runs:
        run_file = Path(run["run_file"])
        record = json.loads(run_file.read_text(encoding="utf-8"))
        if record.get("arm") != run["configuration"]:
            raise SystemExit(f"{run_file}: arm {record.get('arm')!r} is not {run['configuration']!r}")
        prep = (record.get("evaluation") or {}).get("preparation") or {}
        run["docling_conversion_seconds"] = prep.get("docling_conversion_seconds")
        run["score"] = score_run_file(run_file, settings, decisions)
        final_path = run_file.with_name(run_file.name[: -len(".run.json")] + ".json")
        run["final"] = json.loads(final_path.read_text(encoding="utf-8")) if final_path.is_file() else None


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--batch", required=True)
    ap.add_argument("--config", default="config.yaml")
    ap.add_argument("--allow-dirty", action="store_true", help="score with uncommitted code (recorded)")
    args = ap.parse_args(argv)

    config: Config = load_config(args.config)
    configure_logging(config)
    code = code_version()
    if code["dirty"] and not args.allow_dirty:
        raise SystemExit("the working tree has uncommitted changes; commit first:\n  "
                         + "\n  ".join(code["uncommitted_changes"]))
    settings = config.settings["evaluation"]
    out_dir = RESULTS_ROOT / args.batch
    out_dir.mkdir(parents=True, exist_ok=True)
    decisions_path = out_dir / DECISIONS_FILE
    decisions = load_decisions(decisions_path)

    conn = get_connection(config)
    try:
        batch = conn.execute("SELECT code_commit FROM run_batch WHERE batch_id = ?", (args.batch,)).fetchone()
        if batch is None:
            raise SystemExit(f"no batch {args.batch} in the database")
        runs = final_runs(conn, args.batch)
    finally:
        conn.close()
    if not runs:
        raise SystemExit(f"batch {args.batch} has no final runs")
    score_all(runs, settings, decisions)

    rows = [tables.run_row(r) for r in runs]
    summary = tables.configuration_summary(runs, rows)
    contrasts = tables.contrast_table(rows)
    errors = tables.error_log(runs)
    extras = tables.extras_log(runs)
    review = report.review_rows(runs)
    documents = sorted({r["document"] for r in runs}, key=str.casefold)
    codes = report.document_codes(documents)
    gold = {d: json.loads((Path(settings["gold"]) / f"{d}.json").read_text(encoding="utf-8")) for d in documents}
    spot_seed = f"spotcheck/{args.batch}"
    best = report.frontier(summary)

    report.write_csv(out_dir / "results_per_run.csv", rows)
    report.write_csv(out_dir / "configuration_summary.csv", summary)
    report.write_csv(out_dir / "contrast_table.csv", contrasts)
    report.write_csv(out_dir / "error_log.csv", errors)
    report.write_csv(out_dir / "extras_log.csv", extras)
    report.write_csv(out_dir / "review_list.csv", review,
                     ["document", "configuration", "repetition", "run_file", "partner_name", "case",
                      "related_gold_partner", "requested_cents", "reason"])
    report.write_csv(out_dir / "review_decisions_template.csv", report.decisions_template(review),
                     ["document", "partner_name", "cases", "related_gold_partners", "runs", "decision"])
    report.write_csv(out_dir / "document_codes.csv", [{"code": c, "document": d} for d, c in codes.items()])
    plot = report.frontier_plot(summary, out_dir / "frontier_plot.png",
                                "Field accuracy against cost per document, eleven configurations")
    report.write_spot_check(out_dir / "spot_check.md", report.spot_check_sample(runs, spot_seed), gold, spot_seed)

    share = out_dir / "shareable"
    report.write_csv(share / "configuration_summary.csv", summary)
    report.write_csv(share / "contrast_table.csv", report.coded(contrasts, codes))
    report.write_csv(share / "error_log.csv", report.coded(errors, codes), report.SHAREABLE_COLUMNS["error_log"])
    report.write_csv(share / "extras_log.csv", report.coded(extras, codes), report.SHAREABLE_COLUMNS["extras_log"])
    report.frontier_plot(summary, share / "frontier_plot.png",
                         "Field accuracy against cost per document, eleven configurations")

    overview = {
        "batch_id": args.batch, "run_commit": batch[0][:7], "scorer_commit": code["commit"][:7],
        "scorer_dirty": code["dirty"], "scored_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "first_run_utc": min(r["started_utc"] for r in runs), "last_run_utc": max(r["started_utc"] for r in runs),
        "final_runs": len(runs), "configurations": len(summary), "documents": len(documents),
        "repetitions": max(r["repetition"] for r in runs),
        "runs_not_ok": sum(1 for r in runs if r["status"] != "ok"),
        "total_cost_usd": sum(r["cost_usd"] for r in runs),
        "total_end_to_end_hours": sum(r["end_to_end_seconds"] for r in runs) / 3600,
        "decisions_applied": f"{sum(len(v) for v in decisions.values())} from {DECISIONS_FILE}" if decisions else "none",
    }
    report.write_report(out_dir / "report.md", overview=overview, summary=summary, contrasts=contrasts,
                        errors=errors, review=review, frontier_names=best, plot_name=plot.name)

    manifest = {
        "batch_id": args.batch, "run_code_commit": batch[0], "scorer_code": code,
        "scored_utc": overview["scored_utc"], "final_runs_scored": len(runs),
        "superseded_attempts": "not scored and not reported",
        "gold_sets": {d: file_sha256(Path(settings["gold"]) / f"{d}.json") for d in documents},
        "markdown": {d: file_sha256(Path(settings["markdown"]) / f"{d}.md") for d in documents
                     if (Path(settings["markdown"]) / f"{d}.md").is_file()},
        "decisions_file": {"path": str(decisions_path), "sha256": file_sha256(decisions_path)}
        if decisions_path.is_file() else None,
        "spot_check_seed": spot_seed, "document_codes": "document_codes.csv (private)",
        "frontier": sorted(best),
    }
    (out_dir / "scoring_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    logger.info("scored %d final runs of %s; results in %s", len(runs), args.batch, out_dir)


if __name__ == "__main__":
    main()
