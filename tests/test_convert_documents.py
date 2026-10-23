"""Tests for src/evaluation/convert_documents.py. FICTIONAL TEST DATA ONLY; docling itself is
replaced by a stub so the test checks the timing record, not the conversion."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from src.evaluation import convert_documents


@pytest.fixture
def stub_docling(monkeypatch):
    def fake(pdf_path, threshold=100):
        return "# FICTIONAL TEST DATA\n\n| Imaginary Labs Oy | 1,000.00 |\n", {
            "ocr_used": False, "tables": 1, "pictures": 0,
            "setup_seconds": 0.1, "convert_seconds": 0.2, "export_seconds": 0.0,
        }
    monkeypatch.setattr(convert_documents, "convert_pdf_with_stats", fake)


def test_conversion_writes_markdown_record_and_csv_row(stub_docling, fictional_pdf: Path, tmp_path: Path):
    out = tmp_path / "markdown"
    record = convert_documents.convert_one(fictional_pdf, out)
    convert_documents.append_csv(out / "conversions.csv", record)

    md = out / "fictional_proposal.md"
    assert md.read_text(encoding="utf-8").startswith("# FICTIONAL TEST DATA")
    saved = json.loads((out / "fictional_proposal.conversion.json").read_text(encoding="utf-8"))
    assert saved["document"] == "fictional_proposal"
    assert saved["pages"] == 3
    assert saved["total_seconds"] >= 0 and saved["convert_seconds"] == 0.2
    assert saved["seconds_per_page"] == pytest.approx(saved["total_seconds"] / 3, abs=1e-3)
    assert saved["markdown_chars"] == len(md.read_text(encoding="utf-8"))
    assert len(saved["pdf_sha256"]) == 64 and saved["tool"] == "docling"
    rows = list(csv.DictReader((out / "conversions.csv").open(encoding="utf-8")))
    assert [r["document"] for r in rows] == ["fictional_proposal"]


def test_command_converts_every_pdf_in_the_raw_folder(stub_docling, test_config, fictional_pdf: Path):
    test_config.paths.raw.mkdir(parents=True)
    for name in ("FICTA.pdf", "FICTB.pdf"):
        (test_config.paths.raw / name).write_bytes(fictional_pdf.read_bytes())
    config_file = test_config.paths.raw.parent.parent / "config.yaml"
    convert_documents.main(["--config", str(config_file)])
    assert sorted(p.name for p in test_config.paths.markdown.glob("*.md")) == ["FICTA.md", "FICTB.md"]
    rows = list(csv.DictReader((test_config.paths.markdown / "conversions.csv").open(encoding="utf-8")))
    assert [r["document"] for r in rows] == ["FICTA", "FICTB"]
