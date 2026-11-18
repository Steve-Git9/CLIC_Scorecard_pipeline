"""A recorded terms file gives the scorer the same partner classes as the document itself."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.evaluation.document_terms import build_terms, extracted_names
from src.evaluation.partners import DocumentTerms, score_partners

MARKDOWN = "| Partner | Amount |\n|---|---|\n| Fictional Labs Oy | 100 |\n| Nordwind Analytics | 50 |\n"
GOLD = [{"partner_name": "Fictional Labs Oy", "requested_cents": 10000}]
PRED = [{"partner_name": "Fictional Labs Oy", "requested_cents": 10000},
        {"partner_name": "Nordwind Analytics", "requested_cents": 5000},        # in the document
        {"partner_name": "Phantom Dynamics GmbH", "requested_cents": 1},       # not in it
        {"partner_name": "Nordwind Holding", "requested_cents": 2}]            # only a distinctive word in it


def test_terms_give_the_same_partner_score_as_the_markdown():
    names = {" ".join(p["partner_name"].split()).casefold() for p in PRED}
    terms = build_terms(MARKDOWN, names)
    with_text = score_partners(GOLD, PRED, None, MARKDOWN)
    with_terms = score_partners(GOLD, PRED, None, DocumentTerms(terms["present"], terms["absent"]))
    assert json.dumps(with_text, sort_keys=True, default=repr) == json.dumps(with_terms, sort_keys=True, default=repr)
    assert {e["partner_name"]: e["class"] for e in with_terms["entries"]}["Nordwind Analytics"] == "supported_extra"


def test_an_unrecorded_term_is_an_error_not_a_guess():
    with pytest.raises(KeyError):
        score_partners(GOLD, [{"partner_name": "Unknown Org", "requested_cents": 1}], None, DocumentTerms([], []))


def test_extracted_names_come_from_final_records_only(tmp_path: Path):
    (tmp_path / "B").mkdir()
    (tmp_path / "B" / "FICTO_1.json").write_text(json.dumps({"partners": [{"partner_name": " Fictional  Labs Oy"}]}))
    (tmp_path / "B" / "FICTO_1.run.json").write_text(json.dumps({"partners": [{"partner_name": "Not A Record"}]}))
    assert extracted_names(tmp_path, "FICTO") == {"fictional labs oy"}
