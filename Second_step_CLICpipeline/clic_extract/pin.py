"""Choose (pin) the provider for an arm.  Uses the public model list; no token needed.

    python -m clic_extract.pin list --model Qwen/Qwen3.5-9B
    python -m clic_extract.pin set  --arm B --provider together
    python -m clic_extract.pin show
    python -m clic_extract.pin check-token      # validates HF_TOKEN in this terminal, never prints it

Structured-output support differs per provider, so each arm is pinned to ONE
provider that lists supports_structured_output and a price.
"""

import argparse
from datetime import date

from .backends import ARM_DEFAULTS, BackendError, fetch_providers, get_token, load_arms, save_arms, verify_token


def _row(p):
    price = p.get("pricing") or {}
    fmt = lambda v, spec=".6g": "-" if v is None else format(v, spec)
    return (
        f"{p['provider']:<15} {p.get('status', '?'):<6} {fmt(p.get('context_length')):>8} "
        f"{fmt(price.get('input')):>7} {fmt(price.get('output')):>7} "
        f"{str(p.get('supports_structured_output', '-')):>10} "
        f"{fmt(p.get('first_token_latency_ms'), '.0f'):>8} {fmt(p.get('throughput'), '.0f'):>8}"
    )


def cmd_list(model):
    providers = fetch_providers(model)
    print(f"{model}   (prices in USD per 1M tokens, listed by Hugging Face)")
    print(f"{'provider':<15} {'status':<6} {'context':>8} {'in':>7} {'out':>7} {'structured':>10} {'ttft_ms':>8} {'tok/s':>8}")
    for p in providers:
        print(_row(p))


def cmd_set(arm_name, provider, model=None):
    defaults = ARM_DEFAULTS[arm_name]
    model = model or defaults["model"]
    entry = next((p for p in fetch_providers(model) if p["provider"] == provider), None)
    if entry is None:
        raise BackendError(f"{provider!r} does not serve {model!r}")
    price = entry.get("pricing") or {}
    problems = []
    if entry.get("status") != "live":
        problems.append("status is not live")
    if not entry.get("supports_structured_output"):
        problems.append("no structured-output support listed")
    if price.get("input") is None or price.get("output") is None:
        problems.append("no price listed")
    if problems:
        raise BackendError(f"cannot pin {provider} for {model}: " + ", ".join(problems))
    arms = load_arms()
    arms[arm_name] = {
        "model": model,
        "provider": provider,
        "role": defaults["role"],
        "max_tokens": defaults["max_tokens"],
        "extra_body": defaults["extra_body"],
        "context_length": entry.get("context_length"),
        "input_per_m": price["input"],
        "output_per_m": price["output"],
        "pinned_on": date.today().isoformat(),
    }
    save_arms(arms)
    print(f"Pinned arm {arm_name}: {model} on {provider} (in ${price['input']}/M, out ${price['output']}/M)")


def cmd_show():
    arms = load_arms()
    if not arms:
        print("No arms pinned yet. Run: python -m clic_extract.pin set --arm B --provider <name>")
    for name, arm in sorted(arms.items()):
        print(f"{name}: {arm['model']} on {arm['provider']}  in ${arm['input_per_m']}/M out ${arm['output_per_m']}/M  "
              f"ctx {arm.get('context_length')}  pinned {arm.get('pinned_on')}")


def cmd_check_token():
    """Validate HF_TOKEN in THIS terminal without ever printing it."""
    token = get_token()  # raises with a clear message if unset or malformed
    print(f"HF_TOKEN is set: {len(token)} characters, format looks right.")
    info = verify_token(token)
    if info is None:
        print("Could not reach huggingface.co to verify it (network problem?).")
        return
    print(f"Hugging Face accepts the token. Account: {info['user']}; token: {info['token_name'] or '(unnamed)'} ({info['role']}).")
    if info["inference_allowed"]:
        print("It is allowed to call Inference Providers.")
    else:
        raise BackendError(
            "the token is valid but does NOT have 'Make calls to Inference Providers'. "
            "Create a fine-grained token with that permission (or a read token)."
        )


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("check-token", help="validate HF_TOKEN in this terminal (never prints it)")
    p_list = sub.add_parser("list", help="show providers for a model")
    p_list.add_argument("--model", required=True)
    p_set = sub.add_parser("set", help="pin a provider for an arm")
    p_set.add_argument("--arm", choices=sorted(ARM_DEFAULTS), required=True)
    p_set.add_argument("--provider", required=True)
    p_set.add_argument("--model", help="override the arm's default model")
    sub.add_parser("show", help="show pinned arms")
    args = ap.parse_args(argv)
    try:
        if args.cmd == "list":
            cmd_list(args.model)
        elif args.cmd == "set":
            cmd_set(args.arm, args.provider, args.model)
        elif args.cmd == "check-token":
            cmd_check_token()
        else:
            cmd_show()
    except BackendError as exc:
        raise SystemExit(f"error: {exc}")


if __name__ == "__main__":
    main()
