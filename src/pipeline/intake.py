"""Document intake: hash, duplicate check, page count and registration."""

from __future__ import annotations

import argparse
import hashlib
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

import fitz  # pymupdf

from src.pipeline.config import Config, configure_logging, load_config
from src.pipeline.db import get_connection

logger = logging.getLogger("pipeline.intake")

_HASH_CHUNK_SIZE = 1024 * 1024


class DuplicateDocumentError(Exception):
    """Raised when a PDF with the same content hash is already registered."""


def compute_content_hash(path: Path) -> str:
    """Return the sha256 hex digest of a file's bytes, read in chunks."""
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(_HASH_CHUNK_SIZE), b""):
            digest.update(chunk)
    return digest.hexdigest()


def count_pages(path: Path) -> int:
    with fitz.open(path) as pdf:
        return pdf.page_count


def register_document(pdf_path: Path, config: Config) -> int:
    """Hash, count pages and insert a new document row with status 'received'.

    Raises DuplicateDocumentError if a document with the same content hash
    is already registered.
    """
    pdf_path = Path(pdf_path).resolve()
    if not pdf_path.is_file():
        raise FileNotFoundError(f"No such file: {pdf_path}")
    if pdf_path.suffix.lower() != ".pdf":
        raise ValueError(f"Not a PDF file: {pdf_path}")

    content_hash = compute_content_hash(pdf_path)
    page_count = count_pages(pdf_path)
    received_at = datetime.now(timezone.utc).isoformat()

    conn = get_connection(config)
    try:
        existing = conn.execute(
            "SELECT document_id FROM document WHERE content_hash = ?", (content_hash,)
        ).fetchone()
        if existing is not None:
            raise DuplicateDocumentError(
                f"{pdf_path.name} is already registered as document {existing['document_id']} "
                f"(content hash {content_hash})"
            )

        cursor = conn.execute(
            """
            INSERT INTO document (file_name, content_hash, page_count, storage_path, received_at, status)
            VALUES (?, ?, ?, ?, ?, 'received')
            """,
            (pdf_path.name, content_hash, page_count, str(pdf_path), received_at),
        )
        conn.commit()
        document_id = cursor.lastrowid
        logger.info(
            "Registered document %s (%s, %d pages) as document_id %s",
            pdf_path.name, content_hash[:12], page_count, document_id,
        )
        return document_id
    finally:
        conn.close()


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Register a PDF proposal document")
    parser.add_argument("pdf_path", help="Path to the PDF to register")
    parser.add_argument("--config", default="config.yaml", help="Path to config.yaml")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    config = load_config(args.config)
    configure_logging(config)

    try:
        document_id = register_document(Path(args.pdf_path), config)
    except DuplicateDocumentError as exc:
        logger.error(str(exc))
        return 1
    except (FileNotFoundError, ValueError) as exc:
        logger.error(str(exc))
        return 1

    print(document_id)
    return 0


if __name__ == "__main__":
    sys.exit(main())
