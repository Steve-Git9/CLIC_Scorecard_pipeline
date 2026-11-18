# Docling conversion and data checks

Status on 30 October 2026. Record of the preparation of the ten evaluation documents before the full run: the pairing of documents with their gold sets, the Docling conversion, and what a check of the converted text against the gold sets found. Companion to `EVALUATION_PROTOCOL.md`.

## 1. Documents and gold sets

1. Ten PDFs in `data/raw/` and ten gold sets in `evaluation/gold/`, paired by identical name, letter case included: Abico_Synth, ByggMap, CIRCUNOVA, CLIMACITIES, SP01, SP02, SP03A, SP03B, SP04, SP05.
2. Every PDF opens and none is encrypted; every gold set passes the shared final validation.
3. History of the pairing (29 October 2026): the gold set of Abico_Synth was first named `ReCoSE_gold_reference.json` and the PDF of CIRCUNOVA `CIRCUNOVA_synthetic.pdf`; the author renamed them. A case only difference between `Abico_Synth.pdf` and its gold file was then corrected by the author. Gold contents were never changed.
4. SP03B is a scanned copy of SP03A (same proposal, same gold set), with no text layer on any of its 45 pages.
5. In SP05 the partner amounts of the gold set do not add up to the stated total; used as it is.

## 2. Docling conversion

Run on 30 October 2026 with `python -m src.evaluation.convert_documents`, at commit `1380dc7`, one document at a time, Docling 2.130.0. Output: `data/markdown/<document>.md`, with a timing record `<document>.conversion.json` per document and all rows in `data/markdown/conversions.csv`. Total about 44 minutes.

| Document | Pages | Total seconds | Seconds per page | Pages per minute | Tables | Pictures | OCR | Markdown characters |
|---|---|---|---|---|---|---|---|---|
| Abico_Synth | 40 | 244.1 | 6.10 | 9.8 | 36 | 7 | no | 166,674 |
| ByggMap | 22 | 201.4 | 9.15 | 6.6 | 34 | 6 | no | 81,258 |
| CIRCUNOVA | 146 | 649.0 | 4.45 | 13.5 | 131 | 0 | no | 273,909 |
| CLIMACITIES | 45 | 115.0 | 2.56 | 23.5 | 2 | 16 | no | 111,324 |
| SP01 | 66 | 191.8 | 2.91 | 20.7 | 14 | 5 | no | 171,589 |
| SP02 | 41 | 144.0 | 3.51 | 17.1 | 11 | 21 | no | 128,660 |
| SP03A | 45 | 173.4 | 3.85 | 15.6 | 27 | 1 | no | 82,736 |
| SP03B | 45 | 461.0 | 10.24 | 5.9 | 22 | 3 | yes | 80,541 |
| SP04 | 63 | 193.1 | 3.07 | 19.6 | 15 | 4 | no | 135,226 |
| SP05 | 78 | 287.5 | 3.69 | 16.3 | 27 | 11 | no | 257,111 |

1. The first document of the process (Abico_Synth) includes about 23 seconds of Docling start up (total 244.1 against 221.4 seconds of conversion proper); for comparisons between documents the conversion time (`convert_seconds` in the records) is the like for like measure.
2. Speed depends mainly on the number of tables, not on the page count: CLIMACITIES (2 tables) converts at 23.5 pages per minute, ByggMap (34 tables in 22 pages) at 6.6.
3. OCR was used only for SP03B, as intended: it is the only document whose pages lack a usable text layer.

## 3. Check of the converted text against the gold sets

For each document, the Markdown (normalised as the scorer does: entities decoded, emphasis removed, whitespace collapsed, case folded) was searched for the gold acronym, the gold partner names verbatim and the gold total.

| Document | Acronym found | Partner names found verbatim | Total found |
|---|---|---|---|
| Abico_Synth | yes | 5 of 5 | yes |
| ByggMap | yes | 7 of 7 | yes |
| CIRCUNOVA | yes | 18 of 21 | yes |
| CLIMACITIES | yes | 8 of 8 | yes |
| SP01 | yes | 1 of 9 | yes |
| SP02 | yes | 5 of 5 | yes |
| SP03A | yes | 6 of 6 | yes, written as 979300 |
| SP03B | yes | 5 of 6 | yes |
| SP04 | yes | 7 of 7 | yes, written as 2,946.1 in thousands of euros (section 3.3) |
| SP05 | yes | 7 of 8 | yes |

### 3.1 SP03B: OCR quality

The OCR text is almost as long as the clean version's (80,541 against 82,736 characters), and the acronym, the total and five of six partner names come through exactly. "Kestrel Institute for Process Research" is not found verbatim, most likely a small OCR error in that name.

### 3.2 SP01: Docling lost the partner table

The full legal names of the partners (for example "Northbay Materials Oy", "Corvane Polymer Systems AB") are in the PDF's text layer on pages 34 and 41, in a table without ruled lines that pymupdf does not detect as a table. The Docling Markdown contains only one of the nine full names; the others appear only as short names in the running text ("Lead: Northbay"). The PDF itself is correct.

Consequences, recorded so that the results are read correctly:

1. The five text configurations, which read only the Markdown, cannot see the full partner names of SP01; low partner scores on SP01 for them reflect the conversion, not the models.
2. The configurations that read the PDF (images, text layer or located pages) are not affected.
3. The scorer classifies extra partners against the Markdown. On SP01 an extracted partner that matches a gold name is scored normally, but an extra partner whose full name is only in the PDF may be classified as unsupported or unsure instead of supported.

This is a property of Docling as a converter and is kept as a finding; the conversion is not altered.

### 3.3 SP04: total stated in thousands of euros (resolved)

The gold set gives a requested total of 2,946,100 euros (294,610,000 cents), which equals the sum of its seven partner amounts. The search for this figure found nothing because the document states it in another form: in Table 5.2, the total row of the "Requested funding" column reads "2,946.1", in thousands of euros, a scale given only in the table caption. The running text also mentions a "total funding request of EUR 3,207,500", which is not the requested funding of the gold set. Checked and confirmed by the author on 30 October 2026: the gold set is correct.

Expected consequence, accepted by the author: the prompts instruct every model to copy amounts as written and never to convert or scale them, and the post processing does not read scales from captions. A configuration that follows the instruction returns "2,946.1", which is converted to 2,946.10 euros, a thousand times too small; the same applies to partner amounts given in the same table. Wrong amounts on SP04 therefore reflect this design, shared by all configurations, rather than a single model; a configuration may also pick the EUR 3,207,500 of the running text.

Found during the scoring on 31 October 2026: SP04 is not the only such document. SP01, SP02, SP03A, SP03B and SP05 also state their partner amounts in thousands of euros, with the scale only in the table caption or column header (for example SP02, column "Requested funding (EUR thousand)", row value "181.6" for EUR 181,600; SP01, caption "All amounts in EUR thousand"; SP03A, header "Budget (1 000 EUR)"). Most wrong partner amounts in the batch are exactly one thousandth of the gold amount for this reason (`EVALUATION_PROTOCOL.md`, section 9, item 10).

### 3.4 Other observations

1. SP03A states its total without separators ("979300"); it is in the document.
2. CIRCUNOVA (18 of 21) and SP05 (7 of 8) show the usual small losses of table extraction.

## 4. State before the full run

1. Code committed and pushed: commit `1380dc7`, working tree clean.
2. All six model and provider pairs listed as live on the Hugging Face router with structured output support; every configuration has a verified price row in `provider_prices(1).csv`.
3. Database `data/clic.db`: integrity check passed, pipeline layer version 2 in place, the two earlier batches marked as aborted.
4. Tests: 123 in `tests/` and 95 in the pipeline package pass.
5. Run order (seed 20261024): CLIMACITIES, SP01, SP03A, SP03B, Abico_Synth, SP02, SP04, ByggMap, CIRCUNOVA, SP05.

## 5. Run progress

Batch `batch_20261030T105636Z`, commit `1380dc7`, eleven configurations, three repetitions, two documents per chunk, run in the background with `python -m src.evaluation.run_batch --batch batch_20261030T105636Z --next 2`.

### 5.1 Chunk 1: CLIMACITIES and SP01 (30 October 2026)

1. Started 12:56, finished 14:31 local time (about 1 hour 35 minutes).
2. 66 of 66 runs ok, no retries, no failed calls, no provider failures, no context splits; all 66 final outputs pass the final schema validation.
3. Cost USD 0.56 in total.
4. 253 grounding warnings, nearly all on SP01, as expected from the partner table lost by Docling (section 3.2); freeform_light has the most on SP01 (57 over three runs). Whether these are invented or reworded names is left to the scoring.

| Configuration | Mean seconds per run | Cost of 6 runs (USD) |
|---|---|---|
| multimodal_open | 294 | 0.157 |
| multimodal_strict | 209 | 0.153 |
| multimodal_combined_qwen_vl | 192 | 0.078 |
| multimodal_combined_llama4_maverick | 58 | 0.072 |
| C | 157 | 0.025 |
| targeted_multimodal | 59 | 0.021 |
| freeform_B | 182 | 0.017 |
| B | 174 | 0.016 |
| D | 156 | 0.012 |
| targeted_text | 9 | 0.006 |
| freeform_light | 226 | 0.002 |

### 5.2 Chunk 2: SP03A and SP03B (30 October 2026)

1. Started 14:40, finished 18:26 local time (about 3 hours 46 minutes).
2. 60 of 66 runs ok; the 6 runs not ok are the targeted runs on SP03B described below. Three runs needed one retry each after a provider failure and then succeeded (multimodal_combined_qwen_vl on SP03A repetition 1 and on SP03B repetition 3, multimodal_strict on SP03B repetition 1). No text input needed splitting; all 60 successful outputs pass the final schema validation.
   Image batches were split, however: on SP03B every run of the four image based configurations (multimodal_strict, multimodal_open and the two combined configurations, 12 runs) had batches of page images rejected as too large by the router (HTTP 413, request entity too large), since the scanned pages make large images. The code split each rejected batch in two and retried, down to single pages where needed, as designed (`fit.py`); 264 rejected calls in all, 22 per run, each recorded in the run's warnings and as a failed call in `extraction_call`. All twelve runs succeeded. These splits are not counted in the `context_splits` column, which counts text splits only. No other document triggered an image split.
3. Cost USD 0.62 in total.
4. Grounding warnings: 155 on SP03A and 426 on SP03B. The higher count on the scanned copy is expected, since its reference text comes from OCR.
5. The end to end time of the text configurations includes the Docling conversion of the document (section 2), which dominates it: on SP03B the model calls of configuration C took about 3 seconds, the end to end time about 464 seconds, against about 176 seconds on SP03A. The slower image based runs on SP03B reflect the scanned pages.

| Configuration | Mean seconds per run, SP03A | Mean seconds per run, SP03B | Runs ok | Cost of the runs (USD) |
|---|---|---|---|---|
| multimodal_combined_qwen_vl | 578 | 1,374 | 6 | 0.175 |
| multimodal_open | 222 | 895 | 6 | 0.141 |
| multimodal_strict | 138 | 593 | 6 | 0.133 |
| multimodal_combined_llama4_maverick | 119 | 347 | 6 | 0.112 |
| C | 176 | 464 | 6 | 0.016 |
| targeted_multimodal | 50 | failed | 3 | 0.010 |
| freeform_B | 216 | 508 | 6 | 0.010 |
| B | 197 | 482 | 6 | 0.010 |
| D | 176 | 463 | 6 | 0.007 |
| targeted_text | 10 | failed | 3 | 0.003 |
| freeform_light | 203 | 476 | 6 | 0.001 |

**Failed runs on SP03B, kept as failures by decision of the author.** The two targeted configurations (targeted_text and targeted_multimodal) fail on SP03B in all three repetitions, six runs in all, after about one to three seconds and before any extraction call, with the error `could not read or OCR the located pages: No module named 'rapidocr'`.

1. Cause: SP03B has no text layer, so the targeted configurations must OCR the pages they locate, which they do locally with rapidocr. The batch was started with the system Python installation (3.13.2), which lacks rapidocr; the project environment `.venv`, used for the Docling conversion, has rapidocr 3.9.2. This is a fault of the run environment, not of the models or of the configurations' design.
2. Scope: only these six runs. No other configuration uses this OCR step, and CLIMACITIES, SP01 and the remaining documents have a text layer (Docling applied OCR to SP03B only, section 2), so they never call it. Chunk 1 is unaffected.
3. Decision (30 October 2026): the runs are not repeated. They stay in the database with status `failed` and are reported as failures. In the analysis they must be read as an environment failure: the targeted configurations' result on SP03B says nothing about their ability to handle scanned documents, and comparisons of SP03A against SP03B are not possible for these two configurations.
4. The remaining chunks run in the same environment as chunks 1 and 2, so the environment stays constant across the batch.

### 5.3 Chunk 3: Abico_Synth and SP02 (30 October 2026)

1. Started 18:55, finished 21:39 local time (about 2 hours 44 minutes).
2. 66 of 66 slots ok; all 66 final outputs pass the final schema validation; no context splits.
3. The image provider was frequently overloaded during this chunk (HTTP 429, "Model busy, retry later"). The image based configurations needed 17 retries in all, every one of which ended in success. One slot (multimodal_combined_qwen_vl on Abico_Synth, repetition 1) lost one batch of 10 page images after that batch exhausted its retries (HTTP 429), so its output lacked those pages; the run itself ended with status ok, but the runner treats any provider failure inside a run as a reason to requeue, so the slot was run again and succeeded completely at its second slot attempt. The first attempt (cost USD 0.025) is kept in the database as superseded (`is_final` 0) and is not scored; the database therefore holds 67 runs for this chunk, of which 66 are final.
4. Cost USD 0.66 in total, including the requeued attempt.
5. Grounding warnings on the final runs: 139 on Abico_Synth and 102 on SP02.
6. As in section 5.2, the end to end times of the text configurations include the Docling conversion of the document.

| Configuration | Mean seconds per run, Abico_Synth | Mean seconds per run, SP02 | Retries | Cost of the runs (USD) |
|---|---|---|---|---|
| multimodal_combined_qwen_vl | 531 | 494 | 6 | 0.185 |
| multimodal_combined_llama4_maverick | 116 | 107 | 0 | 0.148 |
| multimodal_open | 482 | 435 | 1 | 0.117 |
| multimodal_strict | 270 | 279 | 7 | 0.112 |
| targeted_multimodal | 164 | 101 | 3 | 0.024 |
| C | 247 | 147 | 0 | 0.023 |
| freeform_B | 278 | 170 | 0 | 0.016 |
| B | 253 | 156 | 0 | 0.015 |
| D | 247 | 147 | 0 | 0.011 |
| targeted_text | 18 | 9 | 0 | 0.008 |
| freeform_light | 275 | 162 | 0 | 0.001 |

### 5.4 Chunk 4: SP04 and ByggMap (31 October 2026)

1. Started 09:29, finished 11:15 local time (about 1 hour 46 minutes).
2. 66 of 66 runs ok, no retries, no failed calls, no provider failures, no context splits; all 66 final outputs pass the final schema validation.
3. Cost USD 0.77 in total.
4. Grounding warnings: 354 on SP04 and 18 on ByggMap. SP04 was run unchanged, as decided by the author (section 3.3); its amounts are stated in thousands of euros, and the effect on the extracted amounts is left to the scoring.
5. As in section 5.2, the end to end times of the text configurations include the Docling conversion of the document.

| Configuration | Mean seconds per run, SP04 | Mean seconds per run, ByggMap | Cost of the runs (USD) |
|---|---|---|---|
| multimodal_combined_qwen_vl | 680 | 81 | 0.245 |
| multimodal_combined_llama4_maverick | 230 | 56 | 0.212 |
| multimodal_open | 322 | 102 | 0.119 |
| multimodal_strict | 250 | 79 | 0.118 |
| targeted_multimodal | 50 | 49 | 0.021 |
| C | 196 | 203 | 0.017 |
| freeform_B | 231 | 257 | 0.012 |
| B | 228 | 223 | 0.012 |
| D | 195 | 203 | 0.007 |
| targeted_text | 8 | 7 | 0.005 |
| freeform_light | 215 | 217 | 0.001 |

### 5.5 Chunk 5: CIRCUNOVA and SP05 (31 October 2026)

1. Started 12:33, finished 16:52 local time (about 4 hours 19 minutes).
2. 66 of 66 runs ok, no retries, no failed calls, no provider failures; all 66 final outputs pass the final schema validation.
3. No context splits: even CIRCUNOVA (146 pages, 273,909 characters of Markdown) fitted the context of every configuration in one call.
4. Cost USD 1.96 in total, the highest of the chunks, as these are the two longest documents.
5. Grounding warnings: 1,327 on CIRCUNOVA and 188 on SP05. The CIRCUNOVA count is far above that of any other document; its cause is left to the scoring.
6. As in section 5.2, the end to end times of the text configurations include the Docling conversion of the document (649 seconds for CIRCUNOVA).

| Configuration | Mean seconds per run, CIRCUNOVA | Mean seconds per run, SP05 | Cost of the runs (USD) |
|---|---|---|---|
| multimodal_combined_llama4_maverick | 890 | 166 | 0.594 |
| multimodal_combined_qwen_vl | 1,105 | 755 | 0.568 |
| multimodal_open | 587 | 326 | 0.320 |
| multimodal_strict | 498 | 192 | 0.315 |
| C | 655 | 292 | 0.045 |
| freeform_B | 725 | 348 | 0.030 |
| B | 681 | 316 | 0.029 |
| targeted_multimodal | 111 | 57 | 0.028 |
| D | 654 | 291 | 0.022 |
| targeted_text | 42 | 16 | 0.009 |
| freeform_light | 811 | 343 | 0.003 |

### 5.6 Batch total

1. Five chunks, 30 and 31 October 2026, all at commit `1380dc7` and in the same run environment.
2. 330 slots (11 configurations, 10 documents, 3 repetitions): 324 final runs ok, 6 failed (targeted_text and targeted_multimodal on SP03B, section 5.2). 331 runs are stored, as one slot was requeued once (section 5.3).
3. 20 retries in all, every one followed by success. No text input was split on any document; image batches were split only on SP03B (264 calls rejected with HTTP 413 and split, section 5.2).
4. Total cost USD 4.57; 22,194,950 input tokens and 426,962 output tokens.
5. Note of 18 November 2026: items 3 and 4 and the table below count all 331 stored runs, the superseded attempt included. The reported figures count final runs only, and time and cost completed runs only (`EVALUATION_PROTOCOL.md`, sections 5.3 and 6.2): 16 retries in 11 runs; 22,073,526 input and 425,654 output tokens; total cost USD 4.54 (`Final_Results/EVALUATION_RESULTS.md`, section 1).

| Configuration | Final runs ok (of 30) | Cost of all runs (USD) |
|---|---|---|
| multimodal_combined_qwen_vl | 30 | 1.251 |
| multimodal_combined_llama4_maverick | 30 | 1.138 |
| multimodal_open | 30 | 0.854 |
| multimodal_strict | 30 | 0.832 |
| C | 30 | 0.126 |
| targeted_multimodal | 27 | 0.103 |
| freeform_B | 30 | 0.085 |
| B | 30 | 0.082 |
| D | 30 | 0.059 |
| targeted_text | 27 | 0.032 |
| freeform_light | 30 | 0.008 |
