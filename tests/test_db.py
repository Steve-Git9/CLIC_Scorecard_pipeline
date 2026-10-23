from __future__ import annotations

from pathlib import Path

from src.pipeline.config import Config
from src.pipeline.db import get_connection, init_db

SCHEMA_PATH = Path(__file__).resolve().parents[1] / "sql" / "schema.sql"


def test_init_db_creates_document_table(test_config: Config) -> None:
    init_db(test_config, schema_path=SCHEMA_PATH)

    conn = get_connection(test_config)
    try:
        row = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='document'"
        ).fetchone()
    finally:
        conn.close()

    assert row is not None


def test_get_connection_enables_foreign_keys(test_config: Config) -> None:
    init_db(test_config, schema_path=SCHEMA_PATH)

    conn = get_connection(test_config)
    try:
        value = conn.execute("PRAGMA foreign_keys").fetchone()[0]
    finally:
        conn.close()

    assert value == 1
