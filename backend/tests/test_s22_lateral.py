"""S22 — Spot round and lateral entry.

Spot admissions use the same buckets. Lateral entry counts against lateral_intake.
If lateral_intake=0, result is RULE_NOT_CONFIRMED.
"""
import pytest
from datetime import date, datetime, timezone
from uuid import uuid4

from app.models.admission_event import AdmissionEvent
from app.models.course import CourseApproval
from app.models.institution import Institution
from app.models.student import Student
from app.models.upload import Upload
from app.services.ingestion import process_upload
from app.services.ledger import evaluate, bucket_counts


@pytest.fixture()
def lateral_setup(db):
    if not db.query(Institution).filter(Institution.id == "LAT-INST-01").first():
        db.add(Institution(
            id="LAT-INST-01",
            name="Lateral Test College",
            region="South",
            state="Karnataka",
            city="Bengaluru",
            type="Private",
            status="Open",
        ))
    if not db.query(CourseApproval).filter(CourseApproval.id == "LAT-COURSE-WITH").first():
        db.add(CourseApproval(
            id="LAT-COURSE-WITH",
            institution_id="LAT-INST-01",
            name="B.Tech CSE",
            level="UG",
            domain="Engineering and Technology",
            academic_year="2026-27",
            approved_intake=120,
            lateral_intake=20,
        ))
    if not db.query(CourseApproval).filter(CourseApproval.id == "LAT-COURSE-WITHOUT").first():
        db.add(CourseApproval(
            id="LAT-COURSE-WITHOUT",
            institution_id="LAT-INST-01",
            name="B.Tech ECE",
            level="UG",
            domain="Engineering and Technology",
            academic_year="2026-27",
            approved_intake=60,
            lateral_intake=0,
        ))
    db.commit()
    yield db


def _admit(db, student_id: str, course_id: str, seat_cat: str, entry_type: str, round_: str, day: int):
    stu = Student(
        id=student_id,
        full_name=f"Student {student_id}",
        date_of_birth=date(2003, 6, 15),
        identity_tier="T1",
    )
    db.add(stu)
    db.flush()
    db.add(AdmissionEvent(
        id=str(uuid4()),
        student_id=student_id,
        course_approval_id=course_id,
        seat_category=seat_cat,
        event_type="ADMIT",
        admission_round=round_,
        entry_type=entry_type,
        nationality_status="INDIAN",
        event_time=datetime(2026, 8, day, 10, 0, tzinfo=timezone.utc),
    ))
    db.commit()


def test_s22_spot_round_uses_regular_bucket(lateral_setup):
    """SPOT round admissions count against the REGULAR bucket."""
    db = lateral_setup
    _admit(db, "LAT-SPOT-001", "LAT-COURSE-WITH", "REGULAR", "REGULAR", "SPOT", 20)
    counts = bucket_counts(db, "LAT-COURSE-WITH")
    assert counts.get("REGULAR", 0) >= 1


def test_s22_lateral_within_limit_ok(lateral_setup):
    """Lateral admissions within lateral_intake produce no flag."""
    db = lateral_setup
    for i in range(5):
        _admit(db, f"LAT-STU-{i:03d}", "LAT-COURSE-WITH", "LATERAL", "LATERAL", "ROUND_1", i + 1)

    result = evaluate(db, "LAT-COURSE-WITH", as_of=date(2026, 10, 1))
    assert result.status in ("OK", "RULE_NOT_CONFIRMED")
    # With lateral_intake=20 and only 5 laterals, should be OK
    lateral_flags = [f for f in result.flags if f.bucket == "LATERAL"]
    assert len(lateral_flags) == 0, f"Unexpected lateral flag: {lateral_flags}"


def test_s22_lateral_exceeds_limit_flag(lateral_setup):
    """Lateral admissions exceeding lateral_intake triggers a C1 flag."""
    db = lateral_setup
    # Admit 25 laterals (limit is 20)
    for i in range(25):
        _admit(db, f"LAT-OVER-{i:03d}", "LAT-COURSE-WITH", "LATERAL", "LATERAL", "ROUND_1", i % 28 + 1)

    result = evaluate(db, "LAT-COURSE-WITH", as_of=date(2026, 10, 1))
    assert result.status == "FLAG", f"Expected FLAG, got {result.status}"
    lateral_flags = [f for f in result.flags if f.bucket == "LATERAL" and f.check == "C1"]
    assert len(lateral_flags) >= 1, f"Expected C1 flag on LATERAL bucket, flags: {result.flags}"


def test_s22_lateral_without_lateral_intake_rule_not_confirmed(lateral_setup):
    """LATERAL admissions on a course with lateral_intake=0 → RULE_NOT_CONFIRMED."""
    db = lateral_setup
    _admit(db, "LAT-NO-LIMIT-001", "LAT-COURSE-WITHOUT", "LATERAL", "LATERAL", "ROUND_1", 5)

    result = evaluate(db, "LAT-COURSE-WITHOUT", as_of=date(2026, 10, 1))
    assert result.status == "RULE_NOT_CONFIRMED", f"Expected RULE_NOT_CONFIRMED, got {result.status}"
    assert "lateral_intake" in result.review_reason.lower(), f"Review reason: {result.review_reason}"
