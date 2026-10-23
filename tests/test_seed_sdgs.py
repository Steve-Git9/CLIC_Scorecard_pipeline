from __future__ import annotations

from pathlib import Path

from src.pipeline.config import Config
from src.pipeline.db import get_connection, init_db
from src.pipeline.seed_sdgs import seed_sdgs

SCHEMA_PATH = Path(__file__).resolve().parents[1] / "sql" / "schema.sql"


def _write_sdgs_json(dir_path: Path) -> Path:
    import json

    dir_path.mkdir(parents=True, exist_ok=True)
    path = dir_path / "sdgs.json"
    path.write_text(
        json.dumps([
            {"number": 1, "name": "Fictional Goal One"},
            {"number": 2, "name": "Fictional Goal Two"},
        ]),
        encoding="utf-8",
    )
    return path


def test_seed_sdgs_inserts_once_and_skips_on_rerun(test_config: Config) -> None:
    init_db(test_config, schema_path=SCHEMA_PATH)
    sdgs_path = _write_sdgs_json(test_config.paths.database.parent)

    inserted, skipped = seed_sdgs(sdgs_path, test_config)
    assert (inserted, skipped) == (2, 0)

    inserted_again, skipped_again = seed_sdgs(sdgs_path, test_config)
    assert (inserted_again, skipped_again) == (0, 2)

    conn = get_connection(test_config)
    try:
        rows = conn.execute("SELECT sdg_number, sdg_title FROM dim_sdg ORDER BY sdg_number").fetchall()
    finally:
        conn.close()

    assert [dict(r) for r in rows] == [
        {"sdg_number": 1, "sdg_title": "Fictional Goal One"},
        {"sdg_number": 2, "sdg_title": "Fictional Goal Two"},
    ]
