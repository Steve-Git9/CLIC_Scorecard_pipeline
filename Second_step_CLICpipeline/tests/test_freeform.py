"""Tests for the free-form light text arm (clic_extract.freeform). Fictional data only."""

import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from clic_extract.freeform import run_one_freeform
from clic_extract.postprocess import extract_json
from clic_extract.prompts import OPEN_TEXT_SYSTEM_PROMPT

NOW = datetime(2026, 1, 1, tzinfo=timezone.utc)
DOC = "# FAKEPROJ\nFictional Testing Project\n\n| Partner | Requested |\n|---|---|\n| Alpha Test Oy | EUR 100,000.00 |\n"
REPLY = (
    "The acronym {FAKEPROJ} appears in the heading. The table has one row: Alpha Test Oy, EUR 100,000.00.\n\n"
    "```json\n"
    + json.dumps({
        "proposal": {"proposal_acronym": "FAKEPROJ", "proposal_title": "Fictional Testing Project",
                     "call_identifier": None, "submission_date": None},
        "proposal_facts": {"requested_total": None, "trl_start": None, "trl_target": None,
                           "mcrl_start": None, "mcrl_target": None},
        "partners": [{"partner_name": "Alpha Test Oy", "requested": "EUR 100,000.00"}],
    })
    + "\n```"
)


class ExtractJsonTests(unittest.TestCase):
    def test_last_fenced_block_wins_over_braces_in_prose(self):
        self.assertEqual(extract_json('see {this} first\n```json\n{"a": 1}\n```'), {"a": 1})

    def test_bare_object_still_works(self):
        self.assertEqual(extract_json('{"b": 2}'), {"b": 2})


class RunOneFreeformTests(unittest.TestCase):
    def test_no_schema_free_prompt_and_converted_output(self):
        sent = {}

        def fake_chat(arm, messages, schema, token, use_extras=True):
            sent.update(schema=schema, system=messages[0]["content"])
            return {"content": REPLY, "finish_reason": "stop", "seconds": 0.1, "attempts": 1,
                    "prompt_tokens": 10, "completion_tokens": 10, "cost_usd": 0.0, "model_reported": "fake"}

        with tempfile.TemporaryDirectory() as tmp:
            md = Path(tmp) / "fictional.md"
            md.write_text(DOC, encoding="utf-8")
            with patch("clic_extract.run_extract.chat", fake_chat):
                run = run_one_freeform(md, Path(tmp), "fake_token", NOW)
            self.assertEqual(run["status"], "ok", run["error"])
            self.assertTrue(run["free_form"])
            final = json.loads((Path(tmp) / run["output_file"]).read_text(encoding="utf-8"))
            freeform = (Path(tmp) / run["freeform_file"]).read_text(encoding="utf-8")
        self.assertIn("The acronym {FAKEPROJ}", freeform)
        self.assertIsNone(sent["schema"])
        self.assertEqual(sent["system"], OPEN_TEXT_SYSTEM_PROMPT)
        self.assertEqual(final["partners"], [{"partner_name": "Alpha Test Oy", "requested_cents": 10_000_000}])


if __name__ == "__main__":
    unittest.main()


class FreeformBContrastTests(unittest.TestCase):
    """freeform_B must differ from arm B only in the output protocol."""

    def test_request_matches_b_except_for_prompt_and_response_format(self):
        from clic_extract.backends import build_request, load_arms
        from clic_extract.freeform import config_for
        from clic_extract.prompts import build_messages, build_open_messages
        from clic_extract.schema import RAW_SCHEMA

        b = load_arms()["B"]
        self.assertEqual(config_for("freeform_B"), b)
        strict = build_request(b, build_messages(DOC), RAW_SCHEMA)
        free = build_request(config_for("freeform_B"), build_open_messages(DOC), None)
        self.assertIn("response_format", strict)
        self.assertNotIn("response_format", free)
        for key in ("model", "temperature", "max_tokens", "chat_template_kwargs"):
            self.assertEqual(strict.get(key), free.get(key), key)
        self.assertEqual(set(strict) - {"response_format", "messages"}, set(free) - {"messages"})
        self.assertEqual(strict["messages"][1], free["messages"][1])  # same document input
        self.assertEqual(free["messages"][0]["content"], OPEN_TEXT_SYSTEM_PROMPT)

    def test_run_records_arm_and_b_model(self):
        def fake_chat(arm, messages, schema, token, use_extras=True):
            return {"content": REPLY, "finish_reason": "stop", "seconds": 0.1, "attempts": 1,
                    "prompt_tokens": 10, "completion_tokens": 10, "cost_usd": 0.0, "model_reported": "fake"}

        with tempfile.TemporaryDirectory() as tmp:
            md = Path(tmp) / "fictional.md"
            md.write_text(DOC, encoding="utf-8")
            with patch("clic_extract.run_extract.chat", fake_chat):
                run = run_one_freeform(md, Path(tmp), "fake_token", NOW, arm_name="freeform_B")
        from clic_extract.backends import load_arms
        self.assertEqual(run["status"], "ok", run["error"])
        self.assertEqual(run["arm"], "freeform_B")
        self.assertEqual(run["model"], load_arms()["B"]["model"])
        self.assertTrue(run["free_form"])
