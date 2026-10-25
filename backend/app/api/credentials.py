"""Credential (certificate) endpoints — spec 6.7."""
import json
from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.audit import append_audit_entry
from app.core.clock import app_now
from app.core.database import get_db
from app.core.security import get_current_user, require_roles
from app.core.signing import sign_credential, verify_credential
from app.models.admission_event import AdmissionEvent
from app.models.course import CourseApproval
from app.models.credential import Credential
from app.models.institution import Institution
from app.models.student import Student
from app.models.user import User

router = APIRouter()


class IssueBody(BaseModel):
    student_id: str
    course_id: Optional[str] = None


class RevokeBody(BaseModel):
    reason: str = ""


@router.post("/certificates", status_code=201)
def issue_certificate(
    body: IssueBody,
    db: Session = Depends(get_db),
    user: dict = Depends(require_roles("COLLEGE_ADMIN", "SYSTEM_ADMIN", "STUDENT")),
):
    student = db.query(Student).filter(Student.id == body.student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    ev = db.query(AdmissionEvent).filter(
        AdmissionEvent.student_id == body.student_id,
        AdmissionEvent.event_type == "ADMIT",
    ).order_by(AdmissionEvent.event_time.desc()).first()

    course = db.query(CourseApproval).filter(
        CourseApproval.id == (body.course_id or (ev.course_approval_id if ev else ""))
    ).first()
    inst = db.query(Institution).filter(Institution.id == course.institution_id).first() if course else None

    now = app_now(db)
    withdraw_ev = db.query(AdmissionEvent).filter(
        AdmissionEvent.student_id == body.student_id,
        AdmissionEvent.event_type == "WITHDRAW",
    ).first()

    claims = {
        "iss": "trueroll.demo",
        "sub": student.id,
        "inst": inst.name if inst else "Unknown",
        "programme": course.name if course else "Unknown",
        "status": "WITHDRAWN" if withdraw_ev else "ENROLLED",
        "period": f"{ev.event_time.year}-{ev.event_time.year + 4}" if ev else "Unknown",
        "iat": int(now.timestamp()),
        "exp": int((now.replace(year=now.year + 1)).timestamp()),
        "cert_type": "enrollment",
    }

    vc_jwt = sign_credential(claims)

    cred = Credential(
        student_id=body.student_id,
        admission_event_id=ev.id if ev else "none",
        credential_type="admission",
        did=f"did:trueroll:{str(uuid4())}",
        vc_jwt=vc_jwt,
        public_key_kid="key-2026-10-a",
        issued_at=now,
    )
    db.add(cred)

    append_audit_entry(
        db, actor=user.get("email", user["sub"]), role=user.get("role", "SYSTEM"),
        action="CERTIFICATE_ISSUED", object_type="Credential", object_id=cred.id, time=now,
    )
    db.commit()
    db.refresh(cred)

    return {
        "credential_id": cred.id,
        "student_id": student.id,
        "programme": course.name if course else "Unknown",
        "institution": inst.name if inst else "Unknown",
        "issued_at": now.isoformat(),
        "vc_jwt": vc_jwt,
        "download_url": f"/credentials/certificates/{cred.id}",
    }


@router.get("/certificates")
def list_certificates(
    student_id: Optional[str] = None,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    role = user.get("role")
    # Students can only see their own
    if role == "STUDENT":
        uid = db.query(User).filter(User.id == user["sub"]).first()
        if not uid or not uid.student_id:
            return []
        student_id = uid.student_id

    q = db.query(Credential)
    if student_id:
        q = q.filter(Credential.student_id == student_id)
    creds = q.order_by(Credential.issued_at.desc()).limit(50).all()

    result = []
    for c in creds:
        student = db.query(Student).filter(Student.id == c.student_id).first()
        result.append({
            "id": c.id,
            "student_id": c.student_id,
            "student_name": student.full_name if student else "Unknown",
            "credential_type": c.credential_type,
            "issued_at": c.issued_at.isoformat(),
            "expires_at": c.expires_at.isoformat() if c.expires_at else None,
            "revoked": c.revoked,
            "revocation_reason": c.revocation_reason,
            "download_url": f"/credentials/certificates/{c.id}",
        })
    return result


@router.get("/certificates/{credential_id}")
def get_certificate(
    credential_id: str,
    db: Session = Depends(get_db),
):
    """Public endpoint — returns signed credential JSON for QR verification."""
    cred = db.query(Credential).filter(Credential.id == credential_id).first()
    if not cred:
        raise HTTPException(status_code=404, detail="Credential not found")
    if cred.revoked:
        return {"revoked": True, "reason": cred.revocation_reason}
    return {"vc_jwt": cred.vc_jwt, "revoked": False}


@router.post("/certificates/{credential_id}/revoke")
def revoke_certificate(
    credential_id: str,
    body: RevokeBody,
    db: Session = Depends(get_db),
    user: dict = Depends(require_roles("COLLEGE_ADMIN", "SYSTEM_ADMIN")),
):
    cred = db.query(Credential).filter(Credential.id == credential_id).first()
    if not cred:
        raise HTTPException(status_code=404, detail="Credential not found")
    if cred.revoked:
        raise HTTPException(status_code=400, detail="Already revoked")

    now = app_now(db)
    cred.revoked = True
    cred.revoked_at = now
    cred.revocation_reason = body.reason

    append_audit_entry(
        db, actor=user.get("email", user["sub"]), role=user.get("role", "SYSTEM"),
        action="CERTIFICATE_REVOKED", object_type="Credential", object_id=cred.id, time=now,
    )
    db.commit()
    return {"revoked": True, "credential_id": credential_id}
