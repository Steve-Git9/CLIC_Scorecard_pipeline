from __future__ import annotations

from pathlib import Path

import pytest

from src.pipeline.config import Config
from src.pipeline.db import get_connection, init_db
from src.pipeline.load import DuplicateProposalError, load_extraction

SCHEMA_PATH = Path(__file__).resolve().parents[1] / "sql" / "schema.sql"


@pytest.fixture
def seeded_config(test_config: Config) -> Config:
    init_db(test_config, schema_path=SCHEMA_PATH)
    conn = get_connection(test_config)
    try:
        conn.execute(
            "INSERT INTO dim_partner (partner_name, partner_category, is_clic) VALUES (?, ?, 0)",
            ("Fictional University", "Research and Education"),
        )
        conn.execute(
            "INSERT INTO dim_partner (partner_name, partner_category, is_clic) VALUES (?, ?, 0)",
            ("XYZ", "SME"),
        )
        conn.execute("INSERT INTO dim_sdg (sdg_number, sdg_title) VALUES (7, 'Fictional Clean Energy')")
        conn.execute("INSERT INTO dim_sdg (sdg_number, sdg_title) VALUES (13, 'Fictional Climate Action')")
        conn.commit()
    finally:
        conn.close()
    return test_config


def _extraction(acronym: str = "FICT-1") -> dict:
    return {
        "proposal": {
            "proposal_acronym": acronym,
            "proposal_title": "A Fictional Proposal",
            "call_identifier": "FICT-CALL-01",
            "submission_date": "2026-01-15",
        },
        "proposal_facts": {
            "requested_total_cents": 100000,
            "trl_start": 3,
            "trl_target": 6,
            "mcrl_start": None,
            "mcrl_target": None,
        },
        "partners": [
            {"partner_name": "Fictional University", "requested_cents": 60000},
            {"partner_name": "Fictional Research Centre XYZ", "requested_cents": 40000},
        ],
    }


def test_load_extraction_inserts_proposal_facts_partners_and_sdgs(seeded_config: Config) -> None:
    sdg_result = {"sdgs": [{"number": 7, "name": "x"}, {"number": 13, "name": "y"}]}

    result = load_extraction(_extraction(), sdg_result, seeded_config)

    assert result["partners_inserted"] == 2
    assert result["sdgs_inserted"] == 2
    assert result["flagged_partners"] == []  # both partners match well above 80%

    conn = get_connection(seeded_config)
    try:
        proposal = conn.execute(
            "SELECT * FROM dim_proposal WHERE proposal_key = ?", (result["proposal_key"],)
        ).fetchone()
        facts = conn.execute(
            "SELECT * FROM fact_proposal WHERE proposal_key = ?", (result["proposal_key"],)
        ).fetchone()
        partners = conn.execute(
            """
            SELECT dp.partner_name, fp.requested_cents
            FROM fact_participation fp JOIN dim_partner dp ON dp.partner_id = fp.partner_id
            WHERE fp.proposal_key = ? ORDER BY dp.partner_name
            """,
            (result["proposal_key"],),
        ).fetchall()
        sdgs = conn.execute(
            "SELECT sdg_number FROM fact_proposal_sdg WHERE proposal_key = ? ORDER BY sdg_number",
            (result["proposal_key"],),
        ).fetchall()
    finally:
        conn.close()

    assert proposal["proposal_acronym"] == "FICT-1"
    assert proposal["status"] == "Pending"
    assert facts["requested_total_cents"] == 100000
    # "Fictional Research Centre XYZ" must resolve to the existing partner "XYZ".
    assert [dict(r) for r in partners] == [
        {"partner_name": "Fictional University", "requested_cents": 60000},
        {"partner_name": "XYZ", "requested_cents": 40000},
    ]
    assert [r["sdg_number"] for r in sdgs] == [7, 13]


def test_load_extraction_refuses_duplicate_acronym(seeded_config: Config) -> None:
    load_extraction(_extraction(), None, seeded_config)

    with pytest.raises(DuplicateProposalError):
        load_extraction(_extraction(), None, seeded_config)

    conn = get_connection(seeded_config)
    try:
        count = conn.execute("SELECT COUNT(*) FROM dim_proposal").fetchone()[0]
    finally:
        conn.close()
    assert count == 1


def test_load_extraction_flags_low_confidence_partner_but_still_links_it(seeded_config: Config) -> None:
    data = _extraction("FICT-2")
    data["partners"] = [{"partner_name": "Totally Unrelated Org Name", "requested_cents": 5000}]

    result = load_extraction(data, None, seeded_config)

    assert result["partners_inserted"] == 1
    assert len(result["flagged_partners"]) == 1
    assert "Totally Unrelated Org Name" in result["flagged_partners"][0]
