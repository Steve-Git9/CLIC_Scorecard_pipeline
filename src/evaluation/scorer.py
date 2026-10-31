"""Score one extraction run against the gold set of the same document.

Scored: the scalar fields of `proposal` and `proposal_facts` from the shared schema, and the
partner list. Not scored: `metadata` (extraction_timestamp, source_file).

Outcomes per value: correct (null against null included), miss (null where gold has a value),
unsupported (a value where gold is null), wrong (both present, different after normalisation).
A run that is not valid after repair has every scored field counted as a miss.

Fully correct (protocol section 6.5): 1 when the run is valid after repair and has no error,
0.5 when its only errors come from unsure partner names (half scores, section 6.4), 0 as soon
as it has one certain error or is not valid after repair.
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
from src.evaluation.partners import Decision, score_partners
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
    """Partner score of a run that is not valid after repair: every gold partner missed."""
    gold_partners = gold.get("partners", [])
    status = [{"partner_name": p["partner_name"], "requested_cents": p.get("requested_cents"),
               "found": 0.0, "unsure": False} for p in gold_partners]
    return {"entries": [], "gold_status": status, "gold_count": len(status), "matched_count": 0.0,
            "missed_gold": [s["partner_name"] for s in status], "missed_weight": float(len(status)),
            "recall": 0.0 if status else None, "amount_accuracy": None, "amount_outcomes": {},
            "classes": {"matched": 0.0, "duplicate": 0.0, "supported_extra": 0.0, "unsupported_extra": 0.0},
            "extracted_count": 0, "extra_weight": 0.0, "unsure": [], "unsure_error_weight": 0.0,
            "sum_check": None}


def score_run(
    final: dict | None,
    gold: dict,
    replies: list[str] | None,
    protocol: str,
    document_markdown: str | None,
    decisions: dict[str, Decision] | None = None,
) -> dict[str, Any]:
    _check_gold(gold)
    first_ok, first_reason = first_attempt_validity(replies, protocol)
    repaired_ok, repaired_problems = after_repair_validity(final)

    scalars = score_scalars(gold, final, repaired_ok)
    if repaired_ok:
        partners = score_partners(gold.get("partners", []), final.get("partners", []),
                                  gold.get("proposal_facts", {}).get("requested_total_cents"),
                                  document_markdown, decisions)
    else:
        partners = _empty_partner_score(gold)

    outcomes = [row["outcome"] for row in scalars]
    amounts = partners["amount_outcomes"]
    classes = partners["classes"]
    errors = {
        "misses": outcomes.count("miss") + partners["missed_weight"] + amounts.get("miss", 0.0),
        "wrong_values": outcomes.count("wrong") + amounts.get("wrong", 0.0),
        "unsupported_values": outcomes.count("unsupported") + amounts.get("unsupported", 0.0),
        "unsupported_extras": classes["unsupported_extra"],
        "duplicates": classes["duplicate"],
    }
    errors["total"] = sum(errors.values())
    errors["from_unsure_names"] = partners["unsure_error_weight"]
    errors["certain"] = errors["total"] - errors["from_unsure_names"]
    has_unsure = bool(partners["unsure"])
    if not repaired_ok or errors["certain"] > 0:
        fully_correct = 0.0
    else:
        fully_correct = 0.5 if has_unsure else 1.0

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
            "supported_extras": classes["supported_extra"],
            "unsure_names": len(partners["unsure"]),
        },
        "contains_unsure": has_unsure,
        "fully_correct": fully_correct,
    }
