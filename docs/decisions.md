# Decisions

Short notes on schema changes made after the initial sql/schema.sql, per CLAUDE.md rule 5.

## 2026-10-02: dim_proposal.call_identifier made nullable

Was `TEXT NOT NULL`. Integration-testing `src/pipeline/load.py` against a real extraction
(ABiCo) showed the LLM extraction frequently cannot find a call identifier in the source
document at all (`call_identifier: null` in clic_extract's output), so the NOT NULL
constraint made it impossible to save a large share of real, otherwise-valid extractions.

Changed to nullable `TEXT`. The `UNIQUE (proposal_acronym, call_identifier)` constraint
still exists, but since SQL treats each NULL as distinct, it no longer by itself prevents
two rows with the same acronym and both-NULL call_identifier. Duplicate protection for
that case is instead enforced at the application level, in
`src/pipeline/load.find_duplicate_proposal`, which blocks saving any proposal whose acronym
(normalised) already exists in `dim_proposal`, regardless of call_identifier.

## 2026-10-09: extracted_value.page_reference dropped

`clic_extract`'s model is never asked for a page number (no such field exists in its
`RAW_SCHEMA`), and nothing in the codebase populates `extracted_value` at all yet (0 rows).
The column was dead weight with no producer. Dropped rather than left in place; a page
reference can be added back to both the model's schema and this table together, as one
change, if page-level traceability is actually implemented later.

## 2026-10-19: database emptied and rebuilt from import/clic_full.sql

The previous data/clic.db (3 proposals, 203 partners) was copied to backup/clic_db_2026-10-19/
(binary copy and SQL dump) and the database was rebuilt from sql/schema.sql. The data in
import/clic_full.sql uses a flat schema (project, project_partner, project_sdg, amounts as euro
floats), so import/migrate_clic_full.py converts it into the star schema.

Mapping choices where the source has no direct equivalent:
1. Amounts are converted from euros to whole cents.
2. Verdict Declined becomes status Rejected. Funding scope becomes two programmes, "EU funding (imported)" and "National funding (imported)".
3. Only years are known, so submission_date and decision_date are stored as the first of January of that year. A missing decision year falls back to the submission year.
4. The single avg_trl and avg_mcrl values are stored as trl_target and mcrl_target. The start values stay empty, so the start averages of KPI 7 are empty.
5. The partner role (Leader or Partner) has no column in the star schema and is not carried over.
6. No partner is flagged as CLIC, because none is identifiable in the source.

## 2026-10-19: original partner list restored

dim_partner was replaced with the original 203 partners (taken from the backup of the previous
database), so partner name matching at save time works against the full list again. The 53
placeholder partners of the imported data were remapped, category by category, onto original
partners of the same category (never CLIC itself), so every participation and every category
based KPI is unchanged. The names shown for the imported projects are therefore arbitrary
members of the right category, not the real partners of those projects. import/restore_partner_list.py
does the remapping. A copy of the database from before this step is in backup/clic_db_2026-10-19/.

## 2026-10-19: events and communications added (fact_outreach)

New table fact_outreach in sql/schema.sql: one row per activity kind (Event or Communication),
activity type and month (ISO 8601 text, YYYY-MM), with the number of activities and the reach
(participants or views). The view v_kpi_12_outreach_by_type totals it per type. The column
is_mock marks fictional demonstration rows. import/seed_mock_outreach.py adds the table to an
existing database and loads mock rows for January to October 2026 whose totals follow the layout
of the reference screenshot: 16 events with 772 participants, 11 communications with 4,947 views.
The scorecard shows a "Mock data" badge while any mock row is present. These numbers are not
CLIC figures.

## 2026-10-23: inputs too large for the model's context are split, not refused

The extraction no longer refuses a document estimated to be too large for the model. Each
configuration sends its input whole; only if the provider rejects the request as too large (HTTP 400
with a context length message, or HTTP 413) is the input split in two, recursively, and the answers
merged (first value per field, partner lists joined). The local estimate it replaces (3.5 characters
per token, refuse above 80 percent of the context) would have refused CIRCULANDIA and OLinWASTE for
the gpt oss configurations although both fit. Details and the reasons for not splitting every
document are in Second_step_CLICpipeline/PIPELINE_SUMMARY.md, section 15. No database change.

## 2026-10-23: pipeline layer version 2 (run batches, calls, attempts, raw replies)

Before the full run of the extraction configurations, the run part of the pipeline layer was
rebuilt in sql/schema.sql (its tables held no rows; a copy of the database from before the change
is in backup/clic_db_2026-10-23_before_pipeline_v2/). New tables: run_batch (code version, prompt
digests, price file, manifest, start and end), extraction_call (every model call with the
provider's usage object and the reply exactly as returned) and call_attempt (every HTTP attempt,
retries included). model_config gained the configuration name, all parameters as JSON and prices;
extraction_run gained the batch, input kind, repetition, slot attempt, status, timings, call and
retry counts, reasoning, image and cached tokens, and the run file paths. conversion_run is now
optional on extraction_run, because six configurations read the PDF itself.

Costs and prices are stored as integers in millionths of a US dollar. The rule of whole cents in
integer columns stays for proposal amounts; API prices (for example USD 0.075 per million tokens)
and run costs (a fraction of a cent) cannot be expressed in whole cents, and floats are not used.
Existing databases are brought to version 2 with python -m src.pipeline.db migrate-pipeline-v2,
which takes its definitions from sql/schema.sql and stops if any of these tables holds rows.

## 2026-10-23: streamed replies; first batch aborted

The first run batch (batch_20261023T083538Z, commit 93cc327) was stopped after 12 runs. Long
requests on deepinfra (configurations B and freeform_B on CIRCULANDIA, about 450 KB of Markdown)
failed with HTTP 504 after exactly 120 seconds in all four attempts: the Hugging Face router ends
a request whose complete answer takes longer than that, so repeating cannot help. The model client
now requests streamed replies ("stream": true, with token usage in the last chunk) and rebuilds
the same reply from the stream; prompts, models and generation settings are unchanged. A stream
that breaks off or reports an error is retried like a network error. The aborted batch is kept as
it is, marked in its manifest, and is not part of the results; a new batch is started on the new
commit.
