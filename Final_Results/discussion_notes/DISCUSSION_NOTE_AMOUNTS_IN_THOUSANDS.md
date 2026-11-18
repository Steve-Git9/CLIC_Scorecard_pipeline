# Discussion note: partner amounts stated in thousands of euros

Status on 8 November 2026. A reminder for the discussion chapter. Source: batch `batch_20261030T105636Z`, final scoring (second pass, author's partner name decisions applied), first run on 8 November 2026 at scorer commit `bc3d42b` and repeated on 9 November 2026 at commit `86e6d71`, which leaves failed runs out of time and cost; the amount figures are the same in both. Documents are named by their codes (D05 to D10; key in `document_codes.csv`).

## 1. Decision

The scoring stays as it is: a partner amount that is a thousand times too small is a wrong amount. No supplementary figure that accepts the missing scale is reported (author's decision of 8 November 2026). The issue is discussed instead.

## 2. What happened

1. Six of the ten documents (D05, D06, D07, D08, D09, D10) state the partner amounts in thousands of euros. The scale appears only once, in a table caption or column header, not next to each number.
2. The reference records store every amount in full euros, as whole cents.
3. Most models copied the numbers as written in the table and did not apply the scale. The result is an amount exactly one thousandth of the correct value.

## 3. Size of the effect

| Measure | Value |
|---|---|
| Wrong partner amounts, all configurations | 383 |
| Of which exactly one thousandth of the correct value | 336 (87.7 %) |
| Runs with at least one such amount | 98 of 330 |
| Requested total wrong because of the scale | 1 of 55 wrong totals; the scale problem concerns partner amounts, not totals |
| Fully correct runs, the six documents in thousands | 2.5 % |
| Fully correct runs, the other four documents | 24.2 % |
| Fully correct runs, all documents | 11.2 % |

Amount accuracy per configuration, on the documents in thousands against the other documents:

| Configuration | Six documents in thousands | Other four documents | Amounts exactly one thousandth |
|---|---|---|---|
| B | 33.4 % | 83.5 % | 54 of 61 wrong |
| C | 8.5 % | 97.2 % | 37 of 40 |
| D | 30.1 % | 75.0 % | 15 of 22 |
| freeform_B | 21.3 % | 94.4 % | 37 of 52 |
| freeform_light | 54.2 % | 100.0 % | 30 of 33 |
| multimodal_strict | 0.0 % | 25.0 % | 0 of 3 |
| multimodal_open | 9.7 % | 50.5 % | 22 of 22 |
| multimodal_combined_qwen_vl | 47.6 % | 100.0 % | 28 of 33 |
| multimodal_combined_llama4_maverick | 23.4 % | 100.0 % | 57 of 61 |
| targeted_text | 17.0 % | 75.0 % | 38 of 38 |
| targeted_multimodal | 45.3 % | 100.0 % | 18 of 18 |

## 4. Points for the discussion chapter

1. **The low amount accuracy and the low share of fully correct runs are mainly a unit problem, not a reading problem.** On the four documents with amounts in full euros, most configurations reach 75 to 100 % amount accuracy.
2. **Every configuration is affected,** whatever the model size, input type or answer format. The scale is stated once, away from the numbers, and the instructions did not ask the model to look for it.
3. **multimodal_strict is an exception of another kind:** its amounts are mostly missing, not scaled, so its low amount accuracy has a different cause.
4. **Some configurations applied the scale more often than others** (freeform_light, multimodal_combined_qwen_vl, targeted_multimodal reach about 45 to 54 % on these documents), but none did so consistently.
5. **Why the scoring was not relaxed:** in the analytical layer an amount a thousand times too small is a wrong value and would distort every KPI built on it. Scoring it as correct would hide a failure that matters for the organisation.
6. **Possible remedies for future work:**
   1. state in the prompt that tables may give amounts in thousands and that amounts must be returned in full euros;
   2. add a validation rule that compares the sum of the partner amounts with the requested total and flags a factor of 1,000;
   3. let the reviewer see the table caption next to the extracted amounts in the review queue.
7. **Relation to the validation layer:** the extraction step already warns when the partner amounts do not add up to the requested total. Where the total was extracted in full euros, scaled partner amounts trigger this warning, so the review step can catch them. This supports the design choice that no value reaches the analytical layer without validation and review.

## 5. Where the evidence is

1. `evaluation/results/batch_20261030T105636Z/error_log.csv`: every wrong amount with its gold and extracted value (published copy: `Final_Results/results_second_pass_final/error_log.csv`).
2. `evaluation/results/batch_20261030T105636Z/report.md`, reading note 3.
3. `EVALUATION_PROTOCOL.md`, section 9, and `CONVERSION_AND_DATA_CHECKS.md`, section 3.3.
