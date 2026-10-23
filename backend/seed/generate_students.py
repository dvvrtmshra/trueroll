"""M3 — Generate ~9,000 synthetic students and admission events.

Hero institution scenarios planted per spec Section 10.1.
"""
import random
import sys
from datetime import date, datetime, timezone
from pathlib import Path
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).parent.parent))

from seed.common import SEED, apaar_id, fake, hmac_token, RNG

from app.models.student import Student
from app.models.admission_event import AdmissionEvent
from app.models.course import CourseApproval
from app.models.institution import Institution

TIER_WEIGHTS = {"T1": 0.55, "T2": 0.12, "T3": 0.25, "T4": 0.08}

# Seat categories aligned with rule buckets
REGULAR_CATS = ["REGULAR", "REGULAR", "REGULAR", "REGULAR", "NRI_IN"]  # weighted toward REGULAR
EXTRA_CATS = ["OCI_FN_EXTRA", "CIWGC_EXTRA"]

NATIONALITY_MAP = {
    "T1": "INDIAN",
    "T2": "INDIAN",
    "T3": "INDIAN",
    "T4": "FOREIGN",  # T4 = foreign nationals or opted-out
}

GENDERS = ["M", "F", "F", "M", "M", "F", None]  # slight variation


def _pick_tier(rng: random.Random) -> str:
    r = rng.random()
    if r < 0.55:
        return "T1"
    if r < 0.67:
        return "T2"
    if r < 0.92:
        return "T3"
    return "T4"


def _pick_seat_category(tier: str, rng: random.Random, extra_slots: int, extra_used: int) -> str:
    if tier == "T4" and extra_used < extra_slots:
        return rng.choice(EXTRA_CATS)
    return rng.choice(["REGULAR", "REGULAR", "REGULAR", "REGULAR", "NRI_IN"])


def _make_student(rng: random.Random, stu_id: str, tier: str) -> Student:
    name = fake.name()
    dob = fake.date_of_birth(minimum_age=17, maximum_age=30)
    gender = rng.choice(GENDERS)
    aid = None
    if tier in ("T1", "T2"):
        aid = apaar_id(rng)

    phone = str(rng.randint(6000000000, 9999999999))
    guardian = fake.name()
    return Student(
        id=stu_id,
        full_name=name,
        date_of_birth=dob,
        gender=gender,
        apaar_id=aid,
        identity_tier=tier,
        contact_token=hmac_token(phone),
        guardian_token=hmac_token(guardian),
    )


def _admit(
    rng: random.Random,
    student_id: str,
    course_id: str,
    cat: str,
    round_: str,
    entry: str,
    year: str,
    at: datetime,
) -> AdmissionEvent:
    return AdmissionEvent(
        id=str(uuid4()),
        student_id=student_id,
        course_approval_id=course_id,
        seat_category=cat,
        event_type="ADMIT",
        admission_round=round_,
        entry_type=entry,
        nationality_status="INDIAN" if cat not in EXTRA_CATS else "FOREIGN",
        event_time=at,
        upload_id=None,
    )


def _seed_course(
    db,
    rng: random.Random,
    course: CourseApproval,
    n_regular: int,
    n_oci: int,
    n_ciwgc: int,
    n_nri: int,
    year: str,
    stu_counter: list,
) -> int:
    base_date = datetime(2026, 7, 1, 9, 0, 0, tzinfo=timezone.utc)

    def _next_id() -> str:
        stu_counter[0] += 1
        return f"STU-{stu_counter[0]:05d}"

    def _at() -> datetime:
        return base_date.__class__.fromtimestamp(
            base_date.timestamp() + rng.randint(0, 90) * 86400, tz=timezone.utc
        )

    # Collect (sid, cat, tier, at) tuples first
    rows: list[tuple] = []
    for cat, n, tier_fn in [
        ("REGULAR", n_regular, None),
        ("NRI_IN", n_nri, lambda: "T1"),
        ("OCI_FN_EXTRA", n_oci, lambda: "T4"),
        ("CIWGC_EXTRA", n_ciwgc, lambda: "T4"),
    ]:
        for _ in range(n):
            sid = _next_id()
            tier = tier_fn() if tier_fn else _pick_tier(rng)
            rows.append((sid, cat, tier, _at()))

    # Add all students first, then flush, then add events
    for sid, cat, tier, at in rows:
        db.add(_make_student(rng, sid, tier))

    db.flush()  # ensure students are persisted before FK-checked events

    for sid, cat, tier, at in rows:
        db.add(_admit(rng, sid, course.id, cat, "ROUND_1", "REGULAR", year, at))

    return len(rows)


def _seed_hero_inst0001(db, rng: random.Random, stu_counter: list) -> int:
    """INST-0001 CSE: 238 regular+NRI (lawful, under 240). Used for upload demo."""
    course = db.query(CourseApproval).filter(CourseApproval.id == "CRS-0001-CSE").first()
    if not course:
        return 0
    return _seed_course(db, rng, course, n_regular=226, n_oci=8, n_ciwgc=4, n_nri=0, year="2026-27", stu_counter=stu_counter)


def _seed_hero_inst0003(db, rng: random.Random, stu_counter: list) -> int:
    """INST-0003 CSE: 282 admitted (S3 — over max). 240 regular+NRI + 24 OCI_FN + 12 CIWGC = 276 lawful + 6 over."""
    course = db.query(CourseApproval).filter(CourseApproval.id == "CRS-0003-CSE").first()
    if not course:
        return 0
    return _seed_course(db, rng, course, n_regular=240, n_oci=24, n_ciwgc=12, n_nri=6, year="2026-27", stu_counter=stu_counter)


def _seed_hero_inst0004(db, rng: random.Random, stu_counter: list) -> int:
    """INST-0004 CSE: EWS students in extra seats — rule not confirmed (draft EWS-ST)."""
    course = db.query(CourseApproval).filter(CourseApproval.id == "CRS-0004-CSE").first()
    if not course:
        return 0
    base_date = datetime(2026, 7, 1, 9, 0, 0, tzinfo=timezone.utc)

    def _next_id() -> str:
        stu_counter[0] += 1
        return f"STU-{stu_counter[0]:05d}"

    rows = []
    for cat, n in [("REGULAR", 165), ("EWS", 15)]:
        for _ in range(n):
            sid = _next_id()
            at = base_date.__class__.fromtimestamp(base_date.timestamp() + rng.randint(0, 90) * 86400, tz=timezone.utc)
            rows.append((sid, cat, at))
    for sid, cat, at in rows:
        db.add(_make_student(rng, sid, _pick_tier(rng)))
    db.flush()
    for sid, cat, at in rows:
        db.add(_admit(rng, sid, course.id, cat, "ROUND_1", "REGULAR", "2026-27", at))
    return len(rows)


def _seed_hero_inst0005(db, rng: random.Random, stu_counter: list) -> int:
    """INST-0005 MBA: late surge anomaly — 70% of admissions in last 14 days of round."""
    course = db.query(CourseApproval).filter(CourseApproval.id == "CRS-0005-MBA").first()
    if not course:
        return 0
    base_date = datetime(2026, 7, 1, 9, 0, 0, tzinfo=timezone.utc)
    late_cutoff = datetime(2026, 9, 17, 9, 0, 0, tzinfo=timezone.utc)

    def _next_id() -> str:
        stu_counter[0] += 1
        return f"STU-{stu_counter[0]:05d}"

    total = 110
    early_n = int(total * 0.28)
    rows = []
    for i in range(total):
        sid = _next_id()
        if i < early_n:
            at = base_date.__class__.fromtimestamp(base_date.timestamp() + rng.randint(0, 77) * 86400, tz=timezone.utc)
        else:
            at = late_cutoff.__class__.fromtimestamp(late_cutoff.timestamp() + rng.randint(0, 13) * 86400, tz=timezone.utc)
        rows.append((sid, "REGULAR", at))
    for sid, cat, at in rows:
        db.add(_make_student(rng, sid, _pick_tier(rng)))
    db.flush()
    for sid, cat, at in rows:
        db.add(_admit(rng, sid, course.id, cat, "ROUND_1", "REGULAR", "2026-27", at))
    return len(rows)


def _seed_hero_inst0006(db, rng: random.Random, stu_counter: list) -> int:
    """INST-0006 MCA: 40% missing APAAR, some foreign, duplicates."""
    course = db.query(CourseApproval).filter(CourseApproval.id == "CRS-0006-MCA").first()
    if not course:
        return 0
    base_date = datetime(2026, 7, 1, 9, 0, 0, tzinfo=timezone.utc)

    def _next_id() -> str:
        stu_counter[0] += 1
        return f"STU-{stu_counter[0]:05d}"

    tiers = (["T1"] * 12 + ["T2"] * 3 + ["T3"] * 36 + ["T4"] * 9)
    rng.shuffle(tiers)
    rows = []
    for tier in tiers[:55]:
        sid = _next_id()
        cat = "OCI_FN_EXTRA" if tier == "T4" else "REGULAR"
        at = base_date.__class__.fromtimestamp(base_date.timestamp() + rng.randint(0, 90) * 86400, tz=timezone.utc)
        rows.append((sid, tier, cat, at))
    for sid, tier, cat, at in rows:
        db.add(_make_student(rng, sid, tier))
    db.flush()
    for sid, tier, cat, at in rows:
        db.add(_admit(rng, sid, course.id, cat, "ROUND_1", "REGULAR", "2026-27", at))
    return len(rows)


def run(db) -> None:
    from app.models.student import Student

    if db.query(Student).count() > 0:
        print("[gen_students] Already seeded — skip")
        return

    rng = random.Random(SEED)
    stu_counter = [0]
    total_added = 0

    # Hero institution scenarios
    total_added += _seed_hero_inst0001(db, rng, stu_counter)
    total_added += _seed_hero_inst0003(db, rng, stu_counter)
    total_added += _seed_hero_inst0004(db, rng, stu_counter)
    total_added += _seed_hero_inst0005(db, rng, stu_counter)
    total_added += _seed_hero_inst0006(db, rng, stu_counter)

    # Remaining institutions — random fill
    all_courses = db.query(CourseApproval).filter(
        CourseApproval.academic_year == "2026-27",
        ~CourseApproval.institution_id.in_(
            ["INST-0001", "INST-0002", "INST-0003", "INST-0004", "INST-0005", "INST-0006"]
        ),
    ).all()

    for course in all_courses:
        n = int(course.approved_intake * rng.uniform(0.70, 0.98))
        n_oci = int(course.approved_intake * 0.10 * rng.uniform(0.0, 1.0))
        n_ciwgc = int(course.approved_intake * 0.05 * rng.uniform(0.0, 0.8))
        n_nri = int(course.approved_intake * 0.05 * rng.uniform(0.0, 0.6))
        added_here = _seed_course(
            db, rng, course,
            n_regular=max(0, n - n_nri),
            n_oci=n_oci,
            n_ciwgc=n_ciwgc,
            n_nri=n_nri,
            year="2026-27",
            stu_counter=stu_counter,
        )
        total_added += added_here
        if stu_counter[0] % 500 == 0:
            db.flush()

    db.commit()
    print(f"[gen_students] {stu_counter[0]} students, {total_added} admission events")
