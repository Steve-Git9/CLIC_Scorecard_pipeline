"""Hugging Face Inference Providers client (OpenAI-compatible router), stdlib only.

The token is read from the HF_TOKEN environment variable and is never printed,
logged or written to disk.
"""

import json
import os
import re
import time
import urllib.error
import urllib.request
from contextlib import contextmanager
from pathlib import Path

from .prompts import PAGE_PICK_PROMPT

ROUTER = "https://router.huggingface.co/v1"
ARMS_PATH = Path(__file__).with_name("arms.json")

# Starting points only; `python -m clic_extract.pin set ...` writes the real pin.
ARM_DEFAULTS = {
    "B": {
        "model": "Qwen/Qwen3.5-9B",
        "role": "light model",
        "max_tokens": 3000,
        "extra_body": {"chat_template_kwargs": {"enable_thinking": False}},
    },
    "C": {
        "model": "openai/gpt-oss-120b",
        "role": "large model (accuracy ceiling)",
        "max_tokens": 3000,
        "extra_body": {"reasoning_effort": "low"},
    },
    "D": {
        "model": "openai/gpt-oss-20b",
        "role": "light model (alternative)",
        "max_tokens": 3000,
        "extra_body": {"reasoning_effort": "low"},
    },
}


# Python's default "Python-urllib/x.y" agent is commonly blocked by the Cloudflare
# firewalls that sit in front of provider APIs, so identify ourselves explicitly.
USER_AGENT = "clic-extract/0.1"


class BackendError(RuntimeError):
    pass


# Call recording, for the evaluation: inside `with record_calls() as calls:`, every chat() call
# appends one entry to `calls`, successful or failed, with every attempt (retries included) and
# the provider's usage fields as returned. Recording never changes the request or the reply.
_RECORDERS: list[list[dict]] = []


@contextmanager
def record_calls():
    log: list[dict] = []
    _RECORDERS.append(log)
    try:
        yield log
    finally:
        _RECORDERS.remove(log)


def _record(entry: dict) -> None:
    for log in _RECORDERS:
        log.append(entry)


def usage_details(usage: dict) -> dict:
    """Token counts from an OpenAI style usage object; None where the provider reports nothing."""
    usage = usage or {}
    prompt_details = usage.get("prompt_tokens_details") or {}
    completion_details = usage.get("completion_tokens_details") or {}
    return {
        "prompt_tokens": usage.get("prompt_tokens"),
        "completion_tokens": usage.get("completion_tokens"),
        "total_tokens": usage.get("total_tokens"),
        "reasoning_tokens": completion_details.get("reasoning_tokens", usage.get("reasoning_tokens")),
        "image_tokens": prompt_details.get("image_tokens", usage.get("image_tokens")),
        "cached_tokens": prompt_details.get("cached_tokens"),
    }


def _call_purpose(messages) -> str:
    system = messages[0].get("content") if messages and isinstance(messages[0], dict) else None
    return "page_pick" if system == PAGE_PICK_PROMPT else "extraction"


def request_headers(token=None, json_body=False):
    headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if json_body:
        headers["Content-Type"] = "application/json"
    return headers


def summarise_error(body):
    """Short, readable form of an HTTP error body (Cloudflare pages are long HTML)."""
    text = body or ""
    if "<html" in text.lower() or "<!doctype" in text.lower():
        title = re.search(r"(?is)<title>(.*?)</title>", text)
        code = re.search(r"(?i)error\s*(?:code)?:?\s*(\d{4})", text)
        parts = []
        if title:
            parts.append(" ".join(title.group(1).split()))
        if code:
            parts.append(f"error code {code.group(1)}")
        return "; ".join(parts) or "HTML error page"
    return text[:600]


def token_problems(token):
    """Format problems that would make Hugging Face reject the token. Never includes the token."""
    problems = []
    if any(c.isspace() for c in token):
        problems.append("contains whitespace or a line break")
    if any(c in "<>\"'" for c in token):
        problems.append("contains quote or angle-bracket characters; use the token itself (hf_...), not '<hf_...>'")
    if token.lower().startswith("bearer"):
        problems.append("starts with 'Bearer'; remove that word")
    if not token.startswith("hf_"):
        problems.append("does not start with 'hf_' (Hugging Face tokens do)")
    if len(token) < 30:
        problems.append(f"is only {len(token)} characters; Hugging Face tokens are usually about 37, so it may be truncated")
    return problems


def get_token():
    token = os.environ.get("HF_TOKEN", "")
    if not token.strip():
        raise BackendError(
            "HF_TOKEN is not set in this terminal. In PowerShell run:  $env:HF_TOKEN = 'hf_yourRealTokenHere'  "
            "(type your actual token between the quotes; it needs only 'Make calls to Inference Providers')."
        )
    problems = token_problems(token)
    if problems:
        raise BackendError("HF_TOKEN looks malformed: it " + "; it ".join(problems) + ".")
    return token


def verify_token(token, timeout=30):
    """Ask Hugging Face who the token belongs to. Raises BackendError if it is rejected.

    Returns a dict with user, token type/name and whether it may call Inference Providers,
    or None if Hugging Face could not be reached (the caller may continue).
    """
    req = urllib.request.Request("https://huggingface.co/api/whoami-v2", headers=request_headers(token))
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            info = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        if exc.code in (401, 403):
            raise BackendError(
                f"Hugging Face rejected the token (HTTP {exc.code}). It is invalid, revoked, expired or mistyped: "
                "create a new token at huggingface.co/settings/tokens and set it again."
            ) from None
        return None
    except (urllib.error.URLError, TimeoutError):
        return None
    auth = (info.get("auth") or {}).get("accessToken") or {}
    role = auth.get("role")
    if role == "fineGrained":
        allowed = "inference.serverless.write" in json.dumps(auth.get("fineGrained", {}))
    else:
        allowed = role in ("read", "write")
    return {"user": info.get("name"), "token_name": auth.get("displayName"), "role": role, "inference_allowed": allowed}


def load_arms(path=ARMS_PATH):
    path = Path(path)
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def save_arms(arms, path=ARMS_PATH):
    Path(path).write_text(json.dumps(arms, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _get_json(url, token=None, timeout=60):
    req = urllib.request.Request(url, headers=request_headers(token))
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raise BackendError(f"HTTP {exc.code} from {url}") from None
    except (urllib.error.URLError, TimeoutError) as exc:
        raise BackendError(f"could not reach {url}: {exc}") from None


def fetch_providers(model, timeout=60):
    """Providers currently serving `model`, with prices and capabilities (public endpoint)."""
    data = _get_json(f"{ROUTER}/models", timeout=timeout)
    for entry in data.get("data", []):
        if entry.get("id") == model:
            return entry.get("providers", [])
    raise BackendError(f"model {model!r} is not served by any Inference Provider")


def build_request(arm, messages, schema, use_extras=True):
    """Request body for POST /v1/chat/completions. Contains no secrets.

    schema=None omits response_format entirely, so the model answers in free text with
    no grammar constraint at decoding time - used by the "open" multimodal path to test
    whether strict JSON mode itself is what is costing a model accuracy on a given task.
    """
    payload = {
        "model": f"{arm['model']}:{arm['provider']}",
        "messages": messages,
        "temperature": 0,
        "max_tokens": arm.get("max_tokens", 8000),
    }
    if schema is not None:
        payload["response_format"] = {
            "type": "json_schema",
            "json_schema": {"name": "proposal_extraction", "schema": schema, "strict": True},
        }
    if use_extras:
        payload.update(arm.get("extra_body", {}))
    return payload


def cost_usd(arm, prompt_tokens, completion_tokens):
    price_in, price_out = arm.get("input_per_m"), arm.get("output_per_m")
    if price_in is None or price_out is None or prompt_tokens is None or completion_tokens is None:
        return None
    return round((prompt_tokens * price_in + completion_tokens * price_out) / 1_000_000, 6)


def chat(arm, messages, schema, token, use_extras=True, timeout=600, max_attempts=4):
    """One extraction call with retry on 429/5xx/network errors. Returns a result dict."""
    body = json.dumps(build_request(arm, messages, schema, use_extras)).encode("utf-8")
    req = urllib.request.Request(
        f"{ROUTER}/chat/completions",
        data=body,
        method="POST",
        headers=request_headers(token, json_body=True),
    )
    started = time.monotonic()
    last_error = "unknown error"
    attempt_log: list[dict] = []
    entry = {"purpose": _call_purpose(messages), "model": arm.get("model"), "provider": arm.get("provider"),
             "response_format": schema is not None, "request_bytes": len(body), "ok": False,
             "attempts": attempt_log, "error": None, "usage": None, **usage_details({})}

    def fail(message):
        entry.update(error=message, seconds=round(time.monotonic() - started, 2))
        _record(entry)
        return BackendError(message)

    for attempt in range(1, max_attempts + 1):
        wait = 2 ** attempt
        attempt_started = time.monotonic()
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                reply = json.loads(resp.read().decode("utf-8"))
            attempt_log.append({"attempt": attempt, "http_status": 200, "error": None,
                                "seconds": round(time.monotonic() - attempt_started, 2)})
            break
        except urllib.error.HTTPError as exc:
            raw_body = exc.read().decode("utf-8", errors="replace")
            last_error = f"HTTP {exc.code}: {summarise_error(raw_body)}"
            attempt_log.append({"attempt": attempt, "http_status": exc.code, "error": last_error[:300],
                                "seconds": round(time.monotonic() - attempt_started, 2)})
            is_html = "<html" in raw_body.lower() or "<!doctype" in raw_body.lower()
            if exc.code == 403 and is_html:
                last_error += (
                    "  -> the provider's firewall blocked the request before any model ran; "
                    "this is not a token problem"
                )
            elif exc.code in (401, 403):
                last_error += "  -> check the token with: python -m clic_extract.pin check-token"
            retriable = exc.code in (408, 429, 500, 502, 503, 504)
            if not retriable or attempt == max_attempts:
                raise fail(last_error) from None
            retry_after = exc.headers.get("Retry-After")
            if retry_after and retry_after.isdigit():
                wait = min(int(retry_after), 60)
        except (urllib.error.URLError, TimeoutError, ConnectionError) as exc:
            last_error = f"network error: {exc}"
            attempt_log.append({"attempt": attempt, "http_status": None, "error": last_error[:300],
                                "seconds": round(time.monotonic() - attempt_started, 2)})
            if attempt == max_attempts:
                raise fail(last_error) from None
        time.sleep(wait)

    seconds = round(time.monotonic() - started, 2)
    usage = reply.get("usage") or {} if isinstance(reply, dict) else {}
    entry.update(usage=usage, **usage_details(usage), seconds=seconds,
                 model_reported=reply.get("model") if isinstance(reply, dict) else None)
    try:
        choice = reply["choices"][0]
        content = choice["message"].get("content")
    except (KeyError, IndexError, TypeError):
        raise fail(f"unexpected response shape: {str(reply)[:300]}") from None
    entry.update(ok=True, finish_reason=choice.get("finish_reason"))
    _record(entry)
    prompt_tokens, completion_tokens = usage.get("prompt_tokens"), usage.get("completion_tokens")
    return {
        "content": content,
        # Reasoning models (for example Granite 4.2) put their prose in a separate field; kept so a
        # free-form run can save what the model actually wrote, not only the final answer.
        "reasoning": choice["message"].get("reasoning_content") or choice["message"].get("reasoning"),
        "finish_reason": choice.get("finish_reason"),
        "seconds": seconds,
        "attempts": attempt,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "cost_usd": cost_usd(arm, prompt_tokens, completion_tokens),
        "model_reported": reply.get("model"),
    }
