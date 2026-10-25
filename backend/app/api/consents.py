"""Student consent (share code) endpoints — spec 6.7."""
import base64
import hashlib
import json
import os
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.audit import append_audit_entry
from app.core.clock import app_now
from app.core.database import get_db
from app.core.security import get_current_user, require_roles
from app.models.employer import Employer
from app.models.outbox import Outbox
from app.models.share_code import ShareCode
from app.models.user import User

router = APIRouter()

PURPOSES = {"Internship", "Employment", "Background Check", "Other"}
VALID_DAYS = {7, 30, 90}


def _generate_code() -> tuple[str, str]:
    """Return (display_code 'XXXX-XXXX', sha256_hex)."""
    raw = os.urandom(5)
    b32 = base64.b32encode(raw).decode().rstrip("=")[:8].upper()
    display = f"{b32[:4]}-{b32[4:]}"
    code_hash = hashlib.sha256(b32.encode()).hexdigest()
    return display, code_hash


def _student_id_from_user(user: dict, db: Session) -> str:
    uid = db.query(User).filter(User.id == user["sub"]).first()
    if not uid or not uid.student_id:
        raise HTTPException(status_code=403, detail="No student record linked to this account")
    return uid.student_id


class CreateShareCode(BaseModel):
    employer_id: str
    purpose: str
    expires_days: int = 30


class WithdrawBody(BaseModel):
    pass


@router.post("", status_code=201)
def create_share_code(
    body: CreateShareCode,
    db: Session = Depends(get_db),
    user: dict = Depends(require_roles("STUDENT")),
):
    if body.purpose not in PURPOSES:
        raise HTTPException(status_code=422, detail=f"purpose must be one of {sorted(PURPOSES)}")
    if body.expires_days not in VALID_DAYS:
        raise HTTPException(status_code=422, detail="expires_days must be 7, 30, or 90")

    student_id = _student_id_from_user(user, db)

    emp = db.query(Employer).filter(Employer.id == body.employer_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employer not found")

    now = app_now(db)
    expires_at = now + timedelta(days=body.expires_days)
    display_code, code_hash = _generate_code()

    sc = ShareCode(
        student_id=student_id,
        employer_id=body.employer_id,
        purpose=body.purpose,
        code_hash=code_hash,
        status="active",
        created_at=now,
        expires_at=expires_at,
    )
    db.add(sc)
    db.flush()

    append_audit_entry(
        db, actor=user.get("email", user["sub"]), role="STUDENT",
        action="CONSENT_CREATED", object_type="ShareCode", object_id=sc.id, time=now,
    )

    # Mock notification to student
    db.add(Outbox(
        event_type="consent_created",
        payload=json.dumps({
            "student_id": student_id,
            "employer": emp.name,
            "purpose": body.purpose,
            "expires_at": expires_at.isoformat(),
            "code_preview": display_code[:4] + "-****",
        }),
    ))
    db.commit()

    return {
        "consent_id": sc.id,
        "code": display_code,
        "qr_url": f"/v/{display_code.replace('-', '')}",
        "expires_at": expires_at.isoformat(),
        "employer_name": emp.name,
        "purpose": body.purpose,
    }


@router.get("")
def list_share_codes(
    db: Session = Depends(get_db),
    user: dict = Depends(require_roles("STUDENT")),
):
    student_id = _student_id_from_user(user, db)
    codes = db.query(ShareCode).filter(ShareCode.student_id == student_id).order_by(
        ShareCode.created_at.desc()
    ).all()

    result = []
    for sc in codes:
        emp = db.query(Employer).filter(Employer.id == sc.employer_id).first()
        result.append({
            "id": sc.id,
            "employer_id": sc.employer_id,
            "employer_name": emp.name if emp else sc.employer_id,
            "purpose": sc.purpose,
            "status": sc.status,
            "created_at": sc.created_at.isoformat(),
            "expires_at": sc.expires_at.isoformat(),
            "withdrawn_at": sc.withdrawn_at.isoformat() if sc.withdrawn_at else None,
            "used_count": sc.used_count,
        })
    return result


@router.get("/{code_id}")
def get_share_code(
    code_id: str,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    sc = db.query(ShareCode).filter(ShareCode.id == code_id).first()
    if not sc:
        raise HTTPException(status_code=404, detail="Share code not found")

    role = user.get("role")
    # Student can see own; employer can see if they are the verifier
    if role == "STUDENT":
        uid = db.query(User).filter(User.id == user["sub"]).first()
        if not uid or uid.student_id != sc.student_id:
            raise HTTPException(status_code=403, detail="Access denied")
    elif role == "EMPLOYER":
        uid = db.query(User).filter(User.id == user["sub"]).first()
        if not uid or uid.employer_id != sc.employer_id:
            raise HTTPException(status_code=403, detail="Access denied")
    else:
        raise HTTPException(status_code=403, detail="Access denied")

    emp = db.query(Employer).filter(Employer.id == sc.employer_id).first()
    return {
        "id": sc.id,
        "employer_name": emp.name if emp else sc.employer_id,
        "purpose": sc.purpose,
        "status": sc.status,
        "created_at": sc.created_at.isoformat(),
        "expires_at": sc.expires_at.isoformat(),
        "withdrawn_at": sc.withdrawn_at.isoformat() if sc.withdrawn_at else None,
        "used_count": sc.used_count,
    }


@router.post("/{code_id}/withdraw")
def withdraw_share_code(
    code_id: str,
    db: Session = Depends(get_db),
    user: dict = Depends(require_roles("STUDENT")),
):
    student_id = _student_id_from_user(user, db)
    sc = db.query(ShareCode).filter(ShareCode.id == code_id, ShareCode.student_id == student_id).first()
    if not sc:
        raise HTTPException(status_code=404, detail="Share code not found")
    if sc.status == "withdrawn":
        raise HTTPException(status_code=400, detail="Already withdrawn")

    now = app_now(db)
    sc.status = "withdrawn"
    sc.withdrawn_at = now

    append_audit_entry(
        db, actor=user.get("email", user["sub"]), role="STUDENT",
        action="CONSENT_WITHDRAWN", object_type="ShareCode", object_id=sc.id, time=now,
    )

    emp = db.query(Employer).filter(Employer.id == sc.employer_id).first()
    db.add(Outbox(
        event_type="consent_withdrawn",
        payload=json.dumps({
            "student_id": student_id,
            "employer": emp.name if emp else sc.employer_id,
            "purpose": sc.purpose,
        }),
    ))
    db.commit()
    return {"status": "withdrawn", "id": code_id}
