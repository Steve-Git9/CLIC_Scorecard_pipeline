import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

import fitz

from clic_extract.backends import BackendError, build_request
from clic_extract.multimodal import (
    build_multimodal_messages,
    chunk_pages,
    merge_raw_dicts,
    pages_needing_visual_check,
    run_one_combined,
    run_one_multimodal,
)
from clic_extract.postprocess import build_final
from clic_extract.prompts import OPEN_VISION_SYSTEM_PROMPT, VISION_SYSTEM_PROMPT
from clic_extract.schema import RAW_SCHEMA, validate_final

NOW = datetime(2026, 1, 1, tzinfo=timezone.utc)


class BuildMultimodalMessagesTests(unittest.TestCase):
    ARM = {"model": "m", "provider": "p", "max_tokens": 3000}

    def test_strict_uses_the_strict_prompt_and_response_format(self):
        messages = build_multimodal_messages([b"page"], strict=True)
        self.assertEqual(messages[0]["content"], VISION_SYSTEM_PROMPT)
        request = build_request(self.ARM, messages, RAW_SCHEMA)
        self.assertIn("response_format", request)

    def test_open_uses_the_open_prompt_and_no_response_format(self):
        messages = build_multimodal_messages([b"page"], strict=False)
        self.assertEqual(messages[0]["content"], OPEN_VISION_SYSTEM_PROMPT)
        request = build_request(self.ARM, messages, None)
        self.assertNotIn("response_format", request)

    def test_open_prompt_still_asks_for_the_same_fields_as_strict(self):
        # Field definitions must stay identical between strict and open so results
        # remain comparable - only the framing instruction should differ.
        for field in ("proposal_acronym", "requested_total", "partner_name"):
            self.assertIn(field, OPEN_VISION_SYSTEM_PROMPT)
            self.assertIn(field, VISION_SYSTEM_PROMPT)


class ChunkPagesTests(unittest.TestCase):
    def test_splits_into_even_groups_with_remainder(self):
        pages = [b"1", b"2", b"3", b"4", b"5", b"6", b"7"]
        self.assertEqual(
            chunk_pages(pages, 3),
            [[b"1", b"2", b"3"], [b"4", b"5", b"6"], [b"7"]],
        )

    def test_batch_size_larger_than_pages_gives_one_batch(self):
        pages = [b"1", b"2"]
        self.assertEqual(chunk_pages(pages, 10), [[b"1", b"2"]])

    def test_overlap_repeats_the_boundary_page_between_batches(self):
        pages = [b"1", b"2", b"3", b"4", b"5", b"6", b"7"]
        self.assertEqual(
            chunk_pages(pages, 3, overlap=1),
            [[b"1", b"2", b"3"], [b"3", b"4", b"5"], [b"5", b"6", b"7"]],
        )

    def test_overlap_still_covers_every_page_with_an_uneven_remainder(self):
        pages = list(range(10))
        batches = chunk_pages(pages, 5, overlap=1)
        covered = {p for batch in batches for p in batch}
        self.assertEqual(covered, set(pages))
        self.assertEqual(batches, [[0, 1, 2, 3, 4], [4, 5, 6, 7, 8], [8, 9]])

    def test_rejects_overlap_not_smaller_than_batch_size(self):
        with self.assertRaises(ValueError):
            chunk_pages([b"1", b"2"], 2, overlap=2)

    def test_rejects_negative_overlap(self):
        with self.assertRaises(ValueError):
            chunk_pages([b"1"], 1, overlap=-1)

    def test_rejects_non_positive_batch_size(self):
        with self.assertRaises(ValueError):
            chunk_pages([b"1"], 0)


class MergeRawDictsTests(unittest.TestCase):
    def test_first_non_null_wins_for_scalars_partners_concatenate(self):
        batch1 = {
            "proposal": {"proposal_acronym": "ABC", "proposal_title": None,
                         "call_identifier": None, "submission_date": None},
            "proposal_facts": {"requested_total": "EUR 3,000.00", "trl_start": None,
                                "trl_target": None, "mcrl_start": None, "mcrl_target": None},
            "partners": [{"partner_name": "Partner A", "requested": "EUR 1,000.00"}],
        }
        batch2 = {
            "proposal": {"proposal_acronym": None, "proposal_title": "Full Title",
                         "call_identifier": None, "submission_date": None},
            "proposal_facts": {"requested_total": None, "trl_start": None,
                                "trl_target": None, "mcrl_start": None, "mcrl_target": None},
            "partners": [{"partner_name": "Partner B", "requested": "EUR 2,000.00"}],
        }
        merged = merge_raw_dicts([batch1, batch2])
        self.assertEqual(merged["proposal"]["proposal_acronym"], "ABC")
        self.assertEqual(merged["proposal"]["proposal_title"], "Full Title")
        self.assertEqual(merged["proposal_facts"]["requested_total"], "EUR 3,000.00")
        self.assertEqual(len(merged["partners"]), 2)

    def test_non_dict_batches_are_ignored(self):
        merged = merge_raw_dicts(["not a dict", {"proposal": {"proposal_acronym": "X"}}])
        self.assertEqual(merged["proposal"]["proposal_acronym"], "X")

    def test_merged_output_flows_cleanly_through_build_final(self):
        batch1 = {
            "proposal": {"proposal_acronym": "ABC", "proposal_title": None,
                         "call_identifier": None, "submission_date": None},
            "proposal_facts": {"requested_total": "EUR 3,000.00", "trl_start": None,
                                "trl_target": None, "mcrl_start": None, "mcrl_target": None},
            "partners": [{"partner_name": "Partner A", "requested": "EUR 1,000.00"}],
        }
        batch2 = {
            "proposal": {"proposal_acronym": None, "proposal_title": "Full Title",
                         "call_identifier": None, "submission_date": None},
            "proposal_facts": {"requested_total": None, "trl_start": None,
                                "trl_target": None, "mcrl_start": None, "mcrl_target": None},
            "partners": [{"partner_name": "Partner B", "requested": "EUR 2,000.00"}],
        }
        merged = merge_raw_dicts([batch1, batch2])
        final, warnings = build_final(merged, None, "fictional.pdf", NOW)

        self.assertEqual(validate_final(final), [])
        self.assertEqual(warnings, [])  # no grounding (document_text=None); sum matches
        self.assertEqual(final["proposal"]["proposal_acronym"], "ABC")
        self.assertEqual(final["proposal"]["proposal_title"], "Full Title")
        self.assertEqual(final["proposal_facts"]["requested_total_cents"], 300000)
        self.assertEqual(len(final["partners"]), 2)

    def test_same_partner_in_two_batches_is_deduplicated_by_build_final(self):
        batch1 = {
            "proposal": {"proposal_acronym": "ABC", "proposal_title": None,
                         "call_identifier": None, "submission_date": None},
            "proposal_facts": {"requested_total": None, "trl_start": None,
                                "trl_target": None, "mcrl_start": None, "mcrl_target": None},
            "partners": [{"partner_name": "Repeated Partner", "requested": "EUR 1,000.00"}],
        }
        batch2 = {
            "proposal": {"proposal_acronym": None, "proposal_title": None,
                         "call_identifier": None, "submission_date": None},
            "proposal_facts": {"requested_total": None, "trl_start": None,
                                "trl_target": None, "mcrl_start": None, "mcrl_target": None},
            "partners": [{"partner_name": "Repeated Partner", "requested": "EUR 1,000.00"}],
        }
        merged = merge_raw_dicts([batch1, batch2])
        final, warnings = build_final(merged, None, "fictional.pdf", NOW)

        self.assertEqual(len(final["partners"]), 1)
        self.assertTrue(any("duplicate partner" in w for w in warnings))


def _draw_fictional_table(page) -> None:
    """A real grid of cells with text inside them, not just drawn lines - find_tables() needs
    actual text arranged in a grid to recognise a table at all; bare lines are invisible to it
    (confirmed: a real 38-page proposal's ordinary bullet points and divider rules produced
    80-336 drawing primitives per page with no table in sight, so counting drawings alone was
    not a reliable table signal and find_tables() replaced it)."""
    cols, rows = [50, 150, 250, 350], [100, 130, 160, 190]
    for x in cols:
        page.draw_line((x, rows[0]), (x, rows[-1]))
    for y in rows:
        page.draw_line((cols[0], y), (cols[-1], y))
    for i, label in enumerate(("Partner", "Amount", "Status")):
        page.insert_text((cols[i] + 5, rows[1] - 5), label)
        page.insert_text((cols[i] + 5, rows[2] - 5), f"value{i}")


def _fictional_pdf(path: Path, page_count: int) -> None:
    """Every page has a real fictional table, not just text, so pages_needing_visual_check
    flags all of them - these tests are about batching/splitting image requests, which needs
    pages that actually produce images to batch in the first place."""
    doc = fitz.open()
    for i in range(page_count):
        page = doc.new_page()
        page.insert_text((72, 72), f"FICTIONAL TEST DATA - page {i + 1}")
        _draw_fictional_table(page)
    doc.save(path)
    doc.close()


def _reply_with_partner(name: str) -> dict:
    return {
        "content": "```json\n" + json.dumps({
            "proposal": {"proposal_acronym": "SPLIT-TEST", "proposal_title": None,
                         "call_identifier": None, "submission_date": None},
            "proposal_facts": {"requested_total": None, "trl_start": None, "trl_target": None,
                               "mcrl_start": None, "mcrl_target": None},
            "partners": [{"partner_name": name, "requested": "EUR 1,000.00"}],
        }) + "\n```",
        "finish_reason": "stop", "seconds": 0.1, "attempts": 1,
        "prompt_tokens": 10, "completion_tokens": 10, "cost_usd": 0.0001, "model_reported": "m",
    }


# Grounded against by the fake replies below (acronym, every "Partner N" name, the amount) so
# these tests exercise batching/splitting behaviour, not incidental grounding warnings.
_SPLIT_TEST_DOCUMENT_TEXT = "SPLIT-TEST proposal. Partner 0, Partner 1, Partner 2: EUR 1,000.00 each."


class RunOneCombinedSplitTests(unittest.TestCase):
    """Only a batch that actually hits 413 should be split - other, already-fine batches must
    stay at the normal batch size, not be pre-emptively shrunk (a large context window on the
    model does not help here: 413 is a transport-layer byte limit, hit before any tokens are
    counted, so it is unrelated to how large a context the model can process)."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.pdf_path = Path(self.tmp.name) / "fictional.pdf"
        _fictional_pdf(self.pdf_path, page_count=4)
        self.out_dir = Path(self.tmp.name) / "output"
        self.out_dir.mkdir()

    def test_batch_that_hits_413_is_split_and_retried_not_abandoned(self):
        calls = []

        def fake_chat(arm, messages, schema, token, use_extras=True):
            batch_image_count = sum(1 for b in messages[1]["content"] if b["type"] == "image_url")
            calls.append(batch_image_count)
            if batch_image_count == 4:  # the original, unsplit batch
                raise BackendError('HTTP 413: {"error":"request entity too large"}')
            # A unique name per call (not per page count: both halves have the same page
            # count, so naming by page count would make the two halves' partners identical
            # and get deduplicated into one by build_final, hiding a real merge bug).
            return _reply_with_partner(f"Partner {len(calls) - 1}")

        with patch("clic_extract.multimodal.chat", fake_chat):
            run = run_one_combined(
                self.pdf_path, _SPLIT_TEST_DOCUMENT_TEXT, self.out_dir, "qwen_vl", "fake_token",
                datetime(2026, 1, 1, tzinfo=timezone.utc), batch_size=4, overlap=0,
            )

        self.assertEqual(run["status"], "ok")
        self.assertEqual(calls, [4, 2, 2])  # one 413, then two successful halves
        self.assertTrue(any("split into" in w for w in run["warnings"]))
        final = json.loads((self.out_dir / run["output_file"]).read_text(encoding="utf-8"))
        self.assertEqual(len(final["partners"]), 2)  # both halves' partners made it in
        self.assertEqual(run["warnings"], [
            "a 4-page batch was too large (413); split into 2 and 2 pages and retrying"
        ])

    def test_batches_that_succeed_are_never_split(self):
        calls = []

        def fake_chat(arm, messages, schema, token, use_extras=True):
            batch_image_count = sum(1 for b in messages[1]["content"] if b["type"] == "image_url")
            calls.append(batch_image_count)
            return _reply_with_partner("Partner 0")

        with patch("clic_extract.multimodal.chat", fake_chat):
            run = run_one_combined(
                self.pdf_path, _SPLIT_TEST_DOCUMENT_TEXT, self.out_dir, "qwen_vl", "fake_token",
                datetime(2026, 1, 1, tzinfo=timezone.utc), batch_size=4, overlap=0,
            )

        self.assertEqual(run["status"], "ok")
        self.assertEqual(calls, [4])  # the one batch, never fragmented
        self.assertEqual(run["warnings"], [])


class RunOneMultimodalSplitTests(unittest.TestCase):
    """Same split-on-413 behaviour as RunOneCombinedSplitTests, for the older images-only path
    (run_one_multimodal) - a real document had its first batch hit 413 and simply vanish from
    every result, every run, until this was added here too."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.pdf_path = Path(self.tmp.name) / "fictional.pdf"
        _fictional_pdf(self.pdf_path, page_count=4)
        self.out_dir = Path(self.tmp.name) / "output"
        self.out_dir.mkdir()

    def test_batch_that_hits_413_is_split_and_retried_not_abandoned(self):
        calls = []

        def fake_chat(arm, messages, schema, token, use_extras=True):
            batch_image_count = sum(1 for b in messages[1]["content"] if b["type"] == "image_url")
            calls.append(batch_image_count)
            if batch_image_count == 4:
                raise BackendError('HTTP 413: {"error":"request entity too large"}')
            return _reply_with_partner(f"Partner {len(calls) - 1}")

        with patch("clic_extract.multimodal.chat", fake_chat):
            run = run_one_multimodal(
                self.pdf_path, self.out_dir, "fake_token",
                datetime(2026, 1, 1, tzinfo=timezone.utc), batch_size=4, overlap=0,
            )

        self.assertEqual(run["status"], "ok")
        self.assertEqual(calls, [4, 2, 2])
        self.assertTrue(any("split into" in w for w in run["warnings"]))
        final = json.loads((self.out_dir / run["output_file"]).read_text(encoding="utf-8"))
        self.assertEqual(len(final["partners"]), 2)

    def test_batches_that_succeed_are_never_split(self):
        calls = []

        def fake_chat(arm, messages, schema, token, use_extras=True):
            batch_image_count = sum(1 for b in messages[1]["content"] if b["type"] == "image_url")
            calls.append(batch_image_count)
            return _reply_with_partner("Partner 0")

        with patch("clic_extract.multimodal.chat", fake_chat):
            run = run_one_multimodal(
                self.pdf_path, self.out_dir, "fake_token",
                datetime(2026, 1, 1, tzinfo=timezone.utc), batch_size=4, overlap=0,
            )

        self.assertEqual(run["status"], "ok")
        self.assertEqual(calls, [4])
        self.assertEqual(run["warnings"], [])


def _pdf_with_text_and_table_pages(path: Path, text_pages: int, table_pages: int) -> None:
    """text_pages plain prose pages, then table_pages pages with a real fictional table
    (grid lines plus cell text - see _draw_fictional_table) that find_tables() recognises."""
    doc = fitz.open()
    for _ in range(text_pages):
        page = doc.new_page()
        page.insert_text((72, 72), "FICTIONAL PROSE TEXT, no tables or charts on this page.")
    for _ in range(table_pages):
        page = doc.new_page()
        _draw_fictional_table(page)
    doc.save(path)
    doc.close()


class PagesNeedingVisualCheckTests(unittest.TestCase):
    def test_plain_text_pages_are_not_flagged(self):
        with tempfile.TemporaryDirectory() as tmp:
            pdf_path = Path(tmp) / "text_only.pdf"
            _pdf_with_text_and_table_pages(pdf_path, text_pages=5, table_pages=0)
            self.assertEqual(pages_needing_visual_check(pdf_path), [])

    def test_table_pages_are_flagged_text_pages_are_not(self):
        with tempfile.TemporaryDirectory() as tmp:
            pdf_path = Path(tmp) / "mixed.pdf"
            _pdf_with_text_and_table_pages(pdf_path, text_pages=3, table_pages=2)
            # pages 0,1,2 are plain text; pages 3,4 have the drawn table grid.
            self.assertEqual(pages_needing_visual_check(pdf_path), [3, 4])

    def test_embedded_raster_image_flags_the_page(self):
        with tempfile.TemporaryDirectory() as tmp:
            pdf_path = Path(tmp) / "with_picture.pdf"
            doc = fitz.open()
            page = doc.new_page()
            pix = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, 2, 2))
            pix.set_rect(pix.irect, (255, 0, 0))
            page.insert_image(fitz.Rect(10, 10, 30, 30), pixmap=pix)
            doc.save(pdf_path)
            doc.close()
            self.assertEqual(pages_needing_visual_check(pdf_path), [0])


class RunOneCombinedSelectivePagesTests(unittest.TestCase):
    """Images should only be sent for pages pages_needing_visual_check flags, not every page -
    a large model context window is irrelevant here; request bytes, not tokens, are the limit
    this is working around (see run_one_combined's docstring)."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.out_dir = Path(self.tmp.name) / "output"
        self.out_dir.mkdir()

    def test_document_with_no_visual_pages_makes_one_text_only_call(self):
        pdf_path = Path(self.tmp.name) / "text_only.pdf"
        _pdf_with_text_and_table_pages(pdf_path, text_pages=5, table_pages=0)
        calls = []

        def fake_chat(arm, messages, schema, token, use_extras=True):
            image_blocks = [b for b in messages[1]["content"] if b["type"] == "image_url"]
            calls.append(len(image_blocks))
            return _reply_with_partner("Fictional Partner")

        with patch("clic_extract.multimodal.chat", fake_chat):
            run = run_one_combined(
                pdf_path, "FICTIONAL DOCUMENT TEXT", self.out_dir, "qwen_vl", "fake_token",
                datetime(2026, 1, 1, tzinfo=timezone.utc),
            )

        self.assertEqual(run["status"], "ok")
        self.assertEqual(run["pages_total"], 5)
        self.assertEqual(run["pages_with_images"], 0)
        self.assertEqual(calls, [0])  # exactly one call, zero images in it

    def test_only_flagged_pages_are_rendered_and_sent(self):
        pdf_path = Path(self.tmp.name) / "mixed.pdf"
        _pdf_with_text_and_table_pages(pdf_path, text_pages=3, table_pages=2)
        calls = []

        def fake_chat(arm, messages, schema, token, use_extras=True):
            image_blocks = [b for b in messages[1]["content"] if b["type"] == "image_url"]
            calls.append(len(image_blocks))
            return _reply_with_partner("Fictional Partner")

        with patch("clic_extract.multimodal.chat", fake_chat):
            run = run_one_combined(
                pdf_path, "FICTIONAL DOCUMENT TEXT", self.out_dir, "qwen_vl", "fake_token",
                datetime(2026, 1, 1, tzinfo=timezone.utc),
            )

        self.assertEqual(run["status"], "ok")
        self.assertEqual(run["pages_total"], 5)
        self.assertEqual(run["pages_with_images"], 2)  # only the 2 table pages
        self.assertEqual(sum(calls), 2)  # total images sent across all calls stays at 2


if __name__ == "__main__":
    unittest.main()
