"""Tests for the half scores of unsure partner names and the author's decisions (protocol
section 6.4). FICTIONAL TEST DATA ONLY: the fixtures come from test_scorer.py and describe no
real CLIC project."""

from __future__ import annotations

import pytest

from src.evaluation.partners import score_partners
from tests.test_scorer import GOLD, MARKDOWN, final_from_gold, partner, score

TOTAL = 300_000_000


def gold_preds(*names: str) -> list[dict]:
    """Extracted partners equal to the named gold partners, amounts included."""
    return [partner(p["partner_name"], p["requested_cents"]) for p in GOLD["partners"] if p["partner_name"] in names]


def test_variant_of_an_unmatched_gold_partner_is_half_a_match():
    preds = gold_preds("Imaginary Labs Oy", "Fictional Research Centre Ltd") + [partner("Nowhere", 150_000_000)]
    r = score_partners(GOLD["partners"], preds, TOTAL, MARKDOWN)
    entry = r["entries"][2]
    assert entry["class"] == "unsure" and entry["unsure_case"] == "variant"
    assert entry["weights"]["matched"] == 0.5 and entry["extra_weight"] == 0.5
    assert r["recall"] == pytest.approx(2.5 / 3)
    assert r["missed_weight"] == 0.5
    assert r["amount_outcomes"] == {"correct": 2.5}
    assert r["amount_accuracy"] == 1.0
    assert r["unsure_error_weight"] == 0.5          # the half missed gold partner
    assert r["extra_weight"] == 0.5


def test_variant_with_a_wrong_amount_counts_half_a_wrong_value():
    preds = gold_preds("Imaginary Labs Oy", "Fictional Research Centre Ltd") + [partner("Nowhere", 1)]
    r = score_partners(GOLD["partners"], preds, TOTAL, MARKDOWN)
    assert r["amount_outcomes"] == {"correct": 2.0, "wrong": 0.5}
    assert r["amount_accuracy"] == pytest.approx(2.0 / 2.5)
    assert r["unsure_error_weight"] == 1.0


def test_second_variant_of_the_same_gold_partner_is_half_a_duplicate():
    preds = [partner("Nowhere", 150_000_000), partner("NOWHERE")]
    r = score_partners(GOLD["partners"], preds, TOTAL, MARKDOWN)
    assert r["entries"][0]["weights"]["matched"] == 0.5
    assert r["entries"][1]["weights"]["duplicate"] == 0.5
    assert r["classes"]["duplicate"] == 0.5


def test_name_containing_a_matched_gold_name_is_half_a_duplicate():
    preds = gold_preds("Imaginary Labs Oy") + [partner("Imaginary Labs Oy Finland branch")]
    r = score_partners(GOLD["partners"], preds, TOTAL, MARKDOWN)
    entry = r["entries"][1]
    assert entry["unsure_case"] == "contains_matched"
    assert entry["weights"]["duplicate"] == 0.5 and entry["extra_weight"] == 1.0


def test_partial_name_is_half_supported_and_half_unsupported():
    r = score_partners(GOLD["partners"], [partner("Zorblax Holdings")], TOTAL, MARKDOWN)
    entry = r["entries"][0]
    assert entry["unsure_case"] == "partial_name"
    assert entry["weights"]["supported_extra"] == 0.5 and entry["weights"]["unsupported_extra"] == 0.5
    assert r["unsure_error_weight"] == 0.5


def test_fully_correct_is_half_when_only_unsure_names_cause_errors():
    final = final_from_gold()
    final["partners"] = gold_preds("Imaginary Labs Oy", "Fictional Research Centre Ltd") + [
        partner("Nowhere", 150_000_000)]
    s = score(final)
    assert s["errors"]["misses"] == 0.5
    assert s["errors"]["certain"] == 0
    assert s["contains_unsure"] is True
    assert s["fully_correct"] == 0.5


def test_fully_correct_is_zero_with_a_certain_error_besides_an_unsure_name():
    final = final_from_gold(proposal__proposal_acronym="WRONG")
    final["partners"].append(partner("Zorblax Holdings"))
    s = score(final)
    assert s["errors"]["certain"] == 1
    assert s["fully_correct"] == 0.0


def test_decision_gold_turns_a_variant_into_a_certain_match():
    final = final_from_gold()
    final["partners"] = gold_preds("Imaginary Labs Oy", "Fictional Research Centre Ltd") + [
        partner("Nowhere", 150_000_000)]
    s = score(final, decisions={"nowhere": ("gold", "Nowhere University")})
    entry = s["partners"]["entries"][2]
    assert entry["class"] == "matched" and entry["decided"] is True
    assert s["partners"]["recall"] == 1.0
    assert s["partners"]["unsure"] == []
    assert s["fully_correct"] == 1.0


def test_decision_gold_for_an_already_matched_partner_is_a_duplicate():
    final = final_from_gold()
    final["partners"].append(partner("Imaginary Labs Oy Finland branch"))
    s = score(final, decisions={"imaginary labs oy finland branch": ("gold", "Imaginary Labs Oy")})
    assert s["partners"]["entries"][3]["class"] == "duplicate"
    assert s["errors"]["duplicates"] == 1
    assert s["fully_correct"] == 0.0


def test_decision_extra_sets_the_class():
    final = final_from_gold()
    final["partners"].append(partner("Zorblax Holdings"))
    supported = score(final, decisions={"zorblax holdings": ("supported_extra",)})
    assert supported["fully_correct"] == 1.0 and supported["reviewer_decisions"]["supported_extras"] == 1
    unsupported = score(final, decisions={"zorblax holdings": ("unsupported_extra",)})
    assert unsupported["errors"]["unsupported_extras"] == 1 and unsupported["fully_correct"] == 0.0


def test_decisions_do_not_change_names_the_rules_settle():
    r = score_partners(GOLD["partners"], [partner("Phantom Dynamics GmbH")], TOTAL, MARKDOWN,
                       {"phantom dynamics gmbh": ("supported_extra",)})
    assert r["entries"][0]["class"] == "unsupported_extra"


def test_decision_naming_an_unknown_gold_partner_is_rejected():
    with pytest.raises(ValueError):
        score_partners(GOLD["partners"], [partner("Nowhere")], TOTAL, MARKDOWN, {"nowhere": ("gold", "Nobody Ltd")})


def test_scoring_is_deterministic():
    final = final_from_gold()
    final["partners"] += [partner("Nowhere"), partner("Zorblax Holdings")]
    assert score(final) == score(final)
