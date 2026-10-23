"""Inputs too large for the model's context are split and retried, never refused. Fictional data only."""

import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

import fitz

from clic_extract.backends import BackendError
from clic_extract.fit import is_too_large, merge_raw_dicts, split_text
from clic_extract.multimodal import run_one_combined, run_one_multimodal
from clic_extract.run_extract import run_one
from clic_extract.targeted import run_one_targeted

NOW = datetime(2026, 1, 1, tzinfo=timezone.utc)
ARM = {"model": "fake/model", "provider": "fake", "max_tokens": 100, "input_per_m": 0, "output_per_m": 0,
       "context_length": 1000}
CONTEXT_ERROR = ("HTTP 400: {\"error\":{\"message\":\"This model's maximum context length is 1000 tokens. "
                 "Please reduce the length of the input prompt.\"}}")
GROQ_ERROR = 'HTTP 400: {"error":{"message":"Please reduce the length of the messages or completion."}}'

PARAGRAPH = "Work plan narrative of the FICTIONAL TEST project, with nothing to extract in it. " * 6


def fictional_document() -> str:
    """FICTIONAL TEST DATA: acronym and total near the top, the partner table near the end."""
    parts = ["# FAKEPROJ Fictional Testing Project\n\nRequested total: EUR 300,000.00\n"]
    parts += [f"## Section {i}\n\n{PARAGRAPH}\n" for i in range(30)]
    parts.append("## Budget\n\n| Partner | Requested |\n|---|---|\n| Alpha Test Oy | EUR 100,000.00 |\n"
                 "| Beta Test Ltd | EUR 200,000.00 |\n")
    return "\n".join(parts)


def reply_for(text: str) -> dict:
    """What a fake model reads off its part of the fictional document."""
    partners = [{"partner_name": n, "requested": a} for n, a in
                (("Alpha Test Oy", "EUR 100,000.00"), ("Beta Test Ltd", "EUR 200,000.00")) if n in text]
    raw = {"proposal": {"proposal_acronym": "FAKEPROJ" if "FAKEPROJ" in text else None, "proposal_title": None,
                        "call_identifier": None, "submission_date": None},
           "proposal_facts": {"requested_total": "EUR 300,000.00" if "Requested total" in text else None,
                              "trl_start": None, "trl_target": None, "mcrl_start": None, "mcrl_target": None},
           "partners": partners}
    return {"content": json.dumps(raw), "finish_reason": "stop", "seconds": 0.1, "attempts": 1,
            "prompt_tokens": len(text) // 4, "completion_tokens": 10, "cost_usd": 0.0, "model_reported": "fake"}


def limited_chat(limit_chars: int, sent: list):
    """A fake provider that rejects any request whose text is longer than limit_chars."""
    def fake_chat(arm, messages, schema, token, use_extras=True):
        content = messages[1]["content"]
        text = content if isinstance(content, str) else " ".join(b.get("text", "") for b in content)
        if len(text) > limit_chars:
            raise BackendError(CONTEXT_ERROR)
        sent.append(text)
        return reply_for(text)
    return fake_chat


class DetectionTests(unittest.TestCase):
    def test_provider_wordings_of_a_context_error_are_recognised(self):
        self.assertTrue(is_too_large(BackendError(CONTEXT_ERROR)))
        self.assertTrue(is_too_large(BackendError(GROQ_ERROR)))
        self.assertTrue(is_too_large(BackendError('HTTP 413: {"error":"request entity too large"}')))

    def test_other_errors_are_not_treated_as_too_large(self):
        self.assertFalse(is_too_large(BackendError("HTTP 400: invalid schema")))
        self.assertFalse(is_too_large(BackendError("HTTP 503: maximum context length")))
        self.assertFalse(is_too_large(BackendError("network error: timed out")))


class SplitTextTests(unittest.TestCase):
    def test_halves_cover_the_whole_text_near_the_middle(self):
        text = fictional_document()
        first, second = split_text(text)
        self.assertTrue(text.startswith(first))
        self.assertIn(second.split("\n", 1)[1].strip()[:200], text)
        self.assertLess(abs(len(first) - len(text) / 2), len(text) / 4)

    def test_a_table_is_never_cut_when_another_place_exists(self):
        text = "# T\n\n" + PARAGRAPH * 20 + "\n\n| a | b |\n|---|---|\n" + "| x | 1 |\n" * 200
        first, second = split_text(text)
        self.assertFalse(first.rstrip().endswith("|") and second.lstrip().startswith("|"))

    def test_a_huge_table_is_cut_between_rows_with_its_header_repeated(self):
        text = "| Partner | Requested |\n|---|---|\n" + "".join(f"| Partner {i} | {i} |\n" for i in range(400))
        first, second = split_text(text)
        self.assertTrue(second.startswith("| Partner | Requested |\n|---|---|\n"))
        self.assertEqual(len(first.splitlines()) + len(second.splitlines()) - 2, len(text.splitlines()))

    def test_section_heading_is_repeated_for_the_second_half(self):
        text = "## Budget\n\n" + (PARAGRAPH + "\n\n") * 20
        _, second = split_text(text)
        self.assertTrue(second.startswith("## Budget (continued)"))

    def test_short_text_is_not_split(self):
        self.assertIsNone(split_text("short"))

    def test_merge_keeps_first_value_and_all_partners(self):
        merged = merge_raw_dicts([
            {"proposal": {"proposal_acronym": "A"}, "proposal_facts": {}, "partners": [{"partner_name": "X"}]},
            {"proposal": {"proposal_acronym": "B"}, "proposal_facts": {"trl_start": 3}, "partners": [{"partner_name": "Y"}]},
        ])
        self.assertEqual(merged["proposal"]["proposal_acronym"], "A")
        self.assertEqual(merged["proposal_facts"]["trl_start"], 3)
        self.assertEqual([p["partner_name"] for p in merged["partners"]], ["X", "Y"])


class TextPathTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dir = Path(self.tmp.name)
        self.md = self.dir / "fictional.md"
        self.md.write_text(fictional_document(), encoding="utf-8")

    def test_document_that_fits_is_sent_whole_in_one_call(self):
        sent = []
        with patch("clic_extract.run_extract.chat", limited_chat(10**9, sent)):
            run = run_one("B", ARM, self.md, self.dir, "fake_token", True, NOW)
        self.assertEqual(run["status"], "ok", run["error"])
        self.assertEqual((len(sent), run["context_splits"], run["parts"]), (1, 0, 1))

    def test_document_too_large_is_split_and_every_value_still_found(self):
        sent = []
        limit = len(fictional_document()) // 3
        with patch("clic_extract.run_extract.chat", limited_chat(limit, sent)):
            run = run_one("B", ARM, self.md, self.dir, "fake_token", True, NOW)
        self.assertEqual(run["status"], "ok", run["error"])
        self.assertGreaterEqual(run["context_splits"], 2)
        self.assertEqual(run["parts"], len(sent))
        self.assertTrue(all(len(t) <= limit for t in sent))
        final = json.loads((self.dir / run["output_file"]).read_text(encoding="utf-8"))
        self.assertEqual(final["proposal"]["proposal_acronym"], "FAKEPROJ")
        self.assertEqual(final["proposal_facts"]["requested_total_cents"], 30_000_000)
        self.assertEqual([p["requested_cents"] for p in final["partners"]], [10_000_000, 20_000_000])
        replies = json.loads((self.dir / run["replies_file"]).read_text(encoding="utf-8"))
        self.assertEqual(len(replies), len(sent))

    def test_free_form_document_too_large_is_split_as_well(self):
        from clic_extract.freeform import run_one_freeform
        sent = []
        with patch("clic_extract.run_extract.chat", limited_chat(len(fictional_document()) // 2, sent)):
            run = run_one_freeform(self.md, self.dir, "fake_token", NOW)
        self.assertEqual(run["status"], "ok", run["error"])
        self.assertGreaterEqual(run["parts"], 2)
        self.assertIn("=== next part ===", (self.dir / run["freeform_file"]).read_text(encoding="utf-8"))

    def test_other_errors_still_fail_the_run(self):
        def fail(*a, **k):
            raise BackendError("HTTP 401: unauthorised")
        with patch("clic_extract.run_extract.chat", fail):
            run = run_one("B", ARM, self.md, self.dir, "fake_token", True, NOW)
        self.assertEqual(run["status"], "failed")
        self.assertIn("401", run["error"])


def _table_pdf(path: Path, pages: int) -> None:
    """FICTIONAL TEST DATA: every page has a small grid table and the partner names."""
    doc = fitz.open()
    for i in range(pages):
        page = doc.new_page()
        page.insert_text((72, 60), f"FICTIONAL TEST DATA page {i + 1} FAKEPROJ Requested total Alpha Test Oy")
        for r in range(3):
            for c in range(2):
                rect = fitz.Rect(72 + 150 * c, 80 + 24 * r, 222 + 150 * c, 104 + 24 * r)
                page.draw_rect(rect, color=(0, 0, 0), width=0.8)
                page.insert_text((rect.x0 + 4, rect.y0 + 16), f"cell {r}{c}", fontsize=10)
    doc.save(path)
    doc.close()


class ImagePathTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dir = Path(self.tmp.name)
        self.pdf = self.dir / "fictional.pdf"
        _table_pdf(self.pdf, 4)

    def test_images_only_batch_rejected_for_context_is_split(self):
        calls = []

        def fake_chat(arm, messages, schema, token, use_extras=True):
            images = sum(1 for b in messages[1]["content"] if b["type"] == "image_url")
            calls.append(images)
            if images > 2:
                raise BackendError(CONTEXT_ERROR)
            return reply_for("FAKEPROJ")

        with patch("clic_extract.multimodal.chat", fake_chat):
            run = run_one_multimodal(self.pdf, self.dir, "fake_token", NOW, batch_size=4, overlap=0)
        self.assertEqual(run["status"], "ok", run["error"])
        self.assertEqual(calls, [4, 2, 2])
        self.assertIn("(context length)", run["warnings"][0])

    def test_combined_splits_images_first_then_the_text(self):
        document_text = fictional_document()
        limit = len(document_text) // 2
        seen = []

        def fake_chat(arm, messages, schema, token, use_extras=True):
            content = messages[1]["content"]
            images = sum(1 for b in content if b["type"] == "image_url")
            text = content[0]["text"]
            if images > 1 or len(text) > limit:
                raise BackendError(CONTEXT_ERROR)
            seen.append((images, len(text)))
            return reply_for(text)

        with patch("clic_extract.multimodal.chat", fake_chat):
            run = run_one_combined(self.pdf, document_text, self.dir, "qwen_vl", "fake_token", NOW,
                                   batch_size=4, overlap=0)
        self.assertEqual(run["status"], "ok", run["error"])
        self.assertTrue(all(images == 1 for images, _ in seen))
        self.assertGreaterEqual(run["context_splits"], 1)
        final = json.loads((self.dir / run["output_file"]).read_text(encoding="utf-8"))
        self.assertEqual(final["proposal_facts"]["requested_total_cents"], 30_000_000)

    def test_targeted_pages_are_split_into_groups_when_rejected(self):
        groups = []

        def fake_chat(arm, messages, schema, token, use_extras=True):
            if schema is None:  # the page picking call, not an extraction
                return {**reply_for(""), "content": '{"pages": {}}'}
            text = messages[1]["content"] if isinstance(messages[1]["content"], str) else messages[1]["content"][0]["text"]
            pages = text.count("<!-- page ")
            if pages > 1:
                raise BackendError(GROQ_ERROR)
            groups.append(pages)
            return reply_for(text)

        with patch("clic_extract.targeted.chat", fake_chat):
            run = run_one_targeted(self.pdf, self.dir, "text", "fake_token", NOW, cache_dir=None)
        self.assertEqual(run["status"], "ok", run["error"])
        self.assertEqual(groups, [1] * len(run["pages_sent"]))
        self.assertEqual(run["context_splits"], len(run["pages_sent"]) - 1)


if __name__ == "__main__":
    unittest.main()
