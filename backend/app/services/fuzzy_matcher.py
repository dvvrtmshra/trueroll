"""Fuzzy matcher for students without APAAR IDs (spec 6.3).

Score = 0.50 * name_sim + 0.35 * dob_sim + 0.15 * course_year_sim
Threshold >= 0.93 -> D4 review case
Threshold 0.85-0.93 -> D5 watch list
Nothing is auto-flagged at any threshold.
"""
import re
import unicodedata
from datetime import date
from typing import Optional

from rapidfuzz import fuzz
from rapidfuzz.distance import JaroWinkler

HONORIFICS = re.compile(r"\b(dr|mr|mrs|ms|prof|shri|smt|kumari)\b\.?", re.I)

ABBREV = {
    "md": "mohammad",
    "mohammed": "mohammad",
    "kumaar": "kumar",
    "aayush": "ayush",
    "shriya": "shreya",
}


def _normalise(name: str) -> str:
    name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    name = name.lower().strip()
    name = HONORIFICS.sub("", name)
    name = re.sub(r"[^a-z ]", " ", name)
    name = re.sub(r"\s+", " ", name).strip()
    words = [ABBREV.get(w, w) for w in name.split()]
    return " ".join(w for w in words if w)


def _name_sim(a: str, b: str) -> float:
    na, nb = _normalise(a), _normalise(b)
    if not na or not nb:
        return 0.0
    ts = fuzz.token_sort_ratio(na, nb) / 100.0
    jw = JaroWinkler.normalized_similarity(na, nb)
    return max(ts, jw)


def _dob_sim(a: Optional[date], b: Optional[date]) -> float:
    if a is None or b is None:
        return 0.0
    if a == b:
        return 1.0
    if a.year == b.year and a.day == b.month and a.month == b.day:
        return 0.9  # day/month swap
    if a.year == b.year and abs(a.month - b.month) <= 1 and abs(a.day - b.day) <= 1:
        return 0.8  # one digit off
    return 0.0


def score(
    name_a: str,
    dob_a: Optional[date],
    name_b: str,
    dob_b: Optional[date],
    same_course: bool = False,
) -> float:
    ns = _name_sim(name_a, name_b)
    ds = _dob_sim(dob_a, dob_b)
    cs = 1.0 if same_course else 0.0
    return round(0.50 * ns + 0.35 * ds + 0.15 * cs, 4)


def duplicate_class(s: float) -> Optional[str]:
    if s >= 0.93:
        return "D4"
    if s >= 0.85:
        return "D5"
    return None
