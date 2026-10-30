"""Load one reviewed extraction (clic_extract's JSON output) into the analytical star schema.

Per CLAUDE.md hard rule 6, no value reaches dim_proposal/fact_proposal/fact_participation
without having passed through extraction and review first - this module is that load step,
called only after a human has seen the extraction (the review step in app/viewer.py).

Never overwrites: if a project with the same acronym already exists, DuplicateProposalError
is raised and nothing is written. Partner names are matched against dim_partner by fuzzy
text match (rapidfuzz token_set_ratio) since partners are master data maintained outside
this pipeline - new partner names are never inserted here, only linked to existing ones.
"""

from __future__ import annotations

import argparse
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from rapidfuzz import fuzz, process

from src.pipeline.config import Config, configure_logging, load_config
from src.pipeline.db import get_connection

logger = logging.getLogger("pipeline.load")

PARTNER_MATCH_THRESHOLD = 80.0


class DuplicateProposalError(Exception):
    """Raised when a proposal with the same acronym already exists in dim_proposal."""


def find_duplicate_proposal(conn, acronym: str | None) -> dict[str, Any] | None:
    """An existing dim_proposal row with the exact same acronym (normalised), if any."""
    if not acronym:
        return None
    norm = " ".join(acronym.split()).casefold()
    for row in conn.execute("SELECT proposal_key, proposal_acronym, call_identifier, status FROM dim_proposal"):
        if " ".join((row["proposal_acronym"] or "").split()).casefold() == norm:
            return dict(row)
    return None


def match_partner_name(name: str, db_names: list[str], threshold: float = PARTNER_MATCH_THRESHOLD) -> dict[str, Any]:
    """Best fuzzy match for `name` among the existing partner master data.

    Uses token_set_ratio, which handles a short official name being a subset of
    words inside a longer, decorated one (e.g. "VTT" inside "Technical Research
    Centre of Finland VTT").
    """
    if not name or not db_names:
        return {"matched": None, "score": 0.0, "flagged": True}
    match, score, _ = process.extractOne(name, db_names, scorer=fuzz.token_set_ratio)
    return {"matched": match, "score": score, "flagged": score < threshold}


def resolve_programme(conn, programme_name: str | None, funding_source: str | None) -> int | None:
    """Get-or-create the dim_funding_programme row for `programme_name`.

    Programmes are not pre-seeded master data like partners (no catalogue exists to
    match against), so the first proposal naming a programme creates its row; every
    later proposal reusing that name reuses the same row, keeping its original
    funding_source rather than whatever is submitted alongside it this time.
    """
    if not programme_name:
        return None
    row = conn.execute(
        "SELECT programme_id FROM dim_funding_programme WHERE programme_name = ?", (programme_name,)
    ).fetchone()
    if row:
        return row[0]
    cursor = conn.execute(
        "INSERT INTO dim_funding_programme (programme_name, funding_source) VALUES (?, ?)",
        (programme_name, funding_source),
    )
    return cursor.lastrowid


def load_extraction(data: dict[str, Any], sdg_result: dict[str, Any] | None, config: Config) -> dict[str, Any]:
    """Insert one extraction into the star schema. Raises DuplicateProposalError instead
    of overwriting if a project with the same acronym already exists.

    Returns {"proposal_key", "partners_inserted", "flagged_partners", "sdgs_inserted"}.
    """
    conn = get_connection(config)
    try:
        proposal = data.get("proposal", {})
        facts = data.get("proposal_facts", {})
        partners = data.get("partners", [])

        duplicate = find_duplicate_proposal(conn, proposal.get("proposal_acronym"))
        if duplicate:
            raise DuplicateProposalError(
                f"'{duplicate['proposal_acronym']}' already exists (proposal_key={duplicate['proposal_key']})"
            )

        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        programme_id = resolve_programme(conn, proposal.get("programme_name"), proposal.get("funding_source"))
        cursor = conn.execute(
            """
            INSERT INTO dim_proposal
                (document_id, proposal_acronym, proposal_title, call_identifier,
                 programme_id, submission_date, ingested_at, decision_date, status)
            VALUES (NULL, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                proposal.get("proposal_acronym"),
                proposal.get("proposal_title"),
                proposal.get("call_identifier"),
                programme_id,
                proposal.get("submission_date"),
                now,
                proposal.get("decision_date"),
                proposal.get("status") or "Pending",
            ),
        )
        proposal_key = cursor.lastrowid

        conn.execute(
            """
            INSERT INTO fact_proposal
                (proposal_key, requested_total_cents, granted_total_cents,
                 trl_start, trl_target, mcrl_start, mcrl_target,
                 builds_on_previous, demo_activity_count)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                proposal_key,
                facts.get("requested_total_cents") or 0,
                facts.get("granted_total_cents") or 0,
                facts.get("trl_start"), facts.get("trl_target"),
                facts.get("mcrl_start"), facts.get("mcrl_target"),
                facts.get("builds_on_previous"),
                facts.get("demo_activity_count"),
            ),
        )

        db_names = [r[0] for r in conn.execute("SELECT partner_name FROM dim_partner")]
        flagged_partners: list[str] = []
        partners_inserted = 0
        for p in partners:
            name = p.get("partner_name") or ""
            m = match_partner_name(name, db_names)
            if m["matched"] is None:
                flagged_partners.append(f"{name} (no partner master data to match against)")
                continue
            if m["flagged"]:
                flagged_partners.append(f"{name} -> {m['matched']} ({m['score']:.0f}%)")
            partner_id = conn.execute(
                "SELECT partner_id FROM dim_partner WHERE partner_name = ?", (m["matched"],)
            ).fetchone()[0]
            conn.execute(
                "INSERT INTO fact_participation (proposal_key, partner_id, requested_cents, granted_cents) "
                "VALUES (?, ?, ?, ?)",
                (proposal_key, partner_id, p.get("requested_cents") or 0, p.get("granted_cents") or 0),
            )
            partners_inserted += 1

        sdgs_inserted = 0
        for s in (sdg_result or {}).get("sdgs", []):
            conn.execute(
                "INSERT INTO fact_proposal_sdg (proposal_key, sdg_number) VALUES (?, ?)",
                (proposal_key, s["number"]),
            )
            sdgs_inserted += 1

        conn.commit()
        logger.info(
            "Loaded proposal_key=%s: %d partner(s), %d flagged, %d SDG(s)",
            proposal_key, partners_inserted, len(flagged_partners), sdgs_inserted,
        )
        return {
            "proposal_key": proposal_key,
            "partners_inserted": partners_inserted,
            "flagged_partners": flagged_partners,
            "sdgs_inserted": sdgs_inserted,
        }
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


class ProposalNotFoundError(Exception):
    """Raised when editing a proposal_key that is not in dim_proposal."""


def update_proposal(
    proposal_key: int,
    proposal_fields: dict[str, Any],
    fact_fields: dict[str, Any],
    partner_updates: list[dict[str, Any]],
    sdg_numbers: list[int],
    config: Config,
) -> None:
    """Overwrite every editable field of an already-saved project (the webapp's project
    edit form). partner_updates is [{"partner_id", "requested_cents", "granted_cents"}] - the
    full desired set of partners for this project, not just changed amounts. Existing
    fact_participation rows are replaced wholesale (delete then re-insert) rather than updated
    in place, the same pattern already used for sdg_numbers below: a partner present in this
    call but not before is thereby added, and one no longer present is thereby removed.
    """
    conn = get_connection(config)
    try:
        if not conn.execute(
            "SELECT 1 FROM dim_proposal WHERE proposal_key = ?", (proposal_key,)
        ).fetchone():
            raise ProposalNotFoundError(f"No proposal with proposal_key={proposal_key}")

        programme_id = resolve_programme(
            conn, proposal_fields.get("programme_name"), proposal_fields.get("funding_source")
        )
        conn.execute(
            """
            UPDATE dim_proposal
            SET proposal_acronym = ?, proposal_title = ?, call_identifier = ?,
                programme_id = ?, submission_date = ?, decision_date = ?, status = ?
            WHERE proposal_key = ?
            """,
            (
                proposal_fields.get("proposal_acronym"),
                proposal_fields.get("proposal_title"),
                proposal_fields.get("call_identifier"),
                programme_id,
                proposal_fields.get("submission_date"),
                proposal_fields.get("decision_date"),
                proposal_fields.get("status") or "Pending",
                proposal_key,
            ),
        )
        conn.execute(
            """
            UPDATE fact_proposal
            SET requested_total_cents = ?, granted_total_cents = ?,
                trl_start = ?, trl_target = ?, mcrl_start = ?, mcrl_target = ?,
                builds_on_previous = ?, demo_activity_count = ?
            WHERE proposal_key = ?
            """,
            (
                fact_fields.get("requested_total_cents") or 0,
                fact_fields.get("granted_total_cents") or 0,
                fact_fields.get("trl_start"), fact_fields.get("trl_target"),
                fact_fields.get("mcrl_start"), fact_fields.get("mcrl_target"),
                fact_fields.get("builds_on_previous"), fact_fields.get("demo_activity_count"),
                proposal_key,
            ),
        )
        conn.execute("DELETE FROM fact_participation WHERE proposal_key = ?", (proposal_key,))
        for pu in partner_updates:
            conn.execute(
                """
                INSERT INTO fact_participation (proposal_key, partner_id, requested_cents, granted_cents)
                VALUES (?, ?, ?, ?)
                """,
                (proposal_key, pu["partner_id"], pu.get("requested_cents") or 0, pu.get("granted_cents") or 0),
            )
        conn.execute("DELETE FROM fact_proposal_sdg WHERE proposal_key = ?", (proposal_key,))
        for number in sdg_numbers:
            conn.execute(
                "INSERT INTO fact_proposal_sdg (proposal_key, sdg_number) VALUES (?, ?)",
                (proposal_key, number),
            )
        conn.commit()
        logger.info("Updated proposal_key=%s", proposal_key)
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Load one clic_extract JSON output into the star schema")
    parser.add_argument("extraction_path", help="Path to a clic_extract <stem>_<UTC>.json file")
    parser.add_argument("--sdgs-path", help="Optional path to a local SDG classifier result JSON ({'sdgs': [...]})")
    parser.add_argument("--config", default="config.yaml", help="Path to config.yaml")
    return parser


def main(argv: list[str] | None = None) -> None:
    args = _build_arg_parser().parse_args(argv)
    config = load_config(args.config)
    configure_logging(config)

    data = json.loads(Path(args.extraction_path).read_text(encoding="utf-8"))
    sdg_result = json.loads(Path(args.sdgs_path).read_text(encoding="utf-8")) if args.sdgs_path else None

    try:
        result = load_extraction(data, sdg_result, config)
    except DuplicateProposalError as exc:
        logger.error(str(exc))
        raise SystemExit(1)

    print(f"proposal_key={result['proposal_key']}")
    print(f"partners inserted: {result['partners_inserted']}")
    print(f"sdgs inserted: {result['sdgs_inserted']}")
    if result["flagged_partners"]:
        print(f"flagged ({len(result['flagged_partners'])}):")
        for f in result["flagged_partners"]:
            print(f"  - {f}")


if __name__ == "__main__":
    main()
