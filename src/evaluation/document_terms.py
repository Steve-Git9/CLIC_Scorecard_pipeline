"""Record which partner name terms occur in a document, for documents whose Markdown is withheld.

    python -m src.evaluation.document_terms --batch batch_20261030T105636Z --document Abico_Synth

The scorer reads a document's Docling Markdown for one purpose only: to check whether an
extracted partner name, or a distinctive word of it, occurs in the document (partners.py,
classify_unmatched). This module runs those checks once, on the Markdown, for every partner name
that any run of the batch extracted from the document, and writes the answers to
<markdown folder>/<document>.terms.json. When the Markdown is absent, the scorer reads that file
instead and reaches the same classes, without the document text being published.

The file holds only names that are already in the published run outputs, each with a yes or no.
"""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

from src.evaluation.partners import _contains, distinctive_words, normalise_document, normalise_name
from src.evaluation.store_runs import file_sha256
from src.pipeline.config import configure_logging, load_config

logger = logging.getLogger("pipeline.evaluation.terms")

RUN_SUFFIXES = (".run.json", ".replies.json", ".score.json", ".trace.json")


def extracted_names(batch_dir: Path, document: str) -> set[str]:
    """Every partner name in the final records of the batch's runs on the document, normalised."""
    names: set[str] = set()
    for path in batch_dir.glob(f"*/{document}_*.json"):
        if path.name.endswith(RUN_SUFFIXES):
            continue
        record = json.loads(path.read_text(encoding="utf-8"))
        for partner in record.get("partners") or []:
            key = normalise_name(partner.get("partner_name") or "")
            if key:
                names.add(key)
    return names


def build_terms(markdown: str, names: set[str]) -> dict[str, list[str]]:
    """Each name and each of its distinctive words, sorted into present and absent."""
    document = normalise_document(markdown)
    terms = set(names) | {w for name in names for w in distinctive_words(name)}
    present = sorted(t for t in terms if _contains(document, t))
    return {"present": present, "absent": sorted(terms - set(present))}


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--batch", required=True)
    ap.add_argument("--document", required=True)
    ap.add_argument("--config", default="config.yaml")
    args = ap.parse_args(argv)
    config = load_config(args.config)
    configure_logging(config)
    markdown_dir = Path(config.settings["evaluation"]["markdown"])
    markdown_path = markdown_dir / f"{args.document}.md"
    names = extracted_names(Path("evaluation/runs") / args.batch, args.document)
    if not names:
        raise SystemExit(f"no extracted partner names for {args.document} in batch {args.batch}")
    record = {"document": args.document, "batch_id": args.batch,
              "markdown_sha256": file_sha256(markdown_path),
              **build_terms(markdown_path.read_text(encoding="utf-8"), names)}
    out = markdown_dir / f"{args.document}.terms.json"
    out.write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    logger.info("%s: %d terms present, %d absent, written to %s", args.document, len(record["present"]),
                len(record["absent"]), out)


if __name__ == "__main__":
    main()
