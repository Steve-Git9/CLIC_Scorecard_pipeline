"""Tests for call recording, cost and the pilot choice. FICTIONAL TEST DATA ONLY: no network,
every model, provider and price below is invented."""

from __future__ import annotations

import io
import json
import urllib.error
from email.message import Message
from pathlib import Path
from unittest.mock import patch

import pytest

from Second_step_CLICpipeline.clic_extract import backends
from Second_step_CLICpipeline.clic_extract.prompts import PAGE_PICK_PROMPT
from src.evaluation.pricing import call_cost, load_prices, run_cost
from src.evaluation.run_configs import choose_document, summarise_calls

ARM = {"model": "fiction/model-1", "provider": "fakeprov", "max_tokens": 10}
MESSAGES = [{"role": "system", "content": "FICTIONAL system prompt"}, {"role": "user", "content": "x"}]
REPLY = {
    "model": "fiction/model-1",
    "choices": [{"message": {"content": "{}"}, "finish_reason": "stop"}],
    "usage": {"prompt_tokens": 1000, "completion_tokens": 200, "total_tokens": 1200,
              "prompt_tokens_details": {"cached_tokens": 100, "image_tokens": 600},
              "completion_tokens_details": {"reasoning_tokens": 150}},
}


class _Response(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def _http_error(code: int) -> urllib.error.HTTPError:
    return urllib.error.HTTPError("https://fiction.invalid", code, "error", Message(), io.BytesIO(b'{"error":"x"}'))


def test_successful_call_is_recorded_with_all_usage_fields():
    with patch("urllib.request.urlopen", return_value=_Response(json.dumps(REPLY).encode())), \
            backends.record_calls() as calls:
        backends.chat(ARM, MESSAGES, None, "hf_fake")
    assert len(calls) == 1
    c = calls[0]
    assert c["ok"] and c["purpose"] == "extraction" and c["provider"] == "fakeprov"
    assert (c["prompt_tokens"], c["completion_tokens"], c["reasoning_tokens"], c["image_tokens"], c["cached_tokens"]) \
        == (1000, 200, 150, 600, 100)
    assert c["usage"] == REPLY["usage"]
    assert [a["http_status"] for a in c["attempts"]] == [200]


def test_retries_and_failed_calls_are_recorded():
    responses = [_http_error(503), _Response(json.dumps(REPLY).encode())]
    with patch("urllib.request.urlopen", side_effect=responses), patch("time.sleep"), \
            backends.record_calls() as calls:
        backends.chat(ARM, MESSAGES, None, "hf_fake")
    assert [a["http_status"] for a in calls[0]["attempts"]] == [503, 200]

    with patch("urllib.request.urlopen", side_effect=_http_error(400)), backends.record_calls() as calls:
        with pytest.raises(backends.BackendError):
            backends.chat(ARM, MESSAGES, None, "hf_fake")
    assert calls[0]["ok"] is False and calls[0]["usage"] is None and "HTTP 400" in calls[0]["error"]


def test_page_pick_call_is_labelled():
    page_pick = [{"role": "system", "content": PAGE_PICK_PROMPT}, {"role": "user", "content": "map"}]
    with patch("urllib.request.urlopen", return_value=_Response(json.dumps(REPLY).encode())), \
            backends.record_calls() as calls:
        backends.chat(ARM, page_pick, None, "hf_fake")
    assert calls[0]["purpose"] == "page_pick"


def test_nothing_is_recorded_outside_a_recording_block():
    with backends.record_calls() as calls:
        pass
    with patch("urllib.request.urlopen", return_value=_Response(json.dumps(REPLY).encode())):
        backends.chat(ARM, MESSAGES, None, "hf_fake")
    assert calls == []


@pytest.fixture
def prices(tmp_path: Path):
    path = tmp_path / "prices.csv"
    path.write_text(
        "configuration,provider,model_id,currency,input_per_million,cached_input_per_million,output_per_million,status,retrieved_on\n"
        "X,fakeprov,fiction/model-1,USD,1.00,0.50,4.00,verified,2099-01-01\n"
        "Y,to confirm,to confirm,USD,,,,to confirm,2099-01-01\n",
        encoding="utf-8")
    return load_prices(path)


def test_cost_uses_cached_rate_and_does_not_add_reasoning_twice(prices):
    call = {"provider": "fakeprov", "model": "fiction/model-1", "usage": {"x": 1},
            "prompt_tokens": 1000, "completion_tokens": 200, "cached_tokens": 100, "reasoning_tokens": 150}
    cost, problem = call_cost(call, prices)
    assert problem is None
    assert cost == pytest.approx((900 * 1.0 + 100 * 0.5 + 200 * 4.0) / 1_000_000)


def test_failed_call_without_usage_costs_nothing_and_unknown_model_is_reported(prices):
    failed = {"provider": "fakeprov", "model": "fiction/model-1", "usage": None}
    unknown = {"provider": "otherprov", "model": "fiction/model-1", "usage": {"x": 1},
               "prompt_tokens": 10, "completion_tokens": 10}
    assert call_cost(failed, prices) == (0.0, None)
    result = run_cost([failed, unknown], prices)
    assert result["cost_usd"] is None
    assert result["problems"] == ["no price row for otherprov / fiction/model-1"]


def test_run_cost_sums_every_call_including_retried_ones(prices):
    call = {"provider": "fakeprov", "model": "fiction/model-1", "usage": {"x": 1},
            "prompt_tokens": 1_000_000, "completion_tokens": 0}
    assert run_cost([call, dict(call)], prices)["cost_usd"] == pytest.approx(2.0)


def test_summary_counts_calls_failures_retries_and_tokens():
    calls = [
        {"ok": True, "attempts": [{}, {}], "prompt_tokens": 10, "completion_tokens": 5, "reasoning_tokens": None,
         "image_tokens": None, "cached_tokens": None},
        {"ok": False, "attempts": [{}], "prompt_tokens": None, "completion_tokens": None, "reasoning_tokens": None,
         "image_tokens": None, "cached_tokens": None},
    ]
    s = summarise_calls(calls)
    assert (s["calls"], s["failed_calls"], s["attempts"], s["retries"]) == (2, 1, 3, 1)
    assert s["tokens"]["prompt_tokens"] == 10 and s["tokens"]["reasoning_tokens"] is None
    assert s["calls_reporting"]["reasoning_tokens"] == 0


def test_pilot_choice_is_fixed_by_the_seed():
    docs = ["FICTA", "FICTB", "FICTC", "FICTD"]
    assert choose_document(docs, 7) == choose_document(list(reversed(docs)), 7)


def _sse(*chunks, done=True) -> _Response:
    lines = [f"data: {json.dumps(c)}\n\n" for c in chunks] + (["data: [DONE]\n\n"] if done else [])
    return _Response(("".join(lines)).encode())


STREAM = [
    {"model": "fiction/model-1", "choices": [{"delta": {"reasoning_content": "Thinking about "}, "finish_reason": None}]},
    {"choices": [{"delta": {"reasoning_content": "the table."}, "finish_reason": None}]},
    {"choices": [{"delta": {"content": '{"a": '}, "finish_reason": None}]},
    {"choices": [{"delta": {"content": "1}"}, "finish_reason": "stop"}]},
    {"choices": [], "usage": REPLY["usage"]},
]


def test_streamed_reply_is_rebuilt_with_usage_and_reasoning():
    with patch("urllib.request.urlopen", return_value=_sse(*STREAM)), backends.record_calls() as calls:
        result = backends.chat(ARM, MESSAGES, None, "hf_fake")
    assert result["content"] == '{"a": 1}'
    assert result["reasoning"] == "Thinking about the table."
    assert result["finish_reason"] == "stop" and result["prompt_tokens"] == 1000
    assert calls[0]["reasoning_tokens"] == 150 and calls[0]["reply"] == '{"a": 1}'


def test_request_asks_for_a_stream_with_usage():
    body = backends.build_request(ARM, MESSAGES, None)
    assert body["stream"] is True and body["stream_options"] == {"include_usage": True}


def test_stream_error_or_early_end_is_retried_and_logged():
    broken = _sse(STREAM[2], done=False)  # no finish reason, no [DONE]
    with_error = _sse({"error": {"message": "fictional provider error"}})
    with patch("urllib.request.urlopen", side_effect=[broken, with_error, _sse(*STREAM)]), patch("time.sleep"), \
            backends.record_calls() as calls:
        result = backends.chat(ARM, MESSAGES, None, "hf_fake")
    assert result["content"] == '{"a": 1}'
    errors = [a["error"] for a in calls[0]["attempts"]]
    assert errors[0].startswith("stream error: the stream ended") and "fictional provider error" in errors[1]
    assert errors[2] is None


def test_stream_errors_count_as_provider_failures_for_the_batch():
    from src.evaluation.run_batch import transient_failure
    assert transient_failure({"status": "failed", "error": "stream error: the stream ended early"})
