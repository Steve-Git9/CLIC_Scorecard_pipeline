"""SQLite connection handling and schema initialisation for the CLIC KPI pipeline."""

from __future__ import annotations

import argparse
import logging
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


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Database management for the CLIC KPI pipeline")
    parser.add_argument("--config", default="config.yaml", help="Path to config.yaml")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("init", help="Apply sql/schema.sql to the configured database")
    return parser


def main(argv: list[str] | None = None) -> None:
    args = _build_arg_parser().parse_args(argv)
    config = load_config(args.config)
    configure_logging(config)

    if args.command == "init":
        init_db(config)


if __name__ == "__main__":
    main()
