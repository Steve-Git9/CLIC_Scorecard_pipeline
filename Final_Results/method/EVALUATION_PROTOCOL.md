# Evaluation protocol of the extraction configurations

Status on 18 November 2026. Companion to `EXTRACTION_CONFIGURATIONS.md`, which specifies the eleven configurations themselves. This document describes how the configurations are run, logged and scored, and which outputs the evaluation produces. It describes the method only and contains no results. The scoring has two passes: an automatic pass by fixed rules, and a second pass that applies the author's review of the partner names the rules cannot settle (section 6.4). The record of the conversion and of the run itself is `CONVERSION_AND_DATA_CHECKS.md`; the author's decisions are listed in section 10.

## 1. Sources of truth

For the evaluation, three sources are authoritative, in this order:

1. the scoring rules agreed with the author (Phase 1 and the later decisions recorded here), which define the protocol;
2. the shared JSON schema (`Second_step_CLICpipeline/clic_extract/schema.py`), which defines the fields;
3. the gold sets in `evaluation/gold/`.

Where the schema leaves a field definition ambiguous (type, unit, normalisation), the question is put to the author instead of being decided by the code.

## 2. Documents and gold sets

The document set was replaced on 29 October 2026. The evaluation uses these ten documents:

| Document | Pages | Partners in gold set | Note |
|---|---|---|---|
| Abico_Synth | 40 | 5 | proposal ReCoSE |
| ByggMap | 22 | 7 | |
| CIRCUNOVA | 146 | 21 | |
| CLIMACITIES | 45 | 8 | |
| SP01 | 66 | 9 | proposal LOOPWEAVE |
| SP02 | 41 | 5 | proposal TIDEMESH |
| SP03A | 45 | 6 | proposal RESENSE, clean version |
| SP03B | 45 | 6 | proposal RESENSE, scanned copy of SP03A |
| SP04 | 63 | 7 | proposal MAROFLOW |
| SP05 | 78 | 8 | proposal NIVALIS |

1. The source PDFs are in `data/raw/<document>.pdf`; each has a gold set with exactly the same name, letter case included, `evaluation/gold/<document>.json`, in the final record format (amounts in integer cents, dates as ISO 8601 text, null where the document does not state a value). Every gold set passes the shared final validation. A gold set is paired with its PDF only by this name.
2. Every document except ByggMap is marked as synthetic in its title or name; the status of ByggMap is not recorded. By the author's decision all documents are treated alike: no separate reporting.
3. **SP03A and SP03B** are the same proposal with the same gold set: SP03A is the clean PDF, SP03B a scanned copy whose 45 pages are images without any text layer. The pair is meant to show how each configuration copes with a scanned document:
   1. the Docling conversion of SP03B runs OCR (section 3), so the five text configurations read OCR text;
   2. the combined configurations receive an empty text layer and work from the page images alone;
   3. the targeted configurations cannot locate pages by keywords in an empty text layer and fall back to the model choosing pages from the page map; their selected pages are then read by local OCR.
4. **Amounts in thousands.** Six documents (SP01, SP02, SP03A, SP03B, SP04, SP05) state the partner amounts in their budget tables in thousands of euros, with the scale given only in the table caption or column header. The gold sets store these amounts in full euros, as whole cents. How this is scored is set in section 6.1.
5. In SP05 the partner amounts of the gold set do not add up to the stated total. The gold set is used as it is.

## 3. Input preparation outside the configurations

The five text configurations (B, C, D, freeform_B, freeform_light) read the Docling Markdown of each document; the scorer uses the same Markdown to classify extra partners. The other six configurations read the PDF and need no Markdown.

The Markdown is produced fresh for every document of the current set with `python -m src.evaluation.convert_documents`, before the full run, and stored as `data/markdown/<document>.md`, with the time, speed and details of each conversion in `<document>.conversion.json` and `conversions.csv`. OCR is used only when a document lacks a usable text layer, which applies to SP03B. The conversion was done on 30 October 2026 at commit `1380dc7`, on the author's laptop (AMD Ryzen 5 7520U, processor only, four threads). A comparison with faster hardware is in `DOCLING_SPEED.md`.

## 4. Pilot run

1. Purpose: to check that every configuration works end to end and that every required quantity is logged. Pilot runs are not part of the evaluation, and no prompt, schema or setting is changed because of pilot outputs.
2. Document chosen at random with a fixed seed: seed 20261023, method `random.Random(seed).choice(sorted(documents))`, result CLIMACITIES. Recorded in `evaluation/pilot/pilot_manifest.json`. The pilot was run on the earlier document set; CLIMACITIES is also part of the current set.

## 5. Full run

### 5.1 Design

1. Every configuration is run on all ten documents, three repetitions each: 330 runs.
2. All runs belong to one batch with a new identifier (`batch_<UTC start time>`). Results are written to `evaluation/runs/<batch>/<configuration>/` and are never overwritten: every batch has its own folder and every run file carries its UTC start time. The evaluated batch is `batch_20261030T105636Z`. Two earlier batches, run on the earlier document set during development, are marked as aborted in their manifests and are not part of the evaluation: `batch_20261023T083538Z` (commit `93cc327`) and `batch_20261023T112945Z` (commit `294529c`).
3. The documents are processed two per chunk, in an order drawn once with a fixed seed (seed 20261024, `random.Random(seed).shuffle(sorted(documents))`): CLIMACITIES, SP01, SP03A, SP03B, Abico_Synth, SP02, SP04, ByggMap, CIRCUNOVA, SP05. After every chunk the batch stops and waits for the author's prompt to continue. All chunks run at the same code commit and with the same Python installation.
4. **Interleaving.** Within a chunk, each repetition runs every configuration and document pair once, in a seeded random order (seed `<batch>/chunk<n>/<repetition>`), and the repetitions follow each other. A provider incident therefore affects runs of many configurations, not a block of one, and the three repetitions of a pair are separated in time. The schedule is recorded in the manifest.
5. Runs are executed one at a time, so that their timings never compete for the processor or the network.

### 5.2 Code version and run manifest

The manifest `evaluation/runs/<batch>/manifest.json` records:

1. the code version: the git commit of the code that ran (the commit is recorded per batch). The runner refuses to start when the working tree has uncommitted changes, and refuses to continue a batch on a different commit, so a batch never mixes code versions;
2. the prompt versions: the SHA 256 digest of every prompt text and of the raw schema; each configuration also carries a combined prompt version over the prompts it uses;
3. the price file (`provider_prices(1).csv`) with its SHA 256 digest and, for every provider and model used, the retrieval date and status of its price row; a batch refuses to continue if the price file changes;
4. every setting of every configuration, read from the code;
5. the document order with its seed, and per chunk the documents, the schedule with its seed, the start and end time, and every run with its outcome, retries and provider failures;
6. the start and end time of the batch.

### 5.3 Retries

1. **Call level.** Every model call is attempted at most four times; HTTP 408, 429 and 5xx, network errors and streams that break off are retried after 2, 4 and 8 seconds or the provider's `Retry-After` value (at most 60 seconds). Every attempt is logged with its HTTP status, error and duration.
2. **Run level.** A run that a provider failure still affected (the run failed, or one of its calls failed, with HTTP 408, 429 or 5xx, a network error, a broken stream or an unexpected response) is run again later in the chunk, at least 60 seconds afterwards, at most three attempts per slot. Every attempt is kept and stored; only the last attempt of a slot counts as the result, the earlier ones are marked as superseded. A failure caused by the content (an answer that is not valid JSON, a record that fails the schema) is a result and is not repeated.
3. **Superseded attempts** stay in the database and in the run folder as the raw record, but they are not scored and appear in no output, total or report; only the final attempt of each slot is reported (decision of 31 October 2026).
4. A request rejected as too large for the model's context is not a failure: the input is split and resent (`EXTRACTION_CONFIGURATIONS.md`, section 3.7). Page images rejected as too large (HTTP 413) are split in the same way, down to single pages where needed; such splits are recorded as warnings in the run file and as failed calls in the database, not in the `context_splits` column, which counts text splits only.

### 5.4 What every run logs

1. **Tokens** from the provider's usage fields, per call and summed per run: input, output, reasoning and cached tokens. Where a provider does not report image tokens separately, they are included in the input tokens.
2. **Conversion call.** None exists: the free form and unconstrained answers are converted to JSON locally in Python. The run records `conversion_call: made false, tokens 0`.
3. **Failed calls and retries:** every call, failed or not, with every HTTP attempt.
4. **Wall clock time** from file to final JSON: the configuration's own time (page rendering, table detection, page location, every call, merging) plus the preparation outside it: the recorded Docling conversion time of the document for the five text configurations, the native text extraction for the combined configurations. The targeted configurations run without their page map cache, so page location is always timed. This end to end time is the time reported for every configuration (decision of 31 October 2026); the Docling conversion is therefore included only for the five text configurations, the only ones that read its output. The per run results file also lists the conversion seconds separately.
5. **Cost** per call and per run from the price list: (input tokens minus cached tokens) times the input price, plus cached tokens times the cached price (the input price where none is listed), plus output tokens times the output price, per million tokens. Reasoning tokens are part of the output tokens and are not added twice. Failed calls without usage cost nothing; every successful call of a final run counts, including calls whose answer was discarded.
6. **Raw outputs:** every reply exactly as returned, before any repair (`<run>.replies.json`).

### 5.5 Storage in the database

Every run is stored in the pipeline layer of `data/clic.db` (schema version 2, `sql/schema.sql`) as soon as it ends:

| Table | Content |
|---|---|
| `run_batch` | code commit, prompt digests, price file and dates, manifest path, start and end |
| `document`, `conversion_run` | the source PDF (by content hash) and its Docling conversion |
| `model_config` | configuration name, model, provider, prompt version, every parameter, prices in millionths of a US dollar per million tokens |
| `extraction_run` | batch, document, configuration, repetition, slot attempt, final flag, status, timings, calls, failed calls, attempts, retries, context splits, tokens by type, cost in millionths of a US dollar, schema validity, file paths |
| `extraction_call` | every call with the provider's usage object unchanged and the reply exactly as returned |
| `call_attempt` | every HTTP attempt of every call |
| `extracted_value` | every value of the final record, so each value is traceable to its run |
| `validation_result` | the final schema check and every pipeline warning |

## 6. Scoring

### 6.1 Fields

1. Scored: the nine fields of `proposal` and `proposal_facts` (acronym, title, call identifier, submission date, requested total, TRL start and target, MCRL start and target) and the partner list. Not scored: `extraction_timestamp` and `source_file`.
2. Comparison by exact match after normalisation: amounts as integer cents (an integer is already cents; text is read as euros, with thousands and decimal separators resolved and ambiguous forms invalid); dates as ISO 8601 (unambiguous written forms converted, ambiguous ones such as 03/04/2024 invalid); text with case folded and whitespace collapsed (an empty string counts as null); readiness levels as integers. A value that cannot be normalised never equals anything.
3. **Amounts in a different scale.** No scale is applied in the scoring. An amount copied from a table stated in thousands of euros, without the scale, is a thousand times too small and is a wrong value (decision of 8 November 2026). The prompts of every configuration ask for amounts copied as written, and the post processing reads a scale only when it is written next to the number, not from a caption or header.
4. Outcome of every value:

| Gold value | Extracted value | Outcome |
|---|---|---|
| null | null | correct |
| present | the same after normalisation | correct |
| present | null | miss |
| null | present | unsupported value |
| present | different | wrong value |

A null is therefore correct only when the gold set is also null.

5. Page references are not part of the schema and are not scored.

### 6.2 Validity and failed runs

1. **At the first attempt:** every extraction reply of the run, read where its protocol places the answer, parses as JSON and conforms to the raw schema, with no repair at all. For schema enforced configurations the whole reply must be the JSON object; for free form and unconstrained configurations the answer is the last fenced `json` block. A reply without that block counts as invalid at the first attempt even when its JSON is otherwise valid; this was confirmed by the author as acceptable, because the field scores are taken from the final record. A run with several calls is valid at the first attempt only if every reply is.
2. **After repair:** the final record written by the pipeline passes the shared final validation.
3. **Failed runs.** A run that ends without a final record, or whose record is not valid after repair, counts as a failure:
   1. in every accuracy measure it has every scored field counted as a miss and every gold partner as missed, even a field whose gold value is null. Its field accuracy, partner recall and fully correct value are 0, and it has no amount accuracy (no partner was matched). Failed final runs are not repeated and there is no separate view that leaves them out (decision of 31 October 2026);
   2. it is left out of every time and cost figure: means, ranges, totals, cost per document and the cost in the cost of pass (decision of 9 November 2026). Time and cost therefore describe completed runs only.

### 6.3 Partners

1. **Matching** by normalised name only (case folded, whitespace collapsed). The gold set is the only reference; the CLIC partner register is not used.
2. **Partner recall:** matched gold partners divided by gold partners. **Amount accuracy:** matched partners whose amount equals the gold amount, divided by matched partners.
3. **Every extracted partner that matches no gold partner is classified:**

| Class | Rule | Error |
|---|---|---|
| duplicate | repeats a gold partner already matched, or is a whole word fragment of an already matched gold name | yes |
| supported extra | the name appears in the Docling Markdown of the document (entities decoded, emphasis and escapes removed, whitespace collapsed, case folded) | no, counted as a reviewer decision |
| unsupported extra | neither the name nor any distinctive word of it appears in the document | yes |
| unsure | anything the rules cannot settle (section 6.4) | half in the first pass, settled in the second |

4. **Sum check:** the sum of the extracted amounts of the matched partners is compared with the total stated in the document (the gold total); separately it is recorded whether adding the amounts of supported extras makes a sum that matched the total deviate from it.

### 6.4 Two scoring passes: automatic, then with the author's review

Exact matching cannot settle every partner name: a model may write the right organisation slightly differently from the gold set (an abbreviation added, a country appended, a shortened name). The scoring therefore runs in two passes over the same final runs. No model is called again in either pass, and the scalar fields are scored identically in both; only the unsure partner names, and the amounts that depend on them, differ.

#### 6.4.1 First pass: automatic scoring with half scores (agreed 23 October 2026)

The first pass runs without any human intervention. When the scorer cannot decide whether an extracted partner name is right, it gives half of the score, marks the case, and lists it for review.

| Unsure case | Possible truths | Half score |
|---|---|---|
| The name could be a variant of a gold partner nobody matched (for example "Nowhere" for "Nowhere University") | it is that partner, or it is an extra | the gold partner counts as half found and half missed; its amount counts half, as correct or wrong |
| The name contains the name of a gold partner that is already matched | it is a duplicate, or a different organisation | half a duplicate |
| The name contains the name of a gold partner nobody matched | it is that partner, or it is an extra | as the first row |
| Only part of the name appears in the document | a supported extra (not an error) or an unsupported one (an error) | half an unsupported extra |

Implementation (`src/evaluation/partners.py`, tests in `tests/test_half_scores.py`):

1. An extracted name is unsure, and receives these values, in four cases:
   1. **variant:** it is a whole word part of, or contains, the name of a gold partner that no extracted name matched exactly. The gold partner counts 0.5 found and 0.5 missed; the extracted amount is compared with the gold amount and its outcome counts 0.5; the name counts 0.5 as an extra in the over inclusion rate. If another unsure name in the same run already took the half match of that gold partner, the name counts as half a duplicate instead.
   2. **contains_matched:** it contains the name of a gold partner that is already matched: half a duplicate; it counts 1 as an extra.
   3. **partial_name:** the whole name is not in the Docling Markdown but a distinctive word of it is: half a supported extra and half an unsupported extra; it counts 1 as an extra.
   4. **no_markdown:** no Docling Markdown exists to check against: as partial_name.
2. Counts can be fractional: partner recall, amount accuracy, error counts and the over inclusion rate may contain halves, for example 2.5 errors.
3. The errors of a run are split into certain errors and errors that come only from unsure names. The fully correct value is 0 when the run is a failure or has a certain error, 0.5 when it has no certain error but contains an unsure name, and 1 otherwise. Fully correct shares and the cost of pass use these values.
4. The sum check uses only partners matched with certainty.
5. Every half score is marked: each run, error log row and extras log row states whether it contains an unsure item.
6. The first pass writes the review list `review_list.csv` (every occurrence, with document, run, name, case and the related gold partner) and `review_decisions_template.csv` (each distinct document and name once, with an empty decision column).

#### 6.4.2 The author's review

1. The author reviews every distinct unsure name of the template once per document, against the gold set and, where needed, the source document, and marks it:
   1. **y:** the name is the related gold partner, written differently;
   2. **x:** the name is not correct.
2. The marks are converted into the scorer's decisions in `review_decisions.csv` in the results folder, which keeps the author's mark in the column `author_mark`:

| Mark | Decision | Effect |
|---|---|---|
| y | `gold:<gold partner name>`, the single related gold partner of the template | a certain match with that gold partner, whose amount is then scored in full; a certain duplicate if that partner is already matched in the run |
| x | `unsupported_extra` | a certain extra partner that is not correct: a full error |

3. The scorer also accepts the decision `supported_extra` (a real organisation named in the document that is not a partner, not an error); the author's marks do not use it, because "not correct" is an error.
4. A decision applies to every run of that document in which the name (normalised as for matching) is unsure; it never changes a name the rules settle with certainty. An unknown decision or gold partner stops the scorer. A template row without a decision keeps its half score.
5. The review is done by one reviewer, the author, who also built the gold sets.

#### 6.4.3 Second pass: scoring with the review applied

1. The scorer is run again on the same final runs with `review_decisions.csv` in the results folder. It applies the decisions instead of the half scores; with every unsure name decided, no half scores remain and every fully correct value is 0 or 1.
2. The digest of the decisions file is recorded in the scoring manifest. The scorer is deterministic: the same outputs and the same decisions always give the same scores.
3. **The second pass gives the final results of the evaluation.** The first pass is kept for comparison: it shows what the fixed rules alone give, and the difference between the two passes shows the effect of the human review. The first pass results are kept in `backup/<batch>_provisional_scores/` (the results folder and every per run score file) and published in `Final_Results/results_first_pass/`; the second pass writes to `evaluation/results/<batch>/`, published in `Final_Results/results_second_pass_final/`.

### 6.5 Run and document level

1. **Fully correct document (run):** every scored scalar field correct, every gold partner matched with the correct amount, and no unsupported extra or duplicate. Supported extras are allowed. Values 0, 0.5 or 1 in the first pass, 0 or 1 in the second (section 6.4).
2. **Field errors per run:** misses, wrong values, unsupported values, unsupported extras and duplicates, each counted and summed. Supported extras are counted separately as reviewer decisions.
3. Only the final attempt of each slot is scored and reported (section 5.3).

## 7. Outputs (*Phase 4*)

All outputs go to `evaluation/results/<batch>/`, written by `python -m src.evaluation.score_batch --batch <batch>`, which also writes `<run>.score.json` next to every scored run and `scoring_manifest.json` (scorer commit, digests of the gold sets, the Markdown and the decisions file, the spot check seed). The scorer refuses to run on uncommitted code unless told otherwise, and records the commit either way. Both scoring passes (section 6.4) produce the same set of outputs.

Definitions used by the outputs:

1. **Field accuracy:** the share of the nine scalar fields scored correct in a run. Partners are measured separately by partner recall and amount accuracy (section 6.3).
2. **Per document value** of a configuration: the mean of its three final runs on that document. **Summary mean:** the mean of its ten per document values; **range:** their minimum and maximum. Amount accuracy is undefined for a run without a matched partner and is then left out of the means. Time and cost leave out failed runs (section 6.2), so for a document on which every run of a configuration failed, that configuration has no time or cost value.
3. **Time:** the end to end seconds of section 5.4. **Cost:** the cost of the final run in US dollars. Both over completed runs only.
4. **Contrast differences** are the varied configuration minus the reference configuration (for example, freeform_B minus B).
5. **Spot check sample:** seed `spotcheck/<batch>`; per configuration `random.Random(seed).sample(runs, 2)`, with the runs sorted by document and repetition, one generator for all configurations in alphabetical order.
6. **Document codes:** D01 to D10 in alphabetical order of the document names, case folded; the key is `document_codes.csv` in the results folder.

### 7.1 Full files, with document names and values

1. **Per run results (CSV):** one row per configuration, document and run, with validity at the first attempt and after repair; field accuracy, misses, wrong values and unsupported values; partner recall and amount accuracy; counts of supported extras, unsupported extras and duplicates; the sum check; the fully correct value and the field errors; tokens by type, cost and wall clock time with the Docling conversion seconds; the unsure marker.
2. **Configuration summary (CSV):** means and ranges per configuration over all ten documents, with:
   1. **consistency:** the share of items with the same value across the three runs of a document, over the nine scalar fields plus one item for the partner list (the same set of names and amounts); a failed run counts as not the same;
   2. **over inclusion rate:** all extra partners (supported, unsupported, duplicates and unsure) divided by all extracted partners;
   3. **cost per document:** the mean cost of a completed run on a document;
   4. **cost of pass:** the cost per document divided by the share of fully correct runs (failed runs included in that share as 0); when no run is fully correct the value is written as "not defined", never as a number.
3. **Contrast table (CSV):** per document differences for each planned contrast, using the mean of the three runs per document, for field accuracy, partner recall, amount accuracy, fully correct share, cost and time. Statistics are descriptive; no significance tests. For the three way contrast the pairwise differences D minus B, C minus D and C minus B are shown. A column lists the other differences between the configurations of each contrast, so that no difference is read as caused by one factor alone.

| Contrast | Configurations | Intended factor | Other differences found in Phase 0 |
|---|---|---|---|
| Model size, text | B, D, C | model | B is another model family and provider, thinking disabled against low reasoning effort; C and D differ only in the model |
| Output protocol | B against freeform_B | output protocol | the free form prompt also asks for a written walk through of the fields and the partner table |
| Model, free form | freeform_light against freeform_B | model | provider, max_tokens 16000 against 3000, model generation (Qwen3 against Qwen3.5), extra fields |
| Output constraint | multimodal_strict against multimodal_open | output constraint | max_tokens 3000 against 6000; the open prompt asks for a row by row walk through |
| Context selection, text | C against targeted_text | context selection | input source (Docling Markdown against page text, parsed tables and OCR), prompt, identifier hints, page picking call, reconciliation and identifier filling after the answer |
| Context selection, with images | multimodal_combined_qwen_vl against targeted_multimodal | context selection | protocol (unconstrained against schema enforced), max_tokens, prompt, batching and merge, reconciliation, OCR |
| Model, combined | multimodal_combined_qwen_vl against multimodal_combined_llama4_maverick | model | provider and context window |

4. **Error log (CSV):** every wrong field with configuration, document, run, field name and error class (miss, wrong value, unsupported value, unsupported extra, duplicate), its weight and the unsure marker.
5. **Extras log (CSV):** every extra partner with its class.
6. **Frontier plot (PNG):** field accuracy against cost per document, one point per configuration, with its range as the minimum to maximum of its per document means, over all ten documents. The configurations that no other configuration beats on both accuracy and cost are marked, labelled as descriptive.
7. **Spot check sample:** two runs per configuration chosen at random with a fixed seed, with output, gold set and scores side by side, for the author's manual check of the scorer: for each sampled run the author compares the extracted values with the gold values and confirms that each outcome and class given by the scorer is right.
8. **Review list and decisions template:** every unsure partner name of the first pass (section 6.4.1).
9. **Readable report:** one document with real names, written to be read: the batch overview (code version, dates, number of runs, total cost and time of the completed runs, decisions applied), the configuration summary, per configuration what it got right and wrong, per document the wrong values beside the gold values, the contrasts, the frontier plot and the unsure cases.

### 7.2 Shareable versions

Copies of the configuration summary, the contrast table, the error log and the extras log that contain no extracted values, partner names or amounts: field names, classes and metrics only. The frontier plot, which shows only configuration names and metrics, is copied as well. Folder: `evaluation/results/<batch>/shareable/`. Document names are replaced by neutral codes (D01 to D10); the key from codes to names is `document_codes.csv` in the results folder. They were made when the results were still private and remain as a coded view of the same figures.

## 8. Confidentiality and publication

1. Documents are sent only to the providers named in `EXTRACTION_CONFIGURATIONS.md`, through the Hugging Face router, with the author's authorisation.
2. Published with the code, as a replication package (decision of 18 November 2026): the source PDFs and their Docling Markdown of nine of the ten documents, the ten gold sets, every file of the evaluated batch's run folder (run logs, raw replies, final records, scores, traces, free form answers, manifest), the final and the first pass results, the price file and the method documents. Abico_Synth is published in everything except the document itself: its PDF and its Docling Markdown are withheld because the document contains structures that are part of CLIC's internal knowledge; its gold set, run outputs and results are published. In place of its Markdown, `data/markdown/Abico_Synth.terms.json` records, for every partner name any run extracted, whether the name and each distinctive word of it occur in the document (`src/evaluation/document_terms.py`); the scorer uses it when the Markdown is absent and reaches the same classes (section 6.3).
3. Never published: the database, the backups, the earlier aborted batches, the pilot outputs, the real CLIC partner register, the access token and the assistant files. The `.gitignore` is a whitelist: a file is published only when it is named there.
4. Results are traceable: the manifests record the commit of the code that produced and scored them, and the digests of the gold sets, the Markdown and the decisions file.

## 9. Known limitations of the method

1. The contrasts are not single factor comparisons (section 7.1, item 3); differences are reported descriptively with their confounds.
2. Image tokens are not reported separately by every vision provider; where they are not, they are part of the input tokens.
3. Deepinfra offers several pricing tiers; the usage data does not show which tier was billed, and the standard tier price is used.
4. A null is correct only against a null gold value; fields that are often null in the gold sets (the readiness levels) therefore credit configurations that leave them empty.
5. The review of unsure partner names (section 6.4.2) is done by a single reviewer who also built the gold sets; there is no second reviewer and no agreement measure.
6. SP03B depends on OCR in three different places (Docling for the text configurations, page images for the combined ones, local OCR for the targeted ones); its results measure the configurations together with that OCR.
7. The Docling conversion runs on a four core laptop processor without a supported graphics card, so the end to end times of the five text configurations depend on that hardware (`DOCLING_SPEED.md`).
8. Amounts stated in thousands of euros (section 2, item 4) are scored as wrong when the scale is not applied (section 6.1, item 3). This affects every configuration alike and lowers amount accuracy and the fully correct values; it is treated as a point for discussion and a possible improvement, not corrected in the scoring.

## 10. Decisions of the author

### 10.1 Decisions of 31 October 2026

1. **Time:** the end to end time is reported for every configuration; it includes the Docling conversion only for the five text configurations, which are the only ones that read it (section 5.4).
2. **Failed runs:** runs that end without a final record are not repeated and count as failures under rule 6.2.3 in every accuracy measure.
3. **Superseded attempts:** only final runs are reported; superseded attempts appear in no output, total or report (section 5.3).
4. **Backup:** before scoring, the database and the run folder of the batch were copied to `backup/batch_20261030T105636Z_before_scoring/`.

### 10.2 Decisions of 8 November 2026

1. **Review of unsure partner names:** the author marked every unsure name of the first pass y or x, and the batch was scored a second time with these marks applied (section 6.4). The second pass gives the final results; the first pass results were copied to `backup/batch_20261030T105636Z_provisional_scores/` before the second pass.
2. **Amounts in thousands:** kept as wrong values in the scoring, with no supplementary figure that accepts the missing scale; the issue is treated in the discussion chapter (section 6.1, item 3).

### 10.3 Decisions of 9 November 2026

1. **Time and cost of failed runs:** failed runs are left out of every time and cost figure; they still count as failures in every accuracy measure (section 6.2, item 3).
2. **Protocol:** this document describes the method only; results are reported elsewhere.
3. **Statistics:** results are reported descriptively (section 7.1, item 3).

### 10.4 Decisions of 18 November 2026

1. **Replication package:** the code is published together with the documents, gold sets, run outputs and results of the evaluated batch, except the PDF and the Docling Markdown of Abico_Synth (section 8).
2. **Pilot interface:** the web application offers all eleven evaluated configurations, for the pilot at CLIC. The three repetitions of the evaluation were run with the batch runner, not through the interface.
