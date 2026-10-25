"""Student management endpoints."""
import json
from datetime import date, datetime, timezone
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user, require_roles
from app.models.admission_event import AdmissionEvent
from app.models.audit_entry import AuditEntry
from app.models.course import CourseApproval
from app.models.institution import Institution
from app.models.student import Student
from app.models.user import User
from app.services.ledger import reconcile

router = APIRouter()


class StudentOut(BaseModel):
    id: str
    full_name: str
    apaar_masked: Optional[str]
    identity_tier: str
    date_of_birth_year: Optional[int]

    model_config = {"from_attributes": True}


def _mask_apaar(apaar: Optional[str]) -> Optional[str]:
    if not apaar:
        return None
    return f"****{apaar[-4:]}" if len(apaar) >= 4 else "****"


class WithdrawBody(BaseModel):
    date: str       # YYYY-MM-DD
    reason: str = ""


class ApaarBody(BaseModel):
    apaar_id: str


@router.get("")
def list_students(
    institution_id: Optional[str] = None,
    search: Optional[str] = None,
    academic_year: str = "2026-27",
    page: int = 1,
    page_size: int = 50,
    db: Session = Depends(get_db),
    user: dict = Depends(require_roles(
        "NATIONAL_OFFICER", "REGIONAL_OFFICER", "COLLEGE_ADMIN", "SYSTEM_ADMIN"
    )),
):
    # Scope to institution
    if user.get("role") == "COLLEGE_ADMIN":
        scoped_institution = user.get("institution_id")
        if institution_id and institution_id != scoped_institution:
            raise HTTPException(status_code=403, detail="Access denied to this institution")
        institution_id = scoped_institution

    # Get course IDs for the institution+year
    if institution_id:
        course_ids = [
            c.id for c in db.query(CourseApproval).filter(
                CourseApproval.institution_id == institution_id,
                CourseApproval.academic_year == academic_year,
            ).all()
        ]
        if not course_ids:
            return {"students": [], "total": 0, "page": page}

        # Get student IDs via admission events
        student_id_rows = db.query(AdmissionEvent.student_id).filter(
            AdmissionEvent.course_approval_id.in_(course_ids),
            AdmissionEvent.event_type == "ADMIT",
        ).distinct().all()
        student_ids = [r[0] for r in student_id_rows]
    else:
        student_ids = None

    q = db.query(Student)
    if student_ids is not None:
        q = q.filter(Student.id.in_(student_ids))
    if search:
        q = q.filter(Student.full_name.ilike(f"%{search}%"))

    total = q.count()
    students = q.offset((page - 1) * page_size).limit(page_size).all()

    # Build response with admission info
    result = []
    for s in students:
        # Get most recent ADMIT event
        ev = db.query(AdmissionEvent).filter(
            AdmissionEvent.student_id == s.id,
            AdmissionEvent.event_type == "ADMIT",
        ).order_by(AdmissionEvent.event_time.desc()).first()
        withdraw_ev = db.query(AdmissionEvent).filter(
            AdmissionEvent.student_id == s.id,
            AdmissionEvent.event_type == "WITHDRAW",
        ).first()
        course = None
        if ev:
            course = db.query(CourseApproval).filter(CourseApproval.id == ev.course_approval_id).first()
        result.append({
            "id": s.id,
            "full_name": s.full_name,
            "apaar_masked": _mask_apaar(s.apaar_id),
            "identity_tier": s.identity_tier,
            "date_of_birth_year": s.date_of_birth.year if s.date_of_birth else None,
            "course_name": course.name if course else None,
            "course_id": course.id if course else None,
            "seat_category": ev.seat_category if ev else None,
            "admission_date": ev.event_time.date().isoformat() if ev else None,
            "status": "withdrawn" if withdraw_ev else "enrolled",
        })
    return {"students": result, "total": total, "page": page}


@router.get("/{student_id}")
def get_student(
    student_id: str,
    db: Session = Depends(get_db),
    user: dict = Depends(require_roles(
        "NATIONAL_OFFICER", "REGIONAL_OFFICER", "COLLEGE_ADMIN", "SYSTEM_ADMIN"
    )),
):
    s = db.query(Student).filter(Student.id == student_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Student not found")

    # Scope check for college admin
    if user.get("role") == "COLLEGE_ADMIN":
        ev = db.query(AdmissionEvent).filter(
            AdmissionEvent.student_id == student_id,
            AdmissionEvent.event_type == "ADMIT",
        ).first()
        if ev:
            course = db.query(CourseApproval).filter(CourseApproval.id == ev.course_approval_id).first()
            if not course or course.institution_id != user.get("institution_id"):
                raise HTTPException(status_code=403, detail="Access denied")

    ev = db.query(AdmissionEvent).filter(
        AdmissionEvent.student_id == student_id,
        AdmissionEvent.event_type == "ADMIT",
    ).order_by(AdmissionEvent.event_time.desc()).first()
    course = None
    if ev:
        course = db.query(CourseApproval).filter(CourseApproval.id == ev.course_approval_id).first()

    return {
        "id": s.id,
        "full_name": s.full_name,
        "apaar_masked": _mask_apaar(s.apaar_id),
        "identity_tier": s.identity_tier,
        "date_of_birth_year": s.date_of_birth.year if s.date_of_birth else None,
        "course_name": course.name if course else None,
        "course_id": course.id if course else None,
        "seat_category": ev.seat_category if ev else None,
        "admission_date": ev.event_time.date().isoformat() if ev else None,
    }


@router.post("/{student_id}/withdraw", status_code=200)
def withdraw_student(
    student_id: str,
    body: WithdrawBody,
    db: Session = Depends(get_db),
    user: dict = Depends(require_roles("COLLEGE_ADMIN", "SYSTEM_ADMIN")),
):
    s = db.query(Student).filter(Student.id == student_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Student not found")

    # Find the ADMIT event and course
    ev = db.query(AdmissionEvent).filter(
        AdmissionEvent.student_id == student_id,
        AdmissionEvent.event_type == "ADMIT",
    ).order_by(AdmissionEvent.event_time.desc()).first()
    if not ev:
        raise HTTPException(status_code=400, detail="No admission event found for this student")

    # Scope check
    if user.get("role") == "COLLEGE_ADMIN":
        course = db.query(CourseApproval).filter(CourseApproval.id == ev.course_approval_id).first()
        if not course or course.institution_id != user.get("institution_id"):
            raise HTTPException(status_code=403, detail="Access denied")

    # Check not already withdrawn
    existing_withdraw = db.query(AdmissionEvent).filter(
        AdmissionEvent.student_id == student_id,
        AdmissionEvent.event_type == "WITHDRAW",
    ).first()
    if existing_withdraw:
        raise HTTPException(status_code=400, detail="Student already withdrawn")

    try:
        withdraw_date = date.fromisoformat(body.date)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid date format, expected YYYY-MM-DD")

    withdraw_ev = AdmissionEvent(
        id=str(uuid4()),
        student_id=student_id,
        course_approval_id=ev.course_approval_id,
        seat_category=ev.seat_category,
        event_type="WITHDRAW",
        admission_round=ev.admission_round,
        entry_type=ev.entry_type,
        nationality_status=ev.nationality_status,
        event_time=datetime(withdraw_date.year, withdraw_date.month, withdraw_date.day,
                            12, 0, 0, tzinfo=timezone.utc),
    )
    db.add(withdraw_ev)
    db.commit()

    # Reconcile seat buckets
    try:
        reconcile(db, ev.course_approval_id)
    except Exception:
        pass

    return {"status": "withdrawn", "student_id": student_id, "date": body.date}


@router.patch("/{student_id}/apaar")
def update_apaar(
    student_id: str,
    body: ApaarBody,
    db: Session = Depends(get_db),
    user: dict = Depends(require_roles("COLLEGE_ADMIN", "SYSTEM_ADMIN")),
):
    s = db.query(Student).filter(Student.id == student_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Student not found")

    # Validate APAAR format
    if not (len(body.apaar_id) == 12 and body.apaar_id.isdigit()):
        raise HTTPException(status_code=422, detail="APAAR ID must be exactly 12 digits")

    # Try registry verification
    from app.simulators.registry_sim import verify as reg_verify
    result = reg_verify(db, body.apaar_id, "", "")
    registry_result = result.get("result")

    s.apaar_id = body.apaar_id
    if registry_result == "VERIFIED":
        s.identity_tier = "T1"
    elif registry_result == "UNAVAILABLE":
        s.identity_tier = "T2"  # retry later
    else:
        s.identity_tier = "T2"

    db.commit()
    return {
        "student_id": student_id,
        "apaar_masked": _mask_apaar(s.apaar_id),
        "identity_tier": s.identity_tier,
        "registry_result": registry_result,
    }


@router.get("/me")
def get_my_record(
    db: Session = Depends(get_db),
    user: dict = Depends(require_roles("STUDENT")),
):
    uid = db.query(User).filter(User.id == user["sub"]).first()
    if not uid or not uid.student_id:
        raise HTTPException(status_code=404, detail="No student record linked")
    s = db.query(Student).filter(Student.id == uid.student_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Student not found")

    ev = db.query(AdmissionEvent).filter(
        AdmissionEvent.student_id == s.id,
        AdmissionEvent.event_type == "ADMIT",
    ).order_by(AdmissionEvent.event_time.desc()).first()
    course = db.query(CourseApproval).filter(CourseApproval.id == ev.course_approval_id).first() if ev else None
    inst = db.query(Institution).filter(Institution.id == course.institution_id).first() if course else None
    withdraw_ev = db.query(AdmissionEvent).filter(
        AdmissionEvent.student_id == s.id,
        AdmissionEvent.event_type == "WITHDRAW",
    ).first()

    return {
        "id": s.id,
        "full_name": s.full_name,
        "apaar_last4": s.apaar_id[-4:] if s.apaar_id and len(s.apaar_id) >= 4 else None,
        "identity_tier": s.identity_tier,
        "institution_name": inst.name if inst else None,
        "institution_id": inst.id if inst else None,
        "programme": course.name if course else None,
        "course_id": course.id if course else None,
        "status": "withdrawn" if withdraw_ev else "enrolled",
        "enrolled_period": f"{ev.event_time.year}-{ev.event_time.year + 4}" if ev else None,
    }


@router.get("/me/access-log")
def get_my_access_log(
    db: Session = Depends(get_db),
    user: dict = Depends(require_roles("STUDENT")),
):
    uid = db.query(User).filter(User.id == user["sub"]).first()
    if not uid or not uid.student_id:
        return []
    student_id = uid.student_id
    entries = db.query(AuditEntry).filter(
        AuditEntry.object_id == student_id,
    ).order_by(AuditEntry.time.desc()).limit(50).all()
    return [
        {
            "id": e.id,
            "time": e.time.isoformat() if e.time else None,
            "actor": e.actor,
            "role": e.actor_role,
            "action": e.action,
            "object_type": e.object_type,
        }
        for e in entries
    ]
