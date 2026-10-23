"""Tests for the targeted pipeline (pagemap.py, tables.py, targeted.py). Fictional data only."""

import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

import fitz

from clic_extract import pagemap
from clic_extract.pagemap import build_page_map, locate
from clic_extract.schema import validate_final
from clic_extract.tables import extract_tables, find_partner_budget, verify_table
from clic_extract.targeted import reconcile, run_one_targeted, shortlist

NOW = datetime(2026, 1, 1, tzinfo=timezone.utc)

BUDGET_ROWS = [
    ["Partner", "Requested grant EUR"],
    ["Alpha Test Oy", "100 000"],
    ["Beta Test Ltd", "50 000"],
    ["Total", "150 000"],
]


def _fictional_pdf(path: Path) -> None:
    """Five pages: cover, two filler pages, a readiness page and a gridded budget table."""
    doc = fitz.open()
    cover = doc.new_page()
    cover.insert_text((72, 72), "FICTIONAL TEST PROPOSAL")
    cover.insert_text((72, 100), "Acronym: FAKEPROJ  Title: Fictional Testing Project")
    cover.insert_text((72, 128), "Call: TEST-CALL-01  Submission 2026-01-15")
    for i in range(2):
        filler = doc.new_page()
        for line in range(10):
            filler.insert_text((72, 72 + 20 * line), f"Work plan narrative line {line} of filler page {i}.")
    readiness = doc.new_page()
    readiness.insert_text((72, 72), "Technology readiness")
    readiness.insert_text((72, 100), "The project starts at TRL 3 and targets TRL 6. MCRL 2 to 5.")
    budget = doc.new_page()
    budget.insert_text((72, 60), "Budget and requested funding")
    x0, y0, widths, height = 72, 80, [200, 160], 24
    for r, row in enumerate(BUDGET_ROWS):
        x = x0
        for c, text in enumerate(row):
            budget.draw_rect(fitz.Rect(x, y0 + r * height, x + widths[c], y0 + (r + 1) * height), color=(0, 0, 0), width=0.8)
            budget.insert_text((x + 4, y0 + r * height + 16), text, fontsize=10)
            x += widths[c]
    doc.save(path)
    doc.close()


def _reply(partners):
    return {
        "content": json.dumps({
            "proposal": {"proposal_acronym": "FAKEPROJ", "proposal_title": "Fictional Testing Project",
                         "call_identifier": "TEST-CALL-01", "submission_date": "2026-01-15"},
            "proposal_facts": {"requested_total": "150 000", "trl_start": 3, "trl_target": 6,
                               "mcrl_start": 2, "mcrl_target": 5},
            "partners": partners,
        }),
        "finish_reason": "stop", "seconds": 0.1, "attempts": 1, "prompt_tokens": 100,
        "completion_tokens": 50, "cost_usd": 0.0001, "model_reported": "fake",
    }


class VerifyTableTests(unittest.TestCase):
    def test_column_adding_up_to_total_is_verified(self):
        result = verify_table(BUDGET_ROWS)
        self.assertEqual(result["columns"], {1: "verified"})
        self.assertTrue(result["verified"])

    def test_wrong_total_fails(self):
        rows = BUDGET_ROWS[:-1] + [["Total", "160 000"]]
        result = verify_table(rows)
        self.assertEqual(result["columns"], {1: "failed"})
        self.assertFalse(result["verified"])

    def test_euro_format_and_percentages(self):
        rows = [["Partner", "%", "Requested grant €"],
                ["P1", "60%", "€ 600,000.00"], ["P2", "40%", "€ 400,000.00"],
                ["Tot", "", "€ 1,000,000.00"]]
        self.assertEqual(verify_table(rows)["columns"], {2: "verified"})

    def test_row_total_column_is_checked(self):
        rows = [["", "A", "B", "Total"], ["X", "5 000", "15 000", "20000"], ["Y", "1", "1", "3"]]
        row_checks = [c for c in verify_table(rows)["checks"] if c["kind"] == "row"]
        self.assertEqual([c["ok"] for c in row_checks], [True, False])

    def test_section_heading_resets_the_running_sum(self):
        rows = [["Group A", ""], ["a1", "10"], ["Total", "10"], ["Group B", ""], ["b1", "7"], ["Total", "7"]]
        self.assertEqual(verify_table(rows)["columns"], {1: "verified"})

    def test_find_partner_budget_prefers_requested_column(self):
        table = {"page": 5, "index": 0, "rows": BUDGET_ROWS}
        budget = find_partner_budget([table])
        self.assertEqual([p["name"] for p in budget["partners"]], ["Alpha Test Oy", "Beta Test Ltd"])
        self.assertEqual(budget["total_text"], "150 000")


class LocateTests(unittest.TestCase):
    def _map(self, pages, outline=()):
        return {"page_count": len(pages), "outline": list(outline), "pages": pages}

    def _page(self, n, text="", header=(), tables=0):
        return {"page": n, "hits": pagemap.keyword_hits(text), "header": list(header), "table_count": tables}

    def test_page_with_keywords_and_table_wins(self):
        pm = self._map([self._page(1, "intro"), self._page(2, "budget total EUR", tables=1), self._page(3, "budget")])
        self.assertEqual(locate(pm, "budget")[0]["page"], 2)

    def test_outline_entry_adds_a_bonus(self):
        pm = self._map([self._page(1, "TRL"), self._page(2, "TRL")], outline=[{"level": 1, "title": "Technology readiness", "page": 2}])
        self.assertEqual(locate(pm, "readiness")[0]["page"], 2)

    def test_nothing_found_returns_none(self):
        pm = self._map([self._page(1, "nothing relevant"), self._page(2, "still nothing")])
        self.assertIsNone(locate(pm, "readiness"))

    def test_shortlist_takes_each_groups_best_page_first(self):
        located = {"proposal": [{"page": 1, "score": 3}], "budget": [{"page": 9, "score": 9}, {"page": 4, "score": 5}],
                   "partners": None, "readiness": [{"page": 6, "score": 2}]}
        self.assertEqual(shortlist(located, limit=3), [1, 6, 9])

    def test_shortlist_accepts_pages_without_a_numeric_score(self):
        located = {"proposal": [{"page": 1, "score": 3}, {"page": 7, "score": "hint"}],
                   "budget": None, "partners": None, "readiness": [{"page": 4, "score": None}, {"page": 5, "score": None}]}
        self.assertEqual(shortlist(located), [1, 4, 5, 7])


class PageMapCacheTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.pdf = Path(self.tmp.name) / "fictional.pdf"
        _fictional_pdf(self.pdf)
        self.cache = Path(self.tmp.name) / "cache"

    def test_second_call_reads_the_cache(self):
        first = build_page_map(self.pdf, self.cache)
        second = build_page_map(self.pdf, self.cache)
        self.assertFalse(first["from_cache"])
        self.assertTrue(second["from_cache"])
        self.assertEqual(first["pages"], second["pages"])

    def test_version_change_rebuilds(self):
        build_page_map(self.pdf, self.cache)
        with patch.object(pagemap, "PAGE_MAP_VERSION", pagemap.PAGE_MAP_VERSION + 1):
            self.assertFalse(build_page_map(self.pdf, self.cache)["from_cache"])

    def test_budget_table_is_parsed_and_verified(self):
        pm = build_page_map(self.pdf, self.cache)
        self.assertEqual(locate(pm, "budget")[0]["page"], 5)
        tables = extract_tables(self.pdf, [5])
        self.assertTrue(any(verify_table(t["rows"])["verified"] for t in tables))


class RunOneTargetedTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.pdf = Path(self.tmp.name) / "fictional.pdf"
        _fictional_pdf(self.pdf)
        self.out = Path(self.tmp.name) / "out"
        self.cache = Path(self.tmp.name) / "cache"

    def _run(self, mode, partners):
        sent = []

        def fake_chat(arm, messages, schema, token, use_extras=True):
            sent.append(messages)
            return _reply(partners)

        with patch("clic_extract.targeted.chat", fake_chat):
            run = run_one_targeted(self.pdf, self.out, mode, "fake_token", NOW, cache_dir=self.cache)
        return run, sent

    def test_text_mode_sends_only_located_pages_and_writes_outputs(self):
        partners = [{"partner_name": "Alpha Test Oy", "requested": "100 000"},
                    {"partner_name": "Beta Test Ltd", "requested": None}]
        run, sent = self._run("text", partners)
        self.assertEqual(run["status"], "ok", run["error"])
        self.assertEqual(len(sent), 1)  # every group located by keywords, no page-pick call
        user_text = sent[0][1]["content"]
        self.assertIsInstance(user_text, str)  # text mode never sends images
        self.assertNotIn("filler page", user_text)
        self.assertIn("<!-- page 5 -->", user_text)
        self.assertIn("VERIFIED", user_text)
        final = json.loads((self.out / run["output_file"]).read_text(encoding="utf-8"))
        self.assertEqual(validate_final(final), [])
        # Alpha confirmed by the table; Beta's missing amount filled from the verified table.
        self.assertEqual([p["requested_cents"] for p in final["partners"]], [10_000_000, 5_000_000])
        self.assertEqual(run["partners_confirmed_by_table"], 2)
        self.assertTrue((self.out / run["trace_file"]).exists())
        self.assertNotIn(2, run["pages_sent"])

    def test_multimodal_mode_attaches_page_images(self):
        run, sent = self._run("multimodal", [{"partner_name": "Alpha Test Oy", "requested": "100 000"}])
        self.assertEqual(run["status"], "ok", run["error"])
        images = [b for b in sent[-1][1]["content"] if b["type"] == "image_url"]
        self.assertEqual(len(images), run["images_sent"])
        self.assertEqual(len(images), len(run["pages_sent"]))

    def test_amount_not_on_the_verified_row_is_flagged(self):
        final = {"partners": [{"partner_name": "Alpha Test Oy", "requested_cents": 999}]}
        tables = [{"page": 5, "index": 0, "rows": BUDGET_ROWS, "verification": verify_table(BUDGET_ROWS)}]
        warnings, results = reconcile(final, tables, find_partner_budget(tables))
        self.assertEqual(results[0]["status"], "mismatch")
        self.assertEqual(len(warnings), 1)


if __name__ == "__main__":
    unittest.main()
