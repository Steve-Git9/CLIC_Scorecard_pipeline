"""Partner list scoring: matching, classification of extra partners, recall, amounts, sum check.

Matching (rule 1): an extracted partner matches a gold partner when their names are equal
after normalisation (case folded, whitespace collapsed). The gold set is the only reference.

Every extracted partner that matches no gold partner is classified (rule 3):
    duplicate          repeats a gold partner that another extracted entry already matched,
                       or is a fragment (a whole word sequence) of an already matched gold name
    supported_extra    the name appears in the Docling Markdown of the source document
    unsupported_extra  the name does not appear in that document, nor any distinctive word of it
    manual_review      anything the rules above cannot settle (rule 4): a name that overlaps an
                       unmatched gold name, a name that contains a gold name, a name whose
                       distinctive words appear in the document but not the whole name, or no
                       Docling Markdown to check against
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


def normalise_name(name: str) -> str:
    return " ".join(name.split()).casefold()


def normalise_document(markdown: str) -> str:
    """Docling Markdown as searchable text: entities decoded, emphasis and escapes removed,
    whitespace (including table padding) collapsed, case folded."""
    text = html.unescape(markdown)
    text = re.sub(r"\\(?=[^\w\s])", "", text)
    text = re.sub(r"[*_`]", "", text)
    return " ".join(text.split()).casefold()


def _contains(haystack: str, needle: str) -> bool:
    return bool(needle) and re.search(rf"(?<!\w){re.escape(needle)}(?!\w)", haystack) is not None


def classify_unmatched(
    pred_key: str, gold_keys: list[str], matched_gold: set[int], document: str | None
) -> tuple[str, int | None, str]:
    """(class, index of the related gold partner or None, reason) for one unmatched name."""
    for g, gold_key in enumerate(gold_keys):
        if _contains(gold_key, pred_key):
            if g in matched_gold:
                return "duplicate", g, "fragment of a gold partner that is already matched"
            return "manual_review", g, "part of an unmatched gold partner's name; may be a variant of it"
        if _contains(pred_key, gold_key):
            return "manual_review", g, "contains a gold partner's name"
    if document is None:
        return "manual_review", None, "no Docling Markdown of the source document to check against"
    if _contains(document, pred_key):
        return "supported_extra", None, "name appears in the Docling Markdown"
    distinctive = [w for w in re.findall(r"\w+", pred_key) if len(w) >= 4 and w not in _GENERIC_WORDS]
    found = [w for w in distinctive if _contains(document, w)]
    if found:
        return "manual_review", None, f"whole name not in the document, but {', '.join(found)} is"
    return "unsupported_extra", None, "name does not appear in the Docling Markdown"


def score_partners(
    gold_partners: list[dict],
    pred_partners: list[dict],
    gold_total: int | None,
    document_markdown: str | None,
) -> dict[str, Any]:
    gold_keys = [normalise_name(p["partner_name"]) for p in gold_partners]
    document = normalise_document(document_markdown) if document_markdown is not None else None
    entries: list[dict[str, Any]] = []
    matched_gold: dict[int, int] = {}  # gold index -> entry index

    # Pass 1: name matches, in extraction order.
    for p in pred_partners:
        key = normalise_name(p.get("partner_name") or "")
        entry: dict[str, Any] = {"partner_name": p.get("partner_name"), "class": None, "gold_partner": None,
                                 "reason": None, "requested_cents": p.get("requested_cents")}
        candidates = [g for g, gk in enumerate(gold_keys) if gk == key]
        free = [g for g in candidates if g not in matched_gold]
        if free:
            g = free[0]
            matched_gold[g] = len(entries)
            entry.update({"class": "matched", "gold_partner": gold_partners[g]["partner_name"],
                          "reason": "same name"})
            gold_amount = normalise_amount(gold_partners[g].get("requested_cents"))
            entry["amount_outcome"] = compare(gold_amount, normalise_amount(p.get("requested_cents")))
        elif candidates:
            entry.update({"class": "duplicate", "gold_partner": gold_partners[candidates[0]]["partner_name"],
                          "reason": "repeats a gold partner that is already matched"})
        entries.append(entry)

    # Pass 2: classify the rest, now that every certain match is known.
    for entry in entries:
        if entry["class"] is None:
            cls, g, reason = classify_unmatched(normalise_name(entry["partner_name"] or ""), gold_keys,
                                                set(matched_gold), document)
            entry.update({"class": cls, "reason": reason,
                          "gold_partner": gold_partners[g]["partner_name"] if g is not None else None})

    matched = [e for e in entries if e["class"] == "matched"]
    amounts_correct = sum(1 for e in matched if e["amount_outcome"] == "correct")
    missed = [gold_partners[g]["partner_name"] for g in range(len(gold_partners)) if g not in matched_gold]
    supported = [e for e in entries if e["class"] == "supported_extra"]
    return {
        "entries": entries,
        "gold_count": len(gold_partners),
        "matched_count": len(matched),
        "missed_gold": missed,
        "recall": len(matched) / len(gold_partners) if gold_partners else None,
        "amount_accuracy": amounts_correct / len(matched) if matched else None,
        "amount_outcomes": _count(e["amount_outcome"] for e in matched),
        "classes": _count(e["class"] for e in entries),
        "manual_review": [{"partner_name": e["partner_name"], "reason": e["reason"],
                           "related_gold_partner": e["gold_partner"]}
                          for e in entries if e["class"] == "manual_review"],
        "sum_check": sum_check(matched, supported, gold_total),
    }


def _count(values) -> dict[str, int]:
    counts: dict[str, int] = {}
    for v in values:
        counts[v] = counts.get(v, 0) + 1
    return counts


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
    """Rule 5. The stated total is the total requested amount the document states (gold)."""
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
