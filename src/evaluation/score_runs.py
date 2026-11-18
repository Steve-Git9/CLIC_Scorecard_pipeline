"""Command line scorer: score run files against the gold sets and write the results.

    python -m src.evaluation.score_runs evaluation/B/ABiCo_20261023T100000Z.run.json
    python -m src.evaluation.score_runs evaluation/B evaluation/C        # latest run per document
    python -m src.evaluation.score_runs evaluation/B --all-runs          # every run in the folder

A run is identified by its <stem>_<UTC>.run.json file. Next to it the scorer reads:
    <stem>_<UTC>.json          the final output (absent when the run failed)
    <stem>_<UTC>.replies.json  the raw model replies, a JSON list of strings, one per
                               extraction call; without it first attempt validity is unknown
and it writes <stem>_<UTC>.score.json. The gold set is <gold>/<stem>.json and the Docling
Markdown is <markdown>/<stem>.md, both from config.yaml (evaluation section). For a folder,
the unsure partner names (scored with half values) are written to <folder>/review_list.csv.
For a whole batch, use python -m src.evaluation.score_batch instead.
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
import re
from pathlib import Path
from typing import Any

from src.evaluation.partners import DocumentTerms
from src.evaluation.scorer import score_run
from src.pipeline.config import Config, configure_logging, load_config

logger = logging.getLogger("pipeline.evaluation")

_RUN_SUFFIX = ".run.json"
_STAMPED = re.compile(r"^(?P<stem>.+)_(?P<stamp>\d{8}T\d{6}Z)$")


def run_base(run_file: Path) -> Path:
    if not run_file.name.endswith(_RUN_SUFFIX):
        raise ValueError(f"not a run file: {run_file}")
    return run_file.with_name(run_file.name[: -len(_RUN_SUFFIX)])


def document_stem(base: Path) -> str:
    m = _STAMPED.match(base.name)
    if not m:
        raise ValueError(f"run name {base.name!r} is not <document>_<YYYYMMDDTHHMMSSZ>")
    return m["stem"]


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else None


def latest_runs(folder: Path) -> list[Path]:
    """The newest run file per document in a configuration folder."""
    newest: dict[str, Path] = {}
    for run_file in sorted(folder.glob(f"*{_RUN_SUFFIX}")):
        try:
            stem = document_stem(run_base(run_file))
        except ValueError:
            logger.warning("skipped %s: unexpected file name", run_file.name)
            continue
        newest[stem] = run_file  # sorted by name, so the last stamp wins
    return [newest[s] for s in sorted(newest)]


def score_run_file(run_file: Path, settings: dict, decisions: dict | None = None) -> dict[str, Any]:
    """Score one run file and write <run>.score.json next to it. `decisions` maps document
    stems to the author's decisions on unsure names (see partners.score_partners)."""
    base = run_base(run_file)
    stem = document_stem(base)
    run = _read_json(run_file) or {}
    arm = run.get("arm") or run_file.parent.name
    protocol = settings["protocols"].get(arm)
    if protocol is None:
        raise ValueError(f"no output protocol configured for {arm!r} in config.yaml evaluation.protocols")

    gold_path = Path(settings["gold"]) / f"{stem}.json"
    gold = _read_json(gold_path)
    if gold is None:
        raise FileNotFoundError(f"no gold set {gold_path} for run {run_file.name}")
    markdown_path = Path(settings["markdown"]) / f"{stem}.md"
    terms_path = markdown_path.with_name(f"{stem}.terms.json")
    if markdown_path.is_file():
        markdown = markdown_path.read_text(encoding="utf-8")
    elif terms_path.is_file():  # Markdown withheld: the recorded presence checks stand in for it
        terms = json.loads(terms_path.read_text(encoding="utf-8"))
        markdown = DocumentTerms(terms["present"], terms["absent"])
    else:
        markdown = None
        logger.warning("%s: no Docling Markdown at %s; extra partners are unsure", stem, markdown_path)

    replies_path = base.with_name(base.name + ".replies.json")
    replies = _read_json(replies_path)
    if replies is not None and not (isinstance(replies, list) and all(isinstance(r, str) for r in replies)):
        raise ValueError(f"{replies_path.name} must be a JSON list of reply strings")
    final_path = base.with_name(base.name + ".json")
    final = _read_json(final_path)

    score = score_run(final, gold, replies, protocol, markdown, (decisions or {}).get(stem))
    score.update({"run_file": run_file.name, "configuration": arm, "document": stem, "protocol": protocol,
                  "run_status": run.get("status"), "markdown_available": markdown is not None})
    out = base.with_name(base.name + ".score.json")
    out.write_text(json.dumps(score, indent=2, ensure_ascii=False, default=repr) + "\n", encoding="utf-8")
    return score


def write_review_list(folder: Path, scores: list[dict[str, Any]]) -> Path:
    path = folder / "review_list.csv"
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["run_file", "document", "partner_name", "case", "reason", "related_gold_partner"])
        for s in scores:
            for item in s["partners"]["unsure"]:
                writer.writerow([s["run_file"], s["document"], item["partner_name"], item["case"],
                                 item["reason"], item["related_gold_partner"] or ""])
    return path


def _summary(s: dict[str, Any]) -> str:
    v, p, e = s["validity"], s["partners"], s["errors"]

    def pct(x: float | None) -> str:
        return "n/a" if x is None else f"{100 * x:.0f}%"

    return (f"{s['configuration']:<36} {s['document']:<12} first attempt {str(v['first_attempt']):<5} "
            f"after repair {str(v['after_repair']):<5} scalars {pct(s['scalar_accuracy']):>4}  "
            f"partner recall {pct(p['recall']):>4}  amounts {pct(p['amount_accuracy']):>4}  "
            f"errors {e['total']:>3}  supported extras {s['reviewer_decisions']['supported_extras']}  "
            f"unsure names {s['reviewer_decisions']['unsure_names']}  "
            f"fully correct {s['fully_correct']}")


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("paths", nargs="+", help="run files (*.run.json) or configuration folders")
    ap.add_argument("--all-runs", action="store_true", help="for folders, score every run, not only the latest")
    ap.add_argument("--config", default="config.yaml")
    args = ap.parse_args(argv)

    config: Config = load_config(args.config)
    configure_logging(config)
    settings = config.settings["evaluation"]

    for raw_path in args.paths:
        path = Path(raw_path)
        if path.is_dir():
            files = sorted(path.glob(f"*{_RUN_SUFFIX}")) if args.all_runs else latest_runs(path)
            scores = [score_run_file(f, settings) for f in files]
            for s in scores:
                logger.info(_summary(s))
            if scores:
                logger.info("review list: %s", write_review_list(path, scores))
            else:
                logger.warning("no run files in %s", path)
        else:
            logger.info(_summary(score_run_file(path, settings)))


if __name__ == "__main__":
    main()
