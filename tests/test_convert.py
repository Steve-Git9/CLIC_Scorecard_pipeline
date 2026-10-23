from __future__ import annotations

from pathlib import Path

import fitz

from src.pipeline.convert import _needs_ocr


def _make_pdf(path: Path, page_line_counts: list[int]) -> None:
    """One page per entry, each with that many lines of fictional text (insert_text does not
    wrap, so multiple lines are needed to exceed a char-count threshold realistically)."""
    doc = fitz.open()
    for lines in page_line_counts:
        page = doc.new_page()
        for i in range(lines):
            page.insert_text((72, 72 + i * 14), f"FICTIONAL TEST DATA line {i}")
    doc.save(path)
    doc.close()


def test_every_page_has_text_does_not_need_ocr(tmp_path: Path) -> None:
    pdf_path = tmp_path / "clean.pdf"
    _make_pdf(pdf_path, [10] * 10)
    assert _needs_ocr(pdf_path, ocr_min_chars_per_page=100) is False


def test_single_sparse_cover_page_is_tolerated(tmp_path: Path) -> None:
    """Regression: a real 38-page proposal's cover page (title + date only, 98 characters)
    fell under the threshold and forced OCR across the whole document for one normal, fully
    readable page. One sparse page out of many should not trigger OCR by itself."""
    pdf_path = tmp_path / "cover_page.pdf"
    _make_pdf(pdf_path, [0] + [10] * 9)  # page 1 sparse, 9 pages of real text
    assert _needs_ocr(pdf_path, ocr_min_chars_per_page=100) is False


def test_several_sparse_pages_need_ocr(tmp_path: Path) -> None:
    pdf_path = tmp_path / "mostly_scanned.pdf"
    _make_pdf(pdf_path, [0, 0, 0, 10, 10])  # 3 of 5 pages sparse
    assert _needs_ocr(pdf_path, ocr_min_chars_per_page=100) is True


def test_entirely_blank_document_needs_ocr(tmp_path: Path) -> None:
    pdf_path = tmp_path / "blank.pdf"
    _make_pdf(pdf_path, [0, 0])
    assert _needs_ocr(pdf_path, ocr_min_chars_per_page=100) is True


def test_threshold_is_respected(tmp_path: Path) -> None:
    pdf_path = tmp_path / "short.pdf"
    _make_pdf(pdf_path, [1, 1])
    assert _needs_ocr(pdf_path, ocr_min_chars_per_page=100) is True
    assert _needs_ocr(pdf_path, ocr_min_chars_per_page=1) is False
