"""Files of a scored batch beyond the CSV tables (protocol section 7): the frontier plot, the
spot check sample, the review list with its decisions template, the readable report, and the
shareable copies with neutral document codes.

Everything written here except the shareable folder contains real names and values and stays
in the private results folder, which git never tracks.
"""

from __future__ import annotations

import csv
import json
import random
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

SPOT_CHECK_PER_CONFIGURATION = 2

# Colours from the reference palette of the dataviz guidance: one accent for the frontier,
# a neutral grey for the rest; frontier points are also filled and labelled, never colour alone.
_SURFACE, _INK, _INK_2, _ACCENT, _NEUTRAL, _GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#2a78d6", "#8d8c87", "#e4e3df"


def write_csv(path: Path, rows: list[dict[str, Any]], columns: list[str] | None = None) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    columns = columns or (list(rows[0]) if rows else [])
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({k: _cell(row.get(k)) for k in columns})
    return path


def _cell(value: Any) -> Any:
    if value is None:
        return ""
    if isinstance(value, float):
        return f"{value:.6g}"
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    return value


# --------------------------------------------------------------------------- frontier

def frontier(summary: list[dict[str, Any]]) -> set[str]:
    """Configurations that no other configuration beats on both accuracy and cost: none has
    at least the accuracy at no more cost, with one of the two strictly better."""
    points = {r["configuration"]: (r["field_accuracy_mean"], r["cost_per_document_usd"]) for r in summary}
    best = set()
    for name, (acc, cost) in points.items():
        beaten = any(a >= acc and c <= cost and (a > acc or c < cost)
                     for other, (a, c) in points.items() if other != name)
        if not beaten:
            best.add(name)
    return best


def frontier_plot(summary: list[dict[str, Any]], path: Path, title: str) -> Path:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    best = frontier(summary)
    fig, ax = plt.subplots(figsize=(9, 6), dpi=150, facecolor=_SURFACE)
    ax.set_facecolor(_SURFACE)
    for r in sorted(summary, key=lambda r: r["configuration"]):
        x, y = r["cost_per_document_usd"], r["field_accuracy_mean"]
        on = r["configuration"] in best
        colour = _ACCENT if on else _NEUTRAL
        ax.errorbar(x, y, yerr=[[y - r["field_accuracy_min"]], [r["field_accuracy_max"] - y]],
                    xerr=[[x - r["cost_usd_min"]], [r["cost_usd_max"] - x]],
                    fmt="none", ecolor=colour, elinewidth=1, alpha=0.45, capsize=0, zorder=1)
        ax.scatter([x], [y], s=64, zorder=3, facecolor=colour if on else _SURFACE, edgecolor=colour,
                   linewidth=2)
        ax.annotate(r["configuration"] + (" (frontier)" if on else ""), (x, y), xytext=(7, 5),
                    textcoords="offset points", fontsize=8, color=_INK if on else _INK_2, zorder=4)
    ax.set_xscale("log")
    ax.set_xlabel("Mean cost per document, US dollars (logarithmic scale)", color=_INK_2)
    ax.set_ylabel("Field accuracy, mean over the ten documents", color=_INK_2)
    ax.set_title(title, color=_INK, fontsize=11, loc="left")
    ax.grid(True, color=_GRID, linewidth=0.6)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(_GRID)
    ax.tick_params(colors=_INK_2, labelsize=8)
    fig.text(0.01, 0.01, "Bars: minimum to maximum of the per document means. Filled points: no other "
             "configuration is at least as accurate at no higher cost (descriptive).", fontsize=7, color=_INK_2)
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, facecolor=_SURFACE)
    plt.close(fig)
    return path


# --------------------------------------------------------------------------- spot check

def spot_check_sample(runs: list[dict[str, Any]], seed: str) -> list[dict[str, Any]]:
    """Two final runs per configuration, drawn with a fixed seed from the runs sorted by
    document and repetition: random.Random(seed).sample(runs, 2)."""
    rng = random.Random(seed)
    chosen = []
    for config in sorted({r["configuration"] for r in runs}):
        mine = sorted((r for r in runs if r["configuration"] == config), key=lambda r: (r["document"], r["repetition"]))
        chosen += rng.sample(mine, min(SPOT_CHECK_PER_CONFIGURATION, len(mine)))
    return chosen


def write_spot_check(path: Path, sample: list[dict[str, Any]], gold: dict[str, dict], seed: str) -> Path:
    lines = ["# Spot check sample", "",
             f"Two final runs per configuration, drawn with the seed `{seed}`. For each run: the scored fields "
             "beside the gold values, the partner entries with their classes, and the scores. Private file: it "
             "contains real names and values.", ""]
    for run in sample:
        s = run["score"]
        lines += [f"## {run['configuration']}, {run['document']}, repetition {run['repetition']}", "",
                  f"Run file `{run['run_file']}`; status {run['status']}; valid at the first attempt "
                  f"{s['validity']['first_attempt']}, after repair {s['validity']['after_repair']}; "
                  f"fully correct {s['fully_correct']}; errors {s['errors']['total']:g} "
                  f"(certain {s['errors']['certain']:g}).", "",
                  "| Field | Gold | Extracted | Outcome |", "|---|---|---|---|"]
        for r in s["scalars"]:
            lines.append(f"| {r['field']} | {_md(r['gold'])} | {_md(r['extracted'])} | {r['outcome']} |")
        lines += ["", "| Gold partner | Gold amount (cents) | Found |", "|---|---|---|"]
        for g in s["partners"]["gold_status"]:
            lines.append(f"| {_md(g['partner_name'])} | {_md(g['requested_cents'])} | {g['found']:g} |")
        lines += ["", "| Extracted partner | Amount (cents) | Class | Unsure case | Amount outcome | Reason |",
                  "|---|---|---|---|---|---|"]
        for e in s["partners"]["entries"]:
            lines.append(f"| {_md(e['partner_name'])} | {_md(e['requested_cents'])} | {e['class']} | "
                         f"{e['unsure_case'] or ''} | {e['amount_outcome'] or ''} | {_md(e['reason'])} |")
        lines += ["", "<details><summary>Final record and gold set (JSON)</summary>", "", "```json",
                  json.dumps(run["final"], indent=2, ensure_ascii=False), "```", "", "```json",
                  json.dumps(gold[run["document"]], indent=2, ensure_ascii=False), "```", "", "</details>", ""]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def _md(value: Any) -> str:
    if value is None:
        return "null"
    return str(value).replace("|", "\\|").replace("\n", " ")


# --------------------------------------------------------------------------- review list

def review_rows(runs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{"document": r["document"], "configuration": r["configuration"], "repetition": r["repetition"],
             "run_file": r["run_file"], "partner_name": u["partner_name"], "case": u["case"],
             "related_gold_partner": u["related_gold_partner"] or "", "requested_cents": u["requested_cents"],
             "reason": u["reason"]}
            for r in runs for u in r["score"]["partners"]["unsure"]]


def decisions_template(review: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Each distinct document and name once, with an empty decision to fill in."""
    from src.evaluation.partners import normalise_name
    groups: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for r in review:
        groups[(r["document"], normalise_name(r["partner_name"]))].append(r)
    out = []
    for (doc, _), items in sorted(groups.items()):
        out.append({"document": doc, "partner_name": items[0]["partner_name"],
                    "cases": ", ".join(sorted({i["case"] for i in items})),
                    "related_gold_partners": ", ".join(sorted({i["related_gold_partner"] for i in items} - {""})),
                    "runs": len(items), "decision": ""})
    return out


# --------------------------------------------------------------------------- shareable versions

def document_codes(documents: list[str]) -> dict[str, str]:
    """D01 to D10 in alphabetical order of the document names, case folded."""
    return {d: f"D{i:02d}" for i, d in enumerate(sorted(documents, key=str.casefold), start=1)}


SHAREABLE_COLUMNS = {
    "error_log": ["configuration", "document", "repetition", "item", "field", "error_class", "weight", "unsure"],
    "extras_log": ["configuration", "document", "repetition", "class", "unsure_case", "decided", "weight_matched",
                   "weight_duplicate", "weight_supported_extra", "weight_unsupported_extra", "extra_weight"],
}


def coded(rows: list[dict[str, Any]], codes: dict[str, str]) -> list[dict[str, Any]]:
    return [{**r, "document": codes.get(r["document"], r["document"])} for r in rows]


# --------------------------------------------------------------------------- readable report

def _pct(x: Any) -> str:
    return "n/a" if x is None or isinstance(x, str) else f"{100 * x:.1f} %"


def _usd(x: Any) -> str:
    return x if isinstance(x, str) else f"{x:.4f}"


def write_report(path: Path, *, overview: dict[str, Any], summary: list[dict], contrasts: list[dict],
                 errors: list[dict], review: list[dict], frontier_names: set[str], plot_name: str) -> Path:
    o = overview
    L = ["# Evaluation report", "",
         f"Batch `{o['batch_id']}`. Private report: it contains real document names, partner names and values.", "",
         "## 1. Batch overview", "",
         f"1. Code that produced the runs: commit `{o['run_commit']}`; scored with the scorer at commit "
         f"`{o['scorer_commit']}`{' (with uncommitted changes)' if o['scorer_dirty'] else ''} on {o['scored_utc']}.",
         f"2. Runs from {o['first_run_utc']} to {o['last_run_utc']} (UTC).",
         f"3. {o['final_runs']} final runs: {o['configurations']} configurations, {o['documents']} documents, "
         f"{o['repetitions']} repetitions; {o['runs_not_ok']} runs ended without a final record.",
         f"4. Total cost of the completed final runs USD {o['total_cost_usd']:.2f}; total end to end time "
         f"{o['total_end_to_end_hours']:.1f} hours.",
         f"5. Author's decisions applied: {o['decisions_applied']}.", "",
         "## 2. Reading notes", "",
         "1. Times are end to end, from PDF to final record. For the five text configurations (B, C, D, "
         "freeform_B, freeform_light) they include the Docling conversion of the document, run on the author's "
         "laptop processor; see `DOCLING_SPEED.md`.",
         "2. The six runs of targeted_text and targeted_multimodal on SP03B ended without a final record and are "
         "counted as failures: every field and every gold partner missed. They are left out of every time and "
         "cost figure.",
         "3. Six documents (SP01, SP02, SP03A, SP03B, SP04, SP05) state partner amounts in thousands of euros, "
         "with the scale only in a table caption or header; amounts copied as written are "
         "a thousand times too small and are scored as wrong amounts.",
         "4. SP01: the Docling Markdown lost the partner table, which affects the five text configurations.",
         "5. Values marked unsure come from partner names the rules could not settle; they carry half scores.", "",
         "## 3. Configuration summary", "",
         "Means over the ten per document means (each the mean of three runs), with minimum and maximum.", "",
         "| Configuration | Field accuracy | Partner recall | Amount accuracy | Fully correct | Consistency | "
         "Over inclusion | Valid first attempt | Cost per document (USD) | Cost of pass (USD) | Mean seconds |",
         "|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in sorted(summary, key=lambda r: -(r["field_accuracy_mean"] or 0)):
        star = " (frontier)" if r["configuration"] in frontier_names else ""
        L.append(f"| {r['configuration']}{star} | {_pct(r['field_accuracy_mean'])} "
                 f"({_pct(r['field_accuracy_min'])} to {_pct(r['field_accuracy_max'])}) | "
                 f"{_pct(r['partner_recall_mean'])} | {_pct(r['amount_accuracy_mean'])} | "
                 f"{_pct(r['fully_correct_share'])} | {_pct(r['consistency_mean'])} | {_pct(r['over_inclusion_rate'])} | "
                 f"{_pct(r['first_attempt_valid_share'])} | {_usd(r['cost_per_document_usd'])} | "
                 f"{_usd(r['cost_of_pass_usd'])} | {r['end_to_end_seconds_mean']:.0f} |")
    L += ["", f"![Frontier plot]({plot_name})", "",
          "## 4. Errors per configuration", "",
          "Weighted error counts per field over all thirty final runs of each configuration (0.5 for errors "
          "from unsure names).", ""]
    fields = sorted({(e["field"], e["error_class"]) for e in errors})
    by_config: dict[str, Counter] = defaultdict(Counter)
    for e in errors:
        by_config[e["configuration"]][(e["field"], e["error_class"])] += e["weight"]
    for config in sorted(by_config):
        L += [f"### {config}", "", "| Field | Error class | Weighted count |", "|---|---|---|"]
        for key in fields:
            if by_config[config][key]:
                L.append(f"| {key[0]} | {key[1]} | {by_config[config][key]:g} |")
        L.append("")
    L += ["## 5. Wrong values per document", "",
          "For every document and field, each wrong or missing value beside the gold value, with the "
          "configurations and repetitions that produced it.", ""]
    per_doc: dict[str, dict] = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    for e in errors:
        key = (e["item"], e["field"], e["partner_name"] or "", _md(e["gold_value"]))
        per_doc[e["document"]][key][(e["error_class"], _md(e["extracted_value"]))].append(
            f"{e['configuration']} {e['repetition']}" + (" (unsure)" if e["unsure"] else ""))
    for doc in sorted(per_doc, key=str.casefold):
        L += [f"### {doc}", "", "| Item | Field | Partner | Gold value | Error | Extracted value | Runs |",
              "|---|---|---|---|---|---|---|"]
        for (item, field, partner, gold_value), outcomes in sorted(per_doc[doc].items()):
            for (cls, extracted), who in sorted(outcomes.items()):
                L.append(f"| {item} | {field} | {_md(partner)} | {gold_value} | {cls} | {extracted} | "
                         f"{', '.join(sorted(who))} |")
        L.append("")
    L += ["## 6. Contrasts", "",
          "Mean over documents of the per document differences (varied configuration minus reference). "
          "Descriptive only; each contrast has other differences besides its intended factor.", "",
          "| Contrast | Difference | Field accuracy | Partner recall | Amount accuracy | Fully correct | "
          "Cost (USD) | Seconds | Other differences |", "|---|---|---|---|---|---|---|---|---|"]
    for c in contrasts:
        if c["document"] != "mean over documents":
            continue
        L.append(f"| {c['contrast']} | {c['difference']} | {_signed_pct(c['field_accuracy'])} | "
                 f"{_signed_pct(c['partner_recall'])} | {_signed_pct(c['amount_accuracy'])} | "
                 f"{_signed_pct(c['fully_correct'])} | {_signed(c['cost_usd'], '+.4f')} | "
                 f"{_signed(c['end_to_end_seconds'], '+.0f')} | "
                 f"{c['other_differences']} |")
    L += ["", "## 7. Unsure partner names", "",
          f"{len(review)} occurrences, scored with half values; the full list is `review_list.csv`, and "
          "`review_decisions_template.csv` lists each distinct document and name once for decisions.", "",
          "| Document | Partner name | Case | Related gold partner | Runs |", "|---|---|---|---|---|"]
    counts = Counter((r["document"], r["partner_name"], r["case"], r["related_gold_partner"]) for r in review)
    for (doc, name, case, related), n in sorted(counts.items()):
        L.append(f"| {doc} | {_md(name)} | {case} | {_md(related) if related else ''} | {n} |")
    path.write_text("\n".join(L) + "\n", encoding="utf-8")
    return path


def _signed(x: Any, spec: str) -> str:
    return "n/a" if x is None else format(x, spec)


def _signed_pct(x: Any) -> str:
    return "n/a" if x is None else f"{100 * x:+.1f} points"
