"""Tests for the batch result tables and files (Phase 4). FICTIONAL TEST DATA ONLY: the
fixtures come from test_scorer.py and describe no real CLIC project."""

from __future__ import annotations

import csv
from pathlib import Path

import pytest

from src.evaluation import batch_report as report
from src.evaluation import batch_tables as tables
from src.evaluation.score_batch import load_decisions
from tests.test_scorer import GOLD, MARKDOWN, final_from_gold, partner, score_run


def make_run(config: str, document: str, rep: int, final: dict | None, cost: float = 0.01,
             seconds: float = 10.0) -> dict:
    s = score_run(final, GOLD, None, "schema", MARKDOWN)
    return {"configuration": config, "document": document, "repetition": rep, "run_file": f"{config}/{document}_{rep}",
            "status": "ok" if final is not None else "failed", "cost_usd": cost, "end_to_end_seconds": seconds,
            "docling_conversion_seconds": None, "tokens": {"input": 100, "output": 10}, "final": final, "score": s}


def wrong_acronym() -> dict:
    return final_from_gold(proposal__proposal_acronym="WRONG")


@pytest.fixture
def runs() -> list[dict]:
    out = []
    for doc in ("FICTO", "ALPHA"):
        for rep in (1, 2, 3):
            out.append(make_run("B", doc, rep, final_from_gold(), cost=0.02))
            out.append(make_run("D", doc, rep, wrong_acronym() if rep == 1 else final_from_gold(), cost=0.01))
            out.append(make_run("C", doc, rep, None if doc == "ALPHA" else final_from_gold(), cost=0.005))
    return out


def test_run_row_counts_fields_and_partners(runs):
    row = tables.run_row(runs[1])          # D, FICTO, repetition 1: one wrong field
    assert row["field_accuracy"] == pytest.approx(8 / 9)
    assert row["field_wrong_values"] == 1
    assert row["partner_recall"] == 1.0
    assert row["fully_correct"] == 0.0


def test_failed_run_counts_every_field_and_partner_as_missed(runs):
    row = tables.run_row(next(r for r in runs if r["configuration"] == "C" and r["document"] == "ALPHA"))
    assert row["field_accuracy"] == 0.0 and row["field_misses"] == 9
    assert row["partner_recall"] == 0.0 and row["amount_accuracy"] is None
    assert row["errors_total"] == 9 + 3


def test_consistency_is_shared_items_over_ten(runs):
    cons = tables.consistency(runs)
    assert cons[("B", "FICTO")] == 1.0
    assert cons[("D", "FICTO")] == pytest.approx(9 / 10)    # the acronym differs in one run
    assert cons[("C", "ALPHA")] == 0.0                      # failed runs make every item differ


def test_consistency_sees_a_different_partner_list():
    a, b = final_from_gold(), final_from_gold()
    b["partners"] = b["partners"][:2]
    group = [make_run("B", "FICTO", 1, a), make_run("B", "FICTO", 2, a), make_run("B", "FICTO", 3, b)]
    assert tables.consistency(group)[("B", "FICTO")] == pytest.approx(9 / 10)


def test_summary_means_ranges_and_cost_of_pass(runs):
    rows = [tables.run_row(r) for r in runs]
    summary = {s["configuration"]: s for s in tables.configuration_summary(runs, rows)}
    d = summary["D"]
    assert d["field_accuracy_mean"] == pytest.approx((2 + 8 / 9) / 3)
    assert d["field_accuracy_min"] == d["field_accuracy_max"]           # same on both documents
    assert d["fully_correct_share"] == pytest.approx(4 / 6)
    assert d["cost_of_pass_usd"] == pytest.approx(0.01 / (4 / 6))
    c = summary["C"]
    assert c["runs_not_ok"] == 3 and c["field_accuracy_min"] == 0.0 and c["field_accuracy_max"] == 1.0
    assert c["after_repair_valid_share"] == 0.5


def test_failed_runs_count_in_accuracy_but_not_in_time_or_cost():
    group = [make_run("C", "FICTO", 1, final_from_gold(), cost=0.02, seconds=100.0),
             make_run("C", "ALPHA", 1, None, cost=0.001, seconds=2.0)]
    rows = [tables.run_row(r) for r in group]
    c = tables.configuration_summary(group, rows)[0]
    assert c["field_accuracy_mean"] == pytest.approx(0.5)               # the failure still counts as 0
    assert c["end_to_end_seconds_mean"] == pytest.approx(100.0)         # but not in time
    assert c["cost_usd_mean"] == pytest.approx(0.02)                    # nor in cost
    assert c["cost_per_document_usd"] == pytest.approx(0.02)
    assert c["total_cost_usd"] == pytest.approx(0.02)
    assert c["cost_of_pass_usd"] == pytest.approx(0.02 / 0.5)
    contrast_rows = rows + [tables.run_row(make_run("targeted_text", d, 1, final_from_gold(), seconds=10.0))
                            for d in ("FICTO", "ALPHA")]
    diffs = [r for r in tables.contrast_table(contrast_rows)
             if r["difference"] == "targeted_text minus C" and r["document"] != "mean over documents"]
    alpha = next(r for r in diffs if r["document"] == "ALPHA")
    assert alpha["end_to_end_seconds"] is None and alpha["field_accuracy"] == pytest.approx(1.0)


def test_cost_of_pass_is_not_defined_without_a_fully_correct_run():
    group = [make_run("B", "FICTO", i, wrong_acronym()) for i in (1, 2, 3)]
    rows = [tables.run_row(r) for r in group]
    assert tables.configuration_summary(group, rows)[0]["cost_of_pass_usd"] == "not defined"


def test_over_inclusion_rate_is_pooled_over_runs():
    extra = final_from_gold()
    extra["partners"].append(partner("Phantom Dynamics GmbH"))
    group = [make_run("B", "FICTO", 1, extra), make_run("B", "FICTO", 2, final_from_gold())]
    rows = [tables.run_row(r) for r in group]
    assert tables.configuration_summary(group, rows)[0]["over_inclusion_rate"] == pytest.approx(1 / 7)


def test_contrast_differences_are_varied_minus_reference(runs):
    rows = [tables.run_row(r) for r in runs]
    contrast = [c for c in tables.contrast_table(rows) if c["difference"] == "D minus B"]
    per_doc = [c for c in contrast if c["document"] != "mean over documents"]
    assert len(per_doc) == 2
    assert per_doc[0]["field_accuracy"] == pytest.approx(-(1 / 9) / 3)
    assert per_doc[0]["cost_usd"] == pytest.approx(-0.01)
    mean_row = next(c for c in contrast if c["document"] == "mean over documents")
    assert mean_row["field_accuracy"] == pytest.approx(-(1 / 9) / 3)


def test_error_and_extras_logs(runs):
    errors = tables.error_log(runs)
    d_wrong = [e for e in errors if e["configuration"] == "D"]
    assert [(e["field"], e["error_class"]) for e in d_wrong] == [("proposal.proposal_acronym", "wrong")] * 2
    extra = final_from_gold()
    extra["partners"].append(partner("Nowhere"))       # duplicate of a matched gold partner's name part
    log = tables.extras_log([make_run("B", "FICTO", 1, extra)])
    assert log[0]["class"] == "duplicate"


def test_frontier_keeps_configurations_no_other_beats():
    summary = [{"configuration": "cheap", "field_accuracy_mean": 0.5, "cost_per_document_usd": 0.001},
               {"configuration": "good", "field_accuracy_mean": 0.9, "cost_per_document_usd": 0.01},
               {"configuration": "worse", "field_accuracy_mean": 0.8, "cost_per_document_usd": 0.02}]
    assert report.frontier(summary) == {"cheap", "good"}


def test_spot_check_is_seeded(runs):
    a = report.spot_check_sample(runs, "spotcheck/x")
    b = report.spot_check_sample(runs, "spotcheck/x")
    assert [r["run_file"] for r in a] == [r["run_file"] for r in b]
    assert len(a) == 3 * 2


def test_document_codes_follow_alphabetical_order():
    assert report.document_codes(["b", "A", "c"]) == {"A": "D01", "b": "D02", "c": "D03"}


def test_decisions_file_is_read_and_checked(tmp_path: Path):
    path = tmp_path / "review_decisions.csv"
    path.write_text("document,partner_name,decision\nFICTO,Nowhere ,gold:Nowhere University\n"
                    "FICTO,Zorblax Holdings,supported_extra\nFICTO,Left Open,\n", encoding="utf-8")
    assert load_decisions(path) == {"FICTO": {"nowhere": ("gold", "Nowhere University"),
                                              "zorblax holdings": ("supported_extra",)}}
    path.write_text("document,partner_name,decision\nFICTO,Nowhere,maybe\n", encoding="utf-8")
    with pytest.raises(SystemExit):
        load_decisions(path)
    assert load_decisions(tmp_path / "absent.csv") == {}


def test_written_files_and_shareable_copies_hold_no_names(runs, tmp_path: Path):
    unsure = final_from_gold()
    unsure["partners"].append(partner("Zorblax Holdings"))
    all_runs = runs + [make_run("B", "FICTO", 4, unsure)]
    rows = [tables.run_row(r) for r in all_runs]
    summary = tables.configuration_summary(all_runs, rows)
    contrasts = tables.contrast_table(rows)
    errors, extras = tables.error_log(all_runs), tables.extras_log(all_runs)
    review = report.review_rows(all_runs)
    codes = report.document_codes(["FICTO", "ALPHA"])

    report.write_csv(tmp_path / "share" / "error_log.csv", report.coded(errors, codes),
                     report.SHAREABLE_COLUMNS["error_log"])
    report.write_csv(tmp_path / "share" / "extras_log.csv", report.coded(extras, codes),
                     report.SHAREABLE_COLUMNS["extras_log"])
    report.write_csv(tmp_path / "share" / "contrast_table.csv", report.coded(contrasts, codes))
    shared = " ".join(p.read_text(encoding="utf-8") for p in (tmp_path / "share").glob("*.csv"))
    for secret in ["FICTO", "ALPHA", "Zorblax", "Imaginary", "WRONG", "300000000"]:
        assert secret not in shared

    assert report.decisions_template(review)[0]["partner_name"] == "Zorblax Holdings"
    overview = {"batch_id": "batch_x", "run_commit": "abc1234", "scorer_commit": "def5678", "scorer_dirty": False,
                "scored_utc": "2099", "first_run_utc": "2099", "last_run_utc": "2099", "final_runs": len(all_runs),
                "configurations": 3, "documents": 2, "repetitions": 4, "runs_not_ok": 3, "total_cost_usd": 0.1,
                "total_end_to_end_hours": 0.1, "decisions_applied": "none"}
    text = report.write_report(tmp_path / "report.md", overview=overview, summary=summary, contrasts=contrasts,
                               errors=errors, review=review, frontier_names=report.frontier(summary),
                               plot_name="frontier_plot.png").read_text(encoding="utf-8")
    assert "Zorblax Holdings" in text and "WRONG" in text
    spot = report.write_spot_check(tmp_path / "spot.md", report.spot_check_sample(all_runs, "s"),
                                   {"FICTO": GOLD, "ALPHA": GOLD}, "s").read_text(encoding="utf-8")
    assert spot.count("## ") == 6
    with (tmp_path / "share" / "error_log.csv").open(encoding="utf-8") as f:
        assert next(csv.reader(f)) == report.SHAREABLE_COLUMNS["error_log"]


def test_frontier_plot_is_written(runs, tmp_path: Path):
    pytest.importorskip("matplotlib")
    rows = [tables.run_row(r) for r in runs]
    plot = report.frontier_plot(tables.configuration_summary(runs, rows), tmp_path / "frontier_plot.png", "fictional")
    assert plot.stat().st_size > 0
