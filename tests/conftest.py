from __future__ import annotations

from pathlib import Path

import fitz
import pytest
import yaml

from src.pipeline.config import Config, load_config


@pytest.fixture
def fictional_pdf(tmp_path: Path) -> Path:
    """A small, clearly fictional multi-page PDF used only for tests."""
    pdf_path = tmp_path / "fictional_proposal.pdf"
    doc = fitz.open()
    for i in range(3):
        page = doc.new_page()
        page.insert_text(
            (72, 72),
            f"FICTIONAL TEST DATA - page {i + 1}\nProposal: Imaginary Partnership Initiative",
        )
    doc.save(pdf_path)
    doc.close()
    return pdf_path


@pytest.fixture
def test_config(tmp_path: Path) -> Config:
    """A Config pointed entirely at a temp directory, never touching real data/."""
    data_dir = tmp_path / "data"
    config_path = tmp_path / "config.yaml"
    config_data = {
        "paths": {
            "raw": str(data_dir / "raw"),
            "markdown": str(data_dir / "markdown"),
            "runs": str(data_dir / "runs"),
            "logs": str(data_dir / "logs"),
            "database": str(data_dir / "clic.db"),
        }
    }
    config_path.write_text(yaml.safe_dump(config_data), encoding="utf-8")
    return load_config(config_path)
