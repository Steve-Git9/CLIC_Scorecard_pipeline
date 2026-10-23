from __future__ import annotations

from pathlib import Path

import pytest

from src.pipeline import kpi
from src.pipeline.config import Config
from src.pipeline.db import get_connection, init_db

SCHEMA_PATH = Path(__file__).resolve().parents[1] / "sql" / "schema.sql"


@pytest.fixture
def seeded_conn(test_config: Config):
    """Three fictional proposals (Approved, Rejected, Pending) exercising every KPI view."""
    init_db(test_config, schema_path=SCHEMA_PATH)
    conn = get_connection(test_config)

    conn.execute("INSERT INTO dim_funding_programme (programme_name, funding_source) VALUES ('Programme A', 'EU')")
    conn.execute("INSERT INTO dim_funding_programme (programme_name, funding_source) VALUES ('Programme B', 'National')")

    conn.execute("INSERT INTO dim_partner (partner_name, partner_category, is_clic) VALUES ('Alpha Ltd', 'SME', 0)")
    conn.execute(
        "INSERT INTO dim_partner (partner_name, partner_category, is_clic) VALUES "
        "('Beta University', 'Research and Education', 0)"
    )
    conn.execute(
        "INSERT INTO dim_partner (partner_name, partner_category, is_clic) VALUES ('Fictional CLIC', 'Other', 1)"
    )
    conn.execute("INSERT INTO dim_sdg (sdg_number, sdg_title) VALUES (7, 'Fictional Clean Energy')")
    conn.execute("INSERT INTO dim_sdg (sdg_number, sdg_title) VALUES (13, 'Fictional Climate Action')")

    def partner_id(name: str) -> int:
        return conn.execute("SELECT partner_id FROM dim_partner WHERE partner_name = ?", (name,)).fetchone()[0]

    def programme_id(name: str) -> int:
        return conn.execute(
            "SELECT programme_id FROM dim_funding_programme WHERE programme_name = ?", (name,)
        ).fetchone()[0]

    # P1: Approved, Programme A (EU).
    cur = conn.execute(
        """
        INSERT INTO dim_proposal
            (proposal_acronym, proposal_title, call_identifier, programme_id,
             submission_date, ingested_at, decision_date, status)
        VALUES ('FICT-APPROVED', 'Fictional Approved Proposal', 'CALL-1', ?,
                '2026-01-01', '2026-01-02T00:00:00Z', '2026-02-01', 'Approved')
        """,
        (programme_id("Programme A"),),
    )
    p1 = cur.lastrowid
    conn.execute(
        """
        INSERT INTO fact_proposal
            (proposal_key, requested_total_cents, granted_total_cents,
             trl_start, trl_target, mcrl_start, mcrl_target, builds_on_previous, demo_activity_count)
        VALUES (?, 100000, 80000, 3, 6, 2, 4, 1, 2)
        """,
        (p1,),
    )
    conn.execute(
        "INSERT INTO fact_participation (proposal_key, partner_id, requested_cents, granted_cents) VALUES (?, ?, 60000, 50000)",
        (p1, partner_id("Alpha Ltd")),
    )
    conn.execute(
        "INSERT INTO fact_participation (proposal_key, partner_id, requested_cents, granted_cents) VALUES (?, ?, 40000, 30000)",
        (p1, partner_id("Beta University")),
    )
    conn.execute("INSERT INTO fact_proposal_sdg (proposal_key, sdg_number) VALUES (?, 7)", (p1,))

    # P2: Rejected, Programme B (National).
    cur = conn.execute(
        """
        INSERT INTO dim_proposal
            (proposal_acronym, proposal_title, call_identifier, programme_id,
             submission_date, ingested_at, decision_date, status)
        VALUES ('FICT-REJECTED', 'Fictional Rejected Proposal', 'CALL-2', ?,
                '2026-01-01', '2026-01-02T00:00:00Z', '2026-02-01', 'Rejected')
        """,
        (programme_id("Programme B"),),
    )
    p2 = cur.lastrowid
    conn.execute(
        """
        INSERT INTO fact_proposal
            (proposal_key, requested_total_cents, granted_total_cents,
             trl_start, trl_target, mcrl_start, mcrl_target, builds_on_previous, demo_activity_count)
        VALUES (?, 50000, 0, 2, 5, 1, 3, 0, 0)
        """,
        (p2,),
    )
    conn.execute(
        "INSERT INTO fact_participation (proposal_key, partner_id, requested_cents, granted_cents) VALUES (?, ?, 50000, 0)",
        (p2, partner_id("Alpha Ltd")),
    )

    # P3: Pending, excluded from every decided/approved KPI.
    cur = conn.execute(
        """
        INSERT INTO dim_proposal
            (proposal_acronym, proposal_title, call_identifier, programme_id,
             submission_date, ingested_at, decision_date, status)
        VALUES ('FICT-PENDING', 'Fictional Pending Proposal', 'CALL-3', ?, '2026-01-01', '2026-01-02T00:00:00Z', NULL, 'Pending')
        """,
        (programme_id("Programme A"),),
    )
    p3 = cur.lastrowid
    conn.execute(
        "INSERT INTO fact_proposal (proposal_key, requested_total_cents, granted_total_cents) VALUES (?, 20000, 0)",
        (p3,),
    )
    conn.execute(
        "INSERT INTO fact_participation (proposal_key, partner_id, requested_cents, granted_cents) VALUES (?, ?, 20000, 0)",
        (p3, partner_id("Fictional CLIC")),
    )

    conn.commit()
    yield conn
    conn.close()


def test_success_rate_count(seeded_conn):
    approved, decided, rate = kpi.success_rate_count(seeded_conn)
    assert (approved, decided) == (1, 2)
    assert rate == pytest.approx(0.5)


def test_success_rate_eur(seeded_conn):
    granted, requested, rate = kpi.success_rate_eur(seeded_conn)
    assert granted == pytest.approx(800.0)
    assert requested == pytest.approx(1500.0)
    assert rate == pytest.approx(800.0 / 1500.0, rel=1e-3)


def test_partner_funding_total_excludes_clic_and_non_approved(seeded_conn):
    assert kpi.partner_funding_total(seeded_conn) == pytest.approx(800.0)


def test_funding_by_scope(seeded_conn):
    rows = {r["funding_source"]: r for r in kpi.funding_by_scope(seeded_conn)}
    assert rows["EU"]["requested_eur"] == pytest.approx(1000.0)
    assert rows["EU"]["granted_eur"] == pytest.approx(800.0)
    assert rows["National"]["requested_eur"] == pytest.approx(500.0)
    assert rows["National"]["granted_eur"] == pytest.approx(0.0)


def test_top_partners_only_counts_approved(seeded_conn):
    rows = kpi.top_partners(seeded_conn, limit=5)
    by_name = {r["partner_name"]: r for r in rows}
    assert by_name["Alpha Ltd"]["granted_eur"] == pytest.approx(500.0)
    assert by_name["Alpha Ltd"]["project_count"] == 1
    assert by_name["Beta University"]["granted_eur"] == pytest.approx(300.0)
    assert "Fictional CLIC" not in by_name


def test_network_by_category_excludes_clic(seeded_conn):
    rows = {r["category"]: r for r in kpi.network_by_category(seeded_conn)}
    assert rows["SME"]["count"] == 1
    assert rows["Research and Education"]["count"] == 1
    assert rows["SME"]["share"] == pytest.approx(0.5)
    assert "Other" not in rows  # Fictional CLIC is_clic=1, never Activated via an Approved row


def test_portfolio_impact_totals(seeded_conn):
    building_on_previous, total_demo, with_demo = kpi.portfolio_impact_totals(seeded_conn)
    assert (building_on_previous, total_demo, with_demo) == (1, 2, 1)


def test_trl_mcrl_cloud_only_approved(seeded_conn):
    rows = kpi.trl_mcrl_cloud(seeded_conn)
    assert rows == [{"trl": 6, "mcrl": 4, "project_count": 1}]


def test_sdg_project_counts(seeded_conn):
    rows = {r["sdg_number"]: r["project_count"] for r in kpi.sdg_project_counts(seeded_conn)}
    assert rows[7] == 1
    assert rows[13] == 0


def test_eur_compact():
    assert kpi.eur_compact(None) == "EUR 0"
    assert kpi.eur_compact(850.0) == "EUR 850"
    assert kpi.eur_compact(850_000.0) == "EUR 850K"
    assert kpi.eur_compact(1_200_000.0) == "EUR 1.2M"
