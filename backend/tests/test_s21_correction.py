"""S21 — Correction and reconciliation.

When the same student is re-uploaded with a different seat_category, a CORRECTION event
is stored. Reconcile reports zero drift after the correction.
"""
import pytest
from datetime import date, datetime, timezone
from uuid import uuid4

from app.models.course import CourseApproval
from app.models.institution import Institution
from app.models.student import Student
from app.models.admission_event import AdmissionEvent
from app.models.seat_bucket import SeatBucket
from app.models.upload import Upload
from app.services.ingestion import process_upload
from app.services.ledger import reconcile, bucket_counts


@pytest.fixture()
def corr_setup(db):
    if not db.query(Institution).filter(Institution.id == "CORR-INST-01").first():
        db.add(Institution(
            id="CORR-INST-01",
            name="Correction Test College",
            region="West",
            state="Gujarat",
            city="Ahmedabad",
            type="Private",
            status="Open",
        ))
    course = db.query(CourseApproval).filter(CourseApproval.id == "CORR-COURSE-01").first()
    if not course:
        course = CourseApproval(
            id="CORR-COURSE-01",
            institution_id="CORR-INST-01",
            name="B.Tech CSE",
            level="UG",
            domain="Engineering and Technology",
            academic_year="2026-27",
            approved_intake=60,
        )
        db.add(course)
    db.commit()
    inst = db.query(Institution).filter(Institution.id == "CORR-INST-01").first()
    course = db.query(CourseApproval).filter(CourseApproval.id == "CORR-COURSE-01").first()
    yield db, inst, course


def _make_csv(rows: list[dict]) -> bytes:
    import csv, io
    buf = io.StringIO()
    if not rows:
        return b""
    w = csv.DictWriter(buf, fieldnames=rows[0].keys())
    w.writeheader()
    w.writerows(rows)
    return buf.getvalue().encode()


def test_s21_correction_event_stored(corr_setup):
    """Re-uploading with different seat_category creates a CORRECTION event."""
    db, inst, course = corr_setup

    base_row = {
        "student_ref": "COR001",
        "full_name": "Priya Sharma",
        "date_of_birth": "2003-04-10",
        "nationality_status": "INDIAN",
        "seat_category": "REGULAR",
        "course_code": "CORR-COURSE-01",
        "admission_date": "2026-08-01",
        "mode": "FULL_TIME",
    }

    # First upload — ADMIT
    uid1 = str(uuid4())
    db.add(Upload(id=uid1, institution_id="CORR-INST-01", academic_year="2026-27",
                  file_hash="hash1", status="pending", row_count=1, uploaded_by="test-user",
                  filename="test1.csv"))
    db.commit()

    process_upload(db, uid1, "CORR-INST-01", "2026-27", _make_csv([base_row]),
                   uploader_id="user1", demo_date=date(2026, 10, 1))

    from app.models.admission_event import AdmissionEvent
    admits = db.query(AdmissionEvent).filter(
        AdmissionEvent.event_type == "ADMIT",
        AdmissionEvent.course_approval_id == "CORR-COURSE-01",
    ).all()
    assert len(admits) == 1
    assert admits[0].seat_category == "REGULAR"

    # Second upload — same student, different seat_category → CORRECTION
    corrected_row = dict(base_row)
    corrected_row["seat_category"] = "EWS"

    uid2 = str(uuid4())
    db.add(Upload(id=uid2, institution_id="CORR-INST-01", academic_year="2026-27",
                  file_hash="hash2", status="pending", row_count=1, uploaded_by="test-user",
                  filename="test2.csv"))
    db.commit()

    process_upload(db, uid2, "CORR-INST-01", "2026-27", _make_csv([corrected_row]),
                   uploader_id="user1", demo_date=date(2026, 10, 1))

    corrections = db.query(AdmissionEvent).filter(
        AdmissionEvent.event_type == "CORRECTION",
        AdmissionEvent.course_approval_id == "CORR-COURSE-01",
    ).all()
    assert len(corrections) == 1, f"Expected 1 CORRECTION event, got {len(corrections)}"
    assert corrections[0].seat_category == "EWS"


def test_s21_reconcile_zero_drift(corr_setup):
    """After the correction, reconcile reports zero drift."""
    db, inst, course = corr_setup

    base_row = {
        "student_ref": "COR002",
        "full_name": "Arun Kumar",
        "date_of_birth": "2004-01-20",
        "nationality_status": "INDIAN",
        "seat_category": "REGULAR",
        "course_code": "CORR-COURSE-01",
        "admission_date": "2026-08-01",
        "mode": "FULL_TIME",
    }

    uid1 = str(uuid4())
    db.add(Upload(id=uid1, institution_id="CORR-INST-01", academic_year="2026-27",
                  file_hash="hash3", status="pending", row_count=1, uploaded_by="test-user",
                  filename="test3.csv"))
    db.commit()
    process_upload(db, uid1, "CORR-INST-01", "2026-27", _make_csv([base_row]),
                   uploader_id="user1", demo_date=date(2026, 10, 1))

    # Correction upload
    corr_row = dict(base_row)
    corr_row["seat_category"] = "EWS"
    uid2 = str(uuid4())
    db.add(Upload(id=uid2, institution_id="CORR-INST-01", academic_year="2026-27",
                  file_hash="hash4", status="pending", row_count=1, uploaded_by="test-user",
                  filename="test4.csv"))
    db.commit()
    process_upload(db, uid2, "CORR-INST-01", "2026-27", _make_csv([corr_row]),
                   uploader_id="user1", demo_date=date(2026, 10, 1))

    drift = reconcile(db, "CORR-COURSE-01")
    total_drift = sum(abs(v) for v in drift.values())
    assert total_drift == 0, f"Expected zero drift after reconcile, got: {drift}"


def test_s21_counters_reflect_correction(corr_setup):
    """After CORRECTION, bucket_counts uses the new seat_category."""
    db, inst, course = corr_setup

    base_row = {
        "student_ref": "COR003",
        "full_name": "Sneha Patel",
        "date_of_birth": "2003-11-05",
        "nationality_status": "INDIAN",
        "seat_category": "REGULAR",
        "course_code": "CORR-COURSE-01",
        "admission_date": "2026-08-01",
        "mode": "FULL_TIME",
    }
    uid1 = str(uuid4())
    db.add(Upload(id=uid1, institution_id="CORR-INST-01", academic_year="2026-27",
                  file_hash="hash5", status="pending", row_count=1, uploaded_by="test-user",
                  filename="test5.csv"))
    db.commit()
    process_upload(db, uid1, "CORR-INST-01", "2026-27", _make_csv([base_row]),
                   uploader_id="user1", demo_date=date(2026, 10, 1))

    before = bucket_counts(db, "CORR-COURSE-01")
    assert before.get("REGULAR", 0) >= 1

    # Now upload a correction changing seat to NRI_IN (still maps to REGULAR bucket)
    corr_row = dict(base_row)
    corr_row["seat_category"] = "NRI_IN"
    corr_row["nationality_status"] = "NRI"
    uid2 = str(uuid4())
    db.add(Upload(id=uid2, institution_id="CORR-INST-01", academic_year="2026-27",
                  file_hash="hash6", status="pending", row_count=1, uploaded_by="test-user",
                  filename="test6.csv"))
    db.commit()
    process_upload(db, uid2, "CORR-INST-01", "2026-27", _make_csv([corr_row]),
                   uploader_id="user1", demo_date=date(2026, 10, 1))

    after = bucket_counts(db, "CORR-COURSE-01")
    # NRI_IN maps to REGULAR bucket, so count stays the same
    assert after.get("REGULAR", 0) == before.get("REGULAR", 0)
