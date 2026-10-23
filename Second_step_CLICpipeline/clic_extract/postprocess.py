"""Deterministic clean-up of the model's raw answer into the final JSON.

Everything a small model is bad at (money arithmetic, date formats, enum drift)
is done here in plain Python. Every doubtful value becomes null plus a warning;
nothing is inferred.
"""

import json
import re
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation

_NULLISH = {
    "", "null", "none", "n/a", "na", "not stated", "not specified",
    "not available", "unknown", "-", "—", "–",
}
_CURRENCY = re.compile(r"(?i)\b(?:eur|euros?)\b|[€$£]")
_MULTIPLIER = re.compile(r"(?i)(?<=\d)\s*(million|mio|mln|m|thousand|k)\b\.?")
_DIGIT_SPACES = re.compile(r"(?<=\d)[\s  '’](?=\d)")


# --------------------------------------------------------------------------- money
def parse_amount_to_cents(value):
    """Return (cents, warning). Text like 'EUR 590,625.00' -> 59062500.

    Conventions (documented because they are judgement calls):
      * both '.' and ',' present: the last one is the decimal separator;
      * a single ',' followed by exactly 3 digits is a thousands separator
        ('500,000' -> 500000, as in the brief's example);
      * a single '.' followed by exactly 3 digits is ambiguous ('1.234' may be
        1234 or 1.234) -> null + warning;
      * a decimal part that is not a whole number of cents -> null + warning.
    """
    if value is None:
        return None, None
    if isinstance(value, bool):
        return None, "boolean is not an amount"
    if isinstance(value, int):
        return value * 100, None
    text = repr(value) if isinstance(value, float) else str(value)
    text = text.strip()
    if text.casefold() in _NULLISH:
        return None, None
    original = text

    if re.search(r"(?<![\w])[-−]\s*\d", text):
        return None, f"negative amount {original!r} set to null"

    multiplier = 1
    mult = _MULTIPLIER.search(text)
    if mult:
        word = mult.group(1).casefold()
        multiplier = 1_000_000 if word in ("million", "mio", "mln", "m") else 1_000
        text = text[: mult.start()] + text[mult.end():]

    text = _CURRENCY.sub("", text)
    text = _DIGIT_SPACES.sub("", text).strip()
    text = re.sub(r"[.,]?[-–—]+$", "", text).strip()  # '500,000.-'
    text = re.sub(r"[.,;]+$", "", text).strip()

    if not re.fullmatch(r"\d+(?:[.,]\d+)*", text):
        return None, f"could not parse amount {original!r}"

    dots, commas = text.count("."), text.count(",")
    frac = ""
    if dots and commas:
        last = max(text.rfind("."), text.rfind(","))
        dec_sep = text[last]
        thou_sep = "," if dec_sep == "." else "."
        int_part, frac = text[:last], text[last + 1:]
        if dec_sep in int_part or not re.fullmatch(
            rf"\d{{1,3}}(?:{re.escape(thou_sep)}\d{{3}})*", int_part
        ):
            return None, f"irregular digit grouping in {original!r}"
        int_digits = int_part.replace(thou_sep, "")
    elif dots or commas:
        sep = "." if dots else ","
        if text.count(sep) > 1:
            if not re.fullmatch(rf"\d{{1,3}}(?:{re.escape(sep)}\d{{3}})+", text):
                return None, f"irregular digit grouping in {original!r}"
            int_digits = text.replace(sep, "")
        else:
            left, right = text.split(sep)
            three = len(right) == 3 and multiplier == 1
            if three and sep == "." and left != "0":
                return None, (
                    f"ambiguous amount {original!r}: '.' may be a thousands or "
                    "decimal separator; set to null"
                )
            if three and sep == "," and left != "0" and 1 <= len(left) <= 3:
                int_digits = left + right  # English thousands separator
            else:
                int_digits, frac = left, right
    else:
        int_digits = text

    try:
        amount = Decimal(int_digits + ("." + frac if frac else ""))
    except InvalidOperation:
        return None, f"could not parse amount {original!r}"
    cents = amount * multiplier * 100
    if cents != cents.to_integral_value():
        return None, f"amount {original!r} is not a whole number of cents; set to null"
    return int(cents), None


# --------------------------------------------------------------------------- scalars
def clean_text(value, name="", warnings=None):
    if value is None:
        return None
    text = " ".join(str(value).split())
    if text.casefold() in _NULLISH:
        if text and warnings is not None:
            warnings.append(f"{name}: {text!r} treated as null")
        return None
    return text


def normalise_int(value, lo, hi, name):
    if value is None:
        return None, None
    if isinstance(value, bool):
        return None, f"{name}: boolean {value!r} set to null"
    if isinstance(value, float) and value.is_integer():
        value = int(value)
    elif isinstance(value, str) and re.fullmatch(r"\s*\d+\s*", value):
        value = int(value)
    if not isinstance(value, int):
        return None, f"{name}: {value!r} is not an integer; set to null"
    if not lo <= value <= hi:
        return None, f"{name}: {value} outside {lo}-{hi}; set to null"
    return value, None


_DATE_FORMATS = ("%d %B %Y", "%d %b %Y", "%B %d, %Y", "%b %d, %Y", "%B %d %Y", "%Y/%m/%d", "%d.%m.%Y")


def normalise_date(value, name="submission_date"):
    if value is None:
        return None, None
    text = " ".join(str(value).split())
    if text.casefold() in _NULLISH:
        return None, None
    m = re.match(r"^(\d{4}-\d{2}-\d{2})(?:[T ]|$)", text)
    if m:
        try:
            date.fromisoformat(m.group(1))
            return m.group(1), None
        except ValueError:
            return None, f"{name}: {text!r} is not a real calendar date; set to null"
    stripped = re.sub(r"(?<=\d)(?:st|nd|rd|th)\b", "", text)
    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(stripped, fmt).date().isoformat(), None
        except ValueError:
            pass
    m = re.fullmatch(r"(\d{1,2})/(\d{1,2})/(\d{4})", stripped)
    if m:
        a, b, year = int(m.group(1)), int(m.group(2)), int(m.group(3))
        try:
            if a > 12 or a == b:
                return date(year, b, a).isoformat(), None
            if b > 12:
                return date(year, a, b).isoformat(), None
        except ValueError:
            pass
        return None, f"{name}: {text!r} is ambiguous (day/month); set to null"
    return None, f"{name}: could not parse {text!r}; set to null"


# --------------------------------------------------------------------------- JSON
def extract_json(text):
    """Pull the JSON object out of a model reply (fences, <think> blocks, chatter)."""
    if text is None:
        raise ValueError("empty reply")
    text = re.sub(r"(?s)<think>.*?</think>", "", text)
    # Free-form replies reason in prose before the answer; the last fenced json block is the answer,
    # and prose braces before it must not be mistaken for the start of the object.
    fenced = re.findall(r"(?s)```json\s*(.*?)```", text)
    if fenced:
        block = fenced[-1]
        start, end = block.find("{"), block.rfind("}")
        if start != -1 and end > start:
            return json.loads(block[start : end + 1])
    text = re.sub(r"```(?:json)?", "", text)
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end <= start:
        raise ValueError("no JSON object found in reply")
    return json.loads(text[start : end + 1])


# --------------------------------------------------------------------------- grounding
def _norm_doc(text):
    return re.sub(r"\s+", " ", re.sub(r"[*_`]", "", text or "")).casefold()


def _grounded_text(value, doc_norm):
    return _norm_doc(value) in doc_norm


def _grounded_amount(value, doc_nospace):
    token = re.search(r"\d[\d.,\s'’  ]*\d|\d", str(value))
    if not token:
        return True
    return re.sub(r"[\s'’  ]", "", token.group(0)) in doc_nospace


# --------------------------------------------------------------------------- assembly
def build_final(raw, document_text, source_file, now=None):
    """Turn the model's raw dict into the final document. Returns (final, warnings)."""
    warnings = []
    if not isinstance(raw, dict):
        warnings.append("model output is not a JSON object; everything set to null")
        raw = {}
    now = now or datetime.now(timezone.utc)
    has_document_text = document_text is not None
    doc_norm = _norm_doc(document_text) if has_document_text else ""
    doc_nospace = re.sub(r"[\s'’  ]", "", document_text) if has_document_text else ""

    def section(name):
        value = raw.get(name)
        return value if isinstance(value, dict) else {}

    rp, rf = section("proposal"), section("proposal_facts")

    proposal = {
        "proposal_acronym": clean_text(rp.get("proposal_acronym"), "proposal_acronym", warnings),
        "proposal_title": clean_text(rp.get("proposal_title"), "proposal_title", warnings),
        "call_identifier": clean_text(rp.get("call_identifier"), "call_identifier", warnings),
        "submission_date": None,
    }
    proposal["submission_date"], w = normalise_date(rp.get("submission_date"))
    if w:
        warnings.append(w)
    for key in ("proposal_acronym", "proposal_title", "call_identifier"):
        if has_document_text and proposal[key] and not _grounded_text(proposal[key], doc_norm):
            warnings.append(f"{key} {proposal[key]!r} not found verbatim in the document")

    facts = {}
    facts["requested_total_cents"], w = parse_amount_to_cents(rf.get("requested_total"))
    if w:
        warnings.append(f"requested_total: {w}")
    if has_document_text and rf.get("requested_total") is not None and facts["requested_total_cents"] is not None \
            and not _grounded_amount(rf["requested_total"], doc_nospace):
        warnings.append(f"requested_total {rf['requested_total']!r} not found in the document")
    for key in ("trl_start", "trl_target", "mcrl_start", "mcrl_target"):
        facts[key], w = normalise_int(rf.get(key), 1, 9, key)
        if w:
            warnings.append(w)
    for a, b in (("trl_start", "trl_target"), ("mcrl_start", "mcrl_target")):
        if facts[a] is not None and facts[b] is not None and facts[a] > facts[b]:
            warnings.append(f"{a} ({facts[a]}) is greater than {b} ({facts[b]})")
    ordered_facts = {
        k: facts[k]
        for k in ("requested_total_cents", "trl_start", "trl_target", "mcrl_start", "mcrl_target")
    }

    partners, seen = [], set()
    raw_partners = raw.get("partners")
    for item in raw_partners if isinstance(raw_partners, list) else []:
        if not isinstance(item, dict):
            continue
        name = clean_text(item.get("partner_name"))
        if not name:
            warnings.append("partner without a name dropped")
            continue
        if name.casefold() in seen:
            warnings.append(f"duplicate partner {name!r} dropped")
            continue
        seen.add(name.casefold())
        if has_document_text and not _grounded_text(name, doc_norm):
            warnings.append(f"partner {name!r} not found verbatim in the document")
        entry = {"partner_name": name}
        entry["requested_cents"], w = parse_amount_to_cents(item.get("requested"))
        if w:
            warnings.append(f"requested[{name}]: {w}")
        if has_document_text and item.get("requested") is not None and entry["requested_cents"] is not None \
                and not _grounded_amount(item["requested"], doc_nospace):
            warnings.append(f"requested[{name}] {item['requested']!r} not found in the document")
        partners.append(entry)

    if partners:
        values = [p["requested_cents"] for p in partners]
        total = ordered_facts["requested_total_cents"]
        if total is not None and all(v is not None for v in values) and sum(values) != total:
            warnings.append(f"sum of partner requested_cents ({sum(values)}) != requested_total_cents ({total})")

    final = {
        "proposal": proposal,
        "proposal_facts": ordered_facts,
        "partners": partners,
        "metadata": {
            "extraction_timestamp": now.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "source_file": source_file,
        },
    }
    return final, warnings
