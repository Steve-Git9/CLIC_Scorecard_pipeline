"""Description of the eleven extraction configurations, read from the pipeline code itself.

Every value comes from the constants the configurations actually run with (arms.json,
multimodal.py, freeform.py, targeted.py, prompts.py, schema.py), so the record of a run batch
cannot drift from the code that produced it. Prompt versions are SHA 256 digests of the prompt
texts: any edit to a prompt gives a new version.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

from Second_step_CLICpipeline.clic_extract import prompts
from Second_step_CLICpipeline.clic_extract.backends import load_arms
from Second_step_CLICpipeline.clic_extract.freeform import LIGHT_FREEFORM_MODEL
from Second_step_CLICpipeline.clic_extract.multimodal import (
    COMBINED_MODELS,
    DEFAULT_BATCH_OVERLAP,
    DEFAULT_BATCH_SIZE,
    OPEN_MAX_TOKENS,
    VISION_MODEL,
)
from Second_step_CLICpipeline.clic_extract.schema import RAW_SCHEMA
from Second_step_CLICpipeline.clic_extract.targeted import MAX_IMAGES, MAX_PAGES_SENT, TEXT_ARM

CONFIGURATIONS = [
    "B", "C", "D", "freeform_B", "freeform_light",
    "multimodal_strict", "multimodal_open",
    "multimodal_combined_qwen_vl", "multimodal_combined_llama4_maverick",
    "targeted_text", "targeted_multimodal",
]
PROMPT_NAMES = [
    "FIELD_DEFINITIONS", "SYSTEM_PROMPT", "OPEN_TEXT_SYSTEM_PROMPT", "VISION_SYSTEM_PROMPT",
    "OPEN_VISION_SYSTEM_PROMPT", "COMBINED_VISION_SYSTEM_PROMPT", "TARGETED_SYSTEM_PROMPT", "PAGE_PICK_PROMPT",
]
RENDER_ZOOM = 2.0


def sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def prompt_versions() -> dict[str, str]:
    """SHA 256 of every prompt text and of the raw schema."""
    versions = {name: sha256(getattr(prompts, name)) for name in PROMPT_NAMES}
    versions["RAW_SCHEMA"] = sha256(json.dumps(RAW_SCHEMA, sort_keys=True))
    return versions


def _model(entry: dict[str, Any], max_tokens: int | None = None) -> dict[str, Any]:
    return {"model": entry["model"], "provider": entry["provider"], "temperature": 0,
            "max_tokens": max_tokens or entry.get("max_tokens"), "extra_body": entry.get("extra_body", {}),
            "context_length": entry.get("context_length")}


def describe(name: str) -> dict[str, Any]:
    """Every setting of one configuration, and the prompts it uses."""
    arms = load_arms()
    images = {"render_zoom": RENDER_ZOOM, "image_format": "png", "batch_size": DEFAULT_BATCH_SIZE,
              "batch_overlap": DEFAULT_BATCH_OVERLAP}
    if name in ("B", "C", "D"):
        d = {**_model(arms[name]), "response_format": True, "input": "docling_markdown",
             "prompts": ["SYSTEM_PROMPT"]}
    elif name == "freeform_B":
        d = {**_model(arms["B"]), "response_format": False, "input": "docling_markdown",
             "prompts": ["OPEN_TEXT_SYSTEM_PROMPT"]}
    elif name == "freeform_light":
        d = {**_model(LIGHT_FREEFORM_MODEL), "response_format": False, "input": "docling_markdown",
             "prompts": ["OPEN_TEXT_SYSTEM_PROMPT"]}
    elif name == "multimodal_strict":
        d = {**_model(VISION_MODEL), "response_format": True, "input": "pdf_page_images", **images,
             "prompts": ["VISION_SYSTEM_PROMPT"]}
    elif name == "multimodal_open":
        d = {**_model(VISION_MODEL, OPEN_MAX_TOKENS), "response_format": False, "input": "pdf_page_images",
             **images, "prompts": ["OPEN_VISION_SYSTEM_PROMPT"]}
    elif name.startswith("multimodal_combined_"):
        d = {**_model(COMBINED_MODELS[name.removeprefix("multimodal_combined_")]), "response_format": False,
             "input": "pdf_text_layer_and_selected_page_images", **images,
             "image_pages": "pages with an embedded picture or a detected table",
             "prompts": ["COMBINED_VISION_SYSTEM_PROMPT"]}
    elif name == "targeted_text":
        d = {**_model(arms[TEXT_ARM]), "response_format": True, "input": "pdf_located_pages_and_tables",
             "max_pages_sent": MAX_PAGES_SENT, "prompts": ["TARGETED_SYSTEM_PROMPT", "PAGE_PICK_PROMPT"]}
    elif name == "targeted_multimodal":
        d = {**_model(VISION_MODEL), "response_format": True, "input": "pdf_located_pages_tables_and_images",
             "max_pages_sent": MAX_PAGES_SENT, "max_images": MAX_IMAGES, "render_zoom": RENDER_ZOOM,
             "prompts": ["TARGETED_SYSTEM_PROMPT", "PAGE_PICK_PROMPT"]}
    else:
        raise ValueError(f"unknown configuration {name!r}")
    versions = prompt_versions()
    d["config_name"] = name
    d["input_kind"] = "markdown" if d["input"] == "docling_markdown" else "pdf"
    d["prompt_version"] = sha256("".join(versions[p] for p in d["prompts"]) + versions["RAW_SCHEMA"])
    return d
