"""M16 — 400 true duplicate pairs + 400 near-miss pairs with typos (seed 26263)."""
import random
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from seed.common import SEED, fake

TYPO_TYPES = [
    "spelling_variant",
    "initials",
    "middle_name",
    "case_spaces",
    "transliteration",
    "dob_day_month_swap",
    "dob_digit",
]


def _apply_typo(name: str, dob: date, typo_type: str, rng: random.Random) -> tuple:
    if typo_type == "spelling_variant":
        for orig, repl in [("kumar", "kumaar"), ("mohammad", "md"), ("aayush", "ayush"),
                           ("shriya", "shreya")]:
            if orig in name.lower():
                return name.lower().replace(orig, repl).title(), dob
        return name + " " + rng.choice(["Jr", "Sr"]), dob
    elif typo_type == "initials":
        parts = name.split()
        if len(parts) >= 2:
            return parts[0][0] + ". " + " ".join(parts[1:]), dob
        return name, dob
    elif typo_type == "middle_name":
        parts = name.split()
        if len(parts) == 2:
            return parts[0] + " " + fake.first_name() + " " + parts[1], dob
        elif len(parts) == 3:
            return parts[0] + " " + parts[2], dob
        return name, dob
    elif typo_type == "case_spaces":
        return (name.upper() if rng.random() < 0.5 else name.lower()), dob
    elif typo_type == "transliteration":
        for a, b in [("aa", "a"), ("ee", "i"), ("oo", "u"), ("sh", "s")]:
            if a in name.lower():
                return name.lower().replace(a, b, 1).title(), dob
        return name, dob
    elif typo_type == "dob_day_month_swap":
        if dob.month != dob.day and 1 <= dob.day <= 12:
            try:
                return name, date(dob.year, dob.day, dob.month)
            except ValueError:
                pass
        return name, dob
    elif typo_type == "dob_digit":
        new_day = max(1, min(28, dob.day + rng.choice([-1, 1])))
        try:
            return name, date(dob.year, dob.month, new_day)
        except ValueError:
            return name, dob
    return name, dob


def run(db) -> None:
    from app.models.matching_pair import MatchingPair
    if db.query(MatchingPair).count() > 0:
        print("[gen_matching_pairs] Already seeded — skip")
        return

    rng = random.Random(SEED)
    added = 0

    for _ in range(400):
        name = fake.name()
        dob = fake.date_of_birth(minimum_age=17, maximum_age=30)
        typo_type = rng.choice(TYPO_TYPES)
        name_b, dob_b = _apply_typo(name, dob, typo_type, rng)
        db.add(MatchingPair(
            name_a=name,
            dob_a=dob,
            name_b=name_b,
            dob_b=dob_b,
            is_true_duplicate=True,
            typo_type=typo_type,
            pair_group="true",
        ))
        added += 1

    for _ in range(400):
        db.add(MatchingPair(
            name_a=fake.name(),
            dob_a=fake.date_of_birth(minimum_age=17, maximum_age=30),
            name_b=fake.name(),
            dob_b=fake.date_of_birth(minimum_age=17, maximum_age=30),
            is_true_duplicate=False,
            typo_type=None,
            pair_group="near_miss",
        ))
        added += 1

    db.commit()
    print(f"[gen_matching_pairs] {added} pairs")
