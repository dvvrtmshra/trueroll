"""Feature extraction for anomaly scoring (spec 6.6)."""
from __future__ import annotations

from collections import Counter
from datetime import date, datetime, timezone, timedelta
from typing import Optional

from sqlalchemy.orm import Session

from app.models.admission_event import AdmissionEvent
from app.models.course import CourseApproval
from app.models.institution import Institution
from app.models.seat_bucket import SeatBucket
from app.models.setting import Setting
from app.models.student import Student


CYCLE_END_MONTH = 11  # November — end of admission cycle


def _demo_date(db: Session) -> date:
    s = db.query(Setting).filter(Setting.key == "demo_date").first()
    if s and s.value:
        try:
            return date.fromisoformat(s.value)
        except ValueError:
            pass
    return date.today()


def _audit_date(year: str) -> date:
    """Audit date is Sep 30 of the first year in '2026-27'."""
    y = int(year.split("-")[0])
    return date(y, 9, 30)


def _cycle_end(year: str) -> date:
    y = int(year.split("-")[0])
    return date(y, CYCLE_END_MONTH, 30)


def extract_features(
    db: Session,
    institution_id: str,
    course_id: str,
    academic_year: str,
) -> dict:
    events = (
        db.query(AdmissionEvent)
        .filter(
            AdmissionEvent.course_approval_id == course_id,
            AdmissionEvent.event_type == "ADMIT",
        )
        .all()
    )
    withdraw_events = (
        db.query(AdmissionEvent)
        .filter(
            AdmissionEvent.course_approval_id == course_id,
            AdmissionEvent.event_type == "WITHDRAW",
        )
        .all()
    )

    total = len(events)
    total_withdraw = len(withdraw_events)

    cycle_end = _cycle_end(academic_year)
    cutoff_14d = cycle_end - timedelta(days=14)
    late_events = [e for e in events if e.event_time.date() >= cutoff_14d]
    late_share_14d = len(late_events) / max(1, total)
    surge_ratio = late_share_14d / 0.1 if late_share_14d > 0 else 0.0  # normalised against expected 10%

    cat_counts: Counter = Counter(e.seat_category for e in events)
    mix_ocifn = cat_counts.get("OCI_FN_EXTRA", 0) / max(1, total)
    mix_nri = cat_counts.get("NRI_IN", 0) / max(1, total)
    mix_ciwgc = cat_counts.get("CIWGC_EXTRA", 0) / max(1, total)
    mix_ews = cat_counts.get("EWS", 0) / max(1, total)

    # fill_streak: check if all SeatBucket rows for this course are at cap
    buckets = db.query(SeatBucket).filter(SeatBucket.course_approval_id == course_id).all()
    fill_streak = 0
    if buckets and all(b.used >= b.cap for b in buckets if b.cap > 0):
        fill_streak = 1  # simplified: only check current year; full history would need multi-year query

    withdraw_rate = total_withdraw / max(1, total)

    audit_d = _audit_date(academic_year)
    post_audit = sum(
        1 for e in withdraw_events
        if e.event_time.date() > audit_d
    )

    # max_cluster: find max group of students sharing a contact_token
    student_ids = [e.student_id for e in events]
    students = db.query(Student).filter(Student.id.in_(student_ids)).all()
    token_groups: Counter = Counter(s.contact_token for s in students if s.contact_token)
    max_cluster = max(token_groups.values(), default=0)

    dob_counter: Counter = Counter(s.date_of_birth for s in students if s.date_of_birth)
    dob_concentration = max(dob_counter.values(), default=0) / max(1, total)

    course = db.query(CourseApproval).filter(CourseApproval.id == course_id).first()
    inst = db.query(Institution).filter(Institution.id == institution_id).first()

    return {
        "institution_id": institution_id,
        "course_id": course_id,
        "academic_year": academic_year,
        "institution_name": inst.name if inst else institution_id,
        "course_name": course.name if course else course_id,
        "level": course.level if course else "UG",
        "state": inst.state if inst else "Unknown",
        "region": inst.region if inst else "Unknown",
        "approved_intake": course.approved_intake if course else 0,
        "total_admitted": total,
        "late_share_14d": round(late_share_14d, 4),
        "surge_ratio": round(surge_ratio, 4),
        "mix_ocifn": round(mix_ocifn, 4),
        "mix_nri": round(mix_nri, 4),
        "mix_ciwgc": round(mix_ciwgc, 4),
        "mix_ews": round(mix_ews, 4),
        "fill_streak": fill_streak,
        "withdraw_rate": round(withdraw_rate, 4),
        "post_audit_withdrawals": post_audit,
        "max_cluster": max_cluster,
        "dob_concentration": round(dob_concentration, 4),
    }


def extract_all_features(db: Session, academic_year: str = "2026-27") -> list[dict]:
    courses = db.query(CourseApproval).filter(CourseApproval.academic_year == academic_year).all()
    results = []
    for course in courses:
        try:
            feat = extract_features(db, course.institution_id, course.id, academic_year)
            results.append(feat)
        except Exception:
            pass
    return results
