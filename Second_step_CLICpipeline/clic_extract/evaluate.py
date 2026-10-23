"""Score each arm against hand-checked gold files and flag what a light model cannot do.

    python -m clic_extract.evaluate --arms B C                        # gold/ vs output/
    python -m clic_extract.evaluate --arms B C --gold-dir samples/gold  # smoke test

Gold files are <stem>.json in the final schema, one per input <stem>.md.
For every field:
    accuracy      = share of documents where the answer equals gold (null == null counts)
    hallucinated  = share of gold-null values that the model filled anyway
    verdict       = "OK" if accuracy >= 90% and hallucinated < 5%, else "NOT OK"
"""

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path

from .schema import FACT_KEYS, PROPOSAL_KEYS

ACC_MIN, HALLUC_MAX, SMALL_N = 0.90, 0.05, 5


def norm(v):
    if isinstance(v, str):
        return " ".join(v.split()).casefold()
    return v


def latest(arm_dir, stem, suffix):
    pattern = re.compile(rf"^{re.escape(stem)}_\d{{8}}T\d{{6}}Z{re.escape(suffix)}$")
    hits = sorted(p for p in arm_dir.glob(f"{stem}_*") if pattern.match(p.name))
    return hits[-1] if hits else None


class Tally:
    def __init__(self):
        self.n = self.correct = self.gold_null = self.halluc = self.gold_val = self.missed = self.wrong = 0

    def add(self, gold, pred):
        g, p = norm(gold), norm(pred)
        self.n += 1
        if g is None:
            self.gold_null += 1
            if p is not None:
                self.halluc += 1
        else:
            self.gold_val += 1
            if p is None:
                self.missed += 1
            elif p != g:
                self.wrong += 1
        if g == p:
            self.correct += 1

    def accuracy(self):
        return self.correct / self.n if self.n else None

    def halluc_rate(self):
        return self.halluc / self.gold_null if self.gold_null else None

    def verdict(self):
        acc, hal = self.accuracy(), self.halluc_rate()
        if acc is None:
            return "n/a"
        ok = acc >= ACC_MIN and (hal is None or hal < HALLUC_MAX)
        return "OK" if ok else "NOT OK"


def prf(tp, fp, fn):
    p = tp / (tp + fp) if tp + fp else None
    r = tp / (tp + fn) if tp + fn else None
    f = 2 * p * r / (p + r) if p and r else (0.0 if p is not None and r is not None else None)
    return p, r, f


def score_arm(gold_dir, arm_dir):
    fields = {f"proposal.{k}": Tally() for k in PROPOSAL_KEYS}
    fields.update({f"proposal_facts.{k}": Tally() for k in FACT_KEYS})
    partner_fields = {k: Tally() for k in ("requested_cents",)}
    ptp = pfp = pfn = 0
    docs = ok_docs = 0
    runs = []
    for gold_path in sorted(gold_dir.glob("*.json")):
        stem = gold_path.stem
        docs += 1
        run_path = latest(arm_dir, stem, ".run.json")
        if run_path:
            runs.append(json.loads(run_path.read_text(encoding="utf-8")))
        out_path = latest(arm_dir, stem, ".json")
        if out_path is None:
            continue
        ok_docs += 1
        gold = json.loads(gold_path.read_text(encoding="utf-8"))
        pred = json.loads(out_path.read_text(encoding="utf-8"))
        for k in PROPOSAL_KEYS:
            fields[f"proposal.{k}"].add(gold["proposal"].get(k), pred["proposal"].get(k))
        for k in FACT_KEYS:
            fields[f"proposal_facts.{k}"].add(gold["proposal_facts"].get(k), pred["proposal_facts"].get(k))
        gp = {norm(p["partner_name"]): p for p in gold["partners"]}
        pp = {norm(p["partner_name"]): p for p in pred["partners"]}
        ptp += len(gp.keys() & pp.keys())
        pfp += len(pp.keys() - gp.keys())
        pfn += len(gp.keys() - pp.keys())
        for name in gp.keys() & pp.keys():
            for k, tally in partner_fields.items():
                tally.add(gp[name].get(k), pp[name].get(k))
    return {
        "fields": fields,
        "partner_fields": partner_fields,
        "partners_prf": prf(ptp, pfp, pfn),
        "docs": docs,
        "ok_docs": ok_docs,
        "runs": runs,
    }


def pct(v):
    return "n/a" if v is None else f"{100 * v:.0f}%"


def render(arms_scores, arms_cfg):
    lines = ["# Extraction report", ""]
    lines.append(f"Generated {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}. "
                 f"Rule: a field is OK when accuracy >= {ACC_MIN:.0%} and it fills < {HALLUC_MAX:.0%} of gold-null values.")
    lines.append("")
    lines.append("## Runs")
    lines.append("| arm | model / provider | gold docs | valid output | avg sec/doc | total cost | avg cost/doc |")
    lines.append("|---|---|---|---|---|---|---|")
    for arm, s in arms_scores.items():
        cfg = arms_cfg.get(arm, {})
        runs = [r for r in s["runs"] if r.get("status") == "ok"]
        secs = [r["seconds"] for r in runs if r.get("seconds") is not None]
        costs = [r["cost_usd"] for r in runs if r.get("cost_usd") is not None]
        lines.append(
            f"| {arm} | {cfg.get('model', '?')} / {cfg.get('provider', '?')} | {s['docs']} | {s['ok_docs']}/{s['docs']} "
            f"| {sum(secs) / len(secs):.1f} | ${sum(costs):.4f} | ${sum(costs) / len(costs):.4f} |"
            if runs else f"| {arm} | {cfg.get('model', '?')} / {cfg.get('provider', '?')} | {s['docs']} | {s['ok_docs']}/{s['docs']} | - | - | - |"
        )
    lines.append("")
    names = list(arms_scores)
    lines.append("## Field verdicts (accuracy / hallucinated-on-null / verdict)")
    lines.append("| field | " + " | ".join(names) + " |")
    lines.append("|---|" + "---|" * len(names))
    all_fields = list(next(iter(arms_scores.values()))["fields"])
    for f in all_fields:
        cells = []
        for arm in names:
            t = arms_scores[arm]["fields"][f]
            cells.append(f"{pct(t.accuracy())} / {pct(t.halluc_rate())} / {t.verdict()}")
        lines.append(f"| {f} | " + " | ".join(cells) + " |")
    for f in ("requested_cents",):
        cells = []
        for arm in names:
            t = arms_scores[arm]["partner_fields"][f]
            cells.append(f"{pct(t.accuracy())} / {pct(t.halluc_rate())} / {t.verdict()}")
        lines.append(f"| partners.{f} (matched partners) | " + " | ".join(cells) + " |")
    lines.append("")
    lines.append("## Lists (precision / recall / F1)")
    lines.append("| list | " + " | ".join(names) + " |")
    lines.append("|---|" + "---|" * len(names))
    for label, key in (("partners (by name)", "partners_prf"),):
        cells = [" / ".join(pct(x) for x in arms_scores[a][key]) for a in names]
        lines.append(f"| {label} | " + " | ".join(cells) + " |")
    lines.append("")
    lines.append("## Verdict for a light model")
    for arm in names:
        s = arms_scores[arm]
        bad = [f for f, t in s["fields"].items() if t.verdict() == "NOT OK"]
        bad += [f"partners.{f}" for f, t in s["partner_fields"].items() if t.verdict() == "NOT OK"]
        small = f" (only {s['ok_docs']} document(s): indicative, not conclusive)" if s["ok_docs"] < SMALL_N else ""
        if s["ok_docs"] == 0:
            lines.append(f"- **{arm}**: no valid outputs to score.")
        elif bad:
            lines.append(f"- **{arm}**: NOT suitable for these fields: {', '.join(bad)}{small}")
        else:
            lines.append(f"- **{arm}**: meets the rule on every field{small}")
    return "\n".join(lines) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--arms", nargs="+", required=True)
    ap.add_argument("--gold-dir", default="gold")
    ap.add_argument("--output", default="output")
    ap.add_argument("--no-save", action="store_true", help="print only; do not write output/report_<timestamp>.md")
    args = ap.parse_args(argv)

    gold_dir = Path(args.gold_dir)
    if not list(gold_dir.glob("*.json")):
        raise SystemExit(f"no gold files in {gold_dir}. Add <stem>.json files (final schema) for the documents to score.")
    from .backends import load_arms

    scores = {arm: score_arm(gold_dir, Path(args.output) / arm) for arm in args.arms}
    report = render(scores, load_arms())
    print(report)
    if not args.no_save:
        path = Path(args.output) / f"report_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(report, encoding="utf-8")
        print(f"saved {path}")


if __name__ == "__main__":
    main()
