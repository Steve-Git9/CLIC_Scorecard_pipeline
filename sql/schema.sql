-- CLIC Impact Scorecard pipeline, SQLite schema, version 1
-- Layer 1: pipeline (traceability of every document, run and value)
-- Layer 2: analytical star schema (source of the KPI views)
-- Conventions: amounts in whole cents, dates as ISO 8601 text, booleans as 0 or 1.

PRAGMA foreign_keys = ON;

-- =====================================================================
-- LAYER 1: PIPELINE
-- =====================================================================

CREATE TABLE document (
    document_id   INTEGER PRIMARY KEY,
    file_name     TEXT    NOT NULL,
    content_hash  TEXT    NOT NULL UNIQUE,          -- prevents the same file being processed twice
    page_count    INTEGER,
    storage_path  TEXT    NOT NULL,
    received_at   TEXT    NOT NULL,
    status        TEXT    NOT NULL DEFAULT 'received'
                  CHECK (status IN ('received','converted','extracted','in_review','loaded','failed'))
);

CREATE TABLE conversion_run (
    conversion_id INTEGER PRIMARY KEY,
    document_id   INTEGER NOT NULL REFERENCES document(document_id),
    method        TEXT    NOT NULL CHECK (method IN ('native','ocr','mixed')),
    tool          TEXT    NOT NULL,
    tool_version  TEXT,
    pages_ocr     INTEGER NOT NULL DEFAULT 0,
    markdown_path TEXT    NOT NULL,
    duration_ms   INTEGER,
    created_at    TEXT    NOT NULL
);

CREATE TABLE model_config (
    config_id        INTEGER PRIMARY KEY,
    model_name       TEXT    NOT NULL,
    provider         TEXT    NOT NULL,
    is_local         INTEGER NOT NULL DEFAULT 0 CHECK (is_local IN (0,1)),
    prompt_version   TEXT    NOT NULL,
    parameters       TEXT,                           -- JSON, for example temperature
    cost_in_per_mtok_cents  INTEGER NOT NULL DEFAULT 0,
    cost_out_per_mtok_cents INTEGER NOT NULL DEFAULT 0,
    created_at       TEXT    NOT NULL,
    UNIQUE (model_name, prompt_version, parameters)
);

CREATE TABLE extraction_run (
    run_id          INTEGER PRIMARY KEY,
    document_id     INTEGER NOT NULL REFERENCES document(document_id),
    conversion_id   INTEGER NOT NULL REFERENCES conversion_run(conversion_id),
    config_id       INTEGER NOT NULL REFERENCES model_config(config_id),
    run_kind        TEXT    NOT NULL CHECK (run_kind IN ('development','evaluation','production')),
    started_at      TEXT    NOT NULL,
    duration_ms     INTEGER,
    tokens_in       INTEGER,
    tokens_out      INTEGER,
    cost_cents      INTEGER,
    attempts        INTEGER NOT NULL DEFAULT 1,      -- retries needed for valid JSON
    schema_valid    INTEGER NOT NULL DEFAULT 0 CHECK (schema_valid IN (0,1)),
    raw_output_path TEXT
);

-- Field values as rows, so a new model or a new field needs no schema change.
CREATE TABLE extracted_value (
    value_id       INTEGER PRIMARY KEY,
    run_id         INTEGER NOT NULL REFERENCES extraction_run(run_id),
    target_entity  TEXT    NOT NULL CHECK (target_entity IN ('proposal','participation','sdg')),
    item_index     INTEGER NOT NULL DEFAULT 0,       -- partner or SDG position within the proposal
    field_name     TEXT    NOT NULL,
    value_text     TEXT,
    UNIQUE (run_id, target_entity, item_index, field_name)
);

CREATE TABLE validation_result (
    result_id  INTEGER PRIMARY KEY,
    run_id     INTEGER NOT NULL REFERENCES extraction_run(run_id),
    rule_code  TEXT    NOT NULL,
    passed     INTEGER NOT NULL CHECK (passed IN (0,1)),
    severity   TEXT    NOT NULL CHECK (severity IN ('error','warning')),
    message    TEXT,
    created_at TEXT    NOT NULL
);

CREATE TABLE review_decision (
    decision_id    INTEGER PRIMARY KEY,
    run_id         INTEGER NOT NULL REFERENCES extraction_run(run_id),
    value_id       INTEGER REFERENCES extracted_value(value_id),  -- empty when a value was added by hand
    field_name     TEXT    NOT NULL,
    proposed_value TEXT,
    final_value    TEXT,
    decision       TEXT    NOT NULL CHECK (decision IN ('accepted','corrected','added','rejected')),
    value_source   TEXT    NOT NULL CHECK (value_source IN ('extracted','manual','corrected')),
    reviewer       TEXT    NOT NULL,
    decided_at     TEXT    NOT NULL
);

-- =====================================================================
-- LAYER 2: ANALYTICAL STAR SCHEMA
-- =====================================================================

CREATE TABLE dim_funding_programme (
    programme_id   INTEGER PRIMARY KEY,
    programme_name TEXT NOT NULL UNIQUE,
    funding_source TEXT NOT NULL CHECK (funding_source IN ('EU','National'))
);

CREATE TABLE dim_partner (
    partner_id       INTEGER PRIMARY KEY,
    partner_name     TEXT    NOT NULL UNIQUE,
    partner_category TEXT    NOT NULL
                     CHECK (partner_category IN ('Large Company','SME','Research and Education',
                                                 'Public and Third Sector','Other')),
    is_clic          INTEGER NOT NULL DEFAULT 0 CHECK (is_clic IN (0,1))
);

CREATE TABLE partner_alias (
    alias_id   INTEGER PRIMARY KEY,
    partner_id INTEGER NOT NULL REFERENCES dim_partner(partner_id),
    alias      TEXT    NOT NULL UNIQUE               -- name as written in a proposal
);

CREATE TABLE dim_sdg (
    sdg_number INTEGER PRIMARY KEY CHECK (sdg_number BETWEEN 1 AND 17),
    sdg_title  TEXT NOT NULL
);

CREATE TABLE dim_proposal (
    proposal_key     INTEGER PRIMARY KEY,
    document_id      INTEGER UNIQUE REFERENCES document(document_id),
    proposal_acronym TEXT    NOT NULL,
    proposal_title   TEXT,
    call_identifier  TEXT,                             -- often not stated in the document; see docs/decisions.md
    programme_id     INTEGER REFERENCES dim_funding_programme(programme_id),
    submission_date  TEXT,                            -- stated in the document, may be empty
    ingested_at      TEXT    NOT NULL,                -- set automatically at extraction
    decision_date    TEXT,                            -- required once the status leaves Pending
    status           TEXT    NOT NULL DEFAULT 'Pending'
                     CHECK (status IN ('Pending','Approved','Rejected')),
    UNIQUE (proposal_acronym, call_identifier),       -- a resubmission is a separate proposal;
                                                       -- NULL call_identifier values are distinct per SQL semantics,
                                                       -- so this does not by itself stop two such rows sharing an
                                                       -- acronym - the load step's own duplicate check does that
    CHECK (status = 'Pending' OR decision_date IS NOT NULL)
);

CREATE TABLE fact_proposal (
    proposal_key          INTEGER PRIMARY KEY REFERENCES dim_proposal(proposal_key),
    requested_total_cents INTEGER NOT NULL DEFAULT 0, -- loaded as the sum of fact_participation
    granted_total_cents   INTEGER NOT NULL DEFAULT 0,
    trl_start             INTEGER CHECK (trl_start  BETWEEN 1 AND 9),
    trl_target            INTEGER CHECK (trl_target BETWEEN 1 AND 9),
    mcrl_start            INTEGER CHECK (mcrl_start  BETWEEN 1 AND 9),
    mcrl_target           INTEGER CHECK (mcrl_target BETWEEN 1 AND 9),
    builds_on_previous    INTEGER CHECK (builds_on_previous IN (0,1)),
    demo_activity_count   INTEGER CHECK (demo_activity_count >= 0),
    CHECK (trl_target  IS NULL OR trl_start  IS NULL OR trl_target  >= trl_start),
    CHECK (mcrl_target IS NULL OR mcrl_start IS NULL OR mcrl_target >= mcrl_start)
);

CREATE TABLE fact_participation (
    participation_id INTEGER PRIMARY KEY,
    proposal_key     INTEGER NOT NULL REFERENCES dim_proposal(proposal_key),
    partner_id       INTEGER NOT NULL REFERENCES dim_partner(partner_id),
    requested_cents  INTEGER NOT NULL DEFAULT 0,
    granted_cents    INTEGER NOT NULL DEFAULT 0,
    UNIQUE (proposal_key, partner_id)
);

CREATE TABLE fact_proposal_sdg (
    proposal_key INTEGER NOT NULL REFERENCES dim_proposal(proposal_key),
    sdg_number   INTEGER NOT NULL REFERENCES dim_sdg(sdg_number),
    PRIMARY KEY (proposal_key, sdg_number)
);

-- Events and communications: monthly counts and reach per activity type.
-- is_mock = 1 marks fictional demonstration rows (see docs/decisions.md).
CREATE TABLE fact_outreach (
    outreach_id    INTEGER PRIMARY KEY,
    activity_kind  TEXT    NOT NULL CHECK (activity_kind IN ('Event','Communication')),
    activity_type  TEXT    NOT NULL,
    activity_month TEXT    NOT NULL CHECK (length(activity_month) = 7),  -- ISO 8601, YYYY-MM
    activity_count INTEGER NOT NULL CHECK (activity_count >= 0),
    reach_count    INTEGER NOT NULL CHECK (reach_count >= 0),            -- participants or views
    is_mock        INTEGER NOT NULL DEFAULT 0 CHECK (is_mock IN (0,1)),
    UNIQUE (activity_kind, activity_type, activity_month)
);

CREATE INDEX ix_participation_partner ON fact_participation(partner_id);
CREATE INDEX ix_proposal_status       ON dim_proposal(status);
CREATE INDEX ix_value_run             ON extracted_value(run_id);

-- =====================================================================
-- VIEWS: partner status and the eleven KPIs
-- Pending proposals are excluded everywhere.
-- CLIC is included in the totals of KPI 2 and 4, excluded from KPI 3, 5 and 6.
-- =====================================================================

CREATE VIEW v_partner_status AS
SELECT p.partner_id, p.partner_name, p.partner_category, p.is_clic,
       CASE
         WHEN SUM(CASE WHEN d.status = 'Approved' THEN 1 ELSE 0 END) > 0 THEN 'Activated'
         WHEN SUM(CASE WHEN d.status = 'Pending'  THEN 1 ELSE 0 END) > 0 THEN 'Pending'
         ELSE 'Rejected'
       END AS partner_status
FROM dim_partner p
LEFT JOIN fact_participation f ON f.partner_id = p.partner_id
LEFT JOIN dim_proposal      d ON d.proposal_key = f.proposal_key
GROUP BY p.partner_id;

CREATE VIEW v_kpi_01_success_rate_count AS
SELECT SUM(CASE WHEN status = 'Approved' THEN 1 ELSE 0 END)            AS approved_count,
       COUNT(*)                                                        AS decided_count,
       ROUND(1.0 * SUM(CASE WHEN status = 'Approved' THEN 1 ELSE 0 END) / COUNT(*), 4) AS success_rate
FROM dim_proposal
WHERE status IN ('Approved','Rejected');

CREATE VIEW v_kpi_02_success_rate_eur AS
SELECT SUM(CASE WHEN d.status = 'Approved' THEN f.granted_total_cents ELSE 0 END) / 100.0 AS granted_eur,
       SUM(f.requested_total_cents) / 100.0                                              AS requested_eur,
       ROUND(1.0 * SUM(CASE WHEN d.status = 'Approved' THEN f.granted_total_cents ELSE 0 END)
             / NULLIF(SUM(f.requested_total_cents), 0), 4)                               AS success_rate_eur
FROM dim_proposal d JOIN fact_proposal f ON f.proposal_key = d.proposal_key
WHERE d.status IN ('Approved','Rejected');

CREATE VIEW v_kpi_03_total_partner_funding AS
SELECT SUM(f.granted_cents) / 100.0 AS total_partner_funding_eur
FROM fact_participation f
JOIN dim_proposal d ON d.proposal_key = f.proposal_key
JOIN dim_partner  p ON p.partner_id   = f.partner_id
WHERE d.status = 'Approved' AND p.is_clic = 0;

CREATE VIEW v_kpi_04_applied_vs_granted_by_source AS
SELECT g.funding_source,
       SUM(f.requested_total_cents) / 100.0                                              AS requested_eur,
       SUM(CASE WHEN d.status = 'Approved' THEN f.granted_total_cents ELSE 0 END) / 100.0 AS granted_eur
FROM dim_proposal d
JOIN fact_proposal          f ON f.proposal_key = d.proposal_key
JOIN dim_funding_programme  g ON g.programme_id = d.programme_id
WHERE d.status IN ('Approved','Rejected')
GROUP BY g.funding_source;

CREATE VIEW v_kpi_05_top_partners AS
SELECT p.partner_name, p.partner_category,
       SUM(f.granted_cents) / 100.0 AS funding_enabled_eur,
       COUNT(DISTINCT f.proposal_key) AS project_count
FROM fact_participation f
JOIN dim_proposal d ON d.proposal_key = f.proposal_key
JOIN dim_partner  p ON p.partner_id   = f.partner_id
WHERE d.status = 'Approved' AND p.is_clic = 0
GROUP BY p.partner_id
ORDER BY funding_enabled_eur DESC;

CREATE VIEW v_kpi_06_network_by_category AS
SELECT partner_category,
       COUNT(*) AS partner_count,
       ROUND(1.0 * COUNT(*) / (SELECT COUNT(*) FROM v_partner_status
                               WHERE partner_status = 'Activated' AND is_clic = 0), 4) AS share
FROM v_partner_status
WHERE partner_status = 'Activated' AND is_clic = 0
GROUP BY partner_category;

CREATE VIEW v_kpi_07_trl_mcrl AS
SELECT d.proposal_key, d.proposal_acronym,
       f.trl_start, f.trl_target, f.mcrl_start, f.mcrl_target
FROM dim_proposal d JOIN fact_proposal f ON f.proposal_key = d.proposal_key
WHERE d.status = 'Approved';

CREATE VIEW v_kpi_07_trl_mcrl_average AS
SELECT ROUND(AVG(trl_start), 2)  AS avg_trl_start,
       ROUND(AVG(trl_target), 2) AS avg_trl_target,
       ROUND(AVG(mcrl_start), 2) AS avg_mcrl_start,
       ROUND(AVG(mcrl_target), 2) AS avg_mcrl_target
FROM v_kpi_07_trl_mcrl;

CREATE VIEW v_kpi_08_builds_on_previous AS
SELECT SUM(f.builds_on_previous) AS projects_building_on_previous
FROM dim_proposal d JOIN fact_proposal f ON f.proposal_key = d.proposal_key
WHERE d.status = 'Approved';

CREATE VIEW v_kpi_09_10_demo_activities AS
SELECT SUM(f.demo_activity_count)                                          AS total_demo_activities,
       SUM(CASE WHEN f.demo_activity_count > 0 THEN 1 ELSE 0 END)          AS projects_with_demo
FROM dim_proposal d JOIN fact_proposal f ON f.proposal_key = d.proposal_key
WHERE d.status = 'Approved';

CREATE VIEW v_kpi_11_sdg_by_goal AS
SELECT s.sdg_number, s.sdg_title, COUNT(ps.proposal_key) AS project_count
FROM dim_sdg s
LEFT JOIN fact_proposal_sdg ps ON ps.sdg_number = s.sdg_number
LEFT JOIN dim_proposal      d  ON d.proposal_key = ps.proposal_key AND d.status = 'Approved'
GROUP BY s.sdg_number;

CREATE VIEW v_kpi_11_sdg_projects AS
SELECT COUNT(DISTINCT ps.proposal_key) AS projects_supporting_sdgs
FROM fact_proposal_sdg ps
JOIN dim_proposal d ON d.proposal_key = ps.proposal_key
WHERE d.status = 'Approved';

CREATE VIEW v_kpi_12_outreach_by_type AS
SELECT activity_kind, activity_type,
       SUM(activity_count) AS total_activities,
       SUM(reach_count)    AS total_reach
FROM fact_outreach
GROUP BY activity_kind, activity_type;
