"""The pilot web app offers exactly the eleven evaluated configurations and dispatches them as
the batch runner does. No model is called and no .env is read: every run function is replaced."""

from __future__ import annotations

from pathlib import Path

import dotenv
import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")
dotenv.load_dotenv = lambda *a, **k: False  # never read the real .env in tests

from fastapi.testclient import TestClient  # noqa: E402

import webapp.main as web  # noqa: E402
from src.evaluation.configurations import CONFIGURATIONS as EVALUATED  # noqa: E402


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setattr(web, "INPUT_ROOT", tmp_path / "input")
    monkeypatch.setattr(web, "OUTPUT_ROOT", tmp_path / "output")
    monkeypatch.setenv("HF_TOKEN", "hf_fictional_test_token")
    monkeypatch.setattr(web, "verify_token", lambda token: None)
    monkeypatch.setattr(web, "warm_sdg_result", lambda stem, run: None)
    return TestClient(web.app)


def test_the_app_offers_exactly_the_evaluated_configurations():
    assert [c["key"] for c in web.CONFIGURATIONS] == EVALUATED


def test_the_upload_page_lists_all_eleven(client: TestClient):
    page = client.get("/").text
    for key in EVALUATED:
        assert f'value="{key}"' in page


def test_the_old_multimodal_page_redirects_to_the_main_page(client: TestClient):
    response = client.get("/multimodal", follow_redirects=False)
    assert response.status_code == 307 and response.headers["location"] == "/"


@pytest.mark.parametrize("key, expected", [
    ("B", "run_one"), ("D", "run_one"), ("freeform_light", "run_one_freeform"),
    ("multimodal_strict", "run_one_multimodal"), ("multimodal_open", "run_one_multimodal"),
    ("multimodal_combined_llama4_maverick", "run_one_combined"),
    ("targeted_text", "run_one_targeted"), ("targeted_multimodal", "run_one_targeted"),
])
def test_each_configuration_reaches_its_run_function(key, expected, tmp_path, monkeypatch):
    monkeypatch.setattr(web, "OUTPUT_ROOT", tmp_path)
    monkeypatch.setattr(web, "load_arms", lambda: {"B": {}, "C": {}, "D": {}})
    called = []
    for name in ("run_one", "run_one_freeform", "run_one_multimodal", "run_one_combined", "run_one_targeted"):
        monkeypatch.setattr(web, name, lambda *a, _n=name, **k: called.append((_n, a, k)) or {"status": "ok"})
    md = tmp_path / "fictional.md"
    md.write_text("Fictional proposal text.", encoding="utf-8")
    web.run_configuration(key, tmp_path / "fictional.pdf", md, "hf_fictional_test_token")
    assert called[0][0] == expected
    if key.startswith("targeted_"):
        assert called[0][1][2] == key.removeprefix("targeted_")
    if key.startswith("multimodal_combined_"):
        assert called[0][1][3] == "llama4_maverick"
    if key.startswith("multimodal_") and not key.startswith("multimodal_combined_"):
        assert called[0][2]["strict"] is (key == "multimodal_strict")


def test_a_pdf_configuration_refuses_a_markdown_upload(client: TestClient):
    response = client.post("/extract", data={"arm": "multimodal_strict"},
                           files={"file": ("fictional.md", b"# Fictional", "text/markdown")})
    assert "upload a PDF" in response.text


def test_an_unknown_configuration_is_refused(client: TestClient):
    response = client.post("/extract", data={"arm": "Z"}, files={"file": ("fictional.md", b"# x", "text/markdown")})
    assert "Unknown configuration" in response.text


def test_sdg_text_of_a_pdf_run_is_the_markdown_next_to_it(monkeypatch, tmp_path):
    monkeypatch.setattr(web, "INPUT_ROOT", tmp_path)
    assert web.sdg_source_path({"source_file": "fictional.pdf"}) == tmp_path / "fictional.md"
    assert web.sdg_source_path({"source_file": "fictional.md"}) == tmp_path / "fictional.md"
