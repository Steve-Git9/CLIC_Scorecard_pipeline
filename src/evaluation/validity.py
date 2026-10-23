"""Run validity: at the first attempt (the raw model reply) and after repair (the final output).

First attempt: every extraction reply of the run, read where its output protocol says the
answer is, must parse as JSON and conform to the shared RAW_SCHEMA, with no repair at all.
    schema    protocols with a schema enforced at decoding time: the whole reply is the answer.
    freeform  free form and unconstrained protocols: the prompt asks for one ```json block,
              so the last such block is the answer; the prose around it is allowed.
Anything else the pipeline does to obtain a JSON object (stripping <think> blocks or stray
fences, searching for braces, cleaning or converting values) counts as repair.

After repair: the final output the pipeline wrote must pass the shared validate_final.
"""

from __future__ import annotations

import json
import re

from jsonschema import Draft202012Validator

from Second_step_CLICpipeline.clic_extract.schema import RAW_SCHEMA, validate_final

PROTOCOLS = ("schema", "freeform")
_VALIDATOR = Draft202012Validator(RAW_SCHEMA)
_JSON_BLOCK = re.compile(r"(?s)```json[ \t]*\r?\n?(.*?)```")


def answer_text(reply: str, protocol: str) -> str | None:
    """The part of a reply that the protocol defines as the answer, or None if absent."""
    if protocol == "schema":
        return reply
    if protocol == "freeform":
        blocks = _JSON_BLOCK.findall(reply)
        return blocks[-1] if blocks else None
    raise ValueError(f"unknown output protocol {protocol!r}, expected one of {PROTOCOLS}")


def check_reply(reply: str | None, protocol: str) -> tuple[bool, str | None]:
    """(valid, reason) for one raw reply, without any repair."""
    if not reply or not reply.strip():
        return False, "empty reply"
    text = answer_text(reply, protocol)
    if text is None:
        return False, "no ```json block in the reply"
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        return False, f"not valid JSON: {exc.msg} at position {exc.pos}"
    errors = sorted(_VALIDATOR.iter_errors(data), key=lambda e: [str(p) for p in e.path])
    if errors:
        where = "/".join(str(p) for p in errors[0].path) or "(root)"
        return False, f"does not conform to the schema at {where}: {errors[0].message}"
    return True, None


def first_attempt_validity(replies: list[str] | None, protocol: str) -> tuple[bool | None, str | None]:
    """(valid, reason) over all extraction replies of a run. None when replies were not saved."""
    if replies is None:
        return None, "raw replies were not saved for this run"
    if not replies:
        return False, "the run produced no reply"
    for i, reply in enumerate(replies, start=1):
        ok, reason = check_reply(reply, protocol)
        if not ok:
            return False, f"reply {i} of {len(replies)}: {reason}"
    return True, None


def after_repair_validity(final: dict | None) -> tuple[bool, list[str]]:
    """(valid, problems) for the final output the pipeline wrote, if any."""
    if final is None:
        return False, ["no final output was written"]
    problems = validate_final(final)
    return not problems, problems
