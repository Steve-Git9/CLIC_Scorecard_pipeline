"""Score one extraction run against the gold set of the same document.

Scored: the scalar fields of `proposal` and `proposal_facts` from the shared schema, and the
partner list. Not scored: `metadata` (extraction_timestamp, source_file).

Outcomes per value: correct (null against null included), miss (null where gold has a value),
unsupported (a value where gold is null), wrong (both present, different after normalisation).
A run that is not valid after repair has every scored field counted as a miss.
"""

from __future__ import annotations

from typing import Any, Callable

from Second_step_CLICpipeline.clic_extract.schema import FACT_KEYS, PROPOSAL_KEYS
from src.evaluation.normalise import (
    Invalid,
    compare,
    normalise_amount,
    normalise_date,
    normalise_integer,
    normalise_text,
)
from src.evaluation.partners import score_partners
from src.evaluation.validity import after_repair_validity, first_attempt_validity

NORMALISERS: dict[str, Callable[[Any], Any]] = {
    "proposal.proposal_acronym": normalise_text,
    "proposal.proposal_title": normalise_text,
    "proposal.call_identifier": normalise_text,
    "proposal.submission_date": normalise_date,
    "proposal_facts.requested_total_cents": normalise_amount,
    "proposal_facts.trl_start": normalise_integer,
    "proposal_facts.trl_target": normalise_integer,
    "proposal_facts.mcrl_start": normalise_integer,
    "proposal_facts.mcrl_target": normalise_integer,
}
SCALAR_FIELDS = list(NORMALISERS)

_schema_fields = [f"proposal.{k}" for k in PROPOSAL_KEYS] + [f"proposal_facts.{k}" for k in FACT_KEYS]
if sorted(_schema_fields) != sorted(SCALAR_FIELDS):
    raise RuntimeError(f"scorer fields {SCALAR_FIELDS} no longer match the shared schema {_schema_fields}")


def _value(doc: dict | None, field: str) -> Any:
    section, key = field.split(".")
    container = doc.get(section) if isinstance(doc, dict) else None
    return container.get(key) if isinstance(container, dict) else None


def _check_gold(gold: dict) -> None:
    for field in SCALAR_FIELDS:
        if isinstance(NORMALISERS[field](_value(gold, field)), Invalid):
            raise ValueError(f"gold value for {field} cannot be normalised: {_value(gold, field)!r}")
    for p in gold.get("partners", []):
        if isinstance(normalise_amount(p.get("requested_cents")), Invalid):
            raise ValueError(f"gold amount for partner {p.get('partner_name')!r} is not integer cents")


def score_scalars(gold: dict, final: dict | None, valid: bool) -> list[dict[str, Any]]:
    rows = []
    for field in SCALAR_FIELDS:
        gold_value = _value(gold, field)
        pred_value = _value(final, field) if valid else None
        outcome = compare(NORMALISERS[field](gold_value), NORMALISERS[field](pred_value)) if valid else "miss"
        rows.append({"field": field, "gold": gold_value, "extracted": pred_value, "outcome": outcome})
    return rows


def _empty_partner_score(gold: dict) -> dict[str, Any]:
    names = [p["partner_name"] for p in gold.get("partners", [])]
    return {"entries": [], "gold_count": len(names), "matched_count": 0, "missed_gold": names,
            "recall": 0.0 if names else None, "amount_accuracy": None, "amount_outcomes": {},
            "classes": {}, "manual_review": [], "sum_check": None}


def score_run(
    final: dict | None,
    gold: dict,
    replies: list[str] | None,
    protocol: str,
    document_markdown: str | None,
) -> dict[str, Any]:
    _check_gold(gold)
    first_ok, first_reason = first_attempt_validity(replies, protocol)
    repaired_ok, repaired_problems = after_repair_validity(final)

    scalars = score_scalars(gold, final, repaired_ok)
    if repaired_ok:
        partners = score_partners(gold.get("partners", []), final.get("partners", []),
                                  gold.get("proposal_facts", {}).get("requested_total_cents"),
                                  document_markdown)
    else:
        partners = _empty_partner_score(gold)

    outcomes = [row["outcome"] for row in scalars]
    amounts = partners["amount_outcomes"]
    classes = partners["classes"]
    errors = {
        "misses": outcomes.count("miss") + len(partners["missed_gold"]) + amounts.get("miss", 0),
        "wrong_values": outcomes.count("wrong") + amounts.get("wrong", 0),
        "unsupported_values": outcomes.count("unsupported") + amounts.get("unsupported", 0),
        "unsupported_extras": classes.get("unsupported_extra", 0),
        "duplicates": classes.get("duplicate", 0),
    }
    errors["total"] = sum(errors.values())
    pending = len(partners["manual_review"])
    if errors["total"] > 0 or not repaired_ok:
        fully_correct: bool | None = False
    else:
        fully_correct = None if pending else True

    return {
        "validity": {
            "first_attempt": first_ok,
            "first_attempt_reason": first_reason,
            "after_repair": repaired_ok,
            "after_repair_problems": repaired_problems,
        },
        "scalars": scalars,
        "scalar_accuracy": outcomes.count("correct") / len(outcomes),
        "partners": partners,
        "errors": errors,
        "unsupported_values_including_extras": errors["unsupported_values"] + errors["unsupported_extras"],
        "reviewer_decisions": {
            "supported_extras": classes.get("supported_extra", 0),
            "pending_manual_review": pending,
        },
        "fully_correct": fully_correct,
    }
