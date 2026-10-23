"""Prompts for the extraction call.

The field-level definitions (FIELD_DEFINITIONS) are identical for every arm, text,
strict vision, or open vision, so all of them stay directly comparable. What differs
is the opening instruction: what form the document takes, and whether the model must
answer in bare JSON (strict arms, enforced at decoding time by response_format) or may
reason in prose before writing JSON (the open multimodal path, enforced only by the
instruction itself - see clic_extract.multimodal's strict=False option).
"""

FIELD_DEFINITIONS = """GENERAL RULES
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
"""

# Kept for anything that still imports the old name.
FIELD_RULES = "Return ONE JSON object that follows the provided schema. No commentary, no markdown fences.\n\n" + FIELD_DEFINITIONS

SYSTEM_PROMPT = (
    "You extract structured data from a grant-proposal document written in Markdown.\n"
    "Return ONE JSON object that follows the provided schema. No commentary, no markdown fences.\n\n"
    + FIELD_DEFINITIONS
)

VISION_SYSTEM_PROMPT = (
    "You extract structured data from a grant-proposal document shown to you as a sequence of page images, "
    "in page order. Read the images directly; there is no separate text version.\n"
    "Return ONE JSON object that follows the provided schema. No commentary, no markdown fences.\n\n"
    + FIELD_DEFINITIONS
)

# "Open" path: no response_format constraint at the API level (see backends.build_request,
# schema=None). Explicitly invites working through the partner table in prose first, since
# forcing bare JSON immediately can cost a model some of its ability to work through a task
# step by step (Tam et al., 2024, "Let Me Speak Freely?"). The field definitions, and the
# instruction that the final answer must still be one JSON object, stay identical to the
# strict prompts so the output remains comparable and parseable by the same code.
OPEN_VISION_SYSTEM_PROMPT = (
    "You read a grant-proposal document shown to you as a sequence of page images, in page order. "
    "Read the images directly; there is no separate text version.\n\n"
    "First, in plain prose, find the partner budget table and work through it row by row: write out "
    "each partner's name exactly as the table shows it, together with the amount on that same row, "
    "before writing anything else. Take your time matching each name to the right row and amount.\n\n"
    "When you have gone through every row, write your final answer as ONE JSON object that follows "
    "the shape below, inside a single ```json code block, with nothing after it.\n\n"
    + FIELD_DEFINITIONS
)

# "Combined" path: text and page images are sent together, in one request, the way a general-
# purpose provider's own chat interface receives a PDF (extracted text plus page images, packaged
# together into one context) - see multimodal.build_combined_messages. No response_format constraint
# here either, for the same reason as the open path: the strongest model available for this path on
# the router does not support strict structured output, and free-form reasoning is the closer match
# to how a standard chat interface would actually answer.
COMBINED_VISION_SYSTEM_PROMPT = (
    "You read a grant-proposal document. You are given two things together, the way a general-purpose "
    "document-aware assistant normally receives a PDF: the document's text, already extracted with "
    "layout analysis, and the same document's pages rendered as images, in page order. Use the text as "
    "your primary source; check the images directly wherever the text may be incomplete, garbled, or "
    "where a number, stamp, table or handwriting needs visual confirmation.\n\n"
    "First, in plain prose, find the partner budget table and work through it row by row: write out "
    "each partner's name exactly as shown, together with the amount on that same row, before writing "
    "anything else. Take your time matching each name to the right row and amount.\n\n"
    "When you have gone through every row, write your final answer as ONE JSON object that follows "
    "the shape below, inside a single ```json code block, with nothing after it.\n\n"
    + FIELD_DEFINITIONS
)


def build_messages(document_text):
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": "Extract the data from this document.\n\n<document>\n" + document_text + "\n</document>",
        },
    ]


# "Targeted" path (clic_extract.targeted): the model never sees the whole document, only the few
# pages located locally for each field group, plus the tables on those pages already parsed by a
# table parser and checked arithmetically. The field definitions stay identical to every other arm.
TARGETED_SYSTEM_PROMPT = (
    "You extract structured data from a grant-proposal document. You are NOT given the whole document: "
    "only the few pages that were located as relevant (each marked <!-- page N -->), and the tables on those "
    "pages, already parsed exactly by a table parser. A table marked VERIFIED has columns that add up exactly "
    "to its totals row, so its numbers are reliable; prefer them over the running text. Decide which table and "
    "which column holds each partner's requested grant or funding, and copy those cells as written.\n"
    "If page images are attached, they show the same pages; use them where the text or tables look garbled.\n"
    "IDENTIFIER HINTS lists what a local script found: the largest text on the cover page, labelled lines and "
    "call identifier patterns. The project's name printed as the main heading of the cover page counts as "
    "explicitly stated: use it for proposal_title, and take proposal_acronym from it (the short capitalised "
    "name, for example the last word of 'Advanced Biocomposites with Circular Design ABiCo'). If the cover shows "
    "only a short name, use that name for both the acronym and the title. Take call_identifier only from a call, "
    "topic or programme identifier the pages actually state; otherwise null.\n"
    "Return ONE JSON object that follows the provided schema. No commentary, no markdown fences.\n\n"
    + FIELD_DEFINITIONS
)

PAGE_PICK_PROMPT = (
    "You are given a page map of a grant-proposal document: one line per page with its first lines and "
    "keyword hits. Keyword search did not find the pages for some field groups. For each requested group, "
    "pick at most 3 page numbers most likely to contain that information.\n"
    "Groups: proposal = acronym, title, call identifier, submission date; budget = total and per-partner "
    "requested funding; partners = list of participating organisations; readiness = TRL and MCRL levels.\n"
    'Reply with ONE JSON object only, for example {"pages": {"readiness": [4, 12]}}. Use an empty list if no '
    "page fits."
)


# "Free-form" text path (clic_extract.freeform): a very light model answers without any
# response_format constraint, in prose first, then one JSON block; postprocess.extract_json and
# build_final convert it, exactly as for the open multimodal path. The JSON skeleton is spelled out
# because a small model cannot lean on a schema enforced at decoding time.
OPEN_TEXT_SYSTEM_PROMPT = (
    "You read a grant-proposal document written in Markdown.\n\n"
    "First, in plain prose, note where the document states the acronym, title, call identifier and "
    "submission date, the readiness levels, and the partner budget table. Work through that table row "
    "by row, writing each partner's name exactly as shown together with the amount on the same row.\n\n"
    "Then write your final answer as ONE JSON object inside a single ```json code block, with nothing "
    "after it, in exactly this shape:\n"
    '{"proposal": {"proposal_acronym": null, "proposal_title": null, "call_identifier": null, '
    '"submission_date": null}, "proposal_facts": {"requested_total": null, "trl_start": null, '
    '"trl_target": null, "mcrl_start": null, "mcrl_target": null}, '
    '"partners": [{"partner_name": "...", "requested": null}]}\n\n'
    + FIELD_DEFINITIONS
)


def build_open_messages(document_text):
    return [
        {"role": "system", "content": OPEN_TEXT_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": "Extract the data from this document.\n\n<document>\n" + document_text + "\n</document>",
        },
    ]
