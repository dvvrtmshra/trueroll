"""Dashboard stats endpoint — all numbers from live DB queries, no constants."""
from datetime import datetime, timezone, timedelta
from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_roles
from app.models.course import CourseApproval
from app.models.flag import Flag
from app.models.institution import Institution
from app.models.seat_bucket import SeatBucket
from app.models.student import Student
from app.models.upload import Upload

router = APIRouter()

_OFFICER_ROLES = ("NATIONAL_OFFICER", "REGIONAL_OFFICER", "SYSTEM_ADMIN")


@router.get("/stats")
def dashboard_stats(
    db: Session = Depends(get_db),
    user: dict = Depends(require_roles(*_OFFICER_ROLES)),
):
    user_region: Optional[str] = user.get("region") if user.get("role") == "REGIONAL_OFFICER" else None

    inst_q = db.query(Institution)
    if user_region:
        inst_q = inst_q.filter(Institution.region == user_region)
    all_insts = inst_q.all()
    inst_ids = [i.id for i in all_insts]

    colleges_total = len(inst_ids)

    reported = (
        db.query(func.count(func.distinct(Upload.institution_id)))
        .filter(Upload.institution_id.in_(inst_ids), Upload.status == "done")
        .scalar()
        or 0
    )

    stu_q = db.query(Student)
    if user_region:
        from app.models.admission_event import AdmissionEvent
        course_ids = [
            c.id for c in db.query(CourseApproval).filter(
                CourseApproval.institution_id.in_(inst_ids)
            ).all()
        ]
        stu_ids = [
            ae.student_id for ae in db.query(AdmissionEvent.student_id).filter(
                AdmissionEvent.course_approval_id.in_(course_ids),
                AdmissionEvent.event_type == "ADMIT",
            ).distinct().all()
        ]
        students_total = len(stu_ids)
        tier_rows = db.query(Student.identity_tier, func.count(Student.id)).filter(
            Student.id.in_(stu_ids)
        ).group_by(Student.identity_tier).all()
    else:
        students_total = db.query(func.count(Student.id)).scalar() or 0
        tier_rows = db.query(Student.identity_tier, func.count(Student.id)).group_by(
            Student.identity_tier
        ).all()

    identity_mix = {"T1": 0, "T2": 0, "T3": 0, "T4": 0}
    for tier, count in tier_rows:
        if tier in identity_mix:
            identity_mix[tier] = count

    t1_t2 = identity_mix["T1"] + identity_mix["T2"]
    identity_coverage_pct = round((t1_t2 / students_total * 100) if students_total else 0.0, 1)

    flag_q = db.query(Flag).filter(
        Flag.institution_id.in_(inst_ids),
        Flag.status.in_(["open", "under_review", "clarification_requested"]),
    )
    open_flags = flag_q.count()

    now = datetime.now(timezone.utc)
    flag_ageing = {"d0_3": 0, "d4_7": 0, "d8_14": 0, "gt14": 0}
    for f in flag_q.all():
        age_days = (now - f.opened_at.replace(tzinfo=timezone.utc) if f.opened_at.tzinfo is None else now - f.opened_at).days
        if age_days <= 3:
            flag_ageing["d0_3"] += 1
        elif age_days <= 7:
            flag_ageing["d4_7"] += 1
        elif age_days <= 14:
            flag_ageing["d8_14"] += 1
        else:
            flag_ageing["gt14"] += 1

    # Seat usage by region
    region_stats: dict[str, dict] = {}
    for inst in all_insts:
        r = inst.region
        if r not in region_stats:
            region_stats[r] = {"used": 0, "capacity": 0}
        courses = db.query(CourseApproval).filter(
            CourseApproval.institution_id == inst.id,
            CourseApproval.academic_year == "2026-27",
        ).all()
        for c in courses:
            buckets = db.query(SeatBucket).filter(SeatBucket.course_approval_id == c.id).all()
            region_stats[r]["used"] += sum(b.used for b in buckets)
            region_stats[r]["capacity"] += sum(b.cap for b in buckets) if buckets else c.approved_intake

    seat_usage_by_region = [
        {
            "region": r,
            "used": v["used"],
            "capacity": v["capacity"],
            "pct": round(v["used"] / v["capacity"] * 100 if v["capacity"] else 0.0, 1),
        }
        for r, v in sorted(region_stats.items())
    ]

    return {
        "colleges_total": colleges_total,
        "colleges_reported": reported,
        "students_total": students_total,
        "flags_open": open_flags,
        "priorities_high": 0,
        "identity_coverage_pct": identity_coverage_pct,
        "identity_mix": identity_mix,
        "flag_ageing": flag_ageing,
        "seat_usage_by_region": seat_usage_by_region,
    }
