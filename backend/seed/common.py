"""Shared RNG, Faker instance, and helpers for all seed generators."""
import hashlib
import hmac
import os
import random
from datetime import date, datetime, timezone

from faker import Faker

SEED = 26263
RNG = random.Random(SEED)

fake = Faker("en_IN")
Faker.seed(SEED)

REGIONS = ["North", "South", "East", "West", "Central", "North-East"]

STATES_BY_REGION = {
    "North": ["Delhi", "Haryana", "Punjab", "Uttar Pradesh", "Uttarakhand", "Himachal Pradesh"],
    "South": ["Karnataka", "Tamil Nadu", "Kerala", "Andhra Pradesh", "Telangana"],
    "East": ["West Bengal", "Bihar", "Odisha", "Jharkhand"],
    "West": ["Maharashtra", "Gujarat", "Rajasthan"],
    "Central": ["Madhya Pradesh", "Chhattisgarh"],
    "North-East": ["Assam", "Manipur", "Meghalaya", "Tripura"],
}

INTAKES = [60, 90, 120, 180, 240]
INST_TYPES = ["Private", "Government", "Autonomous"]

DOMAINS = {
    "Engineering and Technology": {
        "UG": ["B.Tech CSE", "B.Tech ECE", "B.Tech Mechanical", "B.Tech Civil", "B.Tech EE"],
        "Diploma": ["Diploma in CSE", "Diploma in Mechanical"],
        "PG": ["M.Tech CSE", "M.Tech ECE"],
    },
    "Management": {
        "MBA/PGDM": ["MBA", "PGDM"],
        "UG": ["BBA"],
    },
    "Computer Applications": {
        "MCA": ["MCA"],
        "UG": ["BCA"],
    },
}

ACADEMIC_YEARS = ["2025-26", "2026-27"]


def apaar_id(rng: random.Random) -> str:
    """Generate a 12-digit synthetic APAAR ID."""
    first = rng.randint(1, 9)
    rest = "".join(str(rng.randint(0, 9)) for _ in range(11))
    return str(first) + rest


def hmac_token(value: str) -> str:
    key = os.environ.get("HMAC_KEY", "change-me-hmac").encode()
    return hmac.new(key, value.encode(), hashlib.sha256).hexdigest()


def fake_phone(rng: random.Random) -> str:
    prefix = rng.choice(["98", "97", "96", "95", "94", "93", "92", "91", "90", "89", "88", "87"])
    return prefix + "".join(str(rng.randint(0, 9)) for _ in range(8))


def fake_name(rng: random.Random) -> str:
    return fake.name()


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def date_between(rng: random.Random, start: date, end: date) -> date:
    delta = (end - start).days
    return start.replace(day=1) + __import__("datetime").timedelta(days=rng.randint(0, max(delta, 0)))
