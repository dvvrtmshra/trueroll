"""Seat-Ledger monitor API — powers N2 (Ledger screen) including Compare mode."""
import json
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_roles
from app.models.course import CourseApproval
from app.models.evaluation import Evaluation
from app.models.flag import Flag
from app.models.institution import Institution
from app.models.rule import RuleVersion
from app.models.seat_bucket import SeatBucket
from app.services.ledger import simple_counter

router = APIRouter()

_OFFICER_ROLES = ("NATIONAL_OFFICER", "REGIONAL_OFFICER", "SYSTEM_ADMIN")


def _region_filter(user: dict, q, model):
    if user.get("role") == "REGIONAL_OFFICER" and user.get("region"):
        inst_ids = None  # resolved lazily below
        return user.get("region")
    return None


def _course_row(db: Session, course: CourseApproval, inst: Institution) -> dict:
    buckets = db.query(SeatBucket).filter(SeatBucket.course_approval_id == course.id).all()
    admitted = sum(b.used for b in buckets)
    lawful = sum(b.cap for b in buckets) if buckets else course.approved_intake
    bucket_counts = {b.bucket_code: {"cap": b.cap, "used": b.used} for b in buckets}

    open_flags = db.query(func.count(Flag.id)).filter(
        Flag.course_approval_id == course.id,
        Flag.status.in_(["open", "under_review", "clarification_requested"]),
    ).scalar() or 0

    last_eval = (
        db.query(Evaluation)
        .filter(Evaluation.course_approval_id == course.id)
        .order_by(Evaluation.evaluated_at.desc())
        .first()
    )

    if open_flags:
        status = "flag"
    elif last_eval and last_eval.result == "RULE_NOT_CONFIRMED":
        status = "rule_unconfirmed"
    elif lawful and admitted / lawful >= 0.95:
        status = "near_cap"
    else:
        status = "within_limit"

    active_rules = db.query(RuleVersion).filter(
        RuleVersion.status == "active",
        RuleVersion.academic_year == course.academic_year,
    ).all()
    rule_chips = [f"{rv.rule_id} v{rv.version}" for rv in active_rules]

    return {
        "course_id": course.id,
        "institution_id": inst.id,
        "institution_name": inst.name,
        "course_name": course.name,
        "level": course.level,
        "domain": course.domain,
        "region": inst.region,
        "state": inst.state,
        "academic_year": course.academic_year,
        "approved_intake": course.approved_intake,
        "lawful_max": lawful,
        "admitted": admitted,
        "bucket_counts": bucket_counts,
        "status": status,
        "flags_open": open_flags,
        "rule_chips": rule_chips,
        "last_evaluated": last_eval.evaluated_at.isoformat() if last_eval else None,
        "last_result": last_eval.result if last_eval else None,
    }


@router.get("")
def list_ledger(
    region: Optional[str] = None,
    state: Optional[str] = None,
    level: Optional[str] = None,
    domain: Optional[str] = None,
    academic_year: str = "2026-27",
    status: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    user: dict = Depends(require_roles(*_OFFICER_ROLES)),
):
    q = db.query(CourseApproval, Institution).join(
        Institution, CourseApproval.institution_id == Institution.id
    ).filter(CourseApproval.academic_year == academic_year)

    if user.get("role") == "REGIONAL_OFFICER" and user.get("region"):
        q = q.filter(Institution.region == user["region"])
    if region:
        q = q.filter(Institution.region == region)
    if state:
        q = q.filter(Institution.state == state)
    if level:
        q = q.filter(CourseApproval.level == level)
    if domain:
        q = q.filter(CourseApproval.domain == domain)

    all_pairs = q.all()
    rows = [_course_row(db, c, i) for c, i in all_pairs]

    if status and status != "all":
        rows = [r for r in rows if r["status"] == status]

    total = len(rows)
    start = (page - 1) * page_size
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": rows[start: start + page_size],
    }


@router.get("/compare")
def compare_ledger(
    academic_year: str = "2026-27",
    db: Session = Depends(get_db),
    user: dict = Depends(require_roles(*_OFFICER_ROLES)),
):
    q = db.query(CourseApproval, Institution).join(
        Institution, CourseApproval.institution_id == Institution.id
    ).filter(CourseApproval.academic_year == academic_year)

    if user.get("role") == "REGIONAL_OFFICER" and user.get("region"):
        q = q.filter(Institution.region == user["region"])

    rows = []
    for course, inst in q.all():
        buckets = db.query(SeatBucket).filter(SeatBucket.course_approval_id == course.id).all()
        admitted = sum(b.used for b in buckets)
        lawful_max = sum(b.cap for b in buckets) if buckets else course.approved_intake

        sc = simple_counter(course, admitted)

        last_eval = (
            db.query(Evaluation)
            .filter(Evaluation.course_approval_id == course.id)
            .order_by(Evaluation.evaluated_at.desc())
            .first()
        )

        if last_eval:
            seat_status = last_eval.result
            detail_raw = last_eval.result_detail
            if detail_raw:
                try:
                    reasons = json.loads(detail_raw)
                except Exception:
                    reasons = []
            else:
                reasons = []

            if seat_status == "OK":
                active_rules = db.query(RuleVersion).filter(
                    RuleVersion.status == "active",
                    RuleVersion.academic_year == academic_year,
                ).all()
                rule_strs = " + ".join(f"{rv.rule_id} v{rv.version}" for rv in active_rules)
                detail = f"Lawful under {rule_strs} ({lawful_max} = {course.approved_intake}+extras)"
            elif seat_status == "FLAG":
                first_reason = reasons[0] if reasons else {}
                check = first_reason.get("check", "")
                msg = first_reason.get("message", "")
                detail = f"FLAG: {msg}" if msg else f"FLAG ({check})"
            elif seat_status == "RULE_NOT_CONFIRMED":
                detail = "Rule not confirmed: human review, no automatic flag"
            else:
                detail = seat_status
        else:
            seat_status = "NOT_EVALUATED"
            detail = "Not yet evaluated"

        open_flags = db.query(func.count(Flag.id)).filter(
            Flag.course_approval_id == course.id,
            Flag.status.in_(["open", "under_review", "clarification_requested"]),
        ).scalar() or 0

        rows.append({
            "course_id": course.id,
            "institution_id": inst.id,
            "institution_name": inst.name,
            "course_name": course.name,
            "admitted": admitted,
            "approved_intake": course.approved_intake,
            "lawful_max": lawful_max,
            "simple_counter_status": sc,
            "seat_ledger_status": "FLAG" if open_flags else seat_status,
            "seat_ledger_detail": detail,
            "flags_open": open_flags,
        })

    return {
        "items": rows,
        "note": "Simple counter alarm is not a regulatory finding. Numbers are illustrative.",
    }


@router.get("/course/{course_id}/reconcile")
def reconcile_course(
    course_id: str,
    db: Session = Depends(get_db),
    user: dict = Depends(require_roles(*_OFFICER_ROLES, "COLLEGE_ADMIN")),
):
    """Recompute seat counts from event history. Returns per-bucket drift (0 = clean)."""
    from fastapi import HTTPException
    from app.services.ledger import reconcile
    course = db.query(CourseApproval).filter(CourseApproval.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    drift = reconcile(db, course_id)
    total_drift = sum(abs(v) for v in drift.values())
    return {"course_id": course_id, "drift": drift, "total_drift": total_drift, "clean": total_drift == 0}


@router.get("/course/{course_id}")
def get_course_ledger(
    course_id: str,
    db: Session = Depends(get_db),
    user: dict = Depends(require_roles(*_OFFICER_ROLES)),
):
    from fastapi import HTTPException
    course = db.query(CourseApproval).filter(CourseApproval.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    inst = db.query(Institution).filter(Institution.id == course.institution_id).first()
    if not inst:
        raise HTTPException(status_code=404, detail="Institution not found")

    if user.get("role") == "REGIONAL_OFFICER" and user.get("region"):
        if inst.region != user["region"]:
            raise HTTPException(status_code=403, detail={"code": "FORBIDDEN", "message": "Outside your region"})

    row = _course_row(db, course, inst)

    evals = (
        db.query(Evaluation)
        .filter(Evaluation.course_approval_id == course_id)
        .order_by(Evaluation.evaluated_at.desc())
        .limit(10)
        .all()
    )
    row["evaluations"] = [
        {"id": e.id, "result": e.result, "evaluated_at": e.evaluated_at.isoformat()}
        for e in evals
    ]
    return row
