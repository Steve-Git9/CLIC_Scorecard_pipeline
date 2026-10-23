"""One-time seed load of the dim_sdg lookup table (the 17 UN Sustainable Development Goals)."""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

from src.pipeline.config import Config, configure_logging, load_config
from src.pipeline.db import get_connection

logger = logging.getLogger("pipeline.seed_sdgs")

DEFAULT_SDGS_PATH = Path("sdgautomation/sdgs.json")


def seed_sdgs(sdgs_path: Path, config: Config) -> tuple[int, int]:
    """Insert new SDGs from sdgs_path into dim_sdg. Existing sdg_number rows are left
    untouched and counted as skipped, so this can be re-run safely.
    Returns (inserted, skipped).
    """
    sdgs = json.loads(Path(sdgs_path).read_text(encoding="utf-8"))

    conn = get_connection(config)
    inserted = skipped = 0
    try:
        for sdg in sdgs:
            existing = conn.execute(
                "SELECT sdg_number FROM dim_sdg WHERE sdg_number = ?", (sdg["number"],)
            ).fetchone()
            if existing is not None:
                skipped += 1
                continue
            conn.execute(
                "INSERT INTO dim_sdg (sdg_number, sdg_title) VALUES (?, ?)",
                (sdg["number"], sdg["name"]),
            )
            inserted += 1
        conn.commit()
        logger.info("Seeded dim_sdg: %d inserted, %d already present", inserted, skipped)
    finally:
        conn.close()

    return inserted, skipped


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Seed dim_sdg from sdgautomation/sdgs.json")
    parser.add_argument("--sdgs-path", default=str(DEFAULT_SDGS_PATH), help="Path to sdgs.json")
    parser.add_argument("--config", default="config.yaml", help="Path to config.yaml")
    return parser


def main(argv: list[str] | None = None) -> None:
    args = _build_arg_parser().parse_args(argv)
    config = load_config(args.config)
    configure_logging(config)
    inserted, skipped = seed_sdgs(Path(args.sdgs_path), config)
    print(f"inserted {inserted}, skipped {skipped} (already present)")


if __name__ == "__main__":
    main()
