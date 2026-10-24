"""M5 — Generate sample upload CSV files for Phase 3 demo.

Files produced in seed/uploads/:
  A_lawful_276.csv      INST-0002 — 240 REGULAR + 24 OCI_FN_EXTRA + 12 CIWGC_EXTRA
  B_domestic_in_extra.csv   Same but 5 OCI rows have nationality_status=INDIAN
  C_over_max_282.csv    INST-0003 — 246 REGULAR (incl 6 NRI_IN) + 24 OCI + 12 CIWGC
  D_bad_format.csv      INST-0001 — format errors (E101-E106)
  E_duplicates.csv      INST-0001 — duplicate cases D1-D5
  F_missing_apaar.csv   INST-0006 — 40% rows no APAAR (W201, T3)
  G_large_5000.csv      INST-0001 — 5000 rows across courses
  H_resubmit_fixed.csv  Corrected version of D_bad_format.csv
  I_registry_down.csv   INST-0001 — APAAR IDs ending in 999
  template.csv          Header + one example row
"""
import csv
import random
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from seed.common import SEED, fake

DEMO_DATE = date(2026, 10, 24)
HEADER = [
    "student_ref", "full_name", "date_of_birth", "apaar_id",
    "nationality_status", "seat_category", "course_code",
    "admission_date", "mode", "timing_slot", "admission_round",
    "entry_type", "gender", "contact_phone", "guardian_name",
]

OUT_DIR = Path(__file__).parent / "uploads"


def _apaar(rng: random.Random, ends_999: bool = False) -> str:
    if ends_999:
        first = rng.randint(1, 9)
        mid = "".join(str(rng.randint(0, 9)) for _ in range(8))
        return str(first) + mid + "999"
    first = rng.randint(1, 9)
    rest = "".join(str(rng.randint(0, 9)) for _ in range(11))
    return str(first) + rest


def _dob(rng: random.Random) -> str:
    age = rng.randint(17, 28)
    d = DEMO_DATE - timedelta(days=age * 365 + rng.randint(0, 364))
    return d.isoformat()


def _row(
    rng: random.Random,
    ref: str,
    course_code: str,
    seat_cat: str,
    nationality: str,
    apaar: str = "",
    opts: dict | None = None,
) -> dict:
    opts = opts or {}
    return {
        "student_ref": ref,
        "full_name": fake.name(),
        "date_of_birth": _dob(rng),
        "apaar_id": apaar,
        "nationality_status": nationality,
        "seat_category": seat_cat,
        "course_code": course_code,
        "admission_date": opts.get("admission_date", "2026-07-15"),
        "mode": opts.get("mode", "FULL_TIME"),
        "timing_slot": "",
        "admission_round": opts.get("admission_round", "ROUND_1"),
        "entry_type": "REGULAR",
        "gender": rng.choice(["M", "F", "O"]),
        "contact_phone": "",
        "guardian_name": "",
    }


def _write(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=HEADER)
        w.writeheader()
        w.writerows(rows)
    print(f"  {path.name}: {len(rows)} rows")


def run() -> None:
    rng = random.Random(SEED)
    print("[gen_uploads] Generating sample CSV files …")

    # ── A: lawful 276 (INST-0002 / CRS-0002-CSE) ─────────────────────────────
    rows = []
    for i in range(240):
        rows.append(_row(rng, f"A-R-{i:04d}", "CRS-0002-CSE", "REGULAR", "INDIAN", _apaar(rng)))
    for i in range(24):
        rows.append(_row(rng, f"A-O-{i:04d}", "CRS-0002-CSE", "OCI_FN_EXTRA", "OCI", _apaar(rng)))
    for i in range(12):
        rows.append(_row(rng, f"A-C-{i:04d}", "CRS-0002-CSE", "CIWGC_EXTRA", "CIWGC", _apaar(rng)))
    _write(OUT_DIR / "A_lawful_276.csv", rows)

    # ── B: 5 OCI rows have nationality=INDIAN (should produce C3 flags) ──────
    rows = []
    for i in range(240):
        rows.append(_row(rng, f"B-R-{i:04d}", "CRS-0002-CSE", "REGULAR", "INDIAN", _apaar(rng)))
    for i in range(24):
        nat = "INDIAN" if i < 5 else "OCI"
        rows.append(_row(rng, f"B-O-{i:04d}", "CRS-0002-CSE", "OCI_FN_EXTRA", nat, _apaar(rng)))
    for i in range(12):
        rows.append(_row(rng, f"B-C-{i:04d}", "CRS-0002-CSE", "CIWGC_EXTRA", "CIWGC", _apaar(rng)))
    _write(OUT_DIR / "B_domestic_in_extra.csv", rows)

    # ── C: over max 282 (INST-0003 / CRS-0003-CSE) ───────────────────────────
    rows = []
    for i in range(240):
        rows.append(_row(rng, f"C-R-{i:04d}", "CRS-0003-CSE", "REGULAR", "INDIAN", _apaar(rng)))
    for i in range(6):
        rows.append(_row(rng, f"C-N-{i:04d}", "CRS-0003-CSE", "NRI_IN", "NRI", _apaar(rng)))
    for i in range(24):
        rows.append(_row(rng, f"C-O-{i:04d}", "CRS-0003-CSE", "OCI_FN_EXTRA", "OCI", _apaar(rng)))
    for i in range(12):
        rows.append(_row(rng, f"C-C-{i:04d}", "CRS-0003-CSE", "CIWGC_EXTRA", "CIWGC", _apaar(rng)))
    _write(OUT_DIR / "C_over_max_282.csv", rows)

    # ── D: bad format rows (INST-0001 / CRS-0001-CSE) ────────────────────────
    bad_rows = []
    # E101 — missing required field (full_name missing)
    bad_rows.append({
        "student_ref": "D-BAD-001", "full_name": "", "date_of_birth": "2003-05-12",
        "apaar_id": _apaar(rng), "nationality_status": "INDIAN", "seat_category": "REGULAR",
        "course_code": "CRS-0001-CSE", "admission_date": "2026-07-15", "mode": "FULL_TIME",
        "timing_slot": "", "admission_round": "ROUND_1", "entry_type": "REGULAR",
        "gender": "M", "contact_phone": "", "guardian_name": "",
    })
    # E102 — 10-digit APAAR
    bad_rows.append(_row(rng, "D-BAD-002", "CRS-0001-CSE", "REGULAR", "INDIAN", "1234567890"))
    # E103 — invalid date
    bad_rows.append({
        "student_ref": "D-BAD-003", "full_name": fake.name(), "date_of_birth": "not-a-date",
        "apaar_id": _apaar(rng), "nationality_status": "INDIAN", "seat_category": "REGULAR",
        "course_code": "CRS-0001-CSE", "admission_date": "2026-07-15", "mode": "FULL_TIME",
        "timing_slot": "", "admission_round": "ROUND_1", "entry_type": "REGULAR",
        "gender": "F", "contact_phone": "", "guardian_name": "",
    })
    # E104 — unknown course code
    bad_rows.append(_row(rng, "D-BAD-004", "UNKNOWN-COURSE", "REGULAR", "INDIAN", _apaar(rng)))
    # E105 — invalid seat category
    bad_rows.append({
        "student_ref": "D-BAD-005", "full_name": fake.name(), "date_of_birth": "2003-05-12",
        "apaar_id": _apaar(rng), "nationality_status": "INDIAN", "seat_category": "INVALID_CAT",
        "course_code": "CRS-0001-CSE", "admission_date": "2026-07-15", "mode": "FULL_TIME",
        "timing_slot": "", "admission_round": "ROUND_1", "entry_type": "REGULAR",
        "gender": "M", "contact_phone": "", "guardian_name": "",
    })
    # E106 — duplicate student_ref
    good = _row(rng, "D-DUP-REF", "CRS-0001-CSE", "REGULAR", "INDIAN", _apaar(rng))
    bad_rows.append(good)
    bad_rows.append(dict(good))  # same ref
    # 3 valid rows to keep
    for i in range(3):
        bad_rows.append(_row(rng, f"D-OK-{i:03d}", "CRS-0001-CSE", "REGULAR", "INDIAN", _apaar(rng)))
    _write(OUT_DIR / "D_bad_format.csv", bad_rows)

    # ── H: corrected version of D ─────────────────────────────────────────────
    good_rows = []
    for i in range(8):
        good_rows.append(_row(rng, f"H-OK-{i:03d}", "CRS-0001-CSE", "REGULAR", "INDIAN", _apaar(rng)))
    _write(OUT_DIR / "H_resubmit_fixed.csv", good_rows)

    # ── E: duplicate cases D1-D5 ──────────────────────────────────────────────
    dup_rows = []
    # D1 — same student_ref twice in file
    r = _row(rng, "E-D1-001", "CRS-0001-CSE", "REGULAR", "INDIAN", _apaar(rng))
    dup_rows.append(r)
    dup_rows.append(dict(r))  # exact duplicate ref = D1
    # D4 — same name + DOB (high fuzzy score, no APAAR)
    name_d4 = "Rahul Kumar"
    dob_d4 = "2003-06-15"
    dup_rows.append({**_row(rng, "E-D4-001", "CRS-0001-CSE", "REGULAR", "INDIAN", ""),
                     "full_name": name_d4, "date_of_birth": dob_d4})
    dup_rows.append({**_row(rng, "E-D4-002", "CRS-0001-CSE", "REGULAR", "INDIAN", ""),
                     "full_name": "Rahul Kumar", "date_of_birth": dob_d4})
    # D5 — similar name + DOB (moderate fuzzy score, no APAAR)
    dup_rows.append({**_row(rng, "E-D5-001", "CRS-0001-CSE", "REGULAR", "INDIAN", ""),
                     "full_name": "Priya Sharma", "date_of_birth": "2004-02-20"})
    dup_rows.append({**_row(rng, "E-D5-002", "CRS-0001-CSE", "REGULAR", "INDIAN", ""),
                     "full_name": "Priya Sharmaa", "date_of_birth": "2004-02-20"})
    # A few clean rows
    for i in range(4):
        dup_rows.append(_row(rng, f"E-OK-{i:03d}", "CRS-0001-CSE", "REGULAR", "INDIAN", _apaar(rng)))
    _write(OUT_DIR / "E_duplicates.csv", dup_rows)

    # ── F: missing APAAR — 40% of rows (INST-0006 / CRS-0006-MCA) ────────────
    f_rows = []
    for i in range(50):
        has_apaar = rng.random() > 0.4
        f_rows.append(_row(rng, f"F-{i:04d}", "CRS-0006-MCA", "REGULAR", "INDIAN",
                           _apaar(rng) if has_apaar else ""))
    _write(OUT_DIR / "F_missing_apaar.csv", f_rows)

    # ── G: large 5000 rows (INST-0001, multiple courses) ─────────────────────
    courses = ["CRS-0001-CSE", "CRS-0001-ECE", "CRS-0001-ME"]
    g_rows = []
    for i in range(5000):
        course = courses[i % len(courses)]
        g_rows.append(_row(rng, f"G-{i:06d}", course, "REGULAR", "INDIAN", _apaar(rng)))
    _write(OUT_DIR / "G_large_5000.csv", g_rows)

    # ── I: registry down — APAAR IDs ending in 999 ───────────────────────────
    i_rows = []
    for i in range(10):
        i_rows.append(_row(rng, f"I-DOWN-{i:04d}", "CRS-0001-CSE", "REGULAR", "INDIAN",
                           _apaar(rng, ends_999=True)))
    for i in range(5):
        i_rows.append(_row(rng, f"I-OK-{i:04d}", "CRS-0001-CSE", "REGULAR", "INDIAN", _apaar(rng)))
    _write(OUT_DIR / "I_registry_down.csv", i_rows)

    # ── template ──────────────────────────────────────────────────────────────
    template_rows = [{
        "student_ref": "EXAMPLE-001",
        "full_name": "Aryan Sharma",
        "date_of_birth": "2003-04-15",
        "apaar_id": "123456789012",
        "nationality_status": "INDIAN",
        "seat_category": "REGULAR",
        "course_code": "CRS-0001-CSE",
        "admission_date": "2026-07-15",
        "mode": "FULL_TIME",
        "timing_slot": "",
        "admission_round": "ROUND_1",
        "entry_type": "REGULAR",
        "gender": "M",
        "contact_phone": "",
        "guardian_name": "",
    }]
    _write(OUT_DIR / "template.csv", template_rows)

    print("[gen_uploads] Done.")


if __name__ == "__main__":
    run()
