from __future__ import annotations

from pathlib import Path

import pytest

from src.pipeline.config import Config
from src.pipeline.db import get_connection, init_db
from src.pipeline.intake import DuplicateDocumentError, compute_content_hash, register_document

SCHEMA_PATH = Path(__file__).resolve().parents[1] / "sql" / "schema.sql"


@pytest.fixture
def initialised_config(test_config: Config) -> Config:
    init_db(test_config, schema_path=SCHEMA_PATH)
    return test_config


def test_register_document_inserts_received_row(initialised_config: Config, fictional_pdf: Path) -> None:
    document_id = register_document(fictional_pdf, initialised_config)

    conn = get_connection(initialised_config)
    try:
        row = conn.execute(
            "SELECT * FROM document WHERE document_id = ?", (document_id,)
        ).fetchone()
    finally:
        conn.close()

    assert row["status"] == "received"
    assert row["page_count"] == 3
    assert row["content_hash"] == compute_content_hash(fictional_pdf)
    assert row["file_name"] == fictional_pdf.name


def test_register_document_refuses_duplicate(initialised_config: Config, fictional_pdf: Path) -> None:
    register_document(fictional_pdf, initialised_config)

    with pytest.raises(DuplicateDocumentError):
        register_document(fictional_pdf, initialised_config)

    conn = get_connection(initialised_config)
    try:
        count = conn.execute("SELECT COUNT(*) FROM document").fetchone()[0]
    finally:
        conn.close()

    assert count == 1
