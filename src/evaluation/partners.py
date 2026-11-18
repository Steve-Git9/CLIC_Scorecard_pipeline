"""Partner list scoring: matching, classification of extra partners, recall, amounts, sum check.

Matching (rule 1): an extracted partner matches a gold partner when their names are equal
after normalisation (case folded, whitespace collapsed). The gold set is the only reference.

Every extracted partner that matches no gold partner is classified (rule 3):
    duplicate          repeats a gold partner that another extracted entry already matched,
                       or is a fragment (a whole word sequence) of an already matched gold name
    supported_extra    the name appears in the Docling Markdown of the source document
    unsupported_extra  the name does not appear in that document, nor any distinctive word of it
    unsure             anything the rules above cannot settle, scored with half values
                       (protocol section 6.4); the case says which half values apply:
        variant            part of, or containing, the name of a gold partner nobody matched:
                           half a match with that partner (its amount counts half) and half an
                           extra; when another unsure name already took that half, half a duplicate
        contains_matched   contains the name of a gold partner that is already matched:
                           half a duplicate
        partial_name       the whole name is not in the document but a distinctive word of it is:
                           half a supported and half an unsupported extra
        no_markdown        no Docling Markdown to check against: as partial_name

Where a document's Markdown cannot be published, a DocumentTerms record (built from the Markdown
by src.evaluation.document_terms) answers the same presence checks for the names of a batch, so
the classes are the same as with the Markdown itself.

A decision of the author (`decisions`, normalised name -> decision) replaces the half values
of an unsure name: ("gold", <gold partner name>) is a certain match with that partner, or a
duplicate when that partner is already matched in the run; ("supported_extra",) and
("unsupported_extra",) set the class. Decisions apply only to names the rules leave unsure.

Every entry carries weights: how much of it counts as each class, and how much of it counts as
an extra in the over inclusion rate. Counts can therefore contain halves.
"""

from __future__ import annotations

import html
import re
from typing import Any

from src.evaluation.normalise import compare, normalise_amount

# Words too common in organisation names to show, on their own, that a name is in a document.
_GENERIC_WORDS = {
    "oy", "oyj", "ab", "abp", "ltd", "limited", "gmbh", "ag", "sa", "srl", "bv", "nv", "inc", "plc",
    "llc", "asa", "spa", "the", "and", "for", "of", "de", "der", "und", "university", "universiteit",
    "universität", "yliopisto", "institute", "research", "centre", "center", "company", "group",
    "technical", "technology", "technologies", "foundation", "association", "finland", "finnish",
    "national", "international", "corporation", "solutions", "services", "sciences",
}

CLASSES = ("matched", "duplicate", "supported_extra", "unsupported_extra")
UNSURE_CASES = ("variant", "contains_matched", "partial_name", "no_markdown")
DECISIONS = ("gold", "supported_extra", "unsupported_extra")
Decision = tuple  # ("gold", name) | ("supported_extra",) | ("unsupported_extra",)


def normalise_name(name: str) -> str:
    return " ".join(name.split()).casefold()


def normalise_document(markdown: str) -> str:
    """Docling Markdown as searchable text: entities decoded, emphasis and escapes removed,
    whitespace (including table padding) collapsed, case folded."""
    text = html.unescape(markdown)
    text = re.sub(r"\\(?=[^\w\s])", "", text)
    text = re.sub(r"[*_`]", "", text)
    return " ".join(text.split()).casefold()


class DocumentTerms:
    """Stand in for a document's normalised Markdown: which terms (normalised names and their
    distinctive words) occur in it, recorded from the Markdown for every name of a batch."""

    def __init__(self, present: list[str], absent: list[str]):
        self.present, self.absent = set(present), set(absent)

    def contains(self, needle: str) -> bool:
        if needle in self.present:
            return True
        if needle in self.absent:
            return False
        raise KeyError(f"term {needle!r} was not recorded from the document; rebuild its terms file")


def _contains(haystack: str | DocumentTerms, needle: str) -> bool:
    if isinstance(haystack, DocumentTerms):
        return bool(needle) and haystack.contains(needle)
    return bool(needle) and re.search(rf"(?<!\w){re.escape(needle)}(?!\w)", haystack) is not None


def distinctive_words(pred_key: str) -> list[str]:
    """The words of a normalised name that can show, on their own, that it is in a document."""
    return [w for w in re.findall(r"\w+", pred_key) if len(w) >= 4 and w not in _GENERIC_WORDS]


def classify_unmatched(
    pred_key: str, gold_keys: list[str], matched_gold: set[int], document: str | DocumentTerms | None
) -> tuple[str, int | None, str, str | None]:
    """(class, index of the related gold partner or None, reason, unsure case or None)."""
    for g, gold_key in enumerate(gold_keys):
        if _contains(gold_key, pred_key):
            if g in matched_gold:
                return "duplicate", g, "fragment of a gold partner that is already matched", None
            return "unsure", g, "part of an unmatched gold partner's name; may be a variant of it", "variant"
        if _contains(pred_key, gold_key):
            if g in matched_gold:
                return "unsure", g, "contains the name of a gold partner that is already matched", "contains_matched"
            return "unsure", g, "contains the name of an unmatched gold partner; may be a variant of it", "variant"
    if document is None:
        return "unsure", None, "no Docling Markdown of the source document to check against", "no_markdown"
    if _contains(document, pred_key):
        return "supported_extra", None, "name appears in the Docling Markdown", None
    found = [w for w in distinctive_words(pred_key) if _contains(document, w)]
    if found:
        return "unsure", None, f"whole name not in the document, but {', '.join(found)} is", "partial_name"
    return "unsupported_extra", None, "name does not appear in the Docling Markdown", None


def _weights(**w: float) -> dict[str, float]:
    return {c: float(w.get(c, 0.0)) for c in CLASSES}


def score_partners(
    gold_partners: list[dict],
    pred_partners: list[dict],
    gold_total: int | None,
    document_markdown: str | DocumentTerms | None,
    decisions: dict[str, Decision] | None = None,
) -> dict[str, Any]:
    decisions = decisions or {}
    gold_keys = [normalise_name(p["partner_name"]) for p in gold_partners]
    gold_index = {k: g for g, k in enumerate(gold_keys)}
    for name, decision in decisions.items():
        if decision[0] not in DECISIONS:
            raise ValueError(f"unknown decision {decision!r} for {name!r}, expected one of {DECISIONS}")
        if decision[0] == "gold" and normalise_name(decision[1]) not in gold_index:
            raise ValueError(f"decision for {name!r} names {decision[1]!r}, which is not a gold partner")
    document = (normalise_document(document_markdown) if isinstance(document_markdown, str)
                else document_markdown)
    entries: list[dict[str, Any]] = []
    matched_gold: set[int] = set()   # gold partners matched with certainty
    half_found: set[int] = set()     # gold partners half found through an unsure name

    def match(entry: dict, g: int, weight: float) -> None:
        gold_amount = normalise_amount(gold_partners[g].get("requested_cents"))
        entry["amount_outcome"] = compare(gold_amount, normalise_amount(entry["requested_cents"]))
        entry["amount_weight"] = weight

    # Pass 1: name matches, in extraction order.
    for p in pred_partners:
        key = normalise_name(p.get("partner_name") or "")
        entry: dict[str, Any] = {"partner_name": p.get("partner_name"), "class": None, "gold_partner": None,
                                 "reason": None, "unsure_case": None, "decided": False,
                                 "requested_cents": p.get("requested_cents"),
                                 "amount_outcome": None, "amount_weight": 0.0}
        candidates = [g for g, gk in enumerate(gold_keys) if gk == key]
        free = [g for g in candidates if g not in matched_gold]
        if free:
            g = free[0]
            matched_gold.add(g)
            entry.update({"class": "matched", "gold_partner": gold_partners[g]["partner_name"],
                          "reason": "same name", "weights": _weights(matched=1), "extra_weight": 0.0})
            match(entry, g, 1.0)
        elif candidates:
            entry.update({"class": "duplicate", "gold_partner": gold_partners[candidates[0]]["partner_name"],
                          "reason": "repeats a gold partner that is already matched",
                          "weights": _weights(duplicate=1), "extra_weight": 1.0})
        entries.append(entry)

    # Pass 2: classify the rest, now that every certain match is known.
    for entry in entries:
        if entry["class"] is not None:
            continue
        key = normalise_name(entry["partner_name"] or "")
        cls, g, reason, case = classify_unmatched(key, gold_keys, matched_gold, document)
        entry.update({"class": cls, "reason": reason,
                      "gold_partner": gold_partners[g]["partner_name"] if g is not None else None})
        if cls != "unsure":
            entry.update({"weights": _weights(**{cls: 1}), "extra_weight": 1.0})
            continue
        decision = decisions.get(key)
        if decision is not None:
            entry.update({"decided": True, "reason": f"author's decision: {':'.join(decision)}"})
            if decision[0] == "gold":
                d = gold_index[normalise_name(decision[1])]
                entry["gold_partner"] = gold_partners[d]["partner_name"]
                if d in matched_gold:
                    entry.update({"class": "duplicate", "weights": _weights(duplicate=1), "extra_weight": 1.0})
                else:
                    matched_gold.add(d)
                    half_found.discard(d)
                    entry.update({"class": "matched", "weights": _weights(matched=1), "extra_weight": 0.0})
                    match(entry, d, 1.0)
            else:
                entry.update({"class": decision[0], "gold_partner": None,
                              "weights": _weights(**{decision[0]: 1}), "extra_weight": 1.0})
            continue
        entry["unsure_case"] = case
        if case == "variant" and g not in matched_gold and g not in half_found:
            half_found.add(g)
            entry.update({"weights": _weights(matched=0.5), "extra_weight": 0.5})
            match(entry, g, 0.5)
        elif case in ("variant", "contains_matched"):
            entry.update({"weights": _weights(duplicate=0.5), "extra_weight": 1.0})
        else:  # partial_name, no_markdown
            entry.update({"weights": _weights(supported_extra=0.5, unsupported_extra=0.5), "extra_weight": 1.0})

    # A gold partner that a decision matched later in the list no longer counts as half found.
    half_found -= matched_gold
    for entry in entries:
        if entry["unsure_case"] == "variant" and entry["weights"]["matched"] == 0.5:
            g = gold_index[normalise_name(entry["gold_partner"])]
            if g in matched_gold:
                entry.update({"weights": _weights(duplicate=0.5), "extra_weight": 1.0,
                              "amount_outcome": None, "amount_weight": 0.0})

    gold_status = []
    for g, gp in enumerate(gold_partners):
        found = 1.0 if g in matched_gold else 0.5 if g in half_found else 0.0
        gold_status.append({"partner_name": gp["partner_name"], "requested_cents": gp.get("requested_cents"),
                            "found": found, "unsure": g in half_found})

    found_total = sum(s["found"] for s in gold_status)
    amount_outcomes: dict[str, float] = {}
    for e in entries:
        if e["amount_weight"]:
            amount_outcomes[e["amount_outcome"]] = amount_outcomes.get(e["amount_outcome"], 0.0) + e["amount_weight"]
    classes = {c: sum(e["weights"][c] for e in entries) for c in CLASSES}
    unsure = [e for e in entries if e["unsure_case"] is not None]
    certain_matched = [e for e in entries if e["class"] == "matched"]
    supported = [e for e in entries if e["class"] == "supported_extra"]
    return {
        "entries": entries,
        "gold_status": gold_status,
        "gold_count": len(gold_partners),
        "matched_count": found_total,
        "missed_gold": [s["partner_name"] for s in gold_status if s["found"] < 1],
        "missed_weight": sum(1 - s["found"] for s in gold_status),
        "recall": found_total / len(gold_partners) if gold_partners else None,
        "amount_accuracy": amount_outcomes.get("correct", 0.0) / found_total if found_total else None,
        "amount_outcomes": amount_outcomes,
        "classes": classes,
        "extracted_count": len(entries),
        "extra_weight": sum(e["extra_weight"] for e in entries),
        "unsure": [{"partner_name": e["partner_name"], "case": e["unsure_case"], "reason": e["reason"],
                    "related_gold_partner": e["gold_partner"], "requested_cents": e["requested_cents"]}
                   for e in unsure],
        "unsure_error_weight": _unsure_error_weight(unsure, gold_status),
        "sum_check": sum_check(certain_matched, supported, gold_total),
    }


def _unsure_error_weight(unsure: list[dict], gold_status: list[dict]) -> float:
    """The part of the run's errors that comes only from unsure names."""
    weight = sum(1 - s["found"] for s in gold_status if s["unsure"])
    for e in unsure:
        weight += e["weights"]["duplicate"] + e["weights"]["unsupported_extra"]
        if e["amount_weight"] and e["amount_outcome"] != "correct":
            weight += e["amount_weight"]
    return weight


def _amounts(entries: list[dict]) -> tuple[int, int]:
    """(sum of the valid amounts, number of entries whose amount is null or invalid)."""
    total, missing = 0, 0
    for e in entries:
        value = normalise_amount(e.get("requested_cents"))
        if isinstance(value, int):
            total += value
        else:
            missing += 1
    return total, missing


def sum_check(matched: list[dict], supported_extras: list[dict], stated_total: int | None) -> dict[str, Any]:
    """Rule 5. The stated total is the total requested amount the document states (gold).
    Only partners matched with certainty and certain supported extras take part."""
    matched_sum, matched_missing = _amounts(matched)
    extras_sum, _ = _amounts(supported_extras)
    complete = matched_missing == 0 and stated_total is not None
    with_extras = matched_sum + extras_sum
    matched_equal = (matched_sum == stated_total) if complete else None
    with_extras_equal = (with_extras == stated_total) if complete else None
    return {
        "stated_total_cents": stated_total,
        "matched_sum_cents": matched_sum,
        "matched_without_amount": matched_missing,
        "matched_sum_equals_total": matched_equal,
        "supported_extras_sum_cents": extras_sum,
        "sum_with_supported_extras_cents": with_extras,
        "sum_with_supported_extras_equals_total": with_extras_equal,
        # True only when the matched partners add up to the total and the extras break that.
        "supported_extras_make_sum_deviate": (
            matched_equal and not with_extras_equal) if complete else None,
    }
