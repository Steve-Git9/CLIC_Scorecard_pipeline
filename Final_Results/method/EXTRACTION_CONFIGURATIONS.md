# Extraction configurations: technical description

Status of the code base on 23 October 2026. Package: `Second_step_CLICpipeline/clic_extract`.

## 1. Purpose and scope

This document specifies the extraction phase of the CLIC KPI pipeline: how a proposal document is turned into one structured JSON record by a language model, in each of the eleven configurations implemented. It describes, for every configuration, the model, the provider, the input preparation, the request, the generation settings, the output protocol, the prompt, the post processing and the files written.

Out of scope, and described elsewhere: the conversion of PDF files to Docling Markdown (the text configurations read its output), the SDG classification, and the evaluation of the configurations.

## 2. The eleven configurations at a glance

| # | Configuration | Model | Provider | Input to the model | Output protocol | max_tokens | Model specific settings |
|---|---|---|---|---|---|---|---|
| 1 | B | `Qwen/Qwen3.5-9B` | deepinfra | Docling Markdown, whole document, one call | schema enforced | 3000 | thinking disabled (`chat_template_kwargs.enable_thinking: false`) |
| 2 | C | `openai/gpt-oss-120b` | groq | Docling Markdown, whole document, one call | schema enforced | 3000 | `reasoning_effort: low` |
| 3 | D | `openai/gpt-oss-20b` | groq | Docling Markdown, whole document, one call | schema enforced | 3000 | `reasoning_effort: low` |
| 4 | freeform_B | `Qwen/Qwen3.5-9B` (configuration B copied at run time) | deepinfra | Docling Markdown, whole document, one call | free form, converted to JSON in Python | 3000 | thinking disabled |
| 5 | freeform_light | `Qwen/Qwen3-4B-Instruct-2507` | nscale | Docling Markdown, whole document, one call | free form, converted to JSON in Python | 16000 | none |
| 6 | multimodal_strict | `Qwen/Qwen3-VL-235B-A22B-Instruct` | deepinfra | every page as a PNG image, batches of 10 pages with 1 page overlap | schema enforced | 3000 | none |
| 7 | multimodal_open | `Qwen/Qwen3-VL-235B-A22B-Instruct` | deepinfra | as multimodal_strict | unconstrained, converted to JSON in Python | 6000 | none |
| 8 | multimodal_combined_qwen_vl | `Qwen/Qwen3-VL-235B-A22B-Instruct` | deepinfra | full embedded text layer plus images of the pages with pictures or tables, batches of 10 images with 1 image overlap, the full text repeated in every batch | unconstrained, converted to JSON in Python | 6000 | none |
| 9 | multimodal_combined_llama4_maverick | `meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8` | novita | as configuration 8 | unconstrained, converted to JSON in Python | 6000 | none |
| 10 | targeted_text | `openai/gpt-oss-120b` (configuration C copied at run time) | groq | at most 8 locally selected pages as text, parsed and arithmetically verified tables, identifier hints | schema enforced | 3000 | `reasoning_effort: low` |
| 11 | targeted_multimodal | `Qwen/Qwen3-VL-235B-A22B-Instruct` | deepinfra | as targeted_text, plus the images of at most 6 of those pages | schema enforced | 3000 | none |

All configurations use temperature 0 and the same field definitions in their prompts, and every answer, whatever its protocol, passes through the same post processing and the same final validation (sections 3.5 and 3.6).

Context windows, as declared by the router at selection: `Qwen/Qwen3.5-9B` 262,144 tokens; `openai/gpt-oss-120b` and `openai/gpt-oss-20b` 131,072; `Qwen/Qwen3-4B-Instruct-2507` 262,144; `Qwen/Qwen3-VL-235B-A22B-Instruct` 262,144; `meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8` 1,048,576.

## 3. Common foundations

### 3.1 Extracted fields and the two schema shapes

The model extracts exactly these fields (module `schema.py`):

| Group | Field | Type in the final record | Meaning |
|---|---|---|---|
| proposal | `proposal_acronym` | text or null | project acronym, copied as written |
| proposal | `proposal_title` | text or null | full project title, copied as written |
| proposal | `call_identifier` | text or null | call, topic or tender identifier |
| proposal | `submission_date` | ISO 8601 date text (`YYYY-MM-DD`) or null | submission date |
| proposal_facts | `requested_total_cents` | integer or null | total requested funding, whole euro cents |
| proposal_facts | `trl_start`, `trl_target` | integer 1 to 9 or null | Technology Readiness Level at start and target |
| proposal_facts | `mcrl_start`, `mcrl_target` | integer 1 to 9 or null | Market Cluster Readiness Level at start and target |
| partners[] | `partner_name` | non empty text | organisation name as written, one entry per organisation, document order |
| partners[] | `requested_cents` | integer or null | that partner's requested funding, whole euro cents |
| metadata | `extraction_timestamp`, `source_file` | text | added by the pipeline, never extracted |

Two shapes exist on purpose:

1. **RAW_SCHEMA**, what the model is asked to return. Monetary values are text copied as written, with currency and separators (`requested_total`, `requested`), because language models are unreliable at arithmetic and at separator conventions. The readiness levels are requested as integers. Every object is closed: all keys are required and `additionalProperties` is false, as strict structured output requires. Every scalar is nullable except `partner_name`. The schema is reproduced in Appendix B.
2. **The final record**, built by `postprocess.build_final` from the raw answer: amounts converted to integer cents, dates normalised to ISO 8601, metadata added. It is checked by `schema.validate_final` (section 3.6). This is the record every configuration writes.

### 3.2 Field definitions shared by every prompt

Every system prompt ends with the same block, `FIELD_DEFINITIONS` (Appendix A.1). It sets three general rules (use only what the document explicitly states, never guess or calculate; use null for anything missing or uncertain and never an empty string, zero, false, "N/A" or "unknown"; copy names exactly as written) and defines each field, including the instruction to copy amounts as written and not to convert, round or add numbers. What differs between configurations is only the opening of the system prompt: what form the document takes (Markdown, page images, text plus images, selected pages) and how the answer must be given (bare JSON, or prose followed by one JSON block).

### 3.3 Model access

**Router.** All calls go to the Hugging Face Inference Providers router, an OpenAI compatible endpoint: `POST https://router.huggingface.co/v1/chat/completions`. The client (`backends.py`) uses the Python standard library only (`urllib`).

**Provider pinning.** The request's `model` field is `"<model id>:<provider>"`, which pins the call to one provider; automatic routing such as `:fastest` is never used, because structured output support and serving behaviour differ between providers and routing could change the host between runs. For configurations B, C and D the pin is stored in `arms.json` and is set with `python -m clic_extract.pin set --arm <B|C|D> --provider <name>`, which reads the router's public model list and accepts a provider only if its status is live, it lists structured output support and it lists a price. Pin dates: B 16 October 2026 (moved from together to deepinfra), C 30 September 2026, D 11 October 2026. The vision model, the two combined models and the free form light model are defined as constants in `multimodal.py` and `freeform.py`. The router lists novita as the only provider of `meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8`.

**Authentication.** The Hugging Face token is read from the `HF_TOKEN` environment variable (loaded from `.env`). It is checked for format and verified once per session against `https://huggingface.co/api/whoami-v2`; it is sent only in the `Authorization: Bearer` header and is never printed, logged or written to disk. Requests carry an explicit `User-Agent: clic-extract/0.1`, because the default Python agent is blocked by some providers' firewalls.

**Request body.** `backends.build_request` produces:

```json
{
  "model": "<model id>:<provider>",
  "messages": [{"role": "system", "content": "..."}, {"role": "user", "content": "..."}],
  "temperature": 0,
  "max_tokens": "<per configuration>",
  "response_format": {"type": "json_schema",
                      "json_schema": {"name": "proposal_extraction", "schema": "<RAW_SCHEMA>", "strict": true}},
  "<model specific extra fields, merged at the top level>": "..."
}
```

Every request sets `"stream": true` and `"stream_options": {"include_usage": true}`: the answer is streamed as server sent events while it is generated, and the client rebuilds the complete reply, with the token usage carried by the last chunk. Streaming is required because the router ends any request whose complete answer takes longer than 120 seconds (HTTP 504), which long documents exceed; it does not change what the model receives or generates. A provider that ignores the stream request and answers in one piece is read the same way.

`response_format` is present only in the schema enforced configurations; the free form and unconstrained configurations omit it entirely. No `top_p`, `seed` or penalty parameters are sent. Temperature 0 makes decoding greedy in principle; providers may still show small run to run variation (batching, floating point), which the configurations do not control.

**Model specific extra fields.** Configuration B and freeform_B send `"chat_template_kwargs": {"enable_thinking": false}`, which disables the Qwen3.5 thinking mode so that the answer is produced directly. C, D and targeted_text send `"reasoning_effort": "low"`: gpt oss always reasons before answering, and the effort level bounds the length of that reasoning; the reasoning tokens count against the same `max_tokens` budget as the answer and are returned separately from the answer content. The vision models, the combined models and freeform_light send no extra field.

**Transport, retries and errors.** One call is attempted at most four times. HTTP 408, 429, 500, 502, 503 and 504 and network errors are retried after a pause of 2, 4 and 8 seconds, or the provider's `Retry-After` value when given (at most 60 seconds). Any other HTTP status ends the call at once. The read timeout is 600 seconds per attempt. A stream that breaks off before the answer is complete, or reports an error part way, is retried like a network error. HTML error pages from provider firewalls are summarised to their title and code. A call records its model time (`seconds`), the number of attempts, the provider's token usage (`prompt_tokens`, `completion_tokens`), the finish reason and the model name the provider reports. An optional recording hook (`backends.record_calls`) can capture every call with every attempt, its HTTP status and the provider's full usage object, including reasoning, image and cached token counts where the provider reports them; it never alters a request or a reply.

### 3.4 Output protocols

| Protocol | Configurations | Request | Prompt instruction | How the JSON is obtained |
|---|---|---|---|---|
| schema enforced | B, C, D, multimodal_strict, targeted_text, targeted_multimodal | `response_format` json_schema with RAW_SCHEMA, `strict: true` | "Return ONE JSON object that follows the provided schema. No commentary, no markdown fences." | the provider constrains decoding to the schema; the reply is the JSON object |
| free form, converted to JSON | freeform_B, freeform_light | no `response_format` | work through the document in prose, then give one JSON object in a single fenced `json` block, in a shape spelled out in the prompt | Python: `postprocess.extract_json` |
| unconstrained, converted to JSON | multimodal_open, multimodal_combined_qwen_vl, multimodal_combined_llama4_maverick | no `response_format` | work through the partner budget table row by row in prose, then give one JSON object in a single fenced `json` block | Python: `postprocess.extract_json` |

The free form and the unconstrained protocols are technically the same mechanism; they differ in the prompt. The free form prompt (text configurations) asks the model to note where every field group is stated and spells out the complete JSON skeleton. The unconstrained prompts (image configurations) ask for the row by row partner table walk through and refer to "the shape below" without giving a skeleton: the shape is conveyed by the field definitions only.

There is no second model call in any configuration: the conversion of a free form answer to JSON is deterministic Python. `extract_json` removes `<think>` blocks, takes the last fenced `json` block when one exists (so braces in the prose cannot be mistaken for the answer), and otherwise takes the text from the first `{` to the last `}`, then parses it with `json.loads`. The same function is applied to schema enforced replies, where it simply parses the object.

### 3.5 Post processing (`postprocess.build_final`)

Every parsed answer, whatever its configuration, goes through the same deterministic clean up. Every doubtful value becomes null and produces a warning; nothing is inferred.

1. **Text fields** (acronym, title, call identifier, partner names): whitespace collapsed. Values such as "", "null", "none", "n/a", "na", "not stated", "not specified", "not available", "unknown" and lone dash characters become null.
2. **Amounts** (`parse_amount_to_cents`): currency words and symbols removed (EUR, euro, euros, €, $, £); spaces, non breaking spaces and apostrophes between digits removed; multipliers applied (million, mio, mln, m, thousand, k); trailing `.-` style endings removed. Separator rules: when both "." and "," occur, the last one is the decimal separator and the other must form regular groups of three digits; a single "," followed by exactly three digits is a thousands separator; a single "." followed by exactly three digits is ambiguous and becomes null; repeated separators must form regular groups of three. Negative amounts, values that are not a whole number of cents, booleans and unparseable text become null. An integer from the model is read as euros. Arithmetic uses `Decimal`, never floats.
3. **Dates** (`normalise_date`): an ISO 8601 prefix (`YYYY-MM-DD`, optionally followed by a time) is kept if it is a real calendar date; ordinal suffixes are removed; the formats "16 October 2024", "16 Oct 2024", "October 16, 2024", "Oct 16, 2024", "October 16 2024", "2024/10/16" and "16.10.2024" are converted; "a/b/yyyy" is read day first when the first number exceeds 12 or both are equal, month first when the second exceeds 12, and is otherwise ambiguous and null.
4. **Readiness levels** (`normalise_int`): integers, integral floats and digit strings accepted; booleans, other values and anything outside 1 to 9 become null. A start level greater than its target produces a warning.
5. **Partners**: an entry without a name is dropped; a repeated name (case insensitive) is dropped; order is preserved.
6. **Grounding checks** (warnings only, values unchanged): each acronym, title, call identifier and partner name must occur verbatim in the input text (after removal of Markdown emphasis characters and whitespace normalisation, case insensitive), and each amount's digit string must occur in the input text. The text checked against is the text the model received: the Docling Markdown, the embedded text layer, or the selected page texts with the parsed tables. For multimodal_strict and multimodal_open there is no text, so these checks are skipped.
7. **Sum check** (warning only): when every partner has an amount and the total is known, the partner amounts must add up to the total.
8. **Metadata**: `extraction_timestamp` (UTC, ISO 8601) and `source_file` are added.

### 3.6 Final validation (`schema.validate_final`)

The final record must have exactly the keys `proposal`, `proposal_facts`, `partners` and `metadata`; each object exactly its expected keys; text fields text or null; amounts and levels integers (booleans excluded) or null; readiness levels within 1 to 9; partner names non empty text. A record that fails is not written and the run is recorded as failed, with the raw reply saved.

### 3.7 Inputs larger than the model's context (`fit.py`)

No configuration refuses a document for its length. Every configuration first sends its input whole, exactly as designed; a document that fits is never split, so its run is identical to a run without this mechanism. Only when the provider rejects a request as too large, with HTTP 413 (request body) or HTTP 400 carrying a context length message ("maximum context length", "reduce the length", "context length", "context window", "too many tokens", "prompt is too long", "input is too long", "max_model_len", "exceeds the limit"), is the input split in two and each half sent on its own, recursively, and the answers merged by the rule of section 3.8.

| Configurations | What is split |
|---|---|
| B, C, D, freeform_B, freeform_light | the Markdown text (`split_text`) |
| multimodal_strict, multimodal_open | the batch of page images, in half |
| multimodal_combined_qwen_vl, multimodal_combined_llama4_maverick | the batch of page images first; once a single image is left, the text, keeping that image |
| targeted_text, targeted_multimodal | the selected pages, in two groups (not expected: at most eight pages are sent) |

`split_text` cuts at a blank line or a heading as close to the middle as possible, never between two table rows; the last heading before the cut is repeated at the top of the second half with "(continued)". Only a text consisting of one table larger than the context is cut inside the table, between two rows, with the header and separator rows repeated. Texts under 2,000 characters are not split.

The provider, not a local estimate, decides whether a request fits, because each model has its own tokenizer. A probe with fictional filler text on 23 October 2026 showed that groq, deepinfra and nscale reject an oversized request with an explicit HTTP 400 before any generation and return no usage, and that none truncates silently. The local estimate previously used (3.5 characters per token, refusal above 80 percent of the context) was removed: on Docling Markdown the providers counted about 5.6 characters per token, so it refused documents that fit.

Every split is recorded in the run file (`context_splits`, `parts`, one warning per split).

### 3.8 Batching and merging

Configurations that make several extraction calls for one document (the batched image configurations, and any configuration after a split) merge the partial answers with `fit.merge_raw_dicts` before post processing: for every scalar field the first non null value in document order; the partner lists concatenated in order, after which `build_final` drops exact repeats by name. Post processing and validation then run once on the merged answer, exactly as for a single call. A batch whose reply cannot be parsed, or whose call fails for a reason other than size, is recorded as a warning and the remaining batches still contribute; the run fails only if no batch produced a usable reply.

### 3.9 Files written by a run

For a document `<document>` and the UTC start time `<UTC>` (format YYYYMMDDTHHMMSSZ), each configuration writes into its own folder:

| File | Content | Written by |
|---|---|---|
| `<document>_<UTC>.json` | the final record | every configuration, successful runs |
| `<document>_<UTC>.run.json` | the run record (below) | every configuration, every run |
| `<document>_<UTC>.replies.json` | every extraction reply exactly as returned, before any repair, a JSON list in call order; written for failed runs too | every configuration |
| `<document>_<UTC>.raw.txt` | the raw reply or replies of a failed run | failed runs |
| `<document>_<UTC>.freeform.txt` | the free form answer (reasoning plus reply), parts separated by "=== next part ===" | freeform_B, freeform_light |
| `<document>_<UTC>.trace.json` | located pages with scores, parsed tables with every arithmetic check, the partner budget table, identifier hints, reconciliation per partner | targeted_text, targeted_multimodal |

The run record always contains: `arm` (configuration name), `model`, `provider`, `source_file`, `started_utc`, `status` (ok or failed), `error`, `warnings`, `seconds` (model time, summed over calls), `total_seconds` (wall clock of the configuration's own function), `attempts`, `prompt_tokens`, `completion_tokens`, `cost_usd` (indicative, from prices stored with the configuration; the dated price list is kept separately), `finish_reason`, `model_reported`, `replies_file`, `output_file`. Configuration specific fields are listed in section 4.

## 4. The configurations in detail

### 4.1 Configuration B: light text model, schema enforced

| Item | Value |
|---|---|
| Model | `Qwen/Qwen3.5-9B`, 9 billion parameter model of the Qwen3.5 family |
| Provider | deepinfra, pinned in `arms.json` on 16 October 2026 |
| Context | 262,144 tokens |
| Input | the Docling Markdown of the document (`data/markdown/<document>.md`), whole |
| Messages | system: `SYSTEM_PROMPT`; user: "Extract the data from this document." followed by the document inside `<document>` tags |
| Generation | temperature 0, `max_tokens` 3000, `chat_template_kwargs.enable_thinking` false |
| Protocol | schema enforced (RAW_SCHEMA, strict) |
| Calls | one (more only after a context split) |
| Entry point | `python -m clic_extract.run_extract --arm B --input <file or folder of .md>` |
| Run record extras | `free_form` false, `context_splits`, `parts` |

Design intent: the light text model and the reference point of the output protocol contrast with freeform_B.

### 4.2 Configuration C: large text model, schema enforced

| Item | Value |
|---|---|
| Model | `openai/gpt-oss-120b`, open weight mixture of experts reasoning model (about 117 billion total, about 5 billion active parameters per token) |
| Provider | groq, pinned on 30 September 2026 |
| Context | 131,072 tokens |
| Input | Docling Markdown, whole |
| Messages | as configuration B |
| Generation | temperature 0, `max_tokens` 3000 (reasoning plus answer), `reasoning_effort` low |
| Protocol | schema enforced |
| Calls | one (more only after a context split) |
| Entry point | `python -m clic_extract.run_extract --arm C --input ...` |

Design intent: the largest text model, the accuracy ceiling of the text configurations. Its settings are also those of targeted_text.

### 4.3 Configuration D: alternative light text model, schema enforced

| Item | Value |
|---|---|
| Model | `openai/gpt-oss-20b`, smaller model of the same family (about 21 billion total, about 3.6 billion active parameters) |
| Provider | groq, pinned on 11 October 2026 |
| Context | 131,072 tokens |
| Input, messages, generation, protocol | identical to configuration C |
| Entry point | `python -m clic_extract.run_extract --arm D --input ...` |

Design intent: the light model of the gpt oss family; C and D differ only in the model.

### 4.4 Configuration freeform_B: model B with the free form protocol

| Item | Value |
|---|---|
| Model and provider | configuration B's entry, read from `arms.json` at run time and used unchanged: `Qwen/Qwen3.5-9B` on deepinfra |
| Input | the same Docling Markdown file as B |
| Messages | system: `OPEN_TEXT_SYSTEM_PROMPT`; user: identical to B |
| Generation | temperature 0, `max_tokens` 3000, thinking disabled, as B |
| Protocol | free form, converted to JSON in Python; no `response_format` |
| Calls | one model call; the conversion makes no call |
| Entry point | `python -m clic_extract.freeform --arm freeform_B --input <file.md>` |
| Run record extras | `free_form` true, `freeform_file` |

The request differs from B's only in the system prompt and the absence of `response_format`; a unit test (`FreeformBContrastTests`) asserts this. With 3000 output tokens, prose before the JSON block can exhaust the budget on long documents; such a run fails and is recorded as failed. This risk is accepted so that the generation settings stay identical to B.

### 4.5 Configuration freeform_light: very light model, free form

| Item | Value |
|---|---|
| Model | `Qwen/Qwen3-4B-Instruct-2507`, 4 billion parameter non thinking instruct model of the Qwen3 family |
| Provider | nscale, chosen from the router's live list on 21 October 2026; it replaced `ibm-granite/granite-4.2-8b` the same day so that the model is clearly lighter than B's |
| Context | 262,144 tokens |
| Input | Docling Markdown, whole |
| Messages | system: `OPEN_TEXT_SYSTEM_PROMPT`; user: identical to B |
| Generation | temperature 0, `max_tokens` 16000, no extra fields |
| Protocol | free form, converted to JSON in Python |
| Entry point | `python -m clic_extract.freeform --input <file.md>` |

`max_tokens` 16000 leaves room for prose before the JSON block (the 8 billion parameter model used before needed about 9,800 output tokens on a 38 page document). In practice the 4 billion parameter model writes little prose.

### 4.6 Configuration multimodal_strict: page images, schema enforced

| Item | Value |
|---|---|
| Model | `Qwen/Qwen3-VL-235B-A22B-Instruct`, vision language mixture of experts model (235 billion total, 22 billion active parameters) |
| Provider | deepinfra |
| Context | 262,144 tokens |
| Input preparation | every page rendered with pymupdf at zoom 2.0 (about 144 DPI) to PNG; pages split into batches of 10 with an overlap of 1 page, so a table crossing a page boundary is complete in at least one batch |
| Messages, per batch | system: `VISION_SYSTEM_PROMPT`; user: the text "Extract the data from this document. Each image is one page, in order." followed by the batch's images as `image_url` parts with base64 PNG data URLs |
| Generation | temperature 0, `max_tokens` 3000 |
| Protocol | schema enforced, per batch |
| Calls | one per batch (a 45 page document: 5 calls) |
| Merge | first non null value per field in batch order, partner lists concatenated (section 3.8) |
| Grounding checks | none (no text input) |
| Entry point | `clic_extract.multimodal.run_one_multimodal(..., strict=True)` |
| Run record extras | `strict`, `batch_size`, `overlap`, `batches`, `context_splits` via warnings |

Choice of model: `deepseek-ai/DeepSeek-V4.1-Flash` was tried first (11 October 2026) and correctly read 1 of 30 partner amounts on a real document; it was replaced on 12 October 2026 by the largest dedicated vision language model on the router. PNG was kept over JPEG because it measured smaller for flat, high contrast pages. Resolution 72 DPI was tried and was too low to read table text reliably.

### 4.7 Configuration multimodal_open: page images, unconstrained

Identical to multimodal_strict in model, provider, rendering, batching, overlap and merge, with three differences:

1. no `response_format`;
2. system prompt `OPEN_VISION_SYSTEM_PROMPT`, which asks the model to work through the partner budget table row by row in prose before answering in one fenced `json` block;
3. `max_tokens` 6000 (`OPEN_MAX_TOKENS`), to leave room for the prose.

Design intent: whether the decoding constraint itself costs accuracy on a task that needs several reasoning steps (matching each table row's name to its amount), as reported by Tam et al. (2024, "Let Me Speak Freely?").

### 4.8 Configuration multimodal_combined_qwen_vl: text and images together

| Item | Value |
|---|---|
| Model and provider | `Qwen/Qwen3-VL-235B-A22B-Instruct` on deepinfra |
| Input preparation | (a) the embedded text layer of every page, extracted with pymupdf `get_text`, each page preceded by `<!-- page N -->`; no OCR and no layout analysis; (b) the pages that contain an embedded raster image or a table detected by pymupdf `find_tables` are rendered to PNG at zoom 2.0; pages without either are sent as text only |
| Batching | the rendered images in batches of 10 with an overlap of 1; the full document text is sent again with every batch; a document with no such page gets a single text only call |
| Messages, per batch | system: `COMBINED_VISION_SYSTEM_PROMPT`; user: "Here is the document's text, extracted with layout analysis:" followed by the text inside `<document_text>` tags, then "Below are the same document's pages rendered as images, in page order. Use the text as your primary source, and check the images directly for anything the text extraction may have missed or gotten wrong.", then the batch's images |
| Generation | temperature 0, `max_tokens` 6000 |
| Protocol | unconstrained, converted to JSON in Python |
| Merge | as section 3.8 |
| Grounding checks | against the embedded text layer |
| Entry point | `clic_extract.multimodal.run_one_combined(pdf, text, out_dir, "qwen_vl", ...)` |
| Run record extras | `pages_total`, `pages_with_images`, `batches`, `calls`, `batch_size`, `overlap`, `context_splits` |

Note on the wording: the prompt and the user message state that the text was "extracted with layout analysis". In this configuration it is the plain embedded text layer, which does not preserve table structure; the images are meant to supply the table reading. The wording is kept unchanged.

Design intent: to reproduce the way a general purpose chat assistant receives a PDF (extracted text and page images in one context), with selective images to keep the request size bounded.

### 4.9 Configuration multimodal_combined_llama4_maverick

Identical to configuration 8 in input preparation, batching, prompts, generation settings (temperature 0, `max_tokens` 6000, no extra fields), protocol and merge, with a different model:

| Item | Value |
|---|---|
| Model | `meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8`, natively multimodal mixture of experts model (17 billion active parameters, 128 experts), FP8 weights |
| Provider | novita, the only provider the router lists for this model |
| Context | 1,048,576 tokens |
| Entry point | `run_one_combined(..., "llama4_maverick", ...)` |

Chosen on 14 October 2026 as the strongest vision capable model with known pricing on the router. At selection it was recorded as lacking strict structured output on the router (the listing of 23 October 2026 reports support); both combined configurations use the unconstrained protocol so that they differ only in the model.

### 4.10 Configuration targeted_text: located pages, parsed tables, schema enforced

The model never sees the whole document. Cheap and exact work is done locally first; the model is called only on the pages that matter.

| Step | What happens | Model call |
|---|---|---|
| 1. Triage and page map (`pagemap.py`) | page count, outline (bookmarks), embedded characters per page; a page with fewer than 100 characters and an embedded picture is flagged as a scan; per page the first three lines (at most 120 characters each), keyword hits per field group and the number of tables pymupdf detects | none |
| 2. Location | every page scored for four field groups (proposal, budget, partners, readiness): 2 points per distinct keyword, 0.25 per occurrence (at most 20), 3 if a keyword is in the page's first lines, 3 if an outline entry with a keyword points to the page, 4 for a detected table (budget and partners), 3 for page 1 and 1.5 for page 2 (proposal); a page without keyword hits scores 0 except for the proposal group; the best three pages kept, and of those only pages scoring at least half of the best | none |
| 3. Identifier hints (`cover.py`) | the largest text on the cover page (font size from pymupdf, lines within 90 percent of the largest size, boilerplate such as "Confidential" dropped), acronym candidates from it, labelled lines anywhere ("Acronym:", "Title:", "Call:", "Topic identifier:"), and tokens shaped like a call identifier (three or more dash separated parts, one of them a year); the pages of these hints join the proposal group, which then keeps its first three pages in page order | none |
| 4. Page picking fallback | only for a group keywords could not place: the model reads the compact page map (one line per page) with `PAGE_PICK_PROMPT` and returns at most three pages per group | one, only if needed, no `response_format` |
| 5. Tables (`tables.py`) | pymupdf `find_tables` on the budget and partner pages; each table verified arithmetically: in every numeric column the rows since the previous totals row or section heading must add up to the next totals row, and a column headed "total" must equal the sum of the row's other amounts; a column is verified only if every check passes, a table if one column is; the partner budget table is chosen among tables with a verified amount column, preferring headers saying requested, grant or funding applied | none |
| 6. Shortlist | the best page of every group first, then the remaining located pages by score, at most 8 pages, sent in page order | none |
| 7. Text and OCR | embedded text of each shortlisted page; scanned pages read with local OCR (rapidocr), only those pages | none |
| 8. Extraction | one call: identifier hints, the page texts each marked `<!-- page N -->`, and the parsed tables as Markdown labelled VERIFIED or NOT VERIFIED (verified tables and every table on a budget page) | one, schema enforced |
| 9. Post processing | `build_final`, grounding against the text actually sent | none |
| 10. Reconciliation | every partner amount compared with the verified table rows: confirmed (equals a verified cell on the partner's row), filled (the model gave none; the verified partner budget cell is used, with a warning), mismatch (warning), unchecked | none |
| 11. Identifier filling | an acronym, title or call identifier the model left null is filled from an unambiguous hint, with a warning naming the source | none |

| Item | Value |
|---|---|
| Model and provider | configuration C's entry from `arms.json`: `openai/gpt-oss-120b` on groq |
| Generation | temperature 0, `max_tokens` 3000, `reasoning_effort` low |
| Messages | system: `TARGETED_SYSTEM_PROMPT`; user: "Extract the data from these selected pages of the document." followed by the context inside `<document_pages>` tags |
| Protocol | schema enforced |
| Entry point | `python -m clic_extract.targeted --mode text --input <file or folder of .pdf>`; `--dry-run` performs steps 1 to 3 and 5 without any call |
| Page map cache | optional, keyed by the SHA 256 of the PDF (`output/targeted/_pagemap_cache`); disabled by passing `cache_dir=None` |
| Run record extras | `mode`, `pages_total`, `pages_sent`, `scanned_pages`, `ocr_pages`, `images_sent`, `located`, `located_by` (keywords or model), `tables_found`, `tables_verified`, `page_map_cached`, `steps` (seconds per step), `calls`, `identifiers_filled`, `partners_confirmed_by_table`, `context_splits`, `trace_file` |

The targeted prompt explains the page markers, the meaning of VERIFIED, and that the cover heading counts as explicitly stated for the title and the acronym. Its worked example ("Advanced Biocomposites with Circular Design ABiCo") is the cover heading of one of the project's documents.

### 4.11 Configuration targeted_multimodal

Identical to targeted_text in every local step, the prompt, the protocol and the post processing, with two differences:

1. model `Qwen/Qwen3-VL-235B-A22B-Instruct` on deepinfra, temperature 0, `max_tokens` 3000, no extra fields;
2. the images of the first six shortlisted pages (in page order), rendered at zoom 2.0, are attached to the extraction call after the text.

The page picking fallback, when needed, also uses the vision model.

## 5. Parameter matrix

| Configuration | Temperature | max_tokens | Extra fields | response_format | System prompt | Text input | Images | Calls per document |
|---|---|---|---|---|---|---|---|---|
| B | 0 | 3000 | enable_thinking false | yes | SYSTEM_PROMPT | Docling Markdown | none | 1 |
| C | 0 | 3000 | reasoning_effort low | yes | SYSTEM_PROMPT | Docling Markdown | none | 1 |
| D | 0 | 3000 | reasoning_effort low | yes | SYSTEM_PROMPT | Docling Markdown | none | 1 |
| freeform_B | 0 | 3000 | enable_thinking false | no | OPEN_TEXT_SYSTEM_PROMPT | Docling Markdown | none | 1 |
| freeform_light | 0 | 16000 | none | no | OPEN_TEXT_SYSTEM_PROMPT | Docling Markdown | none | 1 |
| multimodal_strict | 0 | 3000 | none | yes | VISION_SYSTEM_PROMPT | none | all pages, 10 per batch, overlap 1 | (pages minus 1) ÷ 9, rounded up, at least 1 |
| multimodal_open | 0 | 6000 | none | no | OPEN_VISION_SYSTEM_PROMPT | none | all pages, 10 per batch, overlap 1 | (pages minus 1) ÷ 9, rounded up, at least 1 |
| multimodal_combined_qwen_vl | 0 | 6000 | none | no | COMBINED_VISION_SYSTEM_PROMPT | embedded text layer, full, every batch | pages with pictures or tables, 10 per batch, overlap 1 | (flagged pages minus 1) ÷ 9, rounded up, at least 1 |
| multimodal_combined_llama4_maverick | 0 | 6000 | none | no | COMBINED_VISION_SYSTEM_PROMPT | as above | as above | as above |
| targeted_text | 0 | 3000 | reasoning_effort low | yes | TARGETED_SYSTEM_PROMPT | at most 8 selected pages, parsed tables, hints | none | 1, plus 1 page picking call if needed |
| targeted_multimodal | 0 | 3000 | none | yes | TARGETED_SYSTEM_PROMPT | as targeted_text | at most 6 of the selected pages | 1, plus 1 page picking call if needed |

## 6. Deliberate choices and known characteristics

1. **Amounts as written.** The model never converts or adds amounts; Python converts them to integer cents with explicit, documented separator rules, and doubtful amounts become null rather than guessed.
2. **Null over guessing.** Every prompt and every post processing rule prefers null to an inferred value; post processing never fills a value from elsewhere, except the targeted reconciliation and identifier filling, which use verified tables and unambiguous hints and always leave a warning.
3. **One field definition block.** All eleven prompts share `FIELD_DEFINITIONS`, so the configurations differ in model, input and protocol, not in what they are asked to extract.
4. **Batch merge rule.** In batched configurations the first non null value in document order wins; a value stated correctly later in the document cannot override an earlier wrong one.
5. **Text repeated per batch.** The combined configurations resend the full text with every image batch, so their input token count grows with the number of image batches times the length of the text.
6. **Images only when useful.** The combined configurations attach images only for pages with pictures or detected tables; a page rendered as text only relies on the embedded text layer, which can miss text inside vector graphics.
7. **Output budget shared with reasoning.** For C, D and targeted_text the 3000 token budget covers reasoning and answer; for freeform_B the prose shares 3000 tokens with the JSON block.
8. **Prompt wording kept as built.** The combined prompt's "extracted with layout analysis" and the open vision prompt's reference to "the shape below" are recorded here as characteristics and are not changed, so that every configuration runs as defined.
9. **Confidentiality.** Documents are sent only to the providers named above, through the Hugging Face router, with the author's authorisation; the token never leaves the request header.

## Appendix A. Prompts, verbatim from `clic_extract/prompts.py`
Each system prompt is the opening shown, followed by the shared field definitions of A.1. The user turn of each configuration is given in section 4.

### A.1 FIELD_DEFINITIONS (shared by every extraction prompt)

```text
GENERAL RULES
- Use only what the document explicitly states. Never guess, infer, calculate or fill gaps.
- If a value is not stated or you are not sure, use null. Never use "", 0, false, "N/A" or "unknown" for a missing value.
- Copy names and titles exactly as written (keep acronyms and capitalisation).

proposal
- proposal_acronym: the project acronym. proposal_title: the full project title.
- call_identifier: the call/topic/tender identifier (for example HORIZON-CL5-2026-D3-01).
- submission_date: the submission date as YYYY-MM-DD, or null if it is missing or you cannot be exact.

proposal_facts
- requested_total: the total amount requested (the total grant / funding requested), COPIED AS WRITTEN including
  currency and separators (for example "EUR 2,200,125.00"). Do not convert, round or add up numbers.
- trl_start / trl_target: Technology Readiness Level at the start and at the end of the project, integers 1-9.
- mcrl_start / mcrl_target: Market Cluster Readiness Level at the start and the target, integers 1-9.

partners  (one entry per organisation taking part in the project, in document order)
- partner_name: the organisation name exactly as written.
- requested: that partner's requested grant / funding, COPIED AS WRITTEN with currency and separators. Do not convert
  or add up numbers. Null if the document gives no amount for that partner.
```

### A.2 SYSTEM_PROMPT (B, C, D)

```text
You extract structured data from a grant-proposal document written in Markdown.
Return ONE JSON object that follows the provided schema. No commentary, no markdown fences.

[FIELD_DEFINITIONS, A.1]
```

### A.3 OPEN_TEXT_SYSTEM_PROMPT (freeform_B, freeform_light)

```text
You read a grant-proposal document written in Markdown.

First, in plain prose, note where the document states the acronym, title, call identifier and submission date, the readiness levels, and the partner budget table. Work through that table row by row, writing each partner's name exactly as shown together with the amount on the same row.

Then write your final answer as ONE JSON object inside a single ```json code block, with nothing after it, in exactly this shape:
{"proposal": {"proposal_acronym": null, "proposal_title": null, "call_identifier": null, "submission_date": null}, "proposal_facts": {"requested_total": null, "trl_start": null, "trl_target": null, "mcrl_start": null, "mcrl_target": null}, "partners": [{"partner_name": "...", "requested": null}]}

[FIELD_DEFINITIONS, A.1]
```

### A.4 VISION_SYSTEM_PROMPT (multimodal_strict)

```text
You extract structured data from a grant-proposal document shown to you as a sequence of page images, in page order. Read the images directly; there is no separate text version.
Return ONE JSON object that follows the provided schema. No commentary, no markdown fences.

[FIELD_DEFINITIONS, A.1]
```

### A.5 OPEN_VISION_SYSTEM_PROMPT (multimodal_open)

```text
You read a grant-proposal document shown to you as a sequence of page images, in page order. Read the images directly; there is no separate text version.

First, in plain prose, find the partner budget table and work through it row by row: write out each partner's name exactly as the table shows it, together with the amount on that same row, before writing anything else. Take your time matching each name to the right row and amount.

When you have gone through every row, write your final answer as ONE JSON object that follows the shape below, inside a single ```json code block, with nothing after it.

[FIELD_DEFINITIONS, A.1]
```

### A.6 COMBINED_VISION_SYSTEM_PROMPT (both combined configurations)

```text
You read a grant-proposal document. You are given two things together, the way a general-purpose document-aware assistant normally receives a PDF: the document's text, already extracted with layout analysis, and the same document's pages rendered as images, in page order. Use the text as your primary source; check the images directly wherever the text may be incomplete, garbled, or where a number, stamp, table or handwriting needs visual confirmation.

First, in plain prose, find the partner budget table and work through it row by row: write out each partner's name exactly as shown, together with the amount on that same row, before writing anything else. Take your time matching each name to the right row and amount.

When you have gone through every row, write your final answer as ONE JSON object that follows the shape below, inside a single ```json code block, with nothing after it.

[FIELD_DEFINITIONS, A.1]
```

### A.7 TARGETED_SYSTEM_PROMPT (targeted_text, targeted_multimodal)

```text
You extract structured data from a grant-proposal document. You are NOT given the whole document: only the few pages that were located as relevant (each marked <!-- page N -->), and the tables on those pages, already parsed exactly by a table parser. A table marked VERIFIED has columns that add up exactly to its totals row, so its numbers are reliable; prefer them over the running text. Decide which table and which column holds each partner's requested grant or funding, and copy those cells as written.
If page images are attached, they show the same pages; use them where the text or tables look garbled.
IDENTIFIER HINTS lists what a local script found: the largest text on the cover page, labelled lines and call identifier patterns. The project's name printed as the main heading of the cover page counts as explicitly stated: use it for proposal_title, and take proposal_acronym from it (the short capitalised name, for example the last word of 'Advanced Biocomposites with Circular Design ABiCo'). If the cover shows only a short name, use that name for both the acronym and the title. Take call_identifier only from a call, topic or programme identifier the pages actually state; otherwise null.
Return ONE JSON object that follows the provided schema. No commentary, no markdown fences.

[FIELD_DEFINITIONS, A.1]
```

### A.8 PAGE_PICK_PROMPT (page picking fallback of the targeted configurations)

```text
You are given a page map of a grant-proposal document: one line per page with its first lines and keyword hits. Keyword search did not find the pages for some field groups. For each requested group, pick at most 3 page numbers most likely to contain that information.
Groups: proposal = acronym, title, call identifier, submission date; budget = total and per-partner requested funding; partners = list of participating organisations; readiness = TRL and MCRL levels.
Reply with ONE JSON object only, for example {"pages": {"readiness": [4, 12]}}. Use an empty list if no page fits.
```

## Appendix B. RAW_SCHEMA, verbatim from `clic_extract/schema.py`

Sent as `response_format.json_schema.schema` with `strict: true` in the schema enforced configurations.

```json
{
  "type": "object",
  "properties": {
    "proposal": {
      "type": "object",
      "properties": {
        "proposal_acronym": {
          "type": [
            "string",
            "null"
          ]
        },
        "proposal_title": {
          "type": [
            "string",
            "null"
          ]
        },
        "call_identifier": {
          "type": [
            "string",
            "null"
          ]
        },
        "submission_date": {
          "type": [
            "string",
            "null"
          ]
        }
      },
      "required": [
        "proposal_acronym",
        "proposal_title",
        "call_identifier",
        "submission_date"
      ],
      "additionalProperties": false
    },
    "proposal_facts": {
      "type": "object",
      "properties": {
        "requested_total": {
          "type": [
            "string",
            "null"
          ]
        },
        "trl_start": {
          "type": [
            "integer",
            "null"
          ]
        },
        "trl_target": {
          "type": [
            "integer",
            "null"
          ]
        },
        "mcrl_start": {
          "type": [
            "integer",
            "null"
          ]
        },
        "mcrl_target": {
          "type": [
            "integer",
            "null"
          ]
        }
      },
      "required": [
        "requested_total",
        "trl_start",
        "trl_target",
        "mcrl_start",
        "mcrl_target"
      ],
      "additionalProperties": false
    },
    "partners": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "partner_name": {
            "type": "string"
          },
          "requested": {
            "type": [
              "string",
              "null"
            ]
          }
        },
        "required": [
          "partner_name",
          "requested"
        ],
        "additionalProperties": false
      }
    }
  },
  "required": [
    "proposal",
    "proposal_facts",
    "partners"
  ],
  "additionalProperties": false
}
```

## Appendix C. Location keywords of the targeted configurations (`clic_extract/pagemap.py`)

Keywords of four letters or fewer made of letters only are matched on word boundaries; the others as substrings; all case insensitive.

| Field group | Keywords |
|---|---|
| proposal | `title`, `acronym`, `call`, `topic`, `submission`, `deadline`, `project plan`, `proposal` |
| budget | `budget`, `total costs`, `total cost`, `personnel`, `requested`, `grant`, `funding applied`, `funding`, `eur`, `€`, `total` |
| partners | `partner`, `consortium`, `beneficiary`, `participant`, `coordinator`, `research institute`, `companies` |
| readiness | `trl`, `technology readiness`, `mcrl`, `market readiness`, `readiness level` |
