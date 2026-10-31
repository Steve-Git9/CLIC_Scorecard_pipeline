"""Result tables of a scored batch (protocol section 7.1), built from the scored final runs.

Every function takes `runs`: one dict per final run with the keys
    configuration, document, repetition, run_file, status, cost_usd, end_to_end_seconds,
    docling_conversion_seconds, tokens (dict), final (the final record or None) and score
    (the scorer's result).
and returns plain rows (lists of dicts) that the caller writes as CSV.

Definitions (protocol section 7.1):
    field accuracy       share of the nine scalar fields scored correct in a run
    per document value   mean over the three final runs of a configuration on a document
    summary mean, range  mean, minimum and maximum of the ten per document values
    consistency          per document: share of the ten items (nine fields plus the partner list)
                         with the same normalised value in all three runs; a run that is not
                         valid after repair makes every item differ
    over inclusion rate  all extra partner weight divided by all extracted partners, pooled over
                         every final run of the configuration
    cost of pass         mean cost per run divided by the mean fully correct value, or
                         "not defined" when no run is fully correct
"""

from __future__ import annotations

from collections import defaultdict
from statistics import mean
from typing import Any, Iterable

from src.evaluation.normalise import Invalid, normalise_amount
from src.evaluation.partners import normalise_name
from src.evaluation.scorer import NORMALISERS, SCALAR_FIELDS

METRICS = ("field_accuracy", "partner_recall", "amount_accuracy", "fully_correct", "cost_usd",
           "end_to_end_seconds", "errors_total")
CONTRAST_METRICS = ("field_accuracy", "partner_recall", "amount_accuracy", "fully_correct", "cost_usd",
                    "end_to_end_seconds")

# (contrast, intended factor, [(varied, reference)], other differences found in Phase 0).
# Each difference is the varied configuration minus the reference configuration.
CONTRASTS: list[tuple[str, str, list[tuple[str, str]], str]] = [
    ("Model size, text", "model", [("D", "B"), ("C", "D"), ("C", "B")],
     "B is another model family and provider, thinking disabled against low reasoning effort; "
     "C and D differ only in the model"),
    ("Output protocol", "output protocol", [("freeform_B", "B")],
     "the free form prompt also asks for a written walk through of the fields and the partner table"),
    ("Model, free form", "model", [("freeform_light", "freeform_B")],
     "provider, max_tokens 16000 against 3000, model generation (Qwen3 against Qwen3.5), extra fields"),
    ("Output constraint", "output constraint", [("multimodal_open", "multimodal_strict")],
     "max_tokens 3000 against 6000; the open prompt asks for a row by row walk through"),
    ("Context selection, text", "context selection", [("targeted_text", "C")],
     "input source (Docling Markdown against page text, parsed tables and OCR), prompt, identifier hints, "
     "page picking call, reconciliation and identifier filling after the answer"),
    ("Context selection, with images", "context selection",
     [("targeted_multimodal", "multimodal_combined_qwen_vl")],
     "protocol (unconstrained against schema enforced), max_tokens, prompt, batching and merge, "
     "reconciliation, OCR"),
    ("Model, combined", "model", [("multimodal_combined_llama4_maverick", "multimodal_combined_qwen_vl")],
     "provider and context window"),
]


def _mean(values: Iterable[float | None]) -> float | None:
    vals = [v for v in values if v is not None]
    return mean(vals) if vals else None


def run_row(run: dict[str, Any]) -> dict[str, Any]:
    """One row of the per run results file."""
    s = run["score"]
    p, e, v = s["partners"], s["errors"], s["validity"]
    outcomes = [r["outcome"] for r in s["scalars"]]
    sc = p["sum_check"] or {}
    tokens = run["tokens"]
    return {
        "configuration": run["configuration"], "document": run["document"], "repetition": run["repetition"],
        "run_file": run["run_file"], "run_status": run["status"],
        "first_attempt_valid": v["first_attempt"], "after_repair_valid": v["after_repair"],
        "field_accuracy": s["scalar_accuracy"], "fields_correct": outcomes.count("correct"),
        "field_misses": outcomes.count("miss"), "field_wrong_values": outcomes.count("wrong"),
        "field_unsupported_values": outcomes.count("unsupported"),
        "gold_partners": p["gold_count"], "partners_found": p["matched_count"], "partner_recall": p["recall"],
        "amount_accuracy": p["amount_accuracy"], "extracted_partners": p["extracted_count"],
        "supported_extras": p["classes"]["supported_extra"], "unsupported_extras": p["classes"]["unsupported_extra"],
        "duplicates": p["classes"]["duplicate"], "unsure_names": len(p["unsure"]),
        "extra_partner_weight": p["extra_weight"],
        "over_inclusion_rate": p["extra_weight"] / p["extracted_count"] if p["extracted_count"] else None,
        "sum_of_matched_equals_total": sc.get("matched_sum_equals_total"),
        "supported_extras_make_sum_deviate": sc.get("supported_extras_make_sum_deviate"),
        "errors_total": e["total"], "errors_certain": e["certain"], "errors_from_unsure_names": e["from_unsure_names"],
        "fully_correct": s["fully_correct"], "contains_unsure": s["contains_unsure"],
        "tokens_input": tokens.get("input"), "tokens_output": tokens.get("output"),
        "tokens_reasoning": tokens.get("reasoning"), "tokens_cached": tokens.get("cached"),
        "tokens_image": tokens.get("image"),
        "cost_usd": run["cost_usd"], "end_to_end_seconds": run["end_to_end_seconds"],
        "docling_conversion_seconds": run["docling_conversion_seconds"],
    }


def _metric(row: dict[str, Any], name: str) -> float | None:
    return row[name]


def per_document(rows: list[dict[str, Any]]) -> dict[tuple[str, str], dict[str, float | None]]:
    """(configuration, document) -> mean of each metric over its final runs."""
    groups: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for r in rows:
        groups[(r["configuration"], r["document"])].append(r)
    return {k: {m: _mean(_metric(r, m) for r in g) for m in METRICS} for k, g in groups.items()}


def _comparable(value: Any) -> Any:
    if isinstance(value, Invalid):
        return ("invalid", repr(value.raw))
    return value


def consistency(runs: list[dict[str, Any]]) -> dict[tuple[str, str], float]:
    """(configuration, document) -> share of the ten items equal in all its final runs."""
    groups: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for run in runs:
        groups[(run["configuration"], run["document"])].append(run)
    result = {}
    for key, group in groups.items():
        if any(not r["score"]["validity"]["after_repair"] for r in group):
            result[key] = 0.0
            continue
        same = 0
        for field in SCALAR_FIELDS:
            section, name = field.split(".")
            values = {repr(_comparable(NORMALISERS[field]((r["final"].get(section) or {}).get(name))))
                      for r in group}
            same += len(values) == 1
        lists = set()
        for r in group:
            entries = sorted((normalise_name(p.get("partner_name") or ""),
                              repr(_comparable(normalise_amount(p.get("requested_cents")))))
                             for p in r["final"].get("partners") or [])
            lists.add(tuple(entries))
        same += len(lists) == 1
        result[key] = same / (len(SCALAR_FIELDS) + 1)
    return result


def configuration_summary(runs: list[dict[str, Any]], rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    docs = per_document(rows)
    cons = consistency(runs)
    out = []
    for config in sorted({r["configuration"] for r in rows}):
        mine = [r for r in rows if r["configuration"] == config]
        doc_values = {d: v for (c, d), v in docs.items() if c == config}
        row: dict[str, Any] = {"configuration": config, "documents": len(doc_values), "final_runs": len(mine),
                               "runs_not_ok": sum(1 for r in mine if r["run_status"] != "ok")}
        for m in METRICS:
            values = [v[m] for v in doc_values.values() if v[m] is not None]
            row[f"{m}_mean"] = mean(values) if values else None
            row[f"{m}_min"] = min(values) if values else None
            row[f"{m}_max"] = max(values) if values else None
        cvals = [v for (c, _), v in cons.items() if c == config]
        row.update({"consistency_mean": mean(cvals), "consistency_min": min(cvals), "consistency_max": max(cvals)})
        firsts = [r["first_attempt_valid"] for r in mine if r["first_attempt_valid"] is not None]
        row["first_attempt_valid_share"] = sum(firsts) / len(firsts) if firsts else None
        row["after_repair_valid_share"] = sum(r["after_repair_valid"] for r in mine) / len(mine)
        extracted = sum(r["extracted_partners"] for r in mine)
        row["over_inclusion_rate"] = sum(r["extra_partner_weight"] for r in mine) / extracted if extracted else None
        row["cost_per_document_usd"] = mean(r["cost_usd"] for r in mine)
        fully = mean(r["fully_correct"] for r in mine)
        row["fully_correct_share"] = fully
        row["cost_of_pass_usd"] = row["cost_per_document_usd"] / fully if fully else "not defined"
        row["total_cost_usd"] = sum(r["cost_usd"] for r in mine)
        row["runs_with_unsure_names"] = sum(1 for r in mine if r["contains_unsure"])
        row["unsure_names"] = sum(r["unsure_names"] for r in mine)
        out.append(row)
    return out


def contrast_table(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Per document differences of the per document means, then their mean over documents."""
    docs = per_document(rows)
    documents = sorted({d for _, d in docs})
    out = []
    for name, factor, pairs, others in CONTRASTS:
        for varied, reference in pairs:
            diffs: dict[str, list[float]] = defaultdict(list)
            for d in documents:
                a, b = docs.get((varied, d)), docs.get((reference, d))
                if a is None or b is None:
                    continue
                row = {"contrast": name, "intended_factor": factor, "difference": f"{varied} minus {reference}",
                       "document": d}
                for m in CONTRAST_METRICS:
                    value = a[m] - b[m] if a[m] is not None and b[m] is not None else None
                    row[m] = value
                    if value is not None:
                        diffs[m].append(value)
                row["other_differences"] = others
                out.append(row)
            mean_row = {"contrast": name, "intended_factor": factor, "difference": f"{varied} minus {reference}",
                        "document": "mean over documents"}
            mean_row.update({m: mean(diffs[m]) if diffs[m] else None for m in CONTRAST_METRICS})
            mean_row["other_differences"] = others
            out.append(mean_row)
    return out


def error_log(runs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Every error of every final run, with its weight (0.5 for errors from unsure names)."""
    out = []
    for run in runs:
        s = run["score"]
        base = {"configuration": run["configuration"], "document": run["document"],
                "repetition": run["repetition"], "run_file": run["run_file"]}
        for r in s["scalars"]:
            if r["outcome"] != "correct":
                out.append({**base, "item": "field", "field": r["field"], "error_class": r["outcome"],
                            "weight": 1.0, "unsure": False, "partner_name": "",
                            "gold_value": r["gold"], "extracted_value": r["extracted"]})
        p = s["partners"]
        for g in p["gold_status"]:
            if g["found"] < 1:
                out.append({**base, "item": "partner", "field": "partners", "error_class": "miss",
                            "weight": 1 - g["found"], "unsure": g["unsure"], "partner_name": g["partner_name"],
                            "gold_value": g["partner_name"], "extracted_value": None})
        gold_amounts = {g["partner_name"]: g["requested_cents"] for g in p["gold_status"]}
        for e in p["entries"]:
            if e["amount_weight"] and e["amount_outcome"] != "correct":
                out.append({**base, "item": "partner amount", "field": "partners.requested_cents",
                            "error_class": e["amount_outcome"], "weight": e["amount_weight"],
                            "unsure": e["unsure_case"] is not None, "partner_name": e["gold_partner"],
                            "gold_value": gold_amounts.get(e["gold_partner"]), "extracted_value": e["requested_cents"]})
            for cls in ("duplicate", "unsupported_extra"):
                if e["weights"][cls]:
                    out.append({**base, "item": "extra partner", "field": "partners", "error_class": cls,
                                "weight": e["weights"][cls], "unsure": e["unsure_case"] is not None,
                                "partner_name": e["partner_name"], "gold_value": None,
                                "extracted_value": e["partner_name"]})
    return out


def extras_log(runs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Every extracted partner that matches no gold partner with certainty."""
    out = []
    for run in runs:
        for e in run["score"]["partners"]["entries"]:
            if e["class"] == "matched":
                continue
            out.append({"configuration": run["configuration"], "document": run["document"],
                        "repetition": run["repetition"], "run_file": run["run_file"],
                        "partner_name": e["partner_name"], "class": e["class"], "unsure_case": e["unsure_case"] or "",
                        "decided": e["decided"], "weight_matched": e["weights"]["matched"],
                        "weight_duplicate": e["weights"]["duplicate"],
                        "weight_supported_extra": e["weights"]["supported_extra"],
                        "weight_unsupported_extra": e["weights"]["unsupported_extra"],
                        "extra_weight": e["extra_weight"], "related_gold_partner": e["gold_partner"] or "",
                        "reason": e["reason"], "requested_cents": e["requested_cents"]})
    return out
