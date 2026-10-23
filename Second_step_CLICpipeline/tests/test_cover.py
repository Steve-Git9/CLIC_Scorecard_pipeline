"""Tests for the identifier hints (clic_extract.cover). Fictional data only."""

import tempfile
import unittest
from pathlib import Path

import fitz

from clic_extract.cover import acronym_candidates, fill_identifiers, find_hints


def _pdf(path: Path, cover: list[tuple[str, float]], body: str = "") -> None:
    doc = fitz.open()
    page = doc.new_page()
    y = 80
    for text, size in cover:
        page.insert_text((72, y), text, fontsize=size)
        y += size + 14
    if body:
        page2 = doc.new_page()
        for i, line in enumerate(body.splitlines()):
            page2.insert_text((72, 72 + 18 * i), line, fontsize=10)
    doc.save(path)
    doc.close()


def _final():
    return {"proposal": {"proposal_acronym": None, "proposal_title": None, "call_identifier": None,
                         "submission_date": None}}


class CoverHintTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.pdf = Path(self.tmp.name) / "fictional.pdf"

    def test_largest_cover_lines_form_the_title_and_acronym(self):
        _pdf(self.pdf, [("Fictional Circular Testing", 26), ("Materials FICTO", 26), ("Project plan, January 2026", 18),
                        ("CONFIDENTIAL", 12)])
        hints = find_hints(self.pdf)
        self.assertEqual(hints["cover_title"], "Fictional Circular Testing Materials FICTO")
        self.assertEqual(hints["acronym_candidates"], ["FICTO"])

    def test_labels_and_call_identifier_pattern_are_found(self):
        _pdf(self.pdf, [("FAKEPROJ", 24)],
             body="Acronym: FAKEPROJ\nCall: TESTPROG-CL9-2026-X1-01\nWork package WP1-T1 runs all year.")
        hints = find_hints(self.pdf)
        self.assertEqual([h["value"] for h in hints["labelled"]["acronym"]], ["FAKEPROJ"])
        self.assertEqual([c["id"] for c in hints["call_ids"]], ["TESTPROG-CL9-2026-X1-01"])  # WP1-T1 has no year

    def test_short_cover_name_is_its_own_acronym(self):
        self.assertEqual(acronym_candidates("Fake Map"), ["Fake Map"])
        self.assertEqual(acronym_candidates("A long descriptive title without any short code"), [])

    def test_fill_only_empty_fields_and_warn(self):
        _pdf(self.pdf, [("Fictional Testing Project FAKE", 24)], body="Topic: TESTPROG-CL9-2026-X1-01")
        hints = find_hints(self.pdf)
        final = _final()
        final["proposal"]["proposal_title"] = "Model Title"
        warnings, filled = fill_identifiers(final, hints)
        self.assertEqual(final["proposal"]["proposal_acronym"], "FAKE")
        self.assertEqual(final["proposal"]["proposal_title"], "Model Title")  # the model's value is kept
        self.assertEqual(final["proposal"]["call_identifier"], "TESTPROG-CL9-2026-X1-01")
        self.assertEqual(set(filled), {"proposal_acronym", "call_identifier"})
        self.assertEqual(len(warnings), 2)


if __name__ == "__main__":
    unittest.main()
