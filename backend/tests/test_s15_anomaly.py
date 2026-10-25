"""S15 — Anomaly model scores a planted high-priority institution."""
import json
from datetime import date, datetime, timedelta, timezone
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from app.models.admission_event import AdmissionEvent
from app.models.anomaly_label import AnomalyLabel
from app.models.course import CourseApproval
from app.models.institution import Institution
from app.models.student import Student
from app.services.anomaly_features import extract_features
from app.services.anomaly_scorer import score_one, score_all


CYCLE_END = date(2026, 11, 30)


@pytest.fixture()
def anomaly_db(db):
    """Set up one institution with a planted LATE_SURGE anomaly and several normal peers."""
    inst = Institution(
        id="ANOM-INST-01",
        name="Anomaly Test College",
        region="West",
        state="Maharashtra",
        city="Mumbai",
        type="Private",
        status="Open",
    )
    db.add(inst)

    # Anomalous course
    course = CourseApproval(
        id="ANOM-CRS-01",
        institution_id="ANOM-INST-01",
        name="B.Tech CSE",
        level="UG",
        domain="Engineering and Technology",
        academic_year="2026-27",
        approved_intake=240,
    )
    db.add(course)
    db.flush()

    # 5 normal peers
    for i in range(5):
        peer_inst = Institution(
            id=f"ANOM-PEER-{i:02d}",
            name=f"Peer College {i}",
            region="West",
            state="Maharashtra",
            city="Pune",
            type="Private",
            status="Open",
        )
        db.add(peer_inst)
        peer_course = CourseApproval(
            id=f"ANOM-PEER-CRS-{i:02d}",
            institution_id=f"ANOM-PEER-{i:02d}",
            name="B.Tech CSE",
            level="UG",
            domain="Engineering and Technology",
            academic_year="2026-27",
            approved_intake=240,
        )
        db.add(peer_course)
        db.flush()
        # Normal admissions distributed evenly over the year
        for j in range(40):
            stu = Student(
                id=f"ANOM-PEER-STU-{i}-{j}",
                full_name=f"Peer Student {i}-{j}",
                date_of_birth=date(2003, (j % 12) + 1, 15),
                identity_tier="T1",
            )
            db.add(stu)
            db.flush()
            day_offset = j * 3  # spread over ~120 days
            admit_dt = datetime(2026, 7, 1, 10, 0, tzinfo=timezone.utc) + timedelta(days=day_offset)
            db.add(AdmissionEvent(
                id=str(uuid4()),
                student_id=stu.id,
                course_approval_id=peer_course.id,
                seat_category="REGULAR",
                event_type="ADMIT",
                admission_round="ROUND_1",
                entry_type="REGULAR",
                nationality_status="INDIAN",
                event_time=admit_dt,
            ))

    # Anomalous: 80% of admissions in last 14 days of cycle
    cutoff = CYCLE_END - timedelta(days=14)
    for j in range(50):
        stu = Student(
            id=f"ANOM-SURGE-STU-{j}",
            full_name=f"Surge Student {j}",
            date_of_birth=date(2004, (j % 12) + 1, 10),
            identity_tier="T3",
        )
        db.add(stu)
        db.flush()
        if j < 40:  # 80% late
            admit_dt = datetime(cutoff.year, cutoff.month, cutoff.day, 10, 0, tzinfo=timezone.utc) + timedelta(days=j % 14)
        else:
            admit_dt = datetime(2026, 8, j % 28 + 1, 10, 0, tzinfo=timezone.utc)
        db.add(AdmissionEvent(
            id=str(uuid4()),
            student_id=stu.id,
            course_approval_id=course.id,
            seat_category="REGULAR",
            event_type="ADMIT",
            admission_round="ROUND_1",
            entry_type="REGULAR",
            nationality_status="INDIAN",
            event_time=admit_dt,
        ))

    db.add(AnomalyLabel(
        institution_id="ANOM-INST-01",
        course_id="ANOM-CRS-01",
        academic_year="2026-27",
        anomaly_type="LATE_SURGE",
        planted=True,
    ))
    db.commit()
    yield db


def test_s15_late_surge_scores_high(anomaly_db):
    """Planted LATE_SURGE institution scores Medium or High with LATE_SURGE reason."""
    feats = extract_features(anomaly_db, "ANOM-INST-01", "ANOM-CRS-01", "2026-27")
    assert feats["late_share_14d"] > 0.5, "Expected >50% late admissions"

    # Collect all features for peer comparison
    from app.services.anomaly_features import extract_all_features
    all_feats = extract_all_features(anomaly_db, "2026-27")

    scored = score_one(feats, all_feats)
    assert scored["score"] >= 40, f"Expected score >= 40 (Medium+), got {scored['score']}"
    reason_codes = [r["code"] for r in scored["reasons"]]
    assert "LATE_SURGE" in reason_codes, f"Expected LATE_SURGE in reasons, got {reason_codes}"


def test_s15_result_is_advisory(anomaly_db):
    """Review priority has status='advisory', no flag/violation language."""
    results = score_all(anomaly_db, "2026-27")
    anom_result = next((r for r in results if r["institution_id"] == "ANOM-INST-01"), None)
    assert anom_result is not None

    from app.models.review_priority import ReviewPriority
    rp = anomaly_db.query(ReviewPriority).filter(
        ReviewPriority.institution_id == "ANOM-INST-01"
    ).first()
    assert rp is not None
    assert rp.status == "advisory"
    # Forbidden words must not appear in reasons
    reasons_text = rp.reasons or ""
    for forbidden in ("violation", "fraud", "guilty", "flag"):
        assert forbidden not in reasons_text.lower(), f"Forbidden word '{forbidden}' in reasons"


def test_s15_officer_label(anomaly_db):
    """Officer can label a priority (useful/not_useful/need_more_info)."""
    results = score_all(anomaly_db, "2026-27")
    from app.models.review_priority import ReviewPriority
    rp = anomaly_db.query(ReviewPriority).filter(
        ReviewPriority.institution_id == "ANOM-INST-01"
    ).first()
    assert rp is not None
    rp.officer_label = "useful"
    anomaly_db.commit()
    anomaly_db.refresh(rp)
    assert rp.officer_label == "useful"
