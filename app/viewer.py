"""CLIC extraction evaluation harness.

Upload one proposal PDF, pick any one or any combination of the project's model
configurations, run them, and inspect the JSON each one produced - side by side, with its
token/cost/timing metadata and warnings. Nothing is saved to the database and no review or
approval step runs here: this page exists purely to compare extraction configurations for
the thesis's model-comparison research question. The full review -> approve -> save workflow
for real data lives in the separate FastAPI interface (webapp/main.py), not here.

Every selected model's shared inputs (Markdown text, native text, page images) are prepared
once and reused, regardless of how many models need that same input. Outputs are written to
evaluation/<model>/<stem>_<timestamp>.json (+ .run.json), never to second_step_CLICpipeline/
output/, so these test runs never mix with the project's other extraction history.

Run from the project root:
    .venv\\Scripts\\python -m streamlit run app\\viewer.py --server.address localhost
"""

from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import streamlit as st
from dotenv import load_dotenv

APP_ROOT = Path(__file__).resolve().parent.parent
SECOND_STEP_ROOT = APP_ROOT / "second_step_CLICpipeline"
INPUT_ROOT = SECOND_STEP_ROOT / "input"
EVALUATION_ROOT = APP_ROOT / "evaluation"

load_dotenv(APP_ROOT / ".env")

for _p in (APP_ROOT, SECOND_STEP_ROOT):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from clic_extract.backends import BackendError, load_arms, verify_token  # noqa: E402
from clic_extract.multimodal import (  # noqa: E402
    COMBINED_MODELS,
    DEFAULT_BATCH_OVERLAP,
    DEFAULT_BATCH_SIZE,
    VISION_MODEL,
    extract_native_text,
    run_one_combined,
    run_one_multimodal,
)
from clic_extract.freeform import (  # noqa: E402
    ARM_NAME as FREEFORM_ARM,
    CONTRAST_SOURCE_ARM,
    FREEFORM_B_ARM,
    LIGHT_FREEFORM_MODEL,
    run_one_freeform,
)
from clic_extract.run_extract import run_one  # noqa: E402
from clic_extract.targeted import TEXT_ARM, run_one_targeted  # noqa: E402
from src.pipeline.convert import convert_pdf_to_markdown  # noqa: E402


def resolve_hf_token() -> str | None:
    token = os.environ.get("HF_TOKEN", "").strip()
    return token or None


def save_uploaded_file(uploaded, dest_dir: Path) -> Path:
    """Write an uploaded file to dest_dir, falling back to a timestamped filename if the
    plain name can't be written to (a Windows PermissionError from a lingering handle on
    the previous copy)."""
    dest_dir.mkdir(parents=True, exist_ok=True)
    path = dest_dir / uploaded.name
    try:
        path.write_bytes(uploaded.getvalue())
        return path
    except PermissionError:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        alt_path = dest_dir / f"{path.stem}_{stamp}{path.suffix}"
        alt_path.write_bytes(uploaded.getvalue())
        return alt_path


def format_cents(cents: int | None) -> str:
    return "not stated" if cents is None else f"EUR {cents / 100:,.2f}"


def format_value(value: Any) -> str:
    return "not stated" if value is None or value == "" else str(value)


def build_model_choices() -> dict[str, dict[str, Any]]:
    """Every extraction configuration in the project, keyed by the name its output folder
    (evaluation/<key>/) and its run.json's "arm" field already use elsewhere."""
    arms = load_arms()
    choices: dict[str, dict[str, Any]] = {}
    for arm_name, cfg in arms.items():
        choices[arm_name] = {
            "kind": "text",
            "label": f"{arm_name} - text: {cfg['model']} via {cfg['provider']} ({cfg.get('role', '')})",
            "config": cfg,
        }
    choices[FREEFORM_ARM] = {
        "kind": "text",
        "free_form": True,
        "label": f"{FREEFORM_ARM} - text, very light, free-form answer converted to JSON: "
                 f"{LIGHT_FREEFORM_MODEL['model']} via {LIGHT_FREEFORM_MODEL['provider']}",
        "config": LIGHT_FREEFORM_MODEL,
    }
    if CONTRAST_SOURCE_ARM in arms:
        b = arms[CONTRAST_SOURCE_ARM]
        choices[FREEFORM_B_ARM] = {
            "kind": "text",
            "free_form": True,
            "label": f"{FREEFORM_B_ARM} - text, arm B's model and settings with the free-form protocol "
                     f"(output protocol contrast for B): {b['model']} via {b['provider']}",
            "config": b,
        }
    choices["multimodal_strict"] = {
        "kind": "images_strict",
        "label": f"Multimodal strict - images only, schema-enforced: {VISION_MODEL['model']} via {VISION_MODEL['provider']}",
        "config": VISION_MODEL,
    }
    choices["multimodal_open"] = {
        "kind": "images_open",
        "label": f"Multimodal open - images only, unconstrained: {VISION_MODEL['model']} via {VISION_MODEL['provider']}",
        "config": VISION_MODEL,
    }
    for model_key, cfg in COMBINED_MODELS.items():
        choices[f"multimodal_combined_{model_key}"] = {
            "kind": "combined",
            "label": f"Combined (text + selective images) - {cfg['label']}",
            "config": cfg,
            "model_key": model_key,
        }
    text_arm = arms.get(TEXT_ARM, {})
    choices["targeted_text"] = {
        "kind": "targeted",
        "mode": "text",
        "label": f"Targeted text - located pages + parsed tables only, no images: "
                 f"{text_arm.get('model', TEXT_ARM)} via {text_arm.get('provider', '?')}",
        "config": text_arm,
    }
    choices["targeted_multimodal"] = {
        "kind": "targeted",
        "mode": "multimodal",
        "label": f"Targeted multimodal - located pages + parsed tables + those pages' images: "
                 f"{VISION_MODEL['model']} via {VISION_MODEL['provider']}",
        "config": VISION_MODEL,
    }
    return choices


def render_extraction_json(key: str, run: dict[str, Any], out_dir: Path) -> None:
    st.markdown(f"### {key}")

    if run.get("status") != "ok":
        st.error(f"Failed: {run.get('error')}")
        if run.get("warnings"):
            with st.expander(f"{len(run['warnings'])} warning(s)"):
                for w in run["warnings"]:
                    st.write(f"- {w}")
        return

    cols = st.columns(6)
    cols[0].metric("Model time", run.get("seconds", "-"), help="Time spent in the model API call(s) only.")
    cols[1].metric(
        "This model's total", run.get("total_seconds", "-"),
        help="Model time plus this function's own local work (rendering pages, detecting "
             "tables, batching) - still excludes any one-time shared conversion step shown "
             "above the results, since that cost is not this model's alone.",
    )
    cols[2].metric("Tokens in/out", f"{run.get('prompt_tokens', 0)}/{run.get('completion_tokens', 0)}")
    cost = run.get("cost_usd")
    cols[3].metric("Cost", f"${cost:.5f}" if cost is not None else "-")
    cols[4].metric("Batches", run.get("batches", 1))
    cols[5].metric("Warnings", len(run.get("warnings") or []))
    if run.get("arm", "").startswith("targeted_"):
        tcols = st.columns(4)
        tcols[0].metric("Pages sent", f"{len(run.get('pages_sent') or [])} / {run.get('pages_total', '-')}")
        tcols[1].metric("Tables verified", f"{run.get('tables_verified', 0)} / {run.get('tables_found', 0)}")
        tcols[2].metric("Partners confirmed by a table", run.get("partners_confirmed_by_table", 0))
        tcols[3].metric("OCR pages", len(run.get("ocr_pages") or []))

    output_path = out_dir / run.get("output_file", "")
    try:
        data = json.loads(output_path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        st.error(
            f"Run reported success but its output file could not be read ({exc}). "
            "This can happen if the app was reloaded mid-run (for example, while the code was "
            "being edited) - try running this model again."
        )
        return
    proposal = data.get("proposal", {})
    facts = data.get("proposal_facts", {})
    partners = data.get("partners", [])

    st.write(
        f"**{format_value(proposal.get('proposal_acronym'))}** - {format_value(proposal.get('proposal_title'))}  \n"
        f"Requested total: {format_cents(facts.get('requested_total_cents'))}  |  "
        f"TRL {format_value(facts.get('trl_start'))} -> {format_value(facts.get('trl_target'))}  |  "
        f"{len(partners)} partner(s)"
    )

    st.json(data)

    if run.get("warnings"):
        with st.expander(f"{len(run['warnings'])} warning(s)"):
            for w in run["warnings"]:
                st.write(f"- {w}")
    if run.get("trace_file"):
        with st.expander("Located pages and table checks"):
            st.write({g: run.get("located", {}).get(g) for g in run.get("located", {})},
                     {"located_by": run.get("located_by"), "page_map_cached": run.get("page_map_cached")})
            try:
                trace = json.loads((out_dir / run["trace_file"]).read_text(encoding="utf-8"))
            except (FileNotFoundError, json.JSONDecodeError):
                trace = {}
            for table in trace.get("tables", []):
                v = table.get("verification", {})
                st.markdown(f"**Page {table['page']}, table {table['index'] + 1}**: "
                            f"{'VERIFIED' if v.get('verified') else 'not verified'} {v.get('columns', {})}")
                st.table(table["rows"])
            if trace.get("reconciliation"):
                st.markdown("**Partner amounts against the verified tables**")
                st.table(trace["reconciliation"])
    if run.get("freeform_file"):
        with st.expander("Free-form answer, before conversion to JSON"):
            try:
                st.text((out_dir / run["freeform_file"]).read_text(encoding="utf-8"))
            except FileNotFoundError:
                st.write("The free-form answer file is missing.")
    with st.expander("Full run metadata"):
        st.json(run)


def main() -> None:
    st.set_page_config(page_title="CLIC extraction evaluation", layout="wide")
    st.title("Extraction evaluation")
    st.caption(
        "Upload one PDF, run any one or all model configurations, compare the JSON each one "
        f"produces. Nothing is saved to the database. Outputs go to {EVALUATION_ROOT}/<model>/, "
        "kept separate from the project's other extraction history."
    )

    token = resolve_hf_token()
    if not token:
        st.error(f"No HF_TOKEN found. Add it to {APP_ROOT / '.env'} as HF_TOKEN=hf_... and restart Streamlit.")

    st.subheader("1. Upload a proposal (PDF)")
    uploaded = st.file_uploader("PDF file", type=["pdf"])

    st.subheader("2. Choose which model(s) to run")
    choices = build_model_choices()
    if not choices:
        st.error("No model configurations found.")
        return

    def _apply_select_all() -> None:
        # A checkbox's `value=` argument only sets its *initial* state - once it has a `key`,
        # Streamlit tracks that key's state independently on every rerun after the first, and
        # silently ignores `value=` from then on. Ticking "Select all" has to write into each
        # checkbox's own session_state entry directly (via this callback, before the rerun that
        # draws them) for it to actually change anything.
        new_value = st.session_state["select_all"]
        for key in choices:
            st.session_state[f"select_{key}"] = new_value

    st.checkbox("Select all", key="select_all", on_change=_apply_select_all)
    selected: dict[str, bool] = {}
    cols = st.columns(2)
    for i, (key, info) in enumerate(choices.items()):
        col = cols[i % 2]
        selected[key] = col.checkbox(info["label"], key=f"select_{key}")

    chosen = [k for k, v in selected.items() if v]

    st.subheader("3. Run")
    run_clicked = st.button(
        f"Run {len(chosen)} selected model(s)", type="primary",
        disabled=uploaded is None or not token or not chosen,
    )
    if not run_clicked:
        return

    pdf_path = save_uploaded_file(uploaded, INPUT_ROOT)
    now = datetime.now(timezone.utc)

    try:
        verify_token(token)
    except BackendError as exc:
        st.error(str(exc))
        return

    kinds_needed = {choices[k]["kind"] for k in chosen}
    text_models = [k for k in chosen if choices[k]["kind"] == "text"]
    combined_models = [k for k in chosen if choices[k]["kind"] == "combined"]

    # Timed explicitly and shown once, separately from each model's own numbers below: this
    # cost is paid one time and shared by every model that needs that input on this document,
    # so folding it into each model's reported time would double- or triple-count it (e.g.
    # docling conversion is one run even if B, C and D are all selected).
    markdown_path = None
    if "text" in kinds_needed:
        with st.spinner("Converting to Markdown (docling, OCR only if a page actually needs it)..."):
            t0 = time.monotonic()
            markdown_text = convert_pdf_to_markdown(pdf_path)
            markdown_seconds = round(time.monotonic() - t0, 2)
        markdown_path = pdf_path.with_suffix(".md")
        markdown_path.write_text(markdown_text, encoding="utf-8")
        st.info(
            f"Markdown conversion (docling): **{markdown_seconds}s**, one time, shared by "
            f"{len(text_models)} model(s): {', '.join(text_models)}."
        )

    native_text = None
    if "combined" in kinds_needed:
        t0 = time.monotonic()
        native_text = extract_native_text(pdf_path)
        native_seconds = round(time.monotonic() - t0, 2)
        st.info(
            f"Native text extraction (no docling): **{native_seconds}s**, one time, shared by "
            f"{len(combined_models)} model(s): {', '.join(combined_models)}."
        )

    st.divider()
    for key in chosen:
        info = choices[key]
        out_dir = EVALUATION_ROOT / key
        out_dir.mkdir(parents=True, exist_ok=True)

        with st.spinner(f"Running {key}..."):
            if info["kind"] == "text" and info.get("free_form"):
                run = run_one_freeform(markdown_path, out_dir, token, now, arm_name=key)
            elif info["kind"] == "text":
                run = run_one(key, info["config"], markdown_path, out_dir, token, True, now)
            elif info["kind"] == "images_strict":
                run = run_one_multimodal(
                    pdf_path, out_dir, token, now,
                    batch_size=DEFAULT_BATCH_SIZE, overlap=DEFAULT_BATCH_OVERLAP, strict=True,
                )
            elif info["kind"] == "images_open":
                run = run_one_multimodal(
                    pdf_path, out_dir, token, now,
                    batch_size=DEFAULT_BATCH_SIZE, overlap=DEFAULT_BATCH_OVERLAP, strict=False,
                )
            elif info["kind"] == "combined":
                run = run_one_combined(pdf_path, native_text, out_dir, info["model_key"], token, now)
            elif info["kind"] == "targeted":
                run = run_one_targeted(pdf_path, out_dir, info["mode"], token, now)
            else:
                continue

        render_extraction_json(key, run, out_dir)
        st.divider()


if __name__ == "__main__":
    main()
