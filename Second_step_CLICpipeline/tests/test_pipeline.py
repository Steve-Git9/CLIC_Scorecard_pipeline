import copy
import json
import os
import unittest
from datetime import datetime, timezone
from pathlib import Path

from clic_extract import backends, evaluate
from clic_extract.postprocess import (
    build_final,
    extract_json,
    normalise_date,
    parse_amount_to_cents,
)
from clic_extract.prompts import build_messages
from clic_extract.schema import RAW_SCHEMA, validate_final

ROOT = Path(__file__).resolve().parent.parent
SAMPLE = (ROOT / "samples" / "synthetic_proposal.md").read_text(encoding="utf-8")
GOLD = json.loads((ROOT / "samples" / "gold" / "synthetic_proposal.json").read_text(encoding="utf-8"))
NOW = datetime(2026, 9, 30, 12, 0, 0, tzinfo=timezone.utc)

# What a model would plausibly return for the synthetic document (amounts as written).
RAW = {
    "proposal": {
        "proposal_acronym": "H2-RURAL",
        "proposal_title": "Sustainable Hydrogen Storage for Rural Microgrids",
        "call_identifier": "HORIZON-CL5-2026-D3-01",
        "submission_date": "15 March 2026",
    },
    "proposal_facts": {
        "requested_total": "EUR 2,200,125.00",
        "trl_start": 3, "trl_target": 6, "mcrl_start": 2, "mcrl_target": 4,
    },
    "partners": [
        {"partner_name": "GreenGrid Systems GmbH", "requested": "EUR 590,625.00"},
        {"partner_name": "Universidad del Norte", "requested": "EUR 812,500.00"},
        {"partner_name": "Helios Power AG", "requested": "EUR 450,000.00"},
        {"partner_name": "Municipality of Kalmar", "requested": "EUR 197,000.00"},
        {"partner_name": "Aurora Consulting", "requested": "EUR 150,000.00"},
    ],
}


class MoneyTests(unittest.TestCase):
    def check(self, text, cents):
        self.assertEqual(parse_amount_to_cents(text)[0], cents, text)

    def test_examples_from_the_brief(self):
        self.check("EUR 500,000", 50_000_000)
        self.check("EUR 590,625.00", 59_062_500)

    def test_european_formats(self):
        self.check("590.625,00 €", 59_062_500)
        self.check("€ 1.234.567,89", 123_456_789)
        self.check("1 234 567,50 EUR", 123_456_750)

    def test_suffixes_and_noise(self):
        self.check("EUR 1.2 million", 120_000_000)
        self.check("EUR 500,000.-", 50_000_000)
        self.check("EUR 500,000.", 50_000_000)
        self.check("€2,5m", 250_000_000)

    def test_ambiguous_dot_is_null_with_warning(self):
        cents, warning = parse_amount_to_cents("EUR 1.234")
        self.assertIsNone(cents)
        self.assertIn("ambiguous", warning)

    def test_missing_and_garbage_are_null(self):
        for value in (None, "", "N/A", "not stated"):
            self.assertEqual(parse_amount_to_cents(value), (None, None))
        cents, warning = parse_amount_to_cents("about a lot")
        self.assertIsNone(cents)
        self.assertTrue(warning)
        self.assertIsNone(parse_amount_to_cents("-500")[0])

    def test_sub_cent_is_null(self):
        self.assertIsNone(parse_amount_to_cents("1,234.567")[0])


class DateTests(unittest.TestCase):
    def test_formats(self):
        self.assertEqual(normalise_date("2026-03-15")[0], "2026-03-15")
        self.assertEqual(normalise_date("15 March 2026")[0], "2026-03-15")
        self.assertEqual(normalise_date("March 15, 2026")[0], "2026-03-15")
        self.assertEqual(normalise_date("15.03.2026")[0], "2026-03-15")
        self.assertEqual(normalise_date("15/03/2026")[0], "2026-03-15")
        self.assertEqual(normalise_date("2026-03-15T10:00:00Z")[0], "2026-03-15")

    def test_ambiguous_or_invalid_is_null(self):
        self.assertEqual(normalise_date("01/09/2026")[0], None)
        self.assertEqual(normalise_date("2026-02-30")[0], None)
        self.assertEqual(normalise_date("soon")[0], None)
        self.assertEqual(normalise_date(None), (None, None))


class JsonExtractionTests(unittest.TestCase):
    def test_wrapped_replies(self):
        self.assertEqual(extract_json('Here you go:\n```json\n{"a": 1}\n```'), {"a": 1})
        self.assertEqual(extract_json('<think>hmm {x}</think>{"a": 2}'), {"a": 2})
        with self.assertRaises(ValueError):
            extract_json("no json here")


class BuildFinalTests(unittest.TestCase):
    def test_synthetic_matches_gold(self):
        final, warnings = build_final(copy.deepcopy(RAW), SAMPLE, "synthetic_proposal.md", NOW)
        self.assertEqual(validate_final(final), [])
        self.assertEqual(warnings, [])
        expected = copy.deepcopy(GOLD)
        expected["metadata"]["extraction_timestamp"] = "2026-09-30T12:00:00Z"
        self.assertEqual(final, expected)

    def test_hallucinated_partner_and_bad_sum_are_warned(self):
        raw = copy.deepcopy(RAW)
        raw["partners"].append({"partner_name": "Ghost Corp", "requested": "EUR 1,000.00"})
        final, warnings = build_final(raw, SAMPLE, "x.md", NOW)
        self.assertTrue(any("Ghost Corp" in w and "not found" in w for w in warnings))
        self.assertTrue(any("sum of partner requested_cents" in w for w in warnings))

    def test_bad_values_become_null_never_zero_or_empty(self):
        raw = copy.deepcopy(RAW)
        raw["proposal"]["call_identifier"] = "N/A"
        raw["proposal"]["submission_date"] = "01/09/2026"      # ambiguous day/month
        raw["proposal_facts"]["trl_start"] = 12                # out of range
        raw["proposal_facts"]["mcrl_target"] = "n/a"
        raw["proposal_facts"]["requested_total"] = "EUR 1.234"  # ambiguous separator
        raw["partners"][4]["requested"] = "not stated"
        final, warnings = build_final(raw, SAMPLE, "x.md", NOW)
        self.assertIsNone(final["proposal"]["call_identifier"])
        self.assertIsNone(final["proposal"]["submission_date"])
        self.assertIsNone(final["proposal_facts"]["trl_start"])
        self.assertIsNone(final["proposal_facts"]["mcrl_target"])
        self.assertIsNone(final["proposal_facts"]["requested_total_cents"])
        self.assertIsNone(final["partners"][4]["requested_cents"])
        self.assertEqual(validate_final(final), [])
        self.assertGreaterEqual(len(warnings), 4)

    def test_fields_outside_the_scope_are_dropped(self):
        raw = copy.deepcopy(RAW)
        raw["proposal"]["status"] = "Pending"
        raw["proposal_facts"].update({"granted_total": "EUR 1", "builds_on_previous": 1, "demo_activity_count": 3})
        raw["partners"][0].update({"partner_category": "SME", "granted": "EUR 1"})
        final, warnings = build_final(raw, SAMPLE, "x.md", NOW)
        self.assertEqual(validate_final(final), [])
        self.assertEqual(set(final["proposal"]), {"proposal_acronym", "proposal_title", "call_identifier", "submission_date"})
        self.assertEqual(set(final["proposal_facts"]),
                         {"requested_total_cents", "trl_start", "trl_target", "mcrl_start", "mcrl_target"})
        self.assertEqual(set(final["partners"][0]), {"partner_name", "requested_cents"})
        self.assertEqual(warnings, [])

    def test_garbage_input_gives_valid_empty_document(self):
        final, warnings = build_final("not a dict", SAMPLE, "x.md", NOW)
        self.assertEqual(validate_final(final), [])
        self.assertEqual(final["partners"], [])
        self.assertTrue(warnings)


class SchemaTests(unittest.TestCase):
    def walk(self, node, path="root"):
        if node.get("type") == "object":
            self.assertEqual(sorted(node["required"]), sorted(node["properties"]), path)
            self.assertIs(node["additionalProperties"], False, path)
            for k, v in node["properties"].items():
                self.walk(v, f"{path}.{k}")
        elif node.get("type") == "array":
            self.walk(node["items"], path + "[]")

    def test_raw_schema_is_strict_mode_compatible(self):
        self.walk(RAW_SCHEMA)

    def test_gold_is_valid_final_document(self):
        self.assertEqual(validate_final(GOLD), [])


class RequestTests(unittest.TestCase):
    ARM = {"model": "Qwen/Qwen3.5-9B", "provider": "together", "max_tokens": 100,
           "extra_body": {"chat_template_kwargs": {"enable_thinking": False}},
           "input_per_m": 0.17, "output_per_m": 0.25}

    def test_request_pins_provider_and_has_no_secret(self):
        old = os.environ.get("HF_TOKEN")
        os.environ["HF_TOKEN"] = "hf_SECRET_TEST_TOKEN"
        try:
            payload = backends.build_request(self.ARM, build_messages("doc"), RAW_SCHEMA)
        finally:
            if old is None:
                del os.environ["HF_TOKEN"]
            else:
                os.environ["HF_TOKEN"] = old
        self.assertEqual(payload["model"], "Qwen/Qwen3.5-9B:together")
        self.assertTrue(payload["response_format"]["json_schema"]["strict"])
        self.assertEqual(payload["temperature"], 0)
        self.assertNotIn("SECRET", json.dumps(payload))
        self.assertIn("chat_template_kwargs", payload)
        self.assertNotIn("chat_template_kwargs", backends.build_request(self.ARM, [], RAW_SCHEMA, use_extras=False))

    def test_cost(self):
        self.assertEqual(backends.cost_usd(self.ARM, 30_000, 2_000), round((30_000 * 0.17 + 2_000 * 0.25) / 1e6, 6))
        self.assertIsNone(backends.cost_usd({}, 1, 1))


class HttpDetailsTests(unittest.TestCase):
    CLOUDFLARE_PAGE = (
        "<!doctype html>\n<!--[if lt IE 7]> <html class=\"no-js ie6 oldie\"> <![endif]-->\n"
        "<html><head><title>Access denied | api.together.xyz used Cloudflare to restrict access | Cloudflare</title>"
        "</head><body><span class=\"cf-error-code\">Error code 1010</span> The owner has banned your browser signature."
        "</body></html>"
    )

    def test_cloudflare_page_is_summarised(self):
        text = backends.summarise_error(self.CLOUDFLARE_PAGE)
        self.assertIn("Access denied | api.together.xyz", text)
        self.assertIn("1010", text)
        self.assertLess(len(text), 200)

    def test_json_error_is_kept_and_truncated(self):
        self.assertEqual(backends.summarise_error('{"error":"Invalid username or password."}'), '{"error":"Invalid username or password."}')
        self.assertEqual(len(backends.summarise_error("x" * 5000)), 600)

    def test_default_urllib_agent_is_not_sent(self):
        headers = backends.request_headers("hf_" + "a" * 34, json_body=True)
        self.assertNotIn("urllib", headers["User-Agent"].lower())
        self.assertTrue(headers["User-Agent"].startswith("clic-extract/"))
        self.assertEqual(headers["Content-Type"], "application/json")
        self.assertNotIn("Authorization", backends.request_headers())


class TokenFormatTests(unittest.TestCase):
    GOOD = "hf_" + "a" * 34

    def test_good_token_has_no_problems(self):
        self.assertEqual(backends.token_problems(self.GOOD), [])

    def test_common_mistakes_are_named_and_never_echo_the_token(self):
        cases = {
            "<" + self.GOOD + ">": "angle",
            "'" + self.GOOD + "'": "quote",
            self.GOOD + "\n": "whitespace",
            "Bearer " + self.GOOD: "Bearer",
            "your token": "hf_",
            "hf_short": "truncated",
        }
        for token, word in cases.items():
            problems = backends.token_problems(token)
            self.assertTrue(any(word.lower() in p.lower() for p in problems), (token, problems))
            self.assertFalse(any(token.strip() in p for p in problems if len(token.strip()) > 8))

    def test_get_token_rejects_malformed_and_missing(self):
        old = os.environ.get("HF_TOKEN")
        try:
            os.environ["HF_TOKEN"] = "<" + self.GOOD + ">"
            with self.assertRaises(backends.BackendError) as ctx:
                backends.get_token()
            self.assertNotIn(self.GOOD, str(ctx.exception))
            os.environ.pop("HF_TOKEN")
            with self.assertRaises(backends.BackendError):
                backends.get_token()
        finally:
            if old is not None:
                os.environ["HF_TOKEN"] = old


class EvaluateTests(unittest.TestCase):
    def test_tally_rules(self):
        t = evaluate.Tally()
        t.add("A b", "a  B")       # correct after normalisation
        t.add(None, None)          # correct null
        t.add(None, "x")           # hallucination
        t.add("y", None)           # missed
        t.add("y", "z")            # wrong
        self.assertEqual((t.n, t.correct, t.halluc, t.missed, t.wrong), (5, 2, 1, 1, 1))
        self.assertAlmostEqual(t.halluc_rate(), 0.5)
        self.assertEqual(t.verdict(), "NOT OK")

    def test_perfect_arm_scores_ok(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            arm_dir = Path(tmp) / "B"
            arm_dir.mkdir()
            final, _ = build_final(copy.deepcopy(RAW), SAMPLE, "synthetic_proposal.md", NOW)
            (arm_dir / "synthetic_proposal_20260930T120000Z.json").write_text(json.dumps(final), encoding="utf-8")
            (arm_dir / "synthetic_proposal_20260930T120000Z.run.json").write_text(
                json.dumps({"status": "ok", "seconds": 1.5, "cost_usd": 0.001}), encoding="utf-8")
            score = evaluate.score_arm(ROOT / "samples" / "gold", arm_dir)
        self.assertEqual(score["ok_docs"], 1)
        self.assertTrue(all(t.verdict() == "OK" for t in score["fields"].values()))
        self.assertEqual(score["partners_prf"], (1.0, 1.0, 1.0))


if __name__ == "__main__":
    unittest.main()
