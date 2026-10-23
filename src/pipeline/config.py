"""Configuration loading and logging setup for the CLIC KPI pipeline."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

import yaml
from dotenv import load_dotenv


@dataclass(frozen=True)
class PathsConfig:
    raw: Path
    markdown: Path
    runs: Path
    logs: Path
    database: Path


@dataclass(frozen=True)
class Config:
    paths: PathsConfig
    settings: dict


def load_config(path: str | Path = "config.yaml") -> Config:
    """Load pipeline configuration from a YAML file and .env secrets."""
    config_path = Path(path)
    if not config_path.exists():
        raise FileNotFoundError(
            f"{config_path} not found. Copy config.example.yaml to {config_path} and adjust it."
        )

    load_dotenv()

    with config_path.open("r", encoding="utf-8") as f:
        settings = yaml.safe_load(f) or {}

    paths_settings = settings.get("paths", {})
    paths = PathsConfig(
        raw=Path(paths_settings["raw"]),
        markdown=Path(paths_settings["markdown"]),
        runs=Path(paths_settings["runs"]),
        logs=Path(paths_settings["logs"]),
        database=Path(paths_settings["database"]),
    )
    return Config(paths=paths, settings=settings)


def configure_logging(config: Config) -> None:
    """Configure the "pipeline" logger to write to console and data/logs."""
    config.paths.logs.mkdir(parents=True, exist_ok=True)
    log_file = config.paths.logs / "pipeline.log"

    logger = logging.getLogger("pipeline")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
