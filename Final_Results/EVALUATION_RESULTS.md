# Evaluation results of the extraction configurations

Status on 9 November 2026. Counterpart of `method/EVALUATION_PROTOCOL.md`, which describes the method; this document reports the results it produced. All figures come from the final scoring (second pass, with the author's review of unsure partner names applied) of batch `batch_20261030T105636Z`, scored with the scorer at commit `86e6d71` from the runs produced at commit `1380dc7`. The figures are descriptive: no significance tests are applied. Percentages are means over the ten per document values of a configuration, each the mean of three runs, unless stated otherwise.

## 1. The run

| Item | Value |
|---|---|
| Configurations, documents, repetitions | 11 × 10 × 3 = 330 final runs |
| Run dates | 30 and 31 October 2026, five chunks of two documents |
| Completed runs | 324 |
| Failed runs | 6: targeted_text and targeted_multimodal on SP03B, three runs each |
| Superseded attempts (not scored) | 1: multimodal_combined_qwen_vl on Abico_Synth, repetition 1 |
| Model calls in the final runs | 1,398 |
| Calls retried | 16 retries in 11 runs, all followed by success, all in image based configurations |
| Page image batches rejected as too large and split | 264 calls, all on SP03B, in the four image based configurations |
| Text inputs split | none |
| Input and output tokens, final runs | 22,073,526 input, 425,654 output |
| Total cost, completed runs | USD 4.54 |
| Total end to end time, completed runs | 25.1 hours |

1. **The six failed runs** stopped before any extraction call with the error `No module named 'rapidocr'`: the batch ran under the system Python installation, which lacks the local OCR package used by the targeted configurations on scanned pages. They count as failures in every accuracy measure and are left out of time and cost (protocol, section 6.2).
2. **The superseded attempt** lost one batch of page images to a provider overload (HTTP 429); the slot was run again and only the second attempt is scored.
3. Full record of each chunk: `run_record/CONVERSION_AND_DATA_CHECKS.md`. Its section 5.6 counts the superseded attempt and the failed runs as well (20 retries, USD 4.57, 22,194,950 input and 426,962 output tokens); the figures in the table above count final runs only, and time and cost completed runs only.

## 2. Results per configuration

### 2.1 Accuracy

| Configuration | Model | Field accuracy (range over documents) | Partner recall | Amount accuracy | Fully correct runs | Consistency | Over inclusion |
|---|---|---|---|---|---|---|---|
| multimodal_combined_llama4_maverick | Llama 4 Maverick | 89.3 % (66.7 to 100) | 87.1 % | 54.1 % | 10.0 % | 92.0 % | 22.7 % |
| B | Qwen3.5 9B | 88.5 % (66.7 to 100) | 94.2 % | 53.5 % | 10.0 % | 97.0 % | 10.2 % |
| multimodal_combined_qwen_vl | Qwen3 VL 235B | 84.8 % (37.0 to 100) | 85.9 % | 76.2 % | 16.7 % | 90.0 % | 27.6 % |
| freeform_light | Qwen3 4B | 84.4 % (66.7 to 100) | 90.6 % | 72.5 % | 20.0 % | 99.0 % | 15.7 % |
| freeform_B | Qwen3.5 9B | 83.7 % (66.7 to 100) | 63.2 % | 56.9 % | 10.0 % | 91.0 % | 38.6 % |
| multimodal_strict | Qwen3 VL 235B | 83.0 % (63.0 to 100) | 96.6 % | 10.0 % | 10.0 % | 88.0 % | 50.7 % |
| C | gpt oss 120B | 82.2 % (66.7 to 100) | 67.8 % | 55.0 % | 10.0 % | 97.0 % | 35.5 % |
| D | gpt oss 20B | 77.4 % (63.0 to 100) | 65.5 % | 60.1 % | 10.0 % | 96.0 % | 44.0 % |
| multimodal_open | Qwen3 VL 235B | 75.9 % (25.9 to 100) | 78.1 % | 26.0 % | 10.0 % | 86.0 % | 54.6 % |
| targeted_multimodal | Qwen3 VL 235B | 69.6 % (0 to 100) | 73.1 % | 74.7 % | 6.7 % | 86.0 % | 25.8 % |
| targeted_text | gpt oss 120B | 69.3 % (0 to 100) | 57.2 % | 57.0 % | 10.0 % | 83.0 % | 43.8 % |

Field accuracy: share of the nine single value fields correct. Partner recall: share of the gold partners found. Amount accuracy: share of the found partners whose amount is correct. Fully correct: every field, partner and amount correct with no wrong extra. Consistency: share of the ten items with the same value in all three runs. Over inclusion: share of extracted partners that are extras.

### 2.2 Validity, cost and time

| Configuration | Valid at first attempt | Valid after repair | Cost per document (USD) | Cost of pass (USD) | Total cost (USD) | Seconds per document | Of which Docling | Of which the configuration |
|---|---|---|---|---|---|---|---|---|
| multimodal_combined_llama4_maverick | 100 % | 100 % | 0.0379 | 0.379 | 1.138 | 215 | none | 215 |
| B | 100 % | 100 % | 0.0027 | 0.027 | 0.082 | 288 | 266 | 22 |
| multimodal_combined_qwen_vl | 83.3 % | 100 % | 0.0409 | 0.245 | 1.226 | 598 | none | 598 |
| freeform_light | 10.0 % | 100 % | 0.0003 | 0.001 | 0.008 | 315 | 266 | 49 |
| freeform_B | 100 % | 100 % | 0.0028 | 0.028 | 0.085 | 310 | 266 | 44 |
| multimodal_strict | 100 % | 100 % | 0.0277 | 0.277 | 0.832 | 272 | none | 272 |
| C | 100 % | 100 % | 0.0042 | 0.042 | 0.126 | 270 | 266 | 3 |
| D | 100 % | 100 % | 0.0020 | 0.020 | 0.059 | 269 | 266 | 3 |
| multimodal_open | 86.7 % | 100 % | 0.0285 | 0.285 | 0.854 | 396 | none | 396 |
| targeted_multimodal | 90.0 % | 90.0 % | 0.0038 | 0.057 | 0.103 | 78 | none | 78 |
| targeted_text | 90.0 % | 90.0 % | 0.0012 | 0.012 | 0.032 | 14 | none | 14 |

1. Cost of pass: cost per document divided by the share of fully correct runs.
2. The Docling conversion ran once per document on the author's laptop processor (115 to 649 seconds per document, mean 266); its time is added to every run of the five text configurations (`run_record/DOCLING_SPEED.md`).
3. Time and cost of the targeted configurations are means over nine documents: on SP03B all their runs failed.
4. The invalid first attempts of freeform_light are replies without the fenced `json` block the free form protocol asks for; all of them became valid records after the local repair.

### 2.3 Cost frontier

The configurations that no other configuration beats on both field accuracy and cost per document are B, freeform_light and multimodal_combined_llama4_maverick (`results_second_pass_final/frontier_plot.png`).

## 3. Results per approach

Means of the configurations in each group.

| Approach | Configurations | Field accuracy | Partner recall | Amount accuracy | Fully correct runs | Consistency | Cost per document (USD) | Seconds per document |
|---|---|---|---|---|---|---|---|---|
| Text only | B, C, D, freeform_B, freeform_light | 83.3 % | 76.2 % | 59.6 % | 12.0 % | 96.0 % | 0.0024 | 290 (24 without Docling) |
| Images only | multimodal_strict, multimodal_open | 79.4 % | 87.3 % | 18.0 % | 10.0 % | 87.0 % | 0.0281 | 334 |
| Targeted | targeted_text, targeted_multimodal | 69.4 % | 65.1 % | 65.8 % | 8.3 % | 84.5 % | 0.0025 | 46 |
| Combined | multimodal_combined_qwen_vl, multimodal_combined_llama4_maverick | 87.0 % | 86.5 % | 65.1 % | 13.3 % | 91.0 % | 0.0394 | 407 |

## 4. Planned contrasts

Mean over documents of the per document differences, varied configuration minus reference. Each contrast has other differences besides its intended factor (protocol, section 7.1, item 3), so no difference is read as caused by one factor alone.

| Contrast | Difference | Field accuracy | Partner recall | Amount accuracy | Fully correct | Cost (USD) | Seconds |
|---|---|---|---|---|---|---|---|
| Model size, text | D minus B | 11.1 points lower | 28.7 points lower | 1.5 points lower | equal | 0.0008 lower | 19 lower |
| Model size, text | C minus D | 4.8 points higher | 2.3 points higher | 3.2 points higher | equal | 0.0022 higher | 1 higher |
| Model size, text | C minus B | 6.3 points lower | 26.5 points lower | 1.9 points higher | equal | 0.0015 higher | 19 lower |
| Output protocol | freeform_B minus B | 4.8 points lower | 31.1 points lower | equal | equal | 0.0001 higher | 22 higher |
| Model, free form | freeform_light minus freeform_B | 0.7 points higher | 27.4 points higher | 12.6 points higher | 10.0 points higher | 0.0026 lower | 6 higher |
| Output constraint | multimodal_open minus multimodal_strict | 7.0 points lower | 18.5 points lower | 16.0 points higher | equal | 0.0007 higher | 124 higher |
| Context selection, text | targeted_text minus C | 13.0 points lower | 10.6 points lower | 4.0 points higher | equal | 0.0032 lower | 234 lower |
| Context selection, with images | targeted_multimodal minus multimodal_combined_qwen_vl | 15.2 points lower | 12.8 points lower | 1.5 points lower | 10.0 points lower | 0.0383 lower | 434 lower |
| Model, combined | multimodal_combined_llama4_maverick minus multimodal_combined_qwen_vl | 4.4 points higher | 1.2 points higher | 16.1 points lower | 6.7 points lower | 0.0029 lower | 383 lower |

Time and cost differences of the context selection contrasts leave out SP03B, where the targeted runs failed.

## 5. Results per document

Means over all 33 runs on each document (all configurations together).

| Code | Document | Field accuracy | Partner recall | Amount accuracy | Fully correct runs |
|---|---|---|---|---|---|
| D01 | Abico_Synth | 66.7 % | 52.7 % | 77.4 % | 0 % |
| D02 | ByggMap | 90.6 % | 61.0 % | 86.6 % | 0 % |
| D03 | CIRCUNOVA | 77.1 % | 75.5 % | 70.3 % | 0 % |
| D04 | CLIMACITIES | 99.7 % | 100.0 % | 100.0 % | 97.0 % |
| D05 | SP01 | 94.6 % | 72.7 % | 37.0 % | 15.2 % |
| D06 | SP02 | 72.7 % | 97.0 % | 18.8 % | 0 % |
| D07 | SP03A | 86.2 % | 89.4 % | 27.1 % | 0 % |
| D08 | SP03B | 69.4 % | 48.0 % | 10.5 % | 0 % |
| D09 | SP04 | 81.8 % | 99.1 % | 21.4 % | 0 % |
| D10 | SP05 | 68.7 % | 85.6 % | 65.3 % | 0 % |

1. Almost every fully correct run is on CLIMACITIES; apart from it, only SP01 has fully correct runs. CLIMACITIES was also the pilot document (protocol, section 4).
2. The six documents SP01 to SP05 state partner amounts in thousands of euros (section 6.3); their amount accuracy is the lowest.
3. On SP01 the Docling Markdown lost the partner table, which affects the five text configurations (`run_record/CONVERSION_AND_DATA_CHECKS.md`, section 3.2).
4. SP03B is the scanned copy of SP03A; the difference between the two shows the effect of the scan for each configuration, except for the targeted ones, which failed on SP03B.

## 6. Errors

### 6.1 By kind

Weighted error counts over all 330 final runs.

| Kind | Errors | Share |
|---|---|---|
| Single value fields | 572 | 25.5 % |
| Gold partners missed | 588 | 26.2 % |
| Partner amounts missing (partner found) | 581 | 25.9 % |
| Partner amounts wrong | 383 | 17.1 % |
| Duplicate partners | 112 | 5.0 % |
| Extracted partners that are not correct | 6 | 0.3 % |
| Total | 2,242 | 100 % |

Three quarters of all errors (74.5 %) concern partners.

### 6.2 By field

| Field | Missed | Wrong | Value where the gold set has none | Total |
|---|---|---|---|---|
| Acronym | 15 | 0 | 0 | 15 |
| Title | 12 | 76 | 0 | 88 |
| Call identifier | 37 | 20 | 27 | 84 |
| Submission date | 21 | 3 | 45 | 69 |
| Requested total | 20 | 35 | 0 | 55 |
| TRL start | 67 | 13 | 7 | 87 |
| TRL target | 69 | 6 | 7 | 82 |
| MCRL start | 30 | 2 | 7 | 39 |
| MCRL target | 37 | 4 | 12 | 53 |

### 6.3 Amounts in thousands of euros

Of the 383 wrong partner amounts, 336 (87.7 %) are exactly one thousandth of the correct value: the model copied an amount from a table stated in thousands of euros without the scale. Fully correct runs: 2.5 % on the six documents in thousands, 24.2 % on the other four. Details: `discussion_notes/DISCUSSION_NOTE_AMOUNTS_IN_THOUSANDS.md`.

## 7. Effect of the author's review (first pass against second pass)

The first pass scored 34 distinct partner names (467 occurrences) as unsure, with half scores. The author marked 32 names (461 occurrences) as the gold partner written differently and 2 names (6 occurrences) as not correct. Field accuracy is the same in both passes; amount accuracy changed by less than 0.5 points.

| Configuration | Partner recall, first pass | Partner recall, second pass | Over inclusion, first pass | Over inclusion, second pass |
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

1. Total weighted errors: 2,317.5 in the first pass, 2,242 in the second.
2. Fully correct runs, all runs: 11.5 % in the first pass, 11.2 % in the second (only freeform_B changed, from 13.3 % to 10.0 %).
3. The cost frontier is the same in both passes.
4. The first pass results are in `results_first_pass/`; they were scored at commit `bc3d42b`, before the decision to leave failed runs out of time and cost, so only their accuracy figures are comparable with the second pass. Details: `discussion_notes/DISCUSSION_NOTE_PARTNER_NAME_REVIEW.md`.

## 8. Check of the scorer

The author checked the spot check sample (two runs per configuration drawn with the fixed seed `spotcheck/batch_20261030T105636Z`, 22 runs in all, `results_second_pass_final/spot_check.md`) on 9 November 2026: every outcome and class given by the scorer was found correct. The scoring is deterministic and uses no language model: the same runs and decisions always give the same scores.
