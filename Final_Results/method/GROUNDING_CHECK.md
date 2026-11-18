# The grounding check

Status on 28 October 2026. Code: `postprocess.build_final`, with `_norm_doc`, `_grounded_text` and `_grounded_amount`, in `Second_step_CLICpipeline/clic_extract/postprocess.py`.

## 1. What it is

The grounding check asks one question about every extracted text value and amount: does this value occur, as written, in the text the model was given? A value that does not occur produces a warning. The check never changes a value, never nulls it, never fails a run and plays no part in the scoring. It is a flag for the reviewer, nothing more.

## 2. How it works

### 2.1 The reference text

The check compares against the text the configuration actually sent to the model, not against the PDF:

| Configurations | Reference text |
|---|---|
| B, C, D, freeform_B, freeform_light | the whole Docling Markdown of the document (also when the input was split into parts) |
| multimodal_combined_qwen_vl, multimodal_combined_llama4_maverick | the embedded text layer of the PDF, extracted with pymupdf |
| targeted_text, targeted_multimodal | the context sent: identifier hints, the selected page texts and the parsed tables |
| multimodal_strict, multimodal_open | none: the model sees only page images, so the check is skipped |

### 2.2 Text values

Checked: acronym, title, call identifier and every partner name, when not null.

1. The reference text is normalised once: the Markdown emphasis characters `*`, `_` and `` ` `` are removed, every run of whitespace (spaces, line breaks, table padding) becomes one space, and the text is case folded.
2. The value is normalised in exactly the same way.
3. The value is grounded if the normalised value is a substring of the normalised reference text. There are no word boundaries: a value found inside a longer word also counts.

Warning, for example: `partner 'Fictional Labs Oy' not found verbatim in the document`.

### 2.3 Amounts

Checked: the requested total and every partner amount, as the model wrote them, and only when they were successfully converted to cents.

1. From the reference text all whitespace, non breaking spaces and apostrophes are removed. Case and Markdown characters are left as they are, since only digits and separators matter.
2. From the amount as written (for example "EUR 2,200,125.00") the first numeric token is taken, by the regular expression `\d[\d.,\s'’  ]*\d|\d`, and the same characters are removed from it ("2,200,125.00").
3. The amount is grounded if that token is a substring of the reference text. An amount without any digit is treated as grounded.

Warning, for example: `requested_total 'EUR 2,200,125.00' not found in the document`.

### 2.4 Not checked

Submission date, readiness levels (integers) and nulls are not checked, nor are amounts that could not be converted (those already produce their own warning).

### 2.5 Where the result goes

Every warning is written to the run file (`warnings` in `<run>.run.json`) and to the database as a `validation_result` row with rule code `pipeline_warning`, severity warning.

## 3. Limitations

1. **Values in images.** Text inside a raster image, a scanned page or a chart is not in the text layer or the Docling Markdown. A configuration that reads such a value correctly from the page images (the combined configurations, targeted_multimodal) receives a warning anyway. This is the main reason for false warnings, and the reason the check must never act on a value.
2. **Conversion errors.** A table that Docling or pymupdf garbled, a word split by hyphenation across a line break, or a ligature can hide a value that is in the document.
3. **Reformatted values.** If the model writes a value differently from the document (another separator convention, "EUR 2.2 million" for "2,200,000", an expanded abbreviation), the value is flagged although it is correct. The prompts ask the model to copy values as written, which keeps this rare.
4. **Coincidental matches.** A substring test without word boundaries can pass by chance: a short acronym or a short amount such as "100" can occur anywhere in a long document. A grounded value is therefore not proof of a correct value, and an amount is checked only by its first numeric token.
5. **Reference, not truth.** The check shows whether the value occurs in the text the model received, not whether it is the right value for that field: a real partner name taken from the wrong table passes.

## 4. Why it is still useful

1. **Hallucination signal where the model reads only text.** For the five text configurations and targeted_text, the reference text is the model's entire input. A value that does not occur in it cannot have been copied from it: it was invented, altered or reformatted. Here the check is a strong and precise signal, and these are six of the eleven configurations.
2. **It is free and deterministic.** It needs no second model call and no human, runs on every run in milliseconds, and gives the same result every time.
3. **It cannot remove a correct value.** Because it only warns, a value read correctly from an image is kept; the cost of a false warning is a moment of a reviewer's attention, never a lost value. This answers the concern about data in images.
4. **It directs human review.** In production, where no gold set exists, the warnings show the reviewer which values to check first: a flagged partner name in a text configuration deserves a look at the source; a flagged amount from a combined configuration may simply come from an image.
5. **It separates sources in the combined configurations.** A warning there means the value came from the images (or was invented), not from the text layer. Read together with the run's images, it tells the reviewer where to look.

## 5. Relation to the evaluation

The grounding check is not part of the scoring. The scorer compares every value with the gold set, which is independent of any text extraction, so values read from images are scored on their merits. The scorer uses a similar text search for one purpose only: deciding whether an extra partner (one not in the gold set) is named in the Docling Markdown (supported) or not (unsupported); cases it cannot decide are scored with half values.
