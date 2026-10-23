"""Very light free-form text arm: a 4B model answers in prose plus one JSON block, no schema.

The model receives the same docling Markdown as arms B, C and D, but with no response_format
constraint at all: it may reason in prose first (OPEN_TEXT_SYSTEM_PROMPT) and ends with a ```json
block (the whole free-form reply, plus any separate reasoning text a model returns, is saved as
<stem>_<UTC>.freeform.txt). postprocess.extract_json pulls the JSON block out and build_final / validate_final turn it into
the final JSON, the same conversion the open multimodal path already relies on. Outputs and the
run file are written by run_extract.run_one, so they sit next to the other arms unchanged.

Model: Qwen3 4B Instruct 2507 on nscale, 262,144 token context, picked from the router's live list on
2026-10-21. It replaced IBM Granite 4.2 8B (used from 2026-10-21 earlier the same day) to have a model
clearly lighter than arm B's Qwen3.5 9B, and from the same family, so B against this arm compares model
size alone. It is the non-thinking Instruct variant: its prose arrives in the reply itself.
Not pinned in arms.json on purpose: it is offered only in the Streamlit evaluation app for now.

freeform_B is the output protocol contrast for arm B: B's own pinned entry from arms.json (model,
provider, max_tokens 3000, enable_thinking false, temperature 0) and B's docling Markdown input, with
only the protocol changed to this module's free form prompt and Python conversion. B against
freeform_B therefore compares a schema constrained answer with a free form answer converted to JSON.

    python -m clic_extract.freeform --input "<document>.md"
    python -m clic_extract.freeform --arm freeform_B --input "<document>.md"
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .backends import BackendError, get_token, load_arms, verify_token
from .prompts import build_open_messages
from .run_extract import run_one

ARM_NAME = "freeform_light"
LIGHT_FREEFORM_MODEL: dict[str, Any] = {
    "model": "Qwen/Qwen3-4B-Instruct-2507",
    "provider": "nscale",
    "role": "very light model (4B), free-form answer converted to JSON",
    # Room for the prose working before the JSON block. The 8B model this arm used before needed
    # about 9,800 tokens on a 38 page proposal; kept generous for the same reason.
    "max_tokens": 16000,
    "context_length": 262_144,
    "input_per_m": 0.01,
    "output_per_m": 0.03,
}


FREEFORM_B_ARM = "freeform_B"
CONTRAST_SOURCE_ARM = "B"


def freeform_b_config() -> dict[str, Any]:
    """Arm B's pinned configuration, copied unchanged: same model, provider and generation settings."""
    return dict(load_arms()[CONTRAST_SOURCE_ARM])


def config_for(arm_name: str) -> dict[str, Any]:
    if arm_name == ARM_NAME:
        return LIGHT_FREEFORM_MODEL
    if arm_name == FREEFORM_B_ARM:
        return freeform_b_config()
    raise ValueError(f"unknown free form arm {arm_name!r}")


def run_one_freeform(md_path: Path, out_dir: Path, token: str, now: datetime | None = None,
                     arm_name: str = ARM_NAME) -> dict:
    """One free form run: no response_format, OPEN_TEXT_SYSTEM_PROMPT, then extract_json + build_final."""
    return run_one(arm_name, config_for(arm_name), Path(md_path), Path(out_dir), token, True,
                   now or datetime.now(timezone.utc), schema=None, messages_builder=build_open_messages)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--arm", choices=[ARM_NAME, FREEFORM_B_ARM], default=ARM_NAME)
    ap.add_argument("--input", required=True, help="a docling .md file")
    ap.add_argument("--output", default="output")
    args = ap.parse_args(argv)
    try:
        token = get_token()
        verify_token(token)
    except BackendError as exc:
        raise SystemExit(f"error: {exc}")
    out_dir = Path(args.output) / args.arm
    out_dir.mkdir(parents=True, exist_ok=True)
    run = run_one_freeform(Path(args.input), out_dir, token, arm_name=args.arm)
    if run["status"] != "ok":
        raise SystemExit(f"FAILED  {run['error']}")
    print(f"ok  {run['seconds']}s  {run['prompt_tokens']}+{run['completion_tokens']} tokens  ${run['cost_usd']}  "
          f"{len(run['warnings'])} warning(s)")
    for w in run["warnings"]:
        print(f"    ! {w}")


if __name__ == "__main__":
    main()
