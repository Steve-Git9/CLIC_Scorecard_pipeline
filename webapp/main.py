"""CLIC extraction web app: Markdown + text extraction only, FastAPI + HTMX + Tailwind.

A second, separate interface to the same backend logic already used by app/viewer.py -
no logic is duplicated here, only the presentation layer differs (server-rendered HTML
instead of Streamlit widgets). Reuses clic_extract (extraction), sdgautomation (local
SDG classifier), and src/pipeline (config, db, partner matching, save, dashboard
queries) exactly as they are.

Flow: upload a .md -> pick an arm (B/C/D) -> Extract -> a clean, read-only review page
-> Approve -> a form requiring every field to be filled (per the project's own rule,
stricter than the database's actual NOT NULL constraints) -> Save -> a dashboard of
everything saved so far. The Markdown + text pipeline only: no multimodal/PDF path here.

Run from the project root:
    .venv\\Scripts\\python -m uvicorn webapp.main:app --reload --port 8000
Then open http://127.0.0.1:8000 - bound to localhost only by default with --reload;
add --host 127.0.0.1 explicitly if ever running without --reload to be sure.
"""

from __future__ import annotations

import json
import logging
import os
import sys
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import quote

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from markupsafe import Markup

APP_ROOT = Path(__file__).resolve().parent.parent
SECOND_STEP_ROOT = APP_ROOT / "second_step_CLICpipeline"
SDG_ROOT = APP_ROOT / "sdgautomation"
INPUT_ROOT = SECOND_STEP_ROOT / "input"
OUTPUT_ROOT = SECOND_STEP_ROOT / "output"

load_dotenv(APP_ROOT / ".env")

for _p in (APP_ROOT, SECOND_STEP_ROOT, SDG_ROOT):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from clic_extract.backends import BackendError, load_arms, verify_token  # noqa: E402
from clic_extract.multimodal import COMBINED_MODELS, extract_native_text, run_one_combined  # noqa: E402
from clic_extract.run_extract import run_one  # noqa: E402
from src.pipeline import kpi  # noqa: E402
from src.pipeline.config import load_config  # noqa: E402
from src.pipeline.convert import convert_pdf_to_markdown  # noqa: E402
from src.pipeline.db import get_connection  # noqa: E402
from src.pipeline.load import (  # noqa: E402
    DuplicateProposalError,
    PARTNER_MATCH_THRESHOLD,
    ProposalNotFoundError,
    find_duplicate_proposal,
    load_extraction,
    match_partner_name,
    update_proposal,
)
from src.pipeline.queries import (  # noqa: E402
    fmt,
    fmt_cents,
    load_all_partners,
    load_all_sdgs,
    load_partners_for,
    load_proposal,
    load_proposals,
    load_reference_counts,
    load_sdgs_for,
)

app = FastAPI(title="CLIC extraction")


@app.on_event("startup")
def _startup() -> None:
    preload_sdg_classifier()
templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent / "templates"))
templates.env.filters["fmt_cents"] = fmt_cents
templates.env.filters["fmt"] = fmt
templates.env.filters["eur_compact"] = kpi.eur_compact
templates.env.filters["tojson"] = lambda value: Markup(json.dumps(value))

STATUSES = ["Pending", "Approved", "Rejected"]
FUNDING_SOURCES = ["EU", "National"]

# Loaded once, kept for the life of the server process - the model itself never changes.
_sdg_classifier_cache: dict[str, Any] = {}
# SDG results are reused across page loads for the same run instead of recomputed each time.
_sdg_result_cache: dict[str, dict] = {}


def get_sdg_classifier():
    # Imported here, not at module load time: sdg_core pulls in sentence-transformers (and
    # therefore torch), which alone takes tens of seconds to import. Importing it eagerly at
    # the top of this file meant every server start - and every --reload restart - paid that
    # cost before the app could serve even the index page. Deferred to first actual use instead;
    # still cached afterward, so it is still paid only once per server process.
    from sdg_core import embed_sdgs, load_model as load_sdg_model, load_sdgs

    if not _sdg_classifier_cache:
        model = load_sdg_model()
        sdgs = load_sdgs()
        _sdg_classifier_cache["model"] = model
        _sdg_classifier_cache["sdgs"] = sdgs
        _sdg_classifier_cache["embeddings"] = embed_sdgs(model, sdgs)
    return _sdg_classifier_cache["model"], _sdg_classifier_cache["sdgs"], _sdg_classifier_cache["embeddings"]


_sdg_lock = threading.Lock()


def get_sdg_result(stem: str, source_md_path: Path) -> dict | None:
    from sdg_core import classify_document

    with _sdg_lock:  # one classification at a time; a page waiting on a warm-up reuses its result
        if stem in _sdg_result_cache:
            return _sdg_result_cache[stem]
        if not source_md_path.exists():
            return None
        text = source_md_path.read_text(encoding="utf-8")
        model, sdgs, embeddings = get_sdg_classifier()
        result = classify_document(text, model, sdgs, embeddings)
        _sdg_result_cache[stem] = result
        return result


_sdg_running: set[str] = set()
_sdg_errors: dict[str, str] = {}


def start_sdg_job(stem: str, run: dict) -> None:
    """Start classifying in the background unless it is done or already running."""
    if stem in _sdg_result_cache or stem in _sdg_running:
        return
    _sdg_errors.pop(stem, None)
    _sdg_running.add(stem)

    def work() -> None:
        try:
            get_sdg_result(stem, INPUT_ROOT / run.get("source_file", ""))
        except Exception as exc:  # shown in the review page's SDG panel
            logging.getLogger("webapp").exception("SDG classification failed for %s", stem)
            _sdg_errors[stem] = f"{type(exc).__name__}: {exc}"
        finally:
            _sdg_running.discard(stem)

    threading.Thread(target=work, daemon=True).start()


def warm_sdg_result(stem: str, run: dict) -> None:
    """Classify SDGs in the background right after extraction, so the review page never waits."""
    start_sdg_job(stem, run)


def preload_sdg_classifier() -> None:
    """Load the SDG model in the background when the server starts, so the first document is not slow."""
    def work() -> None:
        try:
            with _sdg_lock:
                get_sdg_classifier()
        except Exception:
            pass

    threading.Thread(target=work, daemon=True).start()


def get_config():
    return load_config(APP_ROOT / "config.yaml")


def get_db():
    return get_connection(get_config())


def resolve_hf_token() -> str | None:
    token = os.environ.get("HF_TOKEN", "").strip()
    return token or None


def save_uploaded_bytes(raw: bytes, filename: str, dest_dir: Path) -> Path:
    """Same Windows file-lock fallback as app/viewer.save_uploaded_file."""
    dest_dir.mkdir(parents=True, exist_ok=True)
    path = dest_dir / filename
    try:
        path.write_bytes(raw)
        return path
    except PermissionError:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        alt_path = dest_dir / f"{path.stem}_{stamp}{path.suffix}"
        alt_path.write_bytes(raw)
        return alt_path


def load_run_and_data(arm: str, stem: str) -> tuple[dict, dict]:
    out_dir = OUTPUT_ROOT / arm
    run = _read_json(out_dir / f"{stem}.run.json")
    data = _read_json(out_dir / f"{stem}.json")
    return run, data


def _read_json(path: Path) -> dict:
    import json

    return json.loads(path.read_text(encoding="utf-8"))


def build_partner_rows(partners: list[dict], db_names: list[str]) -> list[dict]:
    rows = []
    for p in partners:
        name = p.get("partner_name") or ""
        m = match_partner_name(name, db_names)
        rows.append({
            "extracted_name": name,
            "requested_cents": p.get("requested_cents"),
            "requested_eur": None if p.get("requested_cents") is None else p["requested_cents"] / 100,
            "granted_eur": None,
            "matched_partner": m["matched"] or (db_names[0] if db_names else ""),
            "confidence": round(m["score"], 1),
            "flagged": m["flagged"],
        })
    return rows


# --------------------------------------------------------------------------- routes

@app.get("/", response_class=HTMLResponse)
def index(request: Request, error: str | None = None):
    arms = load_arms()
    token = resolve_hf_token()
    return templates.TemplateResponse(request, "index.html", {
        "arms": arms,
        "has_token": bool(token),
        "env_path": str(APP_ROOT / ".env"),
        "error": error,
    })


@app.post("/extract", response_class=HTMLResponse)
async def extract(request: Request, arm: str = Form(...), file: UploadFile = File(...)):
    arms = load_arms()
    token = resolve_hf_token()

    def fail(message: str):
        return templates.TemplateResponse(request, "index.html", {
            "arms": arms, "has_token": bool(token), "env_path": str(APP_ROOT / ".env"),
            "error": message,
        })

    if arm not in arms:
        return fail(f"Unknown arm {arm!r}.")
    if not token:
        return fail(f"No HF_TOKEN found. Add it to {APP_ROOT / '.env'} as HF_TOKEN=hf_... and restart the server.")

    raw = await file.read()
    is_pdf = file.filename.lower().endswith(".pdf")

    if is_pdf:
        pdf_path = save_uploaded_bytes(raw, file.filename, INPUT_ROOT)
        try:
            markdown = convert_pdf_to_markdown(pdf_path)
        except Exception as exc:  # docling failures vary; surface them, do not crash the page
            return fail(f"Conversion to Markdown failed: {exc}")
        md_path = pdf_path.with_suffix(".md")
        md_path.write_text(markdown, encoding="utf-8")
    else:
        md_path = save_uploaded_bytes(raw, file.filename, INPUT_ROOT)

    try:
        verify_token(token)
    except BackendError as exc:
        return fail(str(exc))

    out_dir = OUTPUT_ROOT / arm
    out_dir.mkdir(parents=True, exist_ok=True)
    run = run_one(arm, arms[arm], md_path, out_dir, token, True, datetime.now(timezone.utc))

    if run["status"] != "ok":
        return fail(f"Extraction failed: {run['error']}")

    stem = Path(run["output_file"]).stem
    warm_sdg_result(stem, run)
    return templates.TemplateResponse(request, "extracted.html", {"arm": arm, "stem": stem, "run": run})


@app.get("/multimodal", response_class=HTMLResponse)
def multimodal_index(request: Request, error: str | None = None):
    token = resolve_hf_token()
    return templates.TemplateResponse(request, "multimodal.html", {
        "models": COMBINED_MODELS, "has_token": bool(token), "env_path": str(APP_ROOT / ".env"), "error": error,
    })


@app.post("/multimodal/extract", response_class=HTMLResponse)
async def multimodal_extract(request: Request, model_key: str = Form(...), file: UploadFile = File(...)):
    token = resolve_hf_token()

    def fail(message: str):
        return templates.TemplateResponse(request, "multimodal.html", {
            "models": COMBINED_MODELS, "has_token": bool(token), "env_path": str(APP_ROOT / ".env"),
            "error": message,
        })

    if model_key not in COMBINED_MODELS:
        return fail(f"Unknown model {model_key!r}.")
    if not token:
        return fail(f"No HF_TOKEN found. Add it to {APP_ROOT / '.env'} as HF_TOKEN=hf_... and restart the server.")
    if not file.filename.lower().endswith(".pdf"):
        return fail("Upload a PDF - this page needs the original pages to render as images, not an already-converted Markdown file.")

    raw = await file.read()
    pdf_path = save_uploaded_bytes(raw, file.filename, INPUT_ROOT)

    try:
        verify_token(token)
    except BackendError as exc:
        return fail(str(exc))

    try:
        document_text = extract_native_text(pdf_path)
    except Exception as exc:  # malformed PDFs vary; surface them, do not crash the page
        return fail(f"Could not read the PDF's text: {exc}")
    md_path = pdf_path.with_suffix(".md")
    md_path.write_text(document_text, encoding="utf-8")

    arm_name = f"multimodal_combined_{model_key}"
    out_dir = OUTPUT_ROOT / arm_name
    out_dir.mkdir(parents=True, exist_ok=True)
    run = run_one_combined(pdf_path, document_text, out_dir, model_key, token, datetime.now(timezone.utc))

    if run["status"] != "ok":
        return fail(f"Extraction failed: {run['error']}")

    stem = Path(run["output_file"]).stem
    warm_sdg_result(stem, run)
    return templates.TemplateResponse(request, "extracted.html", {"arm": arm_name, "stem": stem, "run": run})


@app.get("/review/{arm}/{stem}", response_class=HTMLResponse)
def review(request: Request, arm: str, stem: str):
    run, data = load_run_and_data(arm, stem)
    conn = get_db()
    db_names = load_all_partners(conn)
    db_names = [p["partner_name"] for p in db_names]

    proposal = data.get("proposal", {})
    duplicate = find_duplicate_proposal(conn, proposal.get("proposal_acronym"))
    partner_rows = build_partner_rows(data.get("partners", []), db_names)

    return templates.TemplateResponse(request, "review.html", {
        "arm": arm, "stem": stem, "run": run, "proposal": proposal,
        "facts": data.get("proposal_facts", {}), "partner_rows": partner_rows,
        "duplicate": duplicate, "threshold": PARTNER_MATCH_THRESHOLD,
    })


@app.get("/review/{arm}/{stem}/sdgs", response_class=HTMLResponse)
def review_sdgs(request: Request, arm: str, stem: str, retry: bool = False):
    """SDG panel, polled by the review page. Never waits: returns the result, a loading message or the error."""
    run, _ = load_run_and_data(arm, stem)

    def panel(**ctx):
        return templates.TemplateResponse(request, "_sdg_panel.html", {"arm": arm, "stem": stem, **ctx})

    if stem not in _sdg_result_cache:
        if not (INPUT_ROOT / run.get("source_file", "")).exists():
            return panel(error=f"The source Markdown file '{run.get('source_file', '')}' was not found in {INPUT_ROOT}, so the SDGs cannot be classified.")
        if retry:
            _sdg_errors.pop(stem, None)
        if stem in _sdg_errors:
            return panel(error=_sdg_errors[stem])
        start_sdg_job(stem, run)
        if stem in _sdg_running:
            return panel(loading=True)
        if stem in _sdg_errors:  # the job failed before this check
            return panel(error=_sdg_errors[stem])
    result = _sdg_result_cache.get(stem)
    return panel(sdgs=(result or {}).get("sdgs", []))


@app.get("/approve/{arm}/{stem}", response_class=HTMLResponse)
def approve(request: Request, arm: str, stem: str, error: str | None = None):
    run, data = load_run_and_data(arm, stem)
    conn = get_db()
    db_names_rows = load_all_partners(conn)
    db_names = [p["partner_name"] for p in db_names_rows]

    proposal = data.get("proposal", {})
    facts = data.get("proposal_facts", {})
    partner_rows = build_partner_rows(data.get("partners", []), db_names)

    return templates.TemplateResponse(request, "approve.html", {
        "arm": arm, "stem": stem, "proposal": proposal, "facts": facts,
        "partner_rows": partner_rows, "db_names": db_names, "error": error,
        "threshold": PARTNER_MATCH_THRESHOLD, "statuses": STATUSES, "funding_sources": FUNDING_SOURCES,
    })


def build_cloud_points(cloud_rows: list[dict]) -> list[dict]:
    """TRL/MCRL grouped counts as Chart.js bubble points - radius scaled to the largest bubble."""
    max_count = max((r["project_count"] for r in cloud_rows), default=1)
    return [
        {"x": r["trl"], "y": r["mcrl"], "r": 6 + 14 * (r["project_count"] / max_count), "count": r["project_count"]}
        for r in cloud_rows
    ]


def _yes_no_to_int(value: str | None) -> int | None:
    if value == "yes":
        return 1
    if value == "no":
        return 0
    return None


@app.post("/save/{arm}/{stem}", response_class=HTMLResponse)
async def save(request: Request, arm: str, stem: str):
    form = await request.form()
    run, data = load_run_and_data(arm, stem)
    source_md_path = INPUT_ROOT / run.get("source_file", "")
    sdg_result = get_sdg_result(stem, source_md_path)

    def missing_redo(message: str):
        conn = get_db()
        db_names = [p["partner_name"] for p in load_all_partners(conn)]
        # Re-render with whatever the reviewer had just typed, not the original extraction,
        # so a validation error never loses their edits.
        proposal = {
            "proposal_acronym": form.get("proposal_acronym") or None,
            "proposal_title": form.get("proposal_title") or None,
            "call_identifier": form.get("call_identifier") or None,
            "submission_date": form.get("submission_date") or None,
            "status": form.get("status") or None,
            "decision_date": form.get("decision_date") or None,
            "programme_name": form.get("programme_name") or None,
            "funding_source": form.get("funding_source") or None,
        }
        facts = {
            "requested_total_eur": form.get("requested_total_eur") or None,
            "granted_total_eur": form.get("granted_total_eur") or None,
            "trl_start": form.get("trl_start") or None,
            "trl_target": form.get("trl_target") or None,
            "mcrl_start": form.get("mcrl_start") or None,
            "mcrl_target": form.get("mcrl_target") or None,
            "builds_on_previous": form.get("builds_on_previous") or None,
            "demo_activity_count": form.get("demo_activity_count") or None,
        }
        matches = form.getlist("partner_match")
        amounts = form.getlist("partner_amount")
        granted = form.getlist("partner_granted")
        partner_rows = [
            {"extracted_name": matched, "matched_partner": matched, "requested_eur": amount,
             "granted_eur": grant, "confidence": 100.0, "flagged": False}
            for matched, amount, grant in zip(matches, amounts, granted)
        ]
        return templates.TemplateResponse(request, "approve.html", {
            "arm": arm, "stem": stem, "proposal": proposal, "facts": facts,
            "partner_rows": partner_rows, "db_names": db_names, "error": message,
            "threshold": PARTNER_MATCH_THRESHOLD, "statuses": STATUSES, "funding_sources": FUNDING_SOURCES,
        }, status_code=400)

    required_text = [
        "proposal_acronym", "proposal_title", "call_identifier", "submission_date",
        "status", "programme_name", "funding_source", "builds_on_previous",
    ]
    required_numeric = [
        "requested_total_eur", "granted_total_eur", "trl_start", "trl_target",
        "mcrl_start", "mcrl_target", "demo_activity_count",
    ]
    for field in required_text + required_numeric:
        if not (form.get(field) or "").strip():
            return missing_redo(f"'{field}' is required - every field must be filled in before saving.")

    status = form["status"]
    if status not in STATUSES:
        return missing_redo(f"'{status}' is not a valid status.")
    if status != "Pending" and not (form.get("decision_date") or "").strip():
        return missing_redo("'decision_date' is required once status is Approved or Rejected.")
    if form["funding_source"] not in FUNDING_SOURCES:
        return missing_redo(f"'{form['funding_source']}' is not a valid funding source.")

    matches = form.getlist("partner_match")
    amounts = form.getlist("partner_amount")
    granted_amounts = form.getlist("partner_granted")
    if not matches:
        return missing_redo("At least one partner is required.")
    for amount in amounts + granted_amounts:
        if not (amount or "").strip():
            return missing_redo("Every partner's requested and granted amount is required.")

    try:
        requested_total_cents = round(float(form["requested_total_eur"]) * 100)
        granted_total_cents = round(float(form["granted_total_eur"]) * 100)
        trl_start, trl_target = int(form["trl_start"]), int(form["trl_target"])
        mcrl_start, mcrl_target = int(form["mcrl_start"]), int(form["mcrl_target"])
        demo_activity_count = int(form["demo_activity_count"])
        partner_requested_cents = [round(float(a) * 100) for a in amounts]
        partner_granted_cents = [round(float(a) * 100) for a in granted_amounts]
    except ValueError:
        return missing_redo("One of the numeric fields could not be read as a number.")

    builds_on_previous = _yes_no_to_int(form.get("builds_on_previous"))
    if builds_on_previous is None:
        return missing_redo("'builds_on_previous' must be Yes or No.")

    final_proposal = {
        "proposal_acronym": form["proposal_acronym"].strip(),
        "proposal_title": form["proposal_title"].strip(),
        "call_identifier": form["call_identifier"].strip(),
        "submission_date": form["submission_date"].strip(),
        "status": status,
        "decision_date": (form.get("decision_date") or "").strip() or None,
        "programme_name": form["programme_name"].strip(),
        "funding_source": form["funding_source"],
    }
    final_facts = {
        "requested_total_cents": requested_total_cents,
        "granted_total_cents": granted_total_cents,
        "trl_start": trl_start, "trl_target": trl_target,
        "mcrl_start": mcrl_start, "mcrl_target": mcrl_target,
        "builds_on_previous": builds_on_previous,
        "demo_activity_count": demo_activity_count,
    }
    final_partners = [
        {"partner_name": name, "requested_cents": req_cents, "granted_cents": grant_cents}
        for name, req_cents, grant_cents in zip(matches, partner_requested_cents, partner_granted_cents)
    ]
    approved_data = {"proposal": final_proposal, "proposal_facts": final_facts, "partners": final_partners}

    config = get_config()
    try:
        result = load_extraction(approved_data, sdg_result, config)
    except DuplicateProposalError as exc:
        return missing_redo(str(exc))

    return templates.TemplateResponse(request, "saved.html", {"result": result, "proposal": final_proposal})


@app.get("/projects", response_class=HTMLResponse)
def projects(request: Request, q: str = "", project: int | None = None,
             saved: bool = False, error: str | None = None):
    """Project selector (with the full edit form for the chosen project), counts, searchable partners."""
    conn = get_db()
    selected = selected_partners = None
    all_sdgs, linked_sdgs = [], set()
    if project:
        selected = load_proposal(conn, project)
        if selected is not None:
            selected_partners = load_partners_for(conn, project)
            all_sdgs = load_all_sdgs(conn)
            linked_sdgs = {s["sdg_number"] for s in load_sdgs_for(conn, project)}
    counts = load_reference_counts(conn)
    partners = load_all_partners(conn)
    if q:
        partners = [p for p in partners if q.casefold() in p["partner_name"].casefold()]
    proposals = load_proposals(conn)
    return templates.TemplateResponse(request, "projects.html", {
        "counts": counts, "partners": partners, "proposals": proposals, "q": q,
        "proposal_key": project, "selected": selected, "selected_partners": selected_partners,
        "all_sdgs": all_sdgs, "linked_sdgs": linked_sdgs,
        "statuses": STATUSES, "funding_sources": FUNDING_SOURCES, "saved": saved, "error": error,
    })


@app.get("/projects/partners", response_class=HTMLResponse)
def projects_partners_fragment(request: Request, q: str = ""):
    """HTMX fragment: just the partner table, for live search without a full page reload."""
    conn = get_db()
    partners = load_all_partners(conn)
    if q:
        partners = [p for p in partners if q.casefold() in p["partner_name"].casefold()]
    return templates.TemplateResponse(request, "_partner_table.html", {"partners": partners})


@app.get("/projects/{proposal_key}")
def project_edit_form(proposal_key: int, saved: bool = False, error: str | None = None):
    """Old per-project address: the editor now lives on the Projects tab."""
    url = f"/projects?project={proposal_key}"
    if saved:
        url += "&saved=1"
    if error:
        url += f"&error={quote(error)}"
    return RedirectResponse(url=url, status_code=303)


@app.post("/projects/{proposal_key}", response_class=HTMLResponse)
async def project_edit_save(request: Request, proposal_key: int):
    form = await request.form()
    conn = get_db()
    proposal = load_proposal(conn, proposal_key)
    if proposal is None:
        return RedirectResponse(url="/projects", status_code=303)
    partners = load_partners_for(conn, proposal_key)

    def redo(message: str):
        return RedirectResponse(
            url=f"/projects?project={proposal_key}&error={quote(message)}", status_code=303
        )

    required_text = [
        "proposal_acronym", "proposal_title", "call_identifier", "submission_date",
        "status", "programme_name", "funding_source", "builds_on_previous",
    ]
    required_numeric = [
        "requested_total_eur", "granted_total_eur", "trl_start", "trl_target",
        "mcrl_start", "mcrl_target", "demo_activity_count",
    ]
    for field in required_text + required_numeric:
        if not (form.get(field) or "").strip():
            return redo(f"'{field}' is required - every field must be filled in.")

    status = form["status"]
    if status not in STATUSES:
        return redo(f"'{status}' is not a valid status.")
    if status != "Pending" and not (form.get("decision_date") or "").strip():
        return redo("'decision_date' is required once status is Approved or Rejected.")
    if form["funding_source"] not in FUNDING_SOURCES:
        return redo(f"'{form['funding_source']}' is not a valid funding source.")

    partner_ids = [int(v) for v in form.getlist("partner_id")]
    requested = form.getlist("partner_requested")
    granted = form.getlist("partner_granted")
    for amount in requested + granted:
        if not (amount or "").strip():
            return redo("Every partner's requested and granted amount is required.")

    try:
        requested_total_cents = round(float(form["requested_total_eur"]) * 100)
        granted_total_cents = round(float(form["granted_total_eur"]) * 100)
        trl_start, trl_target = int(form["trl_start"]), int(form["trl_target"])
        mcrl_start, mcrl_target = int(form["mcrl_start"]), int(form["mcrl_target"])
        demo_activity_count = int(form["demo_activity_count"])
        partner_requested_cents = [round(float(a) * 100) for a in requested]
        partner_granted_cents = [round(float(a) * 100) for a in granted]
    except ValueError:
        return redo("One of the numeric fields could not be read as a number.")

    builds_on_previous = _yes_no_to_int(form.get("builds_on_previous"))
    if builds_on_previous is None:
        return redo("'builds_on_previous' must be Yes or No.")

    proposal_fields = {
        "proposal_acronym": form["proposal_acronym"].strip(),
        "proposal_title": form["proposal_title"].strip(),
        "call_identifier": form["call_identifier"].strip(),
        "submission_date": form["submission_date"].strip(),
        "status": status,
        "decision_date": (form.get("decision_date") or "").strip() or None,
        "programme_name": form["programme_name"].strip(),
        "funding_source": form["funding_source"],
    }
    fact_fields = {
        "requested_total_cents": requested_total_cents,
        "granted_total_cents": granted_total_cents,
        "trl_start": trl_start, "trl_target": trl_target,
        "mcrl_start": mcrl_start, "mcrl_target": mcrl_target,
        "builds_on_previous": builds_on_previous,
        "demo_activity_count": demo_activity_count,
    }
    partner_updates = [
        {"partner_id": pid, "requested_cents": req_cents, "granted_cents": grant_cents}
        for pid, req_cents, grant_cents in zip(partner_ids, partner_requested_cents, partner_granted_cents)
    ]
    sdg_numbers = [int(n) for n in form.getlist("sdg_number")]

    config = get_config()
    try:
        update_proposal(proposal_key, proposal_fields, fact_fields, partner_updates, sdg_numbers, config)
    except ProposalNotFoundError as exc:
        return redo(str(exc))

    return RedirectResponse(url=f"/projects?project={proposal_key}&saved=1", status_code=303)


@app.get("/dashboard", response_class=HTMLResponse)
def kpi_dashboard(request: Request):
    conn = get_db()
    approved_n, total_n, rate_n = kpi.success_rate_count(conn)
    granted_eur, requested_eur, rate_eur = kpi.success_rate_eur(conn)
    partner_total = kpi.partner_funding_total(conn)
    building_on_previous, total_demo, projects_with_demo = kpi.portfolio_impact_totals(conn)
    return templates.TemplateResponse(request, "kpi_dashboard.html", {
        "approved_n": approved_n, "total_n": total_n, "rate_n": rate_n,
        "granted_eur": granted_eur, "requested_eur": requested_eur, "rate_eur": rate_eur,
        "partner_total": partner_total,
        "by_scope": kpi.funding_by_scope(conn),
        "top_partners": kpi.top_partners(conn),
        "network": kpi.network_by_category(conn),
        "building_on_previous": building_on_previous, "total_demo": total_demo,
        "projects_with_demo": projects_with_demo,
        "cloud": kpi.trl_mcrl_cloud(conn),
        "cloud_points": build_cloud_points(kpi.trl_mcrl_cloud(conn)),
        "sdg_counts": kpi.sdg_project_counts(conn),
    })


@app.get("/scorecard", response_class=HTMLResponse)
def scorecard(request: Request):
    conn = get_db()
    approved_n, total_n, rate_n = kpi.success_rate_count(conn)
    granted_eur, requested_eur, rate_eur = kpi.success_rate_eur(conn)
    partner_total = kpi.partner_funding_total(conn)
    building_on_previous, total_demo, projects_with_demo = kpi.portfolio_impact_totals(conn)
    return templates.TemplateResponse(request, "scorecard.html", {
        "rate_n": rate_n, "rate_eur": rate_eur, "partner_total": partner_total,
        "by_scope": kpi.funding_by_scope(conn),
        "top_partners": kpi.top_partners(conn),
        "network": kpi.network_by_category(conn),
        "building_on_previous": building_on_previous, "total_demo": total_demo,
        "projects_with_demo": projects_with_demo,
        "cloud": kpi.trl_mcrl_cloud(conn),
        "cloud_points": build_cloud_points(kpi.trl_mcrl_cloud(conn)),
        "sdg_counts": kpi.sdg_project_counts(conn)[:7],
        "events": kpi.outreach(conn, "Event"),
        "comms": kpi.outreach(conn, "Communication"),
    })
