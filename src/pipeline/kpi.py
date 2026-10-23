"""Read-only KPI queries for the Impact Scorecard.

Every function here reads one of the v_kpi_* views already defined in sql/schema.sql
(the eleven KPIs plus v_partner_status) and returns plain dicts/tuples - no ORM, no
SQL recomputed here that the views do not already do. Used by the webapp's Dashboard
and Scorecard pages (webapp/main.py), never by the extraction or review steps.
"""

from __future__ import annotations

from typing import Any


def success_rate_count(conn) -> tuple[int, int, float | None]:
    row = conn.execute(
        "SELECT approved_count, decided_count, success_rate FROM v_kpi_01_success_rate_count"
    ).fetchone()
    return (row["approved_count"] or 0, row["decided_count"] or 0, row["success_rate"])


def success_rate_eur(conn) -> tuple[float, float, float | None]:
    row = conn.execute(
        "SELECT granted_eur, requested_eur, success_rate_eur FROM v_kpi_02_success_rate_eur"
    ).fetchone()
    return (row["granted_eur"] or 0.0, row["requested_eur"] or 0.0, row["success_rate_eur"])


def partner_funding_total(conn) -> float:
    row = conn.execute("SELECT total_partner_funding_eur FROM v_kpi_03_total_partner_funding").fetchone()
    return row["total_partner_funding_eur"] or 0.0


def funding_by_scope(conn) -> list[dict[str, Any]]:
    rows = conn.execute(
        "SELECT funding_source, requested_eur, granted_eur FROM v_kpi_04_applied_vs_granted_by_source"
    ).fetchall()
    return [
        {"funding_source": r["funding_source"], "requested_eur": r["requested_eur"] or 0.0,
         "granted_eur": r["granted_eur"] or 0.0}
        for r in rows
    ]


def top_partners(conn, limit: int = 5) -> list[dict[str, Any]]:
    """The top `limit` partners by funding enabled, ties on the cutoff value all included."""
    rows = conn.execute(
        "SELECT partner_name, partner_category, funding_enabled_eur, project_count "
        "FROM v_kpi_05_top_partners"
    ).fetchall()
    ranked = []
    rank = 0
    previous_value = object()
    for r in rows:
        value = r["funding_enabled_eur"] or 0.0
        if value != previous_value:
            rank += 1
            previous_value = value
        ranked.append({
            "partner_name": r["partner_name"], "partner_category": r["partner_category"],
            "granted_eur": value, "project_count": r["project_count"], "rank": rank,
        })
    return [r for r in ranked if r["rank"] <= limit]


def network_by_category(conn) -> list[dict[str, Any]]:
    rows = conn.execute(
        "SELECT partner_category, partner_count, share FROM v_kpi_06_network_by_category"
    ).fetchall()
    return [
        {"category": r["partner_category"], "count": r["partner_count"], "share": r["share"] or 0.0}
        for r in rows
    ]


def portfolio_impact_totals(conn) -> tuple[int, int, int]:
    building_on_previous = conn.execute(
        "SELECT projects_building_on_previous FROM v_kpi_08_builds_on_previous"
    ).fetchone()["projects_building_on_previous"] or 0
    demo = conn.execute(
        "SELECT total_demo_activities, projects_with_demo FROM v_kpi_09_10_demo_activities"
    ).fetchone()
    return (building_on_previous, demo["total_demo_activities"] or 0, demo["projects_with_demo"] or 0)


def trl_mcrl_cloud(conn) -> list[dict[str, Any]]:
    """Approved projects grouped by (TRL target, MCRL target) - a snapshot of where the
    portfolio is heading, not where it started. Rows with either target still null are
    excluded, since they cannot be placed on the chart."""
    rows = conn.execute(
        """
        SELECT trl_target AS trl, mcrl_target AS mcrl, COUNT(*) AS project_count
        FROM v_kpi_07_trl_mcrl
        WHERE trl_target IS NOT NULL AND mcrl_target IS NOT NULL
        GROUP BY trl_target, mcrl_target
        """
    ).fetchall()
    return [dict(r) for r in rows]


def sdg_project_counts(conn) -> list[dict[str, Any]]:
    rows = conn.execute(
        "SELECT sdg_number, sdg_title, project_count FROM v_kpi_11_sdg_by_goal "
        "ORDER BY project_count DESC, sdg_number ASC"
    ).fetchall()
    return [dict(r) for r in rows]


def outreach(conn, kind: str) -> dict[str, Any]:
    """Events or communications: totals, per type totals and monthly counts per type."""
    types = [dict(r) for r in conn.execute(
        "SELECT activity_type, total_activities, total_reach FROM v_kpi_12_outreach_by_type "
        "WHERE activity_kind = ? ORDER BY total_reach DESC", (kind,))]
    monthly = [dict(r) for r in conn.execute(
        "SELECT activity_type, activity_month, activity_count FROM fact_outreach "
        "WHERE activity_kind = ? ORDER BY activity_month", (kind,))]
    is_mock = bool(conn.execute(
        "SELECT COALESCE(MAX(is_mock), 0) FROM fact_outreach WHERE activity_kind = ?", (kind,)).fetchone()[0])
    return {
        "types": types, "monthly": monthly, "is_mock": is_mock,
        "months": sorted({m["activity_month"] for m in monthly}),
        "total_activities": sum(t["total_activities"] for t in types),
        "total_reach": sum(t["total_reach"] for t in types),
    }


def eur_compact(value: float | None) -> str:
    v = value or 0.0
    av = abs(v)
    if av >= 1_000_000:
        return f"EUR {v / 1_000_000:.1f}M"
    if av >= 1_000:
        return f"EUR {v / 1_000:.0f}K"
    return f"EUR {v:,.0f}"
