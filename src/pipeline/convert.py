"""Convert a proposal PDF to Markdown with docling (layout analysis + OCR fallback).

Runs entirely on this machine - the PDF is read from local disk and never leaves it,
per CLAUDE.md's confidentiality rule. docling was chosen over pymupdf4llm for the
webapp's conversion step after the comparison in experiments/convert_compare.py
(more tables and amounts recovered on image-heavy pages).
"""

from __future__ import annotations

import argparse
import logging
import time
from pathlib import Path

from src.pipeline.config import Config, configure_logging, load_config

logger = logging.getLogger("pipeline.convert")


def _needs_ocr(pdf_path: Path, ocr_min_chars_per_page: int) -> bool:
    """True if enough pages lack a usable embedded text layer that OCR is actually worth its cost.

    A cheap pymupdf text probe, not a docling run: measured on a real 38-page proposal with a
    clean text layer on every page, forcing docling's OCR pass anyway cost 577.9s versus 278.5s
    with it off, for a 0.05% difference in recovered text - OCR is expensive and should only run
    when the document actually needs it, per CLAUDE.md's original "native first, OCR fallback
    for image-only pages" design (config.yaml's conversion.ocr_min_chars_per_page, unused until
    now, is exactly this threshold).

    Tolerates exactly one sparse page before triggering: a cover/title page with just a heading
    and a date is common and is not a scan - on that same real proposal, page 1 was 98 characters
    (a title, a date and a confidentiality stamp), 2 characters under the threshold, and would otherwise have forced OCR
    across the whole 38-page document for one normal, fully-readable cover page.
    """
    import fitz  # pymupdf

    doc = fitz.open(pdf_path)
    try:
        sparse_pages = sum(1 for page in doc if len(page.get_text()) < ocr_min_chars_per_page)
        tolerance = max(1, round(0.1 * doc.page_count))
        return sparse_pages > tolerance
    finally:
        doc.close()


def convert_pdf_to_markdown(pdf_path: Path, ocr_min_chars_per_page: int = 100) -> str:
    """Convert one PDF to a Markdown string using docling's layout analysis, with OCR enabled
    only if at least one page lacks a usable embedded text layer (see _needs_ocr)."""
    return convert_pdf_with_stats(pdf_path, ocr_min_chars_per_page)[0]


def convert_pdf_with_stats(pdf_path: Path, ocr_min_chars_per_page: int = 100) -> tuple[str, dict]:
    """As convert_pdf_to_markdown, and also return what the conversion did and how long each
    part took: the OCR probe and converter set up, docling's conversion, and the export."""
    from docling.datamodel.base_models import InputFormat
    from docling.datamodel.pipeline_options import PdfPipelineOptions
    from docling.document_converter import DocumentConverter, PdfFormatOption

    t0 = time.perf_counter()
    needs_ocr = _needs_ocr(pdf_path, ocr_min_chars_per_page)
    opts = PdfPipelineOptions()
    opts.do_ocr = needs_ocr
    opts.do_table_structure = True
    opts.table_structure_options.do_cell_matching = True
    converter = DocumentConverter(format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=opts)})
    setup_seconds = time.perf_counter() - t0

    t1 = time.perf_counter()
    result = converter.convert(str(pdf_path))
    convert_seconds = time.perf_counter() - t1

    t2 = time.perf_counter()
    markdown = result.document.export_to_markdown()
    export_seconds = time.perf_counter() - t2

    stats = {
        "ocr_used": needs_ocr,
        "tables": len(getattr(result.document, "tables", []) or []),
        "pictures": len(getattr(result.document, "pictures", []) or []),
        "setup_seconds": round(setup_seconds, 2),
        "convert_seconds": round(convert_seconds, 2),
        "export_seconds": round(export_seconds, 2),
    }
    logger.info(
        "Converted %s with docling in %.1fs (ocr=%s, %d table(s), %d picture(s))",
        pdf_path.name, convert_seconds, needs_ocr, stats["tables"], stats["pictures"],
    )
    return markdown, stats


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Convert one PDF to Markdown with docling")
    parser.add_argument("pdf_path", help="Path to the PDF to convert")
    parser.add_argument("--config", default="config.yaml", help="Path to config.yaml")
    return parser


def main(argv: list[str] | None = None) -> None:
    args = _build_arg_parser().parse_args(argv)
    config: Config = load_config(args.config)
    configure_logging(config)

    pdf_path = Path(args.pdf_path)
    if not pdf_path.is_file():
        raise FileNotFoundError(f"No such file: {pdf_path}")

    markdown = convert_pdf_to_markdown(pdf_path)
    config.paths.markdown.mkdir(parents=True, exist_ok=True)
    out_path = config.paths.markdown / f"{pdf_path.stem}.md"
    out_path.write_text(markdown, encoding="utf-8")
    print(f"wrote {out_path}")


if __name__ == "__main__":
    main()
