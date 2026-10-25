"""Institution and course endpoints."""
import json
from datetime import date, datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_roles, get_current_user
from app.models.course import CourseApproval
from app.models.flag import Flag
from app.models.institution import Institution
from app.models.seat_bucket import SeatBucket
from app.models.student import Student
from app.models.upload import Upload
from app.models.api_key import ApiKey

router = APIRouter()


def _course_buckets(db: Session, course: CourseApproval) -> list[dict]:
    buckets = db.query(SeatBucket).filter(
        SeatBucket.course_approval_id == course.id
    ).all()
    return [{"bucket": b.bucket_code, "cap": b.cap, "used": b.used} for b in buckets]


def _course_flags(db: Session, course_id: str) -> list[dict]:
    flags = db.query(Flag).filter(
        Flag.course_approval_id == course_id,
        Flag.status.in_(["open", "under_review", "clarification_requested"]),
    ).all()
    return [{"id": f.id, "status": f.status, "severity": f.severity, "bucket": f.bucket} for f in flags]


def _ledger_status(buckets: list[dict], open_flags: int, last_eval_status: Optional[str]) -> str:
    if open_flags > 0:
        return "flag"
    if last_eval_status in ("RULE_NOT_CONFIRMED",):
        return "rule_unconfirmed"
    total_cap = sum(b["cap"] for b in buckets)
    total_used = sum(b["used"] for b in buckets)
    if total_cap > 0 and total_used / total_cap >= 0.95:
        return "near_cap"
    return "within_limit"


def _build_course_detail(db: Session, course: CourseApproval) -> dict:
    buckets = _course_buckets(db, course)
    open_flags_list = _course_flags(db, course.id)
    return {
        "id": course.id,
        "name": course.name,
        "level": course.level,
        "domain": course.domain,
        "academic_year": course.academic_year,
        "approved_intake": course.approved_intake,
        "lateral_intake": course.lateral_intake,
        "buckets": buckets,
        "lawful_max": sum(b["cap"] for b in buckets),
        "admitted": sum(b["used"] for b in buckets),
        "open_flags": len(open_flags_list),
        "flags": open_flags_list,
        "status": _ledger_status(buckets, len(open_flags_list), None),
    }


def _auth_institution(user: dict, institution_id: str, db: Session) -> None:
    role = user.get("role")
    if role in ("NATIONAL_OFFICER", "REGIONAL_OFFICER", "SYSTEM_ADMIN"):
        return
    if role == "COLLEGE_ADMIN" and user.get("institution_id") == institution_id:
        return
    raise HTTPException(status_code=403, detail={"code": "FORBIDDEN", "message": "Access denied to this institution"})


@router.get("")
def list_institutions(
    db: Session = Depends(get_db),
    user: dict = Depends(require_roles("NATIONAL_OFFICER", "REGIONAL_OFFICER", "SYSTEM_ADMIN")),
):
    q = db.query(Institution)
    if user.get("role") == "REGIONAL_OFFICER" and user.get("region"):
        q = q.filter(Institution.region == user["region"])
    insts = q.all()
    return [{"id": i.id, "name": i.name, "region": i.region, "state": i.state, "type": i.type} for i in insts]


@router.get("/{institution_id}")
def get_institution(
    institution_id: str,
    db: Session = Depends(get_db),
    user: dict = Depends(require_roles(
        "NATIONAL_OFFICER", "REGIONAL_OFFICER", "COLLEGE_ADMIN", "SYSTEM_ADMIN"
    )),
):
    _auth_institution(user, institution_id, db)
    inst = db.query(Institution).filter(Institution.id == institution_id).first()
    if not inst:
        raise HTTPException(status_code=404, detail="Institution not found")
    return {"id": inst.id, "name": inst.name, "region": inst.region, "state": inst.state,
            "city": inst.city, "type": inst.type, "status": inst.status}


@router.get("/{institution_id}/courses")
def list_courses(
    institution_id: str,
    academic_year: str = "2026-27",
    db: Session = Depends(get_db),
    user: dict = Depends(require_roles(
        "NATIONAL_OFFICER", "REGIONAL_OFFICER", "COLLEGE_ADMIN", "SYSTEM_ADMIN"
    )),
):
    _auth_institution(user, institution_id, db)
    courses = db.query(CourseApproval).filter(
        CourseApproval.institution_id == institution_id,
        CourseApproval.academic_year == academic_year,
    ).all()
    return [_build_course_detail(db, c) for c in courses]


@router.get("/{institution_id}/dashboard")
def get_college_dashboard(
    institution_id: str,
    academic_year: str = "2026-27",
    db: Session = Depends(get_db),
    user: dict = Depends(require_roles(
        "NATIONAL_OFFICER", "REGIONAL_OFFICER", "COLLEGE_ADMIN", "SYSTEM_ADMIN"
    )),
):
    _auth_institution(user, institution_id, db)

    courses = db.query(CourseApproval).filter(
        CourseApproval.institution_id == institution_id,
        CourseApproval.academic_year == academic_year,
    ).all()
    course_details = [_build_course_detail(db, c) for c in courses]

    # Last upload
    last_upload = db.query(Upload).filter(
        Upload.institution_id == institution_id,
        Upload.academic_year == academic_year,
    ).order_by(Upload.uploaded_at.desc()).first()

    last_upload_info = None
    if last_upload:
        last_upload_info = {
            "id": last_upload.id,
            "filename": last_upload.filename,
            "uploaded_at": last_upload.uploaded_at.isoformat(),
            "rows_accepted": last_upload.rows_accepted,
            "rows_error": last_upload.error_count,
            "status": last_upload.status,
        }

    # Open flags
    course_ids = [c.id for c in courses]
    open_flags = 0
    if course_ids:
        open_flags = db.query(Flag).filter(
            Flag.institution_id == institution_id,
            Flag.status.in_(["open", "under_review", "clarification_requested"]),
        ).count()

    # T3 pending: students in this institution with tier T3
    t3_pending = 0
    if course_ids:
        from app.models.admission_event import AdmissionEvent
        student_ids = db.query(AdmissionEvent.student_id).filter(
            AdmissionEvent.course_approval_id.in_(course_ids),
            AdmissionEvent.event_type == "ADMIT",
        ).distinct().all()
        sid_list = [r[0] for r in student_ids]
        if sid_list:
            t3_pending = db.query(Student).filter(
                Student.id.in_(sid_list),
                Student.identity_tier == "T3",
            ).count()

    return {
        "institution_id": institution_id,
        "courses": course_details,
        "last_upload": last_upload_info,
        "open_flags": open_flags,
        "t3_pending": t3_pending,
        "t3_deadline": "2027-01-31",
    }


@router.get("/{institution_id}/api-key")
def get_api_key(
    institution_id: str,
    reveal: bool = False,
    db: Session = Depends(get_db),
    user: dict = Depends(require_roles("COLLEGE_ADMIN", "SYSTEM_ADMIN")),
):
    _auth_institution(user, institution_id, db)
    # Look up the seeded institution API key (employer_id="system" sentinel from D10)
    key = db.query(ApiKey).filter(
        ApiKey.employer_id == institution_id,
        ApiKey.is_active == True,
    ).first()
    if not key:
        # Fallback: look for "system" sentinel
        key = db.query(ApiKey).filter(
            ApiKey.employer_id == "system",
            ApiKey.is_active == True,
        ).first()

    preview = f"trk_{institution_id.lower()}_****"
    return {
        "key_preview": preview,
        "endpoint": f"/api/institutions/{institution_id}/uploads",
        "rate_limit": "100 uploads/day",
        "simulated": True,
        "note": "Demo API key — not a real credential",
    }
