# Discussion note: the author's review of unsure partner names

Status on 8 November 2026. A reminder for the discussion chapter. Source: batch `batch_20261030T105636Z`, provisional scoring of 31 October 2026 (first pass, scorer commit `bc3d42b`) against the final scoring (second pass), first run on 8 November 2026 at commit `bc3d42b` and repeated on 9 November 2026 at commit `86e6d71`, which leaves failed runs out of time and cost; the partner figures are the same in both. The step itself is explained in `REVIEW_DECISIONS_EXPLAINED.md`.

## 1. What the step is

1. The scorer matches each extracted partner name with the partner names of the reference record by fixed rules. Most names are settled by the rules.
2. Some names cannot be settled: the extracted name is close to a reference partner but not the same (an abbreviation added, a country appended, a shortened form), or only part of it appears in the document. In the provisional scoring these names received half credit.
3. The author reviewed every such name once per document and decided whether it is the reference partner ("y") or not correct ("x"). The decisions were then applied to every run, and the batch was scored again. No model was called again.

## 2. Outcome

| Measure | Value |
|---|---|
| Distinct unsure names reviewed | 34, in 6 of the 10 documents |
| Accepted as the reference partner ("y") | 32 names, 461 occurrences in the runs |
| Rejected as not correct ("x") | 2 names, 6 occurrences |
| Kinds of unsure names | 32 name variants (1 of them also containing a matched name), 2 partial names |
| Total weighted errors, all runs | 2,317.5 provisional, 2,242.0 final |
| Fully correct runs, all runs | 11.5 % provisional, 11.2 % final |

## 3. Effect per configuration

Field accuracy did not change, because the review concerns partner names only. Amount accuracy changed by less than 0.5 points for every configuration.

| Configuration | Partner recall, provisional | Partner recall, final | Over inclusion, provisional | Over inclusion, final |
|---|---|---|---|---|
| multimodal_strict | 82.9 % | 96.6 % | 55.8 % | 50.7 % |
| B | 85.5 % | 94.2 % | 15.4 % | 10.2 % |
| freeform_light | 80.6 % | 90.6 % | 22.5 % | 15.7 % |
| multimodal_combined_llama4_maverick | 81.6 % | 87.1 % | 25.7 % | 22.7 % |
| multimodal_combined_qwen_vl | 74.5 % | 85.9 % | 34.5 % | 27.6 % |
| multimodal_open | 65.1 % | 78.1 % | 60.1 % | 54.6 % |
| targeted_multimodal | 63.0 % | 73.1 % | 32.2 % | 25.8 % |
| C | 57.6 % | 67.8 % | 42.0 % | 35.5 % |
| D | 47.8 % | 65.5 % | 55.5 % | 44.0 % |
| freeform_B | 49.6 % | 63.2 % | 48.9 % | 38.6 % |
| targeted_text | 49.1 % | 57.2 % | 50.9 % | 43.8 % |

Other changes:

1. Duplicates rose from 99 to 112 weighted errors: when a run lists a partner twice, once under its reference name and once as an accepted variant, the second entry is now a duplicate.
2. Errors from names that are not correct rose from 3 to 6: the 6 occurrences of the two rejected names now count fully instead of by half.
3. Partner amount errors rose (missing amounts from 499 to 581, wrong amounts from 339 to 383): accepted variants are now matched partners, so their amounts are now scored in full.
4. The fully correct share of freeform_B fell from 13.3 % to 10.0 %: two runs that were half correct because of unsure names are now settled as not fully correct. No other configuration changed.
5. The cost frontier is unchanged: B, freeform_light and multimodal_combined_llama4_maverick.
6. The ranking by partner recall changed: multimodal_strict now has the highest partner recall (96.6 %), ahead of B (94.2 %).

## 4. Points for the discussion chapter

1. **Name variants are the main source of uncertainty in partner matching.** Almost all unsure names were the correct partner written differently. Fixed matching rules underestimate partner recall; the provisional figures were 5 to 18 points too low.
2. **Human review was needed to settle the evaluation,** which mirrors the pipeline itself: some judgements cannot be automated reliably and are left to a reviewer. This supports the review queue in the design.
3. **Single reviewer.** The decisions were made by one person, the author, who also built the reference records. There is no second reviewer and no agreement measure. Most cases were clear (an abbreviation or country added to the reference name), which limits but does not remove this concern.
4. **One decision per name and document.** Each decision applies to every run that produced that exact name in that document, so the same judgement is applied consistently across configurations.
5. **Traceability.** The original marks, the converted decisions and their checksum are stored; the provisional results are kept in `backup/batch_20261030T105636Z_provisional_scores/` and published in `Final_Results/results_first_pass/`. Both versions can be reproduced.
6. **Implication for the analytical layer.** The same variants will reach the database. Partner names need a normalisation or matching step (for example removing appended abbreviations and countries) and a reviewer check before they enter the partner dimension; otherwise one organisation can appear under several names and distort partner counts.
7. **Possible remedy for future work:** instruct the models to return the partner name exactly as in the partner table, without abbreviations or countries, and add the matching rules for the common variant patterns found here.
