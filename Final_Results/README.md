# Final results of the evaluation

Status on 18 November 2026. Batch `batch_20261030T105636Z`. The published package of the evaluation: method, results, run record and discussion notes, in one place. The result files are copies of the scorer's output: a rescore writes to `evaluation/results/<batch>/`, not to this folder, so the two can be compared.

## Start here

1. `EVALUATION_RESULTS.md`: the results, with the final figures and where each comes from.
2. `method/EVALUATION_PROTOCOL.md`: the method, including the two scoring passes.

## Contents

| Folder | File | What it is |
|---|---|---|
| method | `EVALUATION_PROTOCOL.md` | how the configurations are run, logged and scored |
| method | `EXTRACTION_CONFIGURATIONS.md` | the eleven configurations: models, providers, prompts, settings |
| method | `LLM_INPUT_EMBEDDING.md` | how each configuration feeds a document to the model |
| method | `GROUNDING_CHECK.md` | the check that extracted values occur in the text the model was given |
| method | `SDG_EMBEDDING_MECHANISM.md` | the local SDG suggestion mechanism of the interface |
| results_second_pass_final | `configuration_summary.csv` | means and ranges per configuration (final) |
| results_second_pass_final | `results_per_run.csv` | one row per final run, every measure |
| results_second_pass_final | `contrast_table.csv` | the planned contrasts, per document and as a mean |
| results_second_pass_final | `error_log.csv`, `extras_log.csv` | every error and every extra partner |
| results_second_pass_final | `frontier_plot.png` | field accuracy against cost per document |
| results_second_pass_final | `report.md` | the readable report of the scorer |
| results_second_pass_final | `spot_check.md` | the 22 runs the author checked by hand |
| results_second_pass_final | `review_decisions_author_marks.csv` | the author's y and x marks on unsure partner names |
| results_second_pass_final | `review_decisions.csv` | the same marks converted into the scorer's decisions |
| results_second_pass_final | `document_codes.csv` | document codes D01 to D10 |
| results_second_pass_final | `scoring_manifest.json` | scorer commit, digests of every input, the frontier |
| results_first_pass | same result files, plus `review_list.csv` and `review_decisions_template.csv` | the automatic scoring before the author's review, for comparison; time and cost there still include the failed runs |
| run_record | `run_manifest.json` | the run manifest: commit, prompt digests, prices, settings, schedule, every run |
| run_record | `docling_conversions.csv` | the Docling conversion time of each document |
| run_record | `CONVERSION_AND_DATA_CHECKS.md` | the record of the conversion and of each chunk of the run |
| run_record | `DOCLING_SPEED.md` | the conversion speed against faster hardware |
| discussion_notes | `DISCUSSION_NOTE_AMOUNTS_IN_THOUSANDS.md` | the amounts in thousands, for the discussion chapter |
| discussion_notes | `DISCUSSION_NOTE_PARTNER_NAME_REVIEW.md` | the review of unsure partner names, for the discussion chapter |
| discussion_notes | `REVIEW_DECISIONS_EXPLAINED.md` | how the review was done and applied |

Some generated files still call themselves "private" (`report.md`, `spot_check.md`): they were written before the decision of 18 November 2026 to publish the results.

## Code versions

1. Runs produced at commit `1380dc7`.
2. First pass scored at commit `bc3d42b` (31 October 2026).
3. Second pass scored at commit `86e6d71` (9 November 2026), the final results.
