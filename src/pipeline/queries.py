"""Read-only queries against the analytical star schema.

Pure functions (connection in, plain dict/list out) shared by every front end that
needs to browse what has been saved: the Streamlit Dashboard page (app/pages/1_Dashboard.py)
and the FastAPI web app (webapp/). Kept here, not in either front end, so neither one
re-implements the same SQL.
"""

from __future__ import annotations

from typing import Any

REFERENCE_TABLES = ["dim_proposal", "dim_partner", "dim_sdg", "dim_funding_programme", "document"]


def fmt_cents(cents: int | None) -> str:
    return "not stated" if cents is None else f"EUR {cents / 100:,.2f}"


def fmt(value: Any) -> str:
    return "not stated" if value is None or value == "" else str(value)


def load_reference_counts(conn) -> dict[str, int]:
    return {t: conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0] for t in REFERENCE_TABLES}


def load_funding_programmes(conn) -> list[dict]:
    rows = conn.execute(
        "SELECT programme_id, programme_name, funding_source FROM dim_funding_programme ORDER BY programme_name"
    ).fetchall()
    return [dict(r) for r in rows]


def load_all_partners(conn) -> list[dict]:
    rows = conn.execute(
        """
        SELECT partner_id, partner_name, partner_category, is_clic
        FROM dim_partner
        ORDER BY partner_name
        """
    ).fetchall()
    return [dict(r) for r in rows]


def load_partner(conn, partner_id: int) -> dict | None:
    row = conn.execute(
        "SELECT partner_id, partner_name, partner_category, is_clic FROM dim_partner WHERE partner_id = ?",
        (partner_id,),
    ).fetchone()
    return dict(row) if row else None


def load_projects_for_partner(conn, partner_id: int) -> list[dict]:
    rows = conn.execute(
        """
        SELECT p.proposal_key, p.proposal_acronym, p.proposal_title, p.status,
               fp.requested_cents, fp.granted_cents
        FROM fact_participation fp
        JOIN dim_proposal p ON p.proposal_key = fp.proposal_key
        WHERE fp.partner_id = ?
        ORDER BY p.proposal_key DESC
        """,
        (partner_id,),
    ).fetchall()
    return [dict(r) for r in rows]


def load_proposals(conn) -> list[dict]:
    rows = conn.execute(
        """
        SELECT p.*, d.file_name, d.content_hash, d.page_count, d.storage_path,
               d.received_at AS document_received_at, d.status AS document_status,
               g.programme_name, g.funding_source,
               f.requested_total_cents, f.granted_total_cents,
               f.trl_start, f.trl_target, f.mcrl_start, f.mcrl_target,
               f.builds_on_previous, f.demo_activity_count
        FROM dim_proposal p
        LEFT JOIN document d ON d.document_id = p.document_id
        LEFT JOIN dim_funding_programme g ON g.programme_id = p.programme_id
        LEFT JOIN fact_proposal f ON f.proposal_key = p.proposal_key
        ORDER BY p.proposal_key
        """
    ).fetchall()
    return [dict(r) for r in rows]


def load_proposal(conn, proposal_key: int) -> dict | None:
    for p in load_proposals(conn):
        if p["proposal_key"] == proposal_key:
            return p
    return None


def load_partners_for(conn, proposal_key: int) -> list[dict]:
    rows = conn.execute(
        """
        SELECT pt.partner_id, pt.partner_name, pt.partner_category, pt.is_clic,
               fp.requested_cents, fp.granted_cents
        FROM fact_participation fp
        JOIN dim_partner pt ON pt.partner_id = fp.partner_id
        WHERE fp.proposal_key = ?
        ORDER BY pt.partner_name
        """,
        (proposal_key,),
    ).fetchall()
    return [dict(r) for r in rows]


def load_all_sdgs(conn) -> list[dict]:
    rows = conn.execute("SELECT sdg_number, sdg_title FROM dim_sdg ORDER BY sdg_number").fetchall()
    return [dict(r) for r in rows]


def load_sdgs_for(conn, proposal_key: int) -> list[dict]:
    rows = conn.execute(
        """
        SELECT s.sdg_number, s.sdg_title
        FROM fact_proposal_sdg ps
        JOIN dim_sdg s ON s.sdg_number = ps.sdg_number
        WHERE ps.proposal_key = ?
        ORDER BY s.sdg_number
        """,
        (proposal_key,),
    ).fetchall()
    return [dict(r) for r in rows]
