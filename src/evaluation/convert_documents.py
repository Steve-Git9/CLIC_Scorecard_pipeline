"""Convert the evaluation documents to Docling Markdown, timing each conversion.

    python -m src.evaluation.convert_documents                       # every PDF in data/raw
    python -m src.evaluation.convert_documents data/raw/<document>.pdf    # one document

For each PDF writes, under the markdown folder of config.yaml (paths.markdown):
    <document>.md                  the Markdown the text configurations and the scorer read
    <document>.conversion.json     time, speed and details of that conversion
and appends one row per document to conversions.csv in the same folder.

Documents are converted one at a time, so their timings do not compete for the processor.
A fresh conversion is always made; an existing <document>.md is replaced.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import logging
import os
import platform
import time
from datetime import datetime, timezone
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any

import fitz  # pymupdf

from src.pipeline.config import Config, configure_logging, load_config
from src.pipeline.convert import convert_pdf_with_stats

logger = logging.getLogger("pipeline.evaluation.convert")

CSV_FIELDS = [
    "document", "pdf_file", "pages", "started_utc", "total_seconds", "convert_seconds",
    "seconds_per_page", "pages_per_minute", "ocr_used", "tables", "pictures", "markdown_chars",
    "docling_version", "markdown_file",
]


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _package_version(name: str) -> str | None:
    try:
        return version(name)
    except PackageNotFoundError:
        return None


def convert_one(pdf_path: Path, out_dir: Path, ocr_min_chars_per_page: int = 100) -> dict[str, Any]:
    """Convert one PDF, write <stem>.md and <stem>.conversion.json, return the record."""
    with fitz.open(pdf_path) as doc:
        pages = doc.page_count
    started = datetime.now(timezone.utc)
    t0 = time.perf_counter()
    markdown, stats = convert_pdf_with_stats(pdf_path, ocr_min_chars_per_page)
    total_seconds = time.perf_counter() - t0

    out_dir.mkdir(parents=True, exist_ok=True)
    md_path = out_dir / f"{pdf_path.stem}.md"
    md_path.write_text(markdown, encoding="utf-8")

    record = {
        "document": pdf_path.stem,
        "pdf_file": str(pdf_path),
        "pdf_sha256": sha256_of(pdf_path),
        "pages": pages,
        "started_utc": started.strftime("%Y-%m-%dT%H:%M:%SZ"),
        # total: OCR probe, converter set up (model loading), conversion and export, as a
        # text configuration pays it once per document before its model call.
        "total_seconds": round(total_seconds, 2),
        **stats,
        "seconds_per_page": round(total_seconds / pages, 3) if pages else None,
        "pages_per_minute": round(60 * pages / total_seconds, 2) if total_seconds else None,
        "markdown_file": str(md_path),
        "markdown_chars": len(markdown),
        "markdown_sha256": hashlib.sha256(markdown.encode("utf-8")).hexdigest(),
        "tool": "docling",
        "docling_version": _package_version("docling"),
        "machine": {"platform": platform.platform(), "processor": platform.processor(),
                    "cpu_count": os.cpu_count(), "python": platform.python_version()},
    }
    (out_dir / f"{pdf_path.stem}.conversion.json").write_text(
        json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return record


def append_csv(path: Path, record: dict[str, Any]) -> None:
    new = not path.exists()
    with path.open("a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS, extrasaction="ignore")
        if new:
            writer.writeheader()
        writer.writerow(record)


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pdfs", nargs="*", help="PDF files; default every PDF in paths.raw")
    ap.add_argument("--config", default="config.yaml")
    args = ap.parse_args(argv)

    config: Config = load_config(args.config)
    configure_logging(config)
    pdfs = [Path(p) for p in args.pdfs] or sorted(config.paths.raw.glob("*.pdf"))
    if not pdfs:
        raise SystemExit(f"no PDF files found in {config.paths.raw}")
    threshold = config.settings.get("conversion", {}).get("ocr_min_chars_per_page", 100)

    for pdf in pdfs:
        logger.info("converting %s", pdf.name)
        record = convert_one(pdf, config.paths.markdown, threshold)
        append_csv(config.paths.markdown / "conversions.csv", record)
        logger.info("%s: %d pages in %.1fs (%.2f s/page, %.1f pages/min), ocr=%s, %d chars",
                    record["document"], record["pages"], record["total_seconds"], record["seconds_per_page"],
                    record["pages_per_minute"], record["ocr_used"], record["markdown_chars"])


if __name__ == "__main__":
    main()
