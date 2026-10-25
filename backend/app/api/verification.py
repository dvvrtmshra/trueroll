"""Employer verification endpoints — spec 6.7.

The minimal response is the ONLY thing an employer ever sees.
Never returned: marks, address, DOB, phone, Aadhaar, other institutions, flags.
"""
import base64
import hashlib
import json
from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

import jwt as pyjwt
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.audit import append_audit_entry
from app.core.clock import app_now
from app.core.database import get_db
from app.core.security import get_current_user, require_roles
from app.core.signing import sign_credential, verify_credential
from app.models.admission_event import AdmissionEvent
from app.models.course import CourseApproval
from app.models.employer import Employer
from app.models.institution import Institution
from app.models.outbox import Outbox
from app.models.share_code import ShareCode
from app.models.student import Student
from app.models.user import User
from app.models.verification_event import VerificationEvent

router = APIRouter()

RATE_LIMIT = 20  # per hour per employer


def _hash_code(raw: str) -> str:
    """Hash a display code (XXXX-XXXX → XXXXXXXX → sha256)."""
    normalised = raw.replace("-", "").upper()
    return hashlib.sha256(normalised.encode()).hexdigest()


def _mask_name(full_name: str, apaar: Optional[str]) -> str:
    """Return 'A.K.M. ...4271' style display."""
    parts = full_name.split()
    initials = ".".join(p[0].upper() for p in parts[:-1]) + "." if len(parts) > 1 else ""
    suffix = f"...{apaar[-4:]}" if apaar and len(apaar) >= 4 else ""
    return f"{initials} {suffix}".strip() if initials else suffix or full_name[:3] + "..."


def _check_rate_limit(db: Session, employer_id: str, now: datetime) -> None:
    from datetime import timedelta
    window_start = now - timedelta(hours=1)
    count = db.query(VerificationEvent).filter(
        VerificationEvent.employer_id == employer_id,
        VerificationEvent.verified_at >= window_start,
    ).count()
    if count >= RATE_LIMIT:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit: {RATE_LIMIT} verifications per hour. Try again later.",
        )


class VerifyRequest(BaseModel):
    code: str


@router.post("")
def verify(
    body: VerifyRequest,
    db: Session = Depends(get_db),
    user: dict = Depends(require_roles("EMPLOYER")),
):
    now = app_now(db)
    uid = db.query(User).filter(User.id == user["sub"]).first()
    employer_id = uid.employer_id if uid else None
    if not employer_id:
        raise HTTPException(status_code=403, detail="No employer record linked to this account")

    _check_rate_limit(db, employer_id, now)

    code_hash = _hash_code(body.code)
    sc = db.query(ShareCode).filter(ShareCode.code_hash == code_hash).first()

    verification_id = "vf_" + str(uuid4())[:8]

    def _log(result: str, sig_valid: bool = False):
        ev = VerificationEvent(
            share_code_id=sc.id if sc else None,
            employer_id=employer_id,
            result=result,
            verification_id=verification_id,
            signature_valid=sig_valid,
            verified_at=now,
        )
        db.add(ev)
        append_audit_entry(
            db, actor=user.get("email", employer_id), role="EMPLOYER",
            action="VERIFICATION", object_type="ShareCode",
            object_id=sc.id if sc else body.code[:8],
            time=now,
        )
        db.commit()

    if not sc:
        _log("NOT_FOUND")
        return {"result": "NOT_FOUND", "message": "No such code."}

    if sc.status == "withdrawn":
        _log("WITHDRAWN")
        return {"result": "WITHDRAWN", "message": "The student has withdrawn consent."}

    if now > sc.expires_at:
        sc.status = "expired"
        db.commit()
        _log("EXPIRED")
        return {"result": "EXPIRED", "message": "This code has expired. Ask the student for a new one."}

    if sc.employer_id != employer_id:
        _log("NOT_FOR_THIS_VERIFIER")
        return {"result": "NOT_FOR_THIS_VERIFIER", "message": "This code was issued to a different verifier."}

    # Look up student enrolment
    student = db.query(Student).filter(Student.id == sc.student_id).first()
    if not student:
        _log("NOT_FOUND")
        return {"result": "NOT_FOUND", "message": "No such code."}

    ev = db.query(AdmissionEvent).filter(
        AdmissionEvent.student_id == student.id,
        AdmissionEvent.event_type == "ADMIT",
    ).order_by(AdmissionEvent.event_time.desc()).first()

    course = db.query(CourseApproval).filter(CourseApproval.id == ev.course_approval_id).first() if ev else None
    inst = db.query(Institution).filter(Institution.id == course.institution_id).first() if course else None
    emp = db.query(Employer).filter(Employer.id == employer_id).first()

    # Check for withdrawal
    withdraw_ev = db.query(AdmissionEvent).filter(
        AdmissionEvent.student_id == student.id,
        AdmissionEvent.event_type == "WITHDRAW",
    ).first()
    enrol_status = "WITHDRAWN" if withdraw_ev else "ENROLLED"

    # Build minimal claims (spec 6.7) — only these fields, never anything else
    claims = {
        "iss": "trueroll.demo",
        "sub": student.id,
        "inst": inst.name if inst else "Unknown",
        "programme": course.name if course else "Unknown",
        "status": enrol_status,
        "period": f"{ev.event_time.year}-{ev.event_time.year + 4}" if ev else "Unknown",
        "verifier": employer_id,
        "purpose": sc.purpose,
        "consent_id": sc.id,
        "iat": int(now.timestamp()),
        "exp": int(sc.expires_at.timestamp()),
    }

    try:
        token = sign_credential(claims)
        verify_credential(token)  # immediate self-verification
        sig_valid = True
    except Exception:
        _log("INVALID_SIGNATURE", sig_valid=False)
        return {"result": "INVALID_SIGNATURE", "message": "This credential failed the signature check."}

    # Increment use count
    sc.used_count += 1
    db.flush()

    _log("VERIFIED", sig_valid=True)

    # Mock notification to student
    db.add(Outbox(
        event_type="verification_performed",
        payload=json.dumps({
            "student_id": student.id,
            "employer": emp.name if emp else employer_id,
            "purpose": sc.purpose,
            "result": "VERIFIED",
        }),
    ))
    db.commit()

    # MINIMAL RESPONSE ONLY — spec 6.7
    return {
        "verification_id": verification_id,
        "result": "VERIFIED",
        "student_display": _mask_name(student.full_name, student.apaar_id),
        "institution": inst.name if inst else "Unknown",
        "programme": course.name if course else "Unknown",
        "status": enrol_status,
        "valid_as_of": now.isoformat(),
        "consent_expires": sc.expires_at.isoformat(),
        "signature_valid": True,
        # shared_by is OK — not a forbidden field
        "shared_by": f"the student, for {emp.name if emp else employer_id} ({sc.purpose})",
    }


@router.get("/history")
def verification_history(
    db: Session = Depends(get_db),
    user: dict = Depends(require_roles("EMPLOYER")),
):
    uid = db.query(User).filter(User.id == user["sub"]).first()
    employer_id = uid.employer_id if uid else None
    if not employer_id:
        raise HTTPException(status_code=403, detail="No employer record")

    events = db.query(VerificationEvent).filter(
        VerificationEvent.employer_id == employer_id
    ).order_by(VerificationEvent.verified_at.desc()).limit(100).all()

    result = []
    for e in events:
        sc = db.query(ShareCode).filter(ShareCode.id == e.share_code_id).first() if e.share_code_id else None
        result.append({
            "verification_id": e.verification_id,
            "result": e.result,
            "verified_at": e.verified_at.isoformat(),
            "consent_expires": sc.expires_at.isoformat() if sc else None,
            "purpose": sc.purpose if sc else None,
        })
    return result


# Public: GET /v/{code} → redirect to verify page
@router.get("/public/{code}", response_class=HTMLResponse)
def public_verify_redirect(code: str):
    """QR code scan landing — redirect to the frontend verify page."""
    safe_code = "".join(c for c in code if c.isalnum() or c == "-")[:9]
    return HTMLResponse(
        f'<meta http-equiv="refresh" content="0;url=/verify?code={safe_code}">',
        status_code=302,
    )
