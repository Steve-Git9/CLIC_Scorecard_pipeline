"""Fitting an input into the model's context: send it whole, split it only when it is rejected.

Every configuration first sends its input exactly as designed. Only when the provider rejects a
request as too large does the caller split that input in two and send each half on its own,
recursively, and merge the partial answers with merge_raw_dicts. A document that fits is
therefore never split, and its run is identical to a run without this module.

Why the provider decides, not a local estimate: each model has its own tokenizer, so a local
count is only a guess. The previous guess (3.5 characters per token) refused documents that fit:
on Docling Markdown the providers counted about 5.6 characters per token. The providers used
here reject an oversized request with an explicit HTTP 400 before any generation, so the
rejection costs nothing, and HTTP 413 means the request body itself was too large.
"""

from __future__ import annotations

import re
from typing import Any

# Phrases providers use when a request does not fit the model's context (checked 2026-10-23 on
# groq, deepinfra and nscale; the others are common wordings of the same error).
_TOO_LARGE_PHRASES = (
    "maximum context length", "reduce the length", "context length", "context_length", "context window",
    "too many tokens", "prompt is too long", "input is too long", "max_model_len", "exceeds the limit",
)
MIN_SPLIT_CHARS = 2000


def is_too_large(exc: Exception) -> bool:
    """True when a BackendError says the request was too large for the request size or context."""
    message = str(exc).lower()
    if message.startswith("http 413"):
        return True
    return message.startswith("http 400") and any(p in message for p in _TOO_LARGE_PHRASES)


def _is_table_line(line: str) -> bool:
    return line.lstrip().startswith("|")


def _is_heading(line: str) -> bool:
    return bool(re.match(r"\s{0,3}#{1,6}\s", line)) or line.startswith("<!-- page ")


def split_text(text: str) -> tuple[str, str] | None:
    """Split a Markdown or page-marked text into two halves of similar length.

    The cut is made at a blank line or a heading, never inside a table, as close to the middle
    as possible; the last heading before the cut is repeated at the top of the second half so it
    keeps its section context. Only when the text has no such place (one huge table) is a table
    cut, between two rows, with its header rows repeated in the second half. Returns None when
    the text is too short to split usefully.
    """
    if len(text) < MIN_SPLIT_CHARS:
        return None
    lines = text.splitlines(keepends=True)
    offsets, pos = [], 0
    for line in lines:
        offsets.append(pos)
        pos += len(line)
    middle = len(text) / 2

    def safe(i: int) -> bool:  # a cut before line i
        if i <= 0 or i >= len(lines):
            return False
        before, here = lines[i - 1], lines[i]
        boundary = here.strip() == "" or _is_heading(here) or before.strip() == ""
        return boundary and not (_is_table_line(before) and _is_table_line(here))

    candidates = [i for i in range(1, len(lines)) if safe(i)]
    if candidates:
        cut = min(candidates, key=lambda i: abs(offsets[i] - middle))
        first, second = "".join(lines[:cut]), "".join(lines[cut:])
        heading = next((lines[j] for j in range(cut - 1, -1, -1) if _is_heading(lines[j])), None)
        if heading and not _is_heading(lines[cut]):
            second = heading.rstrip("\n") + " (continued)\n\n" + second
        return first, second

    # One huge table: cut between rows near the middle and repeat the header rows.
    cut = min(range(1, len(lines)), key=lambda i: abs(offsets[i] - middle))
    start = cut
    while start > 0 and _is_table_line(lines[start - 1]):
        start -= 1
    header = "".join(lines[start:start + 2]) if cut - start > 2 else ""
    return "".join(lines[:cut]), header + "".join(lines[cut:])


def merge_raw_dicts(raw_list: list[Any]) -> dict:
    """Combine the raw extractions of several parts into one, as if the whole input had been
    seen at once. proposal / proposal_facts: first non-null value for each field, in part order.
    partners: every part's list, concatenated; build_final then drops exact repeats by name."""
    proposal: dict[str, Any] = {}
    facts: dict[str, Any] = {}
    partners: list = []
    for raw in raw_list:
        if not isinstance(raw, dict):
            continue
        rp = raw.get("proposal")
        if isinstance(rp, dict):
            for k, v in rp.items():
                if v is not None and proposal.get(k) is None:
                    proposal[k] = v
        rf = raw.get("proposal_facts")
        if isinstance(rf, dict):
            for k, v in rf.items():
                if v is not None and facts.get(k) is None:
                    facts[k] = v
        rpartners = raw.get("partners")
        if isinstance(rpartners, list):
            partners.extend(rpartners)
    return {"proposal": proposal, "proposal_facts": facts, "partners": partners}


_SUMMED = ("seconds", "attempts", "prompt_tokens", "completion_tokens", "cost_usd")


def add_result(run: dict, result: dict) -> None:
    """Accumulate one call's usage into the run record (sums; the last finish reason and model)."""
    for key in _SUMMED:
        if result.get(key) is not None:
            total = (run.get(key) or 0) + result[key]
            run[key] = round(total, 6) if key == "cost_usd" else round(total, 2) if key == "seconds" else total
        else:
            run.setdefault(key, None)
    run["finish_reason"] = result.get("finish_reason")
    run["model_reported"] = result.get("model_reported")
