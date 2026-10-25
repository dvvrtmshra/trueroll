"""Flag list and management endpoints."""
import json
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_roles, get_current_user
from app.models.flag import Flag

router = APIRouter()


class FlagOut(BaseModel):
    id: str
    institution_id: str
    course_approval_id: str
    bucket: str
    rule_id: Optional[str]
    rule_version: Optional[int]
    evaluation_id: Optional[str]
    cap: Optional[int]
    used: Optional[int]
    over_by: Optional[int]
    record_ids: str
    status: str
    severity: str
    opened_at: datetime
    assigned_officer: Optional[str]
    decision: Optional[str]
    decision_reason: Optional[str]
    updated_at: datetime

    model_config = {"from_attributes": True}


class FlagEventBody(BaseModel):
    action: str       # assign | request_clarification | resolve | escalate | reply
    officer_id: Optional[str] = None
    reason: Optional[str] = None
    decision: Optional[str] = None
    message: Optional[str] = None


OFFICER_ROLES = ("NATIONAL_OFFICER", "REGIONAL_OFFICER", "RULES_OWNER", "RULES_APPROVER", "SYSTEM_ADMIN")
ALL_FLAG_ROLES = OFFICER_ROLES + ("COLLEGE_ADMIN",)


@router.get("")
def list_flags(
    institution_id: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    user: dict = Depends(require_roles(*ALL_FLAG_ROLES)),
):
    q = db.query(Flag)
    # College admin: see only own flags
    if user.get("role") == "COLLEGE_ADMIN":
        q = q.filter(Flag.institution_id == user.get("institution_id"))
    else:
        # Scope filter: regional officer sees only their institutions
        if user.get("role") == "REGIONAL_OFFICER" and user.get("region"):
            from app.models.institution import Institution
            inst_ids = [
                i.id for i in db.query(Institution).filter(Institution.region == user["region"]).all()
            ]
            q = q.filter(Flag.institution_id.in_(inst_ids))
        if institution_id:
            q = q.filter(Flag.institution_id == institution_id)
    if status:
        q = q.filter(Flag.status == status)
    return [FlagOut.model_validate(f) for f in q.order_by(Flag.opened_at.desc()).all()]


@router.get("/{flag_id}")
def get_flag(
    flag_id: str,
    db: Session = Depends(get_db),
    user: dict = Depends(require_roles(*ALL_FLAG_ROLES)),
):
    f = db.query(Flag).filter(Flag.id == flag_id).first()
    if not f:
        raise HTTPException(status_code=404, detail="Flag not found")
    # College admin: only own flags
    if user.get("role") == "COLLEGE_ADMIN" and f.institution_id != user.get("institution_id"):
        raise HTTPException(status_code=403, detail="Access denied")
    return FlagOut.model_validate(f)


@router.post("/{flag_id}/events")
def add_flag_event(
    flag_id: str,
    body: FlagEventBody,
    db: Session = Depends(get_db),
    user: dict = Depends(require_roles(*ALL_FLAG_ROLES)),
):
    f = db.query(Flag).filter(Flag.id == flag_id).first()
    if not f:
        raise HTTPException(status_code=404, detail="Flag not found")
    # College admin: only own flags, only reply action
    if user.get("role") == "COLLEGE_ADMIN":
        if f.institution_id != user.get("institution_id"):
            raise HTTPException(status_code=403, detail="Access denied")
        if body.action not in ("reply",):
            raise HTTPException(status_code=403, detail="College admin can only submit replies")
    now = datetime.now(timezone.utc)
    if body.action == "assign":
        f.assigned_officer = body.officer_id or user["user_id"]
        f.status = "under_review"
    elif body.action == "request_clarification":
        f.status = "clarification_requested"
    elif body.action == "resolve":
        f.status = "resolved"
        f.decision = body.decision
        f.decision_reason = body.reason
    elif body.action == "escalate":
        f.status = "escalated"
    elif body.action == "reply":
        # College admin reply — store message in decision_reason, move to under_review
        existing = f.decision_reason or ""
        f.decision_reason = (existing + f"\n[College reply] {body.message or ''}").strip()
        if f.status == "clarification_requested":
            f.status = "clarification_replied"
    else:
        raise HTTPException(status_code=422, detail=f"Unknown action {body.action!r}")
    f.updated_at = now
    db.commit()
    return FlagOut.model_validate(f)
