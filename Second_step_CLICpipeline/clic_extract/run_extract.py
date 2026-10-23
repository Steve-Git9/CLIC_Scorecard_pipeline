"""Run the extraction on markdown files.

    python -m clic_extract.run_extract --arm B --input input
    python -m clic_extract.run_extract --arm B C --input samples/synthetic_proposal.md
    python -m clic_extract.run_extract --arm C --input input --dry-run     # no network, no token

For each document writes, under output/<arm>/:
    <stem>_<UTC timestamp>.json       the extraction (schema from the brief)
    <stem>_<UTC timestamp>.run.json   model, provider, seconds, tokens, cost, warnings
    <stem>_<UTC timestamp>.raw.txt    the raw reply, only when the run failed
"""

import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path

from .backends import BackendError, build_request, chat, get_token, load_arms, verify_token
from .fit import add_result, is_too_large, merge_raw_dicts, split_text
from .postprocess import build_final, extract_json
from .prompts import build_messages
from .schema import RAW_SCHEMA, validate_final


def write_replies(base, replies, run):
    """Save every extraction reply exactly as the model returned it, before any repair, as
    <base>.replies.json (a JSON list of strings, one per extraction call, in call order). The
    evaluation scorer reads it to judge validity at the first attempt. Written for failed runs
    too; an empty list means no extraction call returned a reply."""
    path = base.with_suffix(".replies.json")
    path.write_text(json.dumps(replies, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    run["replies_file"] = path.name


def estimate_tokens(text):
    # Rough (about 3.5 characters per token); only used for a size guard and dry runs.
    return int(len(text) / 3.5)


def collect_inputs(path):
    path = Path(path)
    if path.is_file():
        return [path]
    if path.is_dir():
        return sorted(p for p in path.glob("*.md") if p.is_file())
    raise SystemExit(f"input not found: {path}")


def run_one(arm_name, arm, md_path, out_dir, token, use_extras, now, schema=RAW_SCHEMA, messages_builder=build_messages):
    # schema=None plus a free-form prompt (see clic_extract.freeform) lets the model answer in prose
    # with a JSON block at the end; extract_json and build_final then turn that into the same final
    # JSON as every other arm.
    # "seconds" (set below from chat()'s result) times only the API call itself.
    # "total_seconds" is true wall-clock time for this function, including reading the
    # Markdown file and the local postprocessing steps - it does NOT include converting the
    # source PDF to that Markdown in the first place, since that conversion happens before
    # this function is ever called (see src.pipeline.convert.convert_pdf_to_markdown), is
    # shared across every text arm run on the same document, and would be double-counted if
    # charged again to each one individually.
    started_monotonic = time.monotonic()
    text = md_path.read_text(encoding="utf-8")
    stamp = now.strftime("%Y%m%dT%H%M%SZ")
    base = out_dir / f"{md_path.stem}_{stamp}"
    run = {
        "arm": arm_name,
        "model": arm["model"],
        "provider": arm["provider"],
        "source_file": md_path.name,
        "started_utc": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "status": "failed",
        "error": None,
        "warnings": [],
        "free_form": schema is None,
    }
    replies = []

    def finish(error=None, raw_text=None):
        if error:
            run["error"] = error
        if raw_text is not None:
            base.with_suffix(".raw.txt").write_text(raw_text, encoding="utf-8")
        write_replies(base, replies, run)
        run["total_seconds"] = round(time.monotonic() - started_monotonic, 2)
        base.with_suffix(".run.json").write_text(json.dumps(run, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        return run

    # The whole document is sent in one call. Only if the provider rejects it as too large for the
    # model's context is it split in two (clic_extract.fit.split_text), recursively, and the parts'
    # answers merged; a document that fits is never split.
    run["context_splits"] = 0
    worklist = [text]
    raws, freeform_parts, bad_replies = [], [], []
    while worklist:
        piece = worklist.pop(0)
        try:
            result = chat(arm, messages_builder(piece), schema, token, use_extras=use_extras)
        except BackendError as exc:
            halves = split_text(piece) if is_too_large(exc) else None
            if halves is None:
                return finish(str(exc))
            worklist[0:0] = list(halves)
            run["context_splits"] += 1
            run["warnings"].append(f"a part of {len(piece)} characters was too large for the model's context; "
                                   f"split into {len(halves[0])} and {len(halves[1])} characters")
            continue
        replies.append(result["content"] or "")
        add_result(run, result)
        if schema is None:
            # The free-form answer itself (reasoning plus final reply), before conversion to JSON.
            freeform_parts.append("\n\n".join(p for p in (result.get("reasoning"), result["content"]) if p))
        try:
            raws.append(extract_json(result["content"]))
        except (ValueError, json.JSONDecodeError) as exc:
            note = " (reply was cut off: raise max_tokens)" if result["finish_reason"] == "length" else ""
            bad_replies.append((f"reply is not valid JSON: {exc}{note}", result["content"] or ""))
            if run["context_splits"]:
                run["warnings"].append(f"the reply for part {len(replies)} is not valid JSON: {exc}{note}")

    run["parts"] = len(replies)
    if schema is None and freeform_parts:
        sep = "\n\n=== next part ===\n\n"
        base.with_suffix(".freeform.txt").write_text(sep.join(freeform_parts), encoding="utf-8")
        run["freeform_file"] = base.with_suffix(".freeform.txt").name
    if not raws or (len(replies) == 1 and bad_replies):
        error, raw_text = bad_replies[0] if bad_replies else ("no part produced a reply", "")
        if len(replies) > 1:
            error, raw_text = "no part produced a valid reply", "\n\n".join(r for _, r in bad_replies)
        return finish(error, raw_text=raw_text)
    raw = raws[0] if len(raws) == 1 else merge_raw_dicts(raws)

    final, warnings = build_final(raw, text, md_path.name, now)
    run["warnings"].extend(warnings)
    problems = validate_final(final)
    if problems:
        return finish("final document failed validation: " + "; ".join(problems), raw_text="\n\n".join(replies))

    base.with_suffix(".json").write_text(json.dumps(final, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    run["status"] = "ok"
    run["output_file"] = base.with_suffix(".json").name
    return finish()


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--arm", nargs="+", required=True, help="pinned arm name(s), e.g. B C")
    ap.add_argument("--input", default="input", help="a .md file or a folder of .md files")
    ap.add_argument("--output", default="output")
    ap.add_argument("--dry-run", action="store_true", help="build requests and estimate size; no network, no token")
    ap.add_argument("--no-extras", action="store_true", help="omit the arm's extra request fields (thinking / reasoning controls)")
    ap.add_argument("--limit", type=int, help="process at most N documents")
    args = ap.parse_args(argv)

    arms = load_arms()
    missing = [a for a in args.arm if a not in arms]
    if missing:
        raise SystemExit(f"arm(s) {missing} not pinned. Run: python -m clic_extract.pin set --arm {missing[0]} --provider <name>")
    files = collect_inputs(args.input)[: args.limit]
    if not files:
        raise SystemExit(f"no .md files found in {args.input}")

    token = None
    if not args.dry_run:
        try:
            token = get_token()
            verify_token(token)  # fail once, up front, if Hugging Face rejects the token
        except BackendError as exc:
            raise SystemExit(f"error: {exc}")

    failures = 0
    for arm_name in args.arm:
        arm = arms[arm_name]
        out_dir = Path(args.output) / arm_name
        if not args.dry_run:
            out_dir.mkdir(parents=True, exist_ok=True)
        print(f"== arm {arm_name}: {arm['model']} on {arm['provider']} ==")
        for md in files:
            if args.dry_run:
                text = md.read_text(encoding="utf-8")
                size = len(json.dumps(build_request(arm, build_messages(text), RAW_SCHEMA, not args.no_extras)))
                tokens = estimate_tokens(text)
                est = tokens * arm["input_per_m"] / 1e6 + 2000 * arm["output_per_m"] / 1e6
                print(f"  {md.name}: ~{tokens} tokens in, request {size} bytes, est. cost ~${est:.4f} (assuming 2k output tokens)")
                continue
            run = run_one(arm_name, arm, md, out_dir, token, not args.no_extras, datetime.now(timezone.utc))
            if run["status"] == "ok":
                print(f"  {md.name}: ok  {run['seconds']}s  {run['prompt_tokens']}+{run['completion_tokens']} tokens  "
                      f"${run['cost_usd']}  {len(run['warnings'])} warning(s)")
                for w in run["warnings"]:
                    print(f"      ! {w}")
            else:
                failures += 1
                print(f"  {md.name}: FAILED  {run['error']}")
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
