"""Schemas and constants for the proposal extraction.

Two shapes exist on purpose:

* RAW_SCHEMA   - what the model is asked to return. Money is plain text "as written";
                 the model never does arithmetic.
* FINAL shape  - the JSON specified in the brief (amounts in whole cents). Built by
                 postprocess.build_final().

Extracted fields are exactly:
    proposal:        proposal_acronym, proposal_title, call_identifier, submission_date
    proposal_facts:  requested_total_cents, trl_start, trl_target, mcrl_start, mcrl_target
    partners[]:      partner_name, requested_cents
plus `metadata` (extraction_timestamp, source_file), which the pipeline adds; it is not extracted.

SDGs are not extracted by the model: app/viewer.py's local sentence-embedding classifier
(sdgautomation/sdg_core.py) handles that instead, outside this pipeline.
"""


def _nullable(json_type):
    return {"type": [json_type, "null"]}


def _object(properties):
    # Strict structured-output mode wants every key required and no extras.
    return {
        "type": "object",
        "properties": properties,
        "required": list(properties),
        "additionalProperties": False,
    }


RAW_SCHEMA = _object(
    {
        "proposal": _object(
            {
                "proposal_acronym": _nullable("string"),
                "proposal_title": _nullable("string"),
                "call_identifier": _nullable("string"),
                "submission_date": _nullable("string"),
            }
        ),
        "proposal_facts": _object(
            {
                "requested_total": _nullable("string"),
                "trl_start": _nullable("integer"),
                "trl_target": _nullable("integer"),
                "mcrl_start": _nullable("integer"),
                "mcrl_target": _nullable("integer"),
            }
        ),
        "partners": {
            "type": "array",
            "items": _object(
                {
                    "partner_name": {"type": "string"},
                    "requested": _nullable("string"),
                }
            ),
        },
    }
)

PROPOSAL_KEYS = ["proposal_acronym", "proposal_title", "call_identifier", "submission_date"]
FACT_KEYS = ["requested_total_cents", "trl_start", "trl_target", "mcrl_start", "mcrl_target"]
PARTNER_KEYS = ["partner_name", "requested_cents"]
METADATA_KEYS = ["extraction_timestamp", "source_file"]


def _is_int(v):
    return isinstance(v, int) and not isinstance(v, bool)


def validate_final(doc):
    """Return a list of problems with a final document (empty list = valid)."""
    problems = []
    if not isinstance(doc, dict):
        return ["document is not an object"]

    def check_keys(obj, keys, where):
        if not isinstance(obj, dict):
            problems.append(f"{where} is not an object")
            return False
        if set(obj) != set(keys):
            problems.append(f"{where} keys {sorted(obj)} != expected {sorted(keys)}")
            return False
        return True

    if set(doc) != {"proposal", "proposal_facts", "partners", "metadata"}:
        problems.append(f"top-level keys are {sorted(doc)}")
        return problems

    if check_keys(doc["proposal"], PROPOSAL_KEYS, "proposal"):
        p = doc["proposal"]
        for k in PROPOSAL_KEYS:
            if p[k] is not None and not isinstance(p[k], str):
                problems.append(f"proposal.{k} must be text or null")

    if check_keys(doc["proposal_facts"], FACT_KEYS, "proposal_facts"):
        f = doc["proposal_facts"]
        for k in FACT_KEYS:
            if f[k] is not None and not _is_int(f[k]):
                problems.append(f"proposal_facts.{k} must be an integer or null")
        for k in ("trl_start", "trl_target", "mcrl_start", "mcrl_target"):
            if _is_int(f[k]) and not 1 <= f[k] <= 9:
                problems.append(f"proposal_facts.{k} out of range 1-9")

    if not isinstance(doc["partners"], list):
        problems.append("partners is not a list")
    else:
        for i, partner in enumerate(doc["partners"]):
            if check_keys(partner, PARTNER_KEYS, f"partners[{i}]"):
                if not isinstance(partner["partner_name"], str) or not partner["partner_name"]:
                    problems.append(f"partners[{i}].partner_name must be non-empty text")
                if partner["requested_cents"] is not None and not _is_int(partner["requested_cents"]):
                    problems.append(f"partners[{i}].requested_cents must be an integer or null")

    check_keys(doc["metadata"], METADATA_KEYS, "metadata")
    return problems
