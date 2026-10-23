"""Every run path saves its raw extraction replies, before any repair, as <base>.replies.json.
Fictional data only."""

import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

import fitz

from clic_extract.backends import BackendError
from clic_extract.multimodal import run_one_combined, run_one_multimodal
from clic_extract.run_extract import run_one
from clic_extract.targeted import run_one_targeted

NOW = datetime(2026, 1, 1, tzinfo=timezone.utc)
ARM = {"model": "fake/model", "provider": "fake", "max_tokens": 100, "input_per_m": 0, "output_per_m": 0}
RAW = {
    "proposal": {"proposal_acronym": "FAKEPROJ", "proposal_title": "Fictional Testing Project",
                 "call_identifier": None, "submission_date": None},
    "proposal_facts": {"requested_total": None, "trl_start": None, "trl_target": None,
                       "mcrl_start": None, "mcrl_target": None},
    "partners": [{"partner_name": "Alpha Test Oy", "requested": "EUR 100,000.00"}],
}


def _result(content):
    return {"content": content, "finish_reason": "stop", "seconds": 0.1, "attempts": 1,
            "prompt_tokens": 10, "completion_tokens": 10, "cost_usd": 0.0, "model_reported": "fake"}


def _pdf(path: Path, pages: int) -> None:
    """FICTIONAL TEST DATA: pages with a small text grid, so they count as table pages."""
    doc = fitz.open()
    for i in range(pages):
        page = doc.new_page()
        page.insert_text((72, 60), f"FICTIONAL TEST DATA page {i + 1} FAKEPROJ Alpha Test Oy")
        for r in range(3):
            for c in range(2):
                rect = fitz.Rect(72 + 150 * c, 80 + 24 * r, 222 + 150 * c, 104 + 24 * r)
                page.draw_rect(rect, color=(0, 0, 0), width=0.8)
                page.insert_text((rect.x0 + 4, rect.y0 + 16), f"cell {r}{c}", fontsize=10)
    doc.save(path)
    doc.close()


class RepliesFileTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dir = Path(self.tmp.name)

    def _replies(self, run):
        return json.loads((self.dir / run["replies_file"]).read_text(encoding="utf-8"))

    def test_text_run_saves_the_reply_exactly_as_returned(self):
        md = self.dir / "fictional.md"
        md.write_text("# FAKEPROJ Fictional Testing Project, Alpha Test Oy EUR 100,000.00", encoding="utf-8")
        fenced = "```json\n" + json.dumps(RAW) + "\n```"  # needs repair: the scorer must see the fence
        with patch("clic_extract.run_extract.chat", lambda *a, **k: _result(fenced)):
            run = run_one("B", ARM, md, self.dir, "fake_token", True, NOW)
        self.assertEqual(run["status"], "ok", run["error"])
        self.assertEqual(run["replies_file"], "fictional_20260101T000000Z.replies.json")
        self.assertEqual(self._replies(run), [fenced])

    def test_failed_text_run_still_saves_its_reply(self):
        md = self.dir / "fictional.md"
        md.write_text("# FAKEPROJ", encoding="utf-8")
        with patch("clic_extract.run_extract.chat", lambda *a, **k: _result("not json at all")):
            run = run_one("B", ARM, md, self.dir, "fake_token", True, NOW)
        self.assertEqual(run["status"], "failed")
        self.assertEqual(self._replies(run), ["not json at all"])

    def test_text_run_without_any_reply_saves_an_empty_list(self):
        md = self.dir / "fictional.md"
        md.write_text("# FAKEPROJ", encoding="utf-8")

        def fail(*a, **k):
            raise BackendError("HTTP 500: fictional outage")

        with patch("clic_extract.run_extract.chat", fail):
            run = run_one("B", ARM, md, self.dir, "fake_token", True, NOW)
        self.assertEqual(self._replies(run), [])

    def test_batched_runs_save_one_reply_per_successful_call(self):
        pdf = self.dir / "fictional.pdf"
        _pdf(pdf, pages=4)
        calls = []

        def fake_chat(arm, messages, schema, token, use_extras=True):
            calls.append(1)
            if len(calls) == 1:
                raise BackendError('HTTP 413: {"error":"request entity too large"}')
            return _result(f"reply {len(calls)} " + json.dumps(RAW))

        for runner in (
            lambda: run_one_multimodal(pdf, self.dir, "fake_token", NOW, batch_size=4, overlap=0),
            lambda: run_one_combined(pdf, "FAKEPROJ Alpha Test Oy EUR 100,000.00", self.dir, "qwen_vl",
                                     "fake_token", NOW, batch_size=4, overlap=0),
        ):
            calls.clear()
            with patch("clic_extract.multimodal.chat", fake_chat):
                run = runner()
            self.assertEqual(run["status"], "ok", run["error"])
            replies = self._replies(run)
            self.assertEqual(len(replies), 2)  # the 413 call returned no reply
            self.assertTrue(replies[0].startswith("reply 2 ") and replies[1].startswith("reply 3 "))

    def test_targeted_run_saves_only_the_extraction_reply(self):
        pdf = self.dir / "fictional.pdf"
        _pdf(pdf, pages=2)
        sent = []

        def fake_chat(arm, messages, schema, token, use_extras=True):
            sent.append(schema)
            if schema is None:  # page picking fallback
                return _result('{"pages": {}}')
            return _result(json.dumps(RAW))

        with patch("clic_extract.targeted.chat", fake_chat):
            run = run_one_targeted(pdf, self.dir, "text", "fake_token", NOW, cache_dir=self.dir / "cache")
        self.assertEqual(run["status"], "ok", run["error"])
        self.assertEqual(self._replies(run), [json.dumps(RAW)])


if __name__ == "__main__":
    unittest.main()
