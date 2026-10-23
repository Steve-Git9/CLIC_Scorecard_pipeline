"""SQLite connection handling and schema initialisation for the CLIC KPI pipeline."""

from __future__ import annotations

import argparse
import logging
import re
import sqlite3
from pathlib import Path

from src.pipeline.config import Config, configure_logging, load_config

logger = logging.getLogger("pipeline.db")

DEFAULT_SCHEMA_PATH = Path("sql/schema.sql")


def get_connection(config: Config) -> sqlite3.Connection:
    """Open the pipeline's SQLite database with foreign keys enforced."""
    config.paths.database.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(config.paths.database)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(config: Config, schema_path: Path = DEFAULT_SCHEMA_PATH) -> None:
    """Apply sql/schema.sql to the configured database."""
    schema_sql = Path(schema_path).read_text(encoding="utf-8")
    conn = get_connection(config)
    try:
        conn.executescript(schema_sql)
        conn.commit()
        logger.info("Database initialised at %s using %s", config.paths.database, schema_path)
    finally:
        conn.close()


PIPELINE_V2_TABLES = ["run_batch", "model_config", "extraction_run", "extraction_call", "call_attempt"]


def table_definitions(schema_path: Path = DEFAULT_SCHEMA_PATH) -> dict[str, str]:
    """CREATE TABLE statements of sql/schema.sql, by table name."""
    sql = Path(schema_path).read_text(encoding="utf-8")
    return {m.group(1): m.group(0) for m in re.finditer(r"(?ms)^CREATE TABLE (\w+) \(.*?^\);", sql)}


def migrate_pipeline_v2(config: Config, schema_path: Path = DEFAULT_SCHEMA_PATH) -> list[str]:
    """Bring an existing database to pipeline layer version 2 (docs/decisions.md, 2026-10-23).

    Recreates the version 2 tables from sql/schema.sql. Only tables without rows are dropped; a
    table holding data stops the migration before anything changes. Other tables are untouched.
    """
    definitions = table_definitions(schema_path)
    conn = get_connection(config)
    try:
        existing = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}
        for table in PIPELINE_V2_TABLES:
            if table in existing and conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]:
                raise RuntimeError(f"table {table} holds rows; migration stopped, nothing changed")
        conn.execute("PRAGMA foreign_keys = OFF")
        for table in reversed(PIPELINE_V2_TABLES):
            conn.execute(f"DROP TABLE IF EXISTS {table}")
        for table in PIPELINE_V2_TABLES:
            conn.execute(definitions[table])
        conn.commit()
        conn.execute("PRAGMA foreign_keys = ON")
        problems = [tuple(r) for r in conn.execute("PRAGMA foreign_key_check")]
        if problems:
            raise RuntimeError(f"foreign key check failed after migration: {problems[:5]}")
        logger.info("Pipeline layer migrated to version 2: %s", ", ".join(PIPELINE_V2_TABLES))
        return PIPELINE_V2_TABLES
    finally:
        conn.close()


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Database management for the CLIC KPI pipeline")
    parser.add_argument("--config", default="config.yaml", help="Path to config.yaml")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("init", help="Apply sql/schema.sql to the configured database")
    subparsers.add_parser("migrate-pipeline-v2", help="Recreate the empty pipeline run tables at version 2")
    return parser


def main(argv: list[str] | None = None) -> None:
    args = _build_arg_parser().parse_args(argv)
    config = load_config(args.config)
    configure_logging(config)

    if args.command == "init":
        init_db(config)
    elif args.command == "migrate-pipeline-v2":
        migrate_pipeline_v2(config)


if __name__ == "__main__":
    main()
