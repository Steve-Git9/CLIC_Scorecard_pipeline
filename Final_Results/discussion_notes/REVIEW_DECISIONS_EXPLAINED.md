# The review decisions on unsure partner names

Status on 18 November 2026. Batch `batch_20261030T105636Z`. This note explains the author's review of unsure partner names and how it was applied. The author's marks are `results_second_pass_final/review_decisions_author_marks.csv`; the converted decisions are `results_second_pass_final/review_decisions.csv`. For the meaning for the thesis, see `DISCUSSION_NOTE_PARTNER_NAME_REVIEW.md` in this folder.

## 1. Why decisions were needed

When the scorer compares the partners a model extracted with the partners of the reference record, it matches names by fixed rules. Some names cannot be settled by the rules, for example:

1. **variant:** the name is close to a reference partner but written differently, such as an abbreviation in brackets, a country appended or only the first word of the name;
2. **contains_matched:** the name contains the name of a partner that is already matched;
3. **partial_name:** the whole name does not appear in the document, but a distinctive word of it does.

In the provisional scoring of 31 October 2026 each such name received half credit. The template `review_decisions_template.csv` (in `results_first_pass/`) listed each distinct name once per document (34 names) for the author to decide.

## 2. The author's marks

The author filled in the `decision` column of a copy of the template (`review_decisions_author_marks.csv`) on 8 November 2026:

| Mark | Meaning | Names | Occurrences in the runs |
|---|---|---|---|
| y | the name is the suggested reference partner, written differently | 32 | 461 |
| x | the name is not correct | 2 | 6 |

## 3. How the marks were converted

The scorer accepts three decisions. The marks were converted as follows, without changing this file:

| Mark | Decision given to the scorer | Effect on the score |
|---|---|---|
| y | `gold:<reference partner>`, using the single name in the column `related_gold_partners` | the name counts as that partner found (full credit); its amount is scored against the reference amount; if the same run already lists that partner, it counts as a duplicate |
| x | `unsupported_extra` | the name counts as an extracted partner that is not correct: one full error per occurrence |

The other possible decision, `supported_extra` (a real organisation in the document that is not a partner), was not used, because it does not count as an error and so does not match "not correct".

The converted file is `review_decisions.csv`, written to `evaluation/results/batch_20261030T105636Z/` where the scorer reads it (published copy in `results_second_pass_final/`). It keeps the author's mark in the column `author_mark` next to the converted decision. Its SHA 256 checksum, recorded in `scoring_manifest.json` of the final scoring, is `da5e9a461f2883334b988a5c3e8a02f8240b059107dcb45ac3ef26f712817037`.

## 4. Rescoring

1. Command: `py -3.13 -m src.evaluation.score_batch --batch batch_20261030T105636Z`, run on 8 November 2026 at 13:41 UTC with the scorer at commit `bc3d42b`, and repeated on 9 November 2026 with the scorer at commit `86e6d71`, which leaves failed runs out of time and cost (decision of 9 November 2026); the decisions and every accuracy and partner figure are the same in both.
2. Both times with no uncommitted changes. No model was called.
3. All 330 final runs were scored again, with no unsure names left.
4. The results are in `evaluation/results/batch_20261030T105636Z/` (published copy in `results_second_pass_final/`); the shareable copies were checked again against 227 names, titles and amounts from the reference records, with no match.
5. The provisional results of 31 October 2026 are kept in `backup/batch_20261030T105636Z_provisional_scores/` (not published) and published in `results_first_pass/`.

## 5. Main changes

1. Partner recall rose for every configuration, by 5.5 to 17.7 points; for example B from 85.5 % to 94.2 %.
2. Field accuracy did not change; amount accuracy changed by less than 0.5 points.
3. Total weighted errors fell from 2,317.5 to 2,242.0.
4. Fully correct runs: 11.2 % of all runs (provisional 11.5 %).
5. The cost frontier is unchanged: B, freeform_light and multimodal_combined_llama4_maverick.

The full comparison per configuration is in `DISCUSSION_NOTE_PARTNER_NAME_REVIEW.md`, section 3.
