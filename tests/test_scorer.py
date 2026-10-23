"""Tests for the evaluation scorer (src/evaluation). FICTIONAL TEST DATA ONLY: every proposal,
partner, amount and date below is invented and does not describe any real CLIC project."""

from __future__ import annotations

import copy
import csv
import json
from pathlib import Path

import pytest
import yaml

from src.evaluation.normalise import (
    Invalid,
    compare,
    normalise_amount,
    normalise_date,
    normalise_integer,
    normalise_text,
)
from src.evaluation.partners import score_partners
from src.evaluation.score_runs import document_stem, latest_runs, main, run_base
from src.evaluation.scorer import SCALAR_FIELDS, score_run
from src.evaluation.validity import check_reply, first_attempt_validity

# --------------------------------------------------------------------------- fictional fixtures

GOLD = {
    "proposal": {
        "proposal_acronym": "FICTO",
        "proposal_title": "Fictional Test Initiative",
        "call_identifier": "TEST-CALL-2099-01",
        "submission_date": "2099-03-15",
    },
    "proposal_facts": {
        "requested_total_cents": 300_000_000,
        "trl_start": 3,
        "trl_target": 6,
        "mcrl_start": None,
        "mcrl_target": None,
    },
    "partners": [
        {"partner_name": "Imaginary Labs Oy", "requested_cents": 100_000_000},
        {"partner_name": "Nowhere University", "requested_cents": 150_000_000},
        {"partner_name": "Fictional Research Centre Ltd", "requested_cents": 50_000_000},
    ],
    "metadata": {"extraction_timestamp": None, "source_file": None},
}

MARKDOWN = """# FICTIONAL TEST DATA: Fictional Test Initiative (FICTO)

Call: TEST-CALL-2099-01

| Partner                          | Requested    |
|----------------------------------|--------------|
| Imaginary Labs Oy                | 1,000,000.00 |
| Nowhere   University             | 1,500,000.00 |
| Fictional Research Centre Ltd    |   500,000.00 |

Associated: Pretend Industries &amp; Partners Oy, and the city of
| Dreamland   City |

The Zorblax prototype is mentioned once.
"""


def final_from_gold(**changes) -> dict:
    """A final output equal to the gold set, with metadata filled as the pipeline would."""
    final = copy.deepcopy(GOLD)
    final["metadata"] = {"extraction_timestamp": "2099-01-01T00:00:00Z", "source_file": "FICTO.pdf"}
    for path, value in changes.items():
        section, key = path.split("__")
        final[section][key] = value
    return final


def raw_reply(**facts) -> dict:
    raw = {
        "proposal": dict(GOLD["proposal"]),
        "proposal_facts": {"requested_total": "EUR 3,000,000.00", "trl_start": 3, "trl_target": 6,
                           "mcrl_start": None, "mcrl_target": None},
        "partners": [{"partner_name": p["partner_name"], "requested": "EUR 1,000,000.00"}
                     for p in GOLD["partners"]],
    }
    raw["proposal_facts"].update(facts)
    return raw


def partner(name: str, cents: int | None = None) -> dict:
    return {"partner_name": name, "requested_cents": cents}


def gold_partners(*overrides: dict) -> list[dict]:
    return [dict(p) for p in GOLD["partners"]] + list(overrides)


def score(final, replies=None, protocol="schema", markdown=MARKDOWN):
    if replies is None and final is not None:
        replies = [json.dumps(raw_reply())]
    return score_run(final, GOLD, replies, protocol, markdown)


# --------------------------------------------------------------------------- normalisation

def test_amount_integer_is_already_cents():
    assert normalise_amount(220_012_500) == 220_012_500


@pytest.mark.parametrize("text, cents", [
    ("EUR 2,200,125.00", 220_012_500),
    ("1.234.567,89 €", 123_456_789),
    ("500,000", 50_000_000),
    ("€ 1 500", 150_000),
    ("12,5", 1_250),
    ("2200125", 220_012_500),
])
def test_amount_written_text_is_converted_to_cents(text, cents):
    assert normalise_amount(text) == cents


@pytest.mark.parametrize("value", [12.5, True, "1,2345", "about 3 million", "1.234,567.00", "12,34,567"])
def test_amount_that_is_not_whole_cents_or_is_ambiguous_is_invalid(value):
    assert isinstance(normalise_amount(value), Invalid)


@pytest.mark.parametrize("text", [
    "2099-03-15", "15.3.2099", "15 March 2099", "March 15, 2099", "2099-03-15T10:00:00Z", "15/03/2099", "15th Mar 2099",
])
def test_date_forms_normalise_to_iso_8601(text):
    assert normalise_date(text) == "2099-03-15"


@pytest.mark.parametrize("value", ["03/04/2099", "2099-02-30", "Q1 2099", 20990315])
def test_ambiguous_impossible_or_non_text_dates_are_invalid(value):
    assert isinstance(normalise_date(value), Invalid)


def test_text_is_case_folded_and_whitespace_collapsed():
    assert normalise_text("  Fictional   TEST\nInitiative ") == "fictional test initiative"
    assert normalise_text("") is None
    assert isinstance(normalise_text(5), Invalid)


def test_integer_rejects_booleans_and_text():
    assert normalise_integer(4) == 4
    assert isinstance(normalise_integer(True), Invalid)
    assert isinstance(normalise_integer("4"), Invalid)


def test_invalid_never_equals_anything():
    bad = Invalid("x")
    assert bad != bad and bad != "x"


@pytest.mark.parametrize("gold, pred, outcome", [
    (None, None, "correct"),
    ("a", "a", "correct"),
    ("a", None, "miss"),
    (None, "a", "unsupported"),
    ("a", "b", "wrong"),
    ("a", Invalid("?"), "wrong"),
    (None, Invalid("?"), "unsupported"),
])
def test_compare_outcomes(gold, pred, outcome):
    assert compare(gold, pred) == outcome


# --------------------------------------------------------------------------- validity

def test_schema_reply_that_is_bare_conforming_json_is_valid():
    assert check_reply(json.dumps(raw_reply()), "schema") == (True, None)


def test_schema_reply_inside_a_fence_needs_repair():
    ok, reason = check_reply("```json\n" + json.dumps(raw_reply()) + "\n```", "schema")
    assert not ok and "not valid JSON" in reason


def test_freeform_reply_with_prose_and_a_json_block_is_valid():
    reply = "The partner table is on page 9.\n\n```json\n" + json.dumps(raw_reply()) + "\n```"
    assert check_reply(reply, "freeform") == (True, None)


def test_freeform_reply_without_a_json_block_is_invalid():
    ok, reason = check_reply("Here it is: " + json.dumps(raw_reply()), "freeform")
    assert not ok and "no ```json block" in reason


def test_truncated_json_is_invalid():
    ok, reason = check_reply(json.dumps(raw_reply())[:-20], "schema")
    assert not ok and "not valid JSON" in reason


@pytest.mark.parametrize("raw", [
    raw_reply(trl_start="3"),  # wrong type
    {k: v for k, v in raw_reply().items() if k != "partners"},  # missing key
    {**raw_reply(), "sdgs": []},  # key the schema forbids
])
def test_json_that_does_not_conform_to_the_schema_is_invalid(raw):
    ok, reason = check_reply(json.dumps(raw), "schema")
    assert not ok and "schema" in reason


def test_every_batch_reply_must_be_valid_at_the_first_attempt():
    ok, reason = first_attempt_validity([json.dumps(raw_reply()), "{not json"], "schema")
    assert ok is False and reason.startswith("reply 2 of 2")


def test_first_attempt_is_unknown_without_saved_replies():
    assert first_attempt_validity(None, "schema")[0] is None


# --------------------------------------------------------------------------- scalar fields

def test_identical_output_is_fully_correct():
    s = score(final_from_gold())
    assert s["validity"] == {"first_attempt": True, "first_attempt_reason": None,
                             "after_repair": True, "after_repair_problems": []}
    assert s["scalar_accuracy"] == 1.0
    assert s["errors"]["total"] == 0
    assert s["fully_correct"] is True


def test_metadata_is_not_scored():
    assert not any(f.startswith("metadata") for f in SCALAR_FIELDS)
    s = score(final_from_gold(metadata__source_file="something else.pdf", metadata__extraction_timestamp=None))
    assert s["fully_correct"] is True


def test_null_against_a_gold_value_is_a_miss_and_a_value_against_gold_null_is_unsupported():
    s = score(final_from_gold(proposal__call_identifier=None, proposal_facts__mcrl_start=4))
    outcomes = {r["field"]: r["outcome"] for r in s["scalars"]}
    assert outcomes["proposal.call_identifier"] == "miss"
    assert outcomes["proposal_facts.mcrl_start"] == "unsupported"
    assert s["errors"]["misses"] == 1 and s["errors"]["unsupported_values"] == 1
    assert s["fully_correct"] is False


def test_different_value_is_wrong():
    s = score(final_from_gold(proposal_facts__trl_target=7))
    assert s["errors"]["wrong_values"] == 1


def test_scalar_normalisation_is_applied_before_comparison():
    s = score(final_from_gold(proposal__submission_date="15 March 2099",
                              proposal__proposal_title="  FICTIONAL test\ninitiative"))
    assert s["scalar_accuracy"] == 1.0


# --------------------------------------------------------------------------- partners

def classes(result) -> dict[str, str]:
    return {e["partner_name"]: e["class"] for e in result["entries"]}


def test_partner_matches_by_normalised_name():
    r = score_partners(GOLD["partners"], [partner("IMAGINARY  labs oy", 100_000_000)], 300_000_000, MARKDOWN)
    assert classes(r) == {"IMAGINARY  labs oy": "matched"}
    assert r["entries"][0]["amount_outcome"] == "correct"


def test_partner_repeated_by_name_is_a_duplicate():
    preds = [partner("Imaginary Labs Oy"), partner("imaginary  LABS oy"), partner("Nowhere University")]
    r = score_partners(GOLD["partners"], preds, 300_000_000, MARKDOWN)
    assert [e["class"] for e in r["entries"]] == ["matched", "duplicate", "matched"]


def test_fragment_of_a_matched_gold_partner_is_a_duplicate_split():
    preds = [partner("Fictional Research"), partner("Fictional Research Centre Ltd", 50_000_000)]
    r = score_partners(GOLD["partners"], preds, 300_000_000, MARKDOWN)
    assert classes(r) == {"Fictional Research": "duplicate", "Fictional Research Centre Ltd": "matched"}


def test_extra_partner_named_in_the_markdown_is_supported():
    preds = [partner("Pretend Industries & Partners Oy"), partner("Dreamland City")]
    r = score_partners(GOLD["partners"], preds, 300_000_000, MARKDOWN)
    assert set(classes(r).values()) == {"supported_extra"}


def test_extra_partner_absent_from_the_markdown_is_unsupported():
    r = score_partners(GOLD["partners"], [partner("Phantom Dynamics GmbH")], 300_000_000, MARKDOWN)
    assert classes(r) == {"Phantom Dynamics GmbH": "unsupported_extra"}


@pytest.mark.parametrize("name, markdown, reason_part", [
    ("Zorblax Holdings", MARKDOWN, "zorblax"),                   # distinctive word only
    ("Nowhere", MARKDOWN, "variant"),                           # part of an unmatched gold name
    ("Imaginary Labs Oy Finland branch", MARKDOWN, "contains"),  # contains a gold name
    ("Pretend Industries & Partners Oy", None, "no Docling Markdown"),
])
def test_names_that_cannot_be_classified_go_to_manual_review(name, markdown, reason_part):
    r = score_partners(GOLD["partners"], [partner(name)], 300_000_000, markdown)
    assert classes(r) == {name: "manual_review"}
    assert reason_part in r["manual_review"][0]["reason"]


def test_recall_and_amount_accuracy():
    preds = [partner("Imaginary Labs Oy", 100_000_000), partner("Nowhere University", 1)]
    r = score_partners(GOLD["partners"], preds, 300_000_000, MARKDOWN)
    assert r["recall"] == pytest.approx(2 / 3)
    assert r["amount_accuracy"] == 0.5
    assert r["missed_gold"] == ["Fictional Research Centre Ltd"]


def test_sum_check_with_and_without_supported_extras():
    preds = [partner(p["partner_name"], p["requested_cents"]) for p in GOLD["partners"]]
    plain = score_partners(GOLD["partners"], preds + [partner("Dreamland City")], 300_000_000, MARKDOWN)
    assert plain["sum_check"]["matched_sum_equals_total"] is True
    assert plain["sum_check"]["supported_extras_make_sum_deviate"] is False
    extra = score_partners(GOLD["partners"], preds + [partner("Dreamland City", 2_000_000)], 300_000_000, MARKDOWN)
    assert extra["sum_check"]["sum_with_supported_extras_equals_total"] is False
    assert extra["sum_check"]["supported_extras_make_sum_deviate"] is True


def test_sum_check_is_undetermined_when_a_matched_amount_is_missing():
    preds = [partner("Imaginary Labs Oy", None)]
    r = score_partners(GOLD["partners"], preds, 300_000_000, MARKDOWN)
    assert r["sum_check"]["matched_sum_equals_total"] is None


def test_supported_extra_is_a_reviewer_decision_not_an_error():
    final = final_from_gold()
    final["partners"].append(partner("Dreamland City"))
    s = score(final)
    assert s["errors"]["total"] == 0
    assert s["reviewer_decisions"]["supported_extras"] == 1
    assert s["fully_correct"] is True


def test_unsupported_extra_and_duplicate_are_errors():
    final = final_from_gold()
    final["partners"] += [partner("Phantom Dynamics GmbH"), partner("Fictional Research")]
    s = score(final)
    assert s["errors"]["unsupported_extras"] == 1
    assert s["errors"]["duplicates"] == 1
    assert s["unsupported_values_including_extras"] == 1
    assert s["fully_correct"] is False


def test_missed_partner_and_amount_errors_are_counted():
    final = final_from_gold()
    final["partners"] = [partner("Imaginary Labs Oy", None), partner("Nowhere University", 1)]
    s = score(final)
    assert s["errors"]["misses"] == 2          # one missed partner, one missing amount
    assert s["errors"]["wrong_values"] == 1


def test_document_is_undetermined_while_a_name_awaits_manual_review():
    final = final_from_gold()
    final["partners"].append(partner("Zorblax Holdings"))
    s = score(final)
    assert s["errors"]["total"] == 0
    assert s["fully_correct"] is None


# --------------------------------------------------------------------------- invalid output

def test_invalid_json_with_no_final_output_counts_every_field_as_a_miss():
    s = score(None, replies=['{"proposal": {"proposal_acronym": "FIC'])
    assert s["validity"]["first_attempt"] is False
    assert s["validity"]["after_repair"] is False
    assert [r["outcome"] for r in s["scalars"]] == ["miss"] * 9
    assert s["partners"]["recall"] == 0.0
    assert s["errors"]["misses"] == 9 + 3
    assert s["fully_correct"] is False


def test_final_output_that_fails_the_schema_counts_every_field_as_a_miss():
    s = score(final_from_gold(proposal_facts__trl_start="3"))
    assert s["validity"]["after_repair"] is False
    assert s["errors"]["misses"] == 12


def test_repaired_output_is_valid_after_repair_but_not_at_the_first_attempt():
    fenced = "```json\n" + json.dumps(raw_reply()) + "\n```"
    s = score(final_from_gold(), replies=[fenced])
    assert s["validity"]["first_attempt"] is False
    assert s["validity"]["after_repair"] is True
    assert s["fully_correct"] is True


def test_gold_that_cannot_be_normalised_is_rejected():
    bad = copy.deepcopy(GOLD)
    bad["proposal_facts"]["requested_total_cents"] = 3_000_000.0
    with pytest.raises(ValueError):
        score_run(final_from_gold(), bad, None, "schema", MARKDOWN)


# --------------------------------------------------------------------------- command line

def test_run_names():
    base = run_base(Path("evaluation/B/FICTO_20990101T000000Z.run.json"))
    assert base.name == "FICTO_20990101T000000Z"
    assert document_stem(base) == "FICTO"
    with pytest.raises(ValueError):
        document_stem(Path("FICTO_docling"))


def test_command_line_scores_the_latest_run_and_writes_the_review_list(tmp_path: Path):
    (tmp_path / "gold").mkdir()
    (tmp_path / "gold" / "FICTO.json").write_text(json.dumps(GOLD), encoding="utf-8")
    (tmp_path / "md").mkdir()
    (tmp_path / "md" / "FICTO.md").write_text(MARKDOWN, encoding="utf-8")
    config = tmp_path / "config.yaml"
    config.write_text(yaml.safe_dump({
        "paths": {"raw": str(tmp_path / "raw"), "markdown": str(tmp_path / "md"), "runs": str(tmp_path / "runs"),
                  "logs": str(tmp_path / "logs"), "database": str(tmp_path / "none.db")},
        "evaluation": {"gold": str(tmp_path / "gold"), "markdown": str(tmp_path / "md"),
                       "protocols": {"B": "schema"}},
    }), encoding="utf-8")

    folder = tmp_path / "B"
    folder.mkdir()
    old = folder / "FICTO_20990101T000000Z"
    (old.parent / (old.name + ".run.json")).write_text(json.dumps({"arm": "B", "status": "failed"}), encoding="utf-8")
    new = folder / "FICTO_20990102T000000Z"
    final = final_from_gold()
    final["partners"].append(partner("Zorblax Holdings"))
    (new.parent / (new.name + ".run.json")).write_text(json.dumps({"arm": "B", "status": "ok"}), encoding="utf-8")
    (new.parent / (new.name + ".json")).write_text(json.dumps(final), encoding="utf-8")
    (new.parent / (new.name + ".replies.json")).write_text(json.dumps([json.dumps(raw_reply())]), encoding="utf-8")

    assert [p.name for p in latest_runs(folder)] == ["FICTO_20990102T000000Z.run.json"]
    main([str(folder), "--config", str(config)])

    written = json.loads((folder / "FICTO_20990102T000000Z.score.json").read_text(encoding="utf-8"))
    assert written["validity"]["first_attempt"] is True
    assert written["document"] == "FICTO" and written["configuration"] == "B"
    assert not (folder / "FICTO_20990101T000000Z.score.json").exists()
    rows = list(csv.reader((folder / "manual_review.csv").open(encoding="utf-8")))
    assert rows[1][2] == "Zorblax Holdings"


def test_command_line_without_saved_replies_reports_first_attempt_as_unknown(tmp_path: Path):
    test_command_line_scores_the_latest_run_and_writes_the_review_list(tmp_path)
    (tmp_path / "B" / "FICTO_20990102T000000Z.replies.json").unlink()
    main([str(tmp_path / "B" / "FICTO_20990102T000000Z.run.json"), "--config", str(tmp_path / "config.yaml")])
    written = json.loads((tmp_path / "B" / "FICTO_20990102T000000Z.score.json").read_text(encoding="utf-8"))
    assert written["validity"]["first_attempt"] is None
