"""Normalisation of gold and extracted values before they are compared.

Written independently of the extraction pipeline's own post-processing, so that a bug there
cannot cancel itself out in the score.

Rules:
    text     case folded, whitespace collapsed; an empty string counts as null
    amount   integer cents. An int is already cents (final schema). A string is an amount as
             written, in euros, and is converted to cents. Floats and booleans are invalid.
    date     ISO 8601 calendar date (YYYY-MM-DD). Unambiguous written forms are converted;
             an ambiguous one (03/04/2024) is invalid.
    integer  int only; booleans and other types are invalid.

A value that cannot be normalised becomes Invalid, which never equals anything, so it scores
as a wrong value (or an unsupported value where the gold value is null).
"""

from __future__ import annotations

import re
from datetime import date
from typing import Any


class Invalid:
    """A value that could not be normalised. Never equal to anything, not even itself."""

    __slots__ = ("raw",)

    def __init__(self, raw: Any) -> None:
        self.raw = raw

    def __eq__(self, other: object) -> bool:
        return False

    def __hash__(self) -> int:
        return id(self)

    def __repr__(self) -> str:
        return f"Invalid({self.raw!r})"


Normalised = Any  # None, str, int or Invalid


def normalise_text(value: Any) -> Normalised:
    if value is None:
        return None
    if not isinstance(value, str):
        return Invalid(value)
    text = " ".join(value.split()).casefold()
    return text or None


def normalise_integer(value: Any) -> Normalised:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int):
        return Invalid(value)
    return value


_CURRENCY = re.compile(r"(?i)\beur(?:os?)?\b|€")
_SPACES = re.compile(r"[\s  ']")


def normalise_amount(value: Any) -> Normalised:
    if value is None:
        return None
    if isinstance(value, bool):
        return Invalid(value)
    if isinstance(value, int):
        return value
    if not isinstance(value, str):
        return Invalid(value)
    text = _SPACES.sub("", _CURRENCY.sub("", value))
    if not re.fullmatch(r"\d+(?:[.,]\d+)*", text):
        return Invalid(value)
    euros, cents = _split_amount(text)
    if euros is None:
        return Invalid(value)
    return euros * 100 + cents


def _split_amount(text: str) -> tuple[int | None, int]:
    """Euros and cents from digits with separators. A part of exactly three digits after a
    separator is a thousands group; one or two digits are cents."""
    seps = [i for i, ch in enumerate(text) if ch in ".,"]
    if not seps:
        return int(text), 0
    last = seps[-1]
    frac = text[last + 1:]
    if len(frac) in (1, 2):
        int_part, cents = text[:last], int(frac.ljust(2, "0"))
    elif len(frac) == 3:
        int_part, cents = text, 0
    else:
        return None, 0
    if any(ch in ".," for ch in int_part):
        thousands = {ch for ch in int_part if ch in ".,"}
        decimal_sep = text[last] if len(frac) in (1, 2) else None
        if len(thousands) != 1 or decimal_sep in thousands:
            return None, 0
        sep = thousands.pop()
        if not re.fullmatch(rf"\d{{1,3}}(?:{re.escape(sep)}\d{{3}})+", int_part):
            return None, 0
        int_part = int_part.replace(sep, "")
    return int(int_part), cents


_MONTHS = {
    name: number
    for number, names in enumerate(
        [
            ("january", "jan"), ("february", "feb"), ("march", "mar"), ("april", "apr"),
            ("may",), ("june", "jun"), ("july", "jul"), ("august", "aug"),
            ("september", "sep", "sept"), ("october", "oct"), ("november", "nov"), ("december", "dec"),
        ],
        start=1,
    )
    for name in names
}


def normalise_date(value: Any) -> Normalised:
    if value is None:
        return None
    if not isinstance(value, str):
        return Invalid(value)
    text = value.strip()
    if not text:
        return None
    parts = _date_parts(text)
    if parts is None:
        return Invalid(value)
    try:
        return date(*parts).isoformat()
    except ValueError:
        return Invalid(value)


def _date_parts(text: str) -> tuple[int, int, int] | None:
    if m := re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})(?:[T ][0-9:.+\-Z]*)?", text):
        return int(m[1]), int(m[2]), int(m[3])
    if m := re.fullmatch(r"(\d{1,2})\.(\d{1,2})\.(\d{4})", text):
        return int(m[3]), int(m[2]), int(m[1])
    if m := re.fullmatch(r"(\d{1,2})/(\d{1,2})/(\d{4})", text):
        a, b = int(m[1]), int(m[2])
        if a > 12 >= b:
            return int(m[3]), b, a
        if b > 12 >= a:
            return int(m[3]), a, b
        return None
    if m := re.fullmatch(r"(?i)(\d{1,2})(?:st|nd|rd|th)?\s+([a-z]+)\.?,?\s+(\d{4})", text):
        month = _MONTHS.get(m[2].casefold())
        return (int(m[3]), month, int(m[1])) if month else None
    if m := re.fullmatch(r"(?i)([a-z]+)\.?\s+(\d{1,2})(?:st|nd|rd|th)?,?\s+(\d{4})", text):
        month = _MONTHS.get(m[1].casefold())
        return (int(m[3]), month, int(m[2])) if month else None
    return None


def compare(gold: Normalised, pred: Normalised) -> str:
    """Outcome of one scored value: correct, miss, unsupported or wrong."""
    if gold is None:
        return "correct" if pred is None else "unsupported"
    if pred is None:
        return "miss"
    return "correct" if gold == pred else "wrong"
