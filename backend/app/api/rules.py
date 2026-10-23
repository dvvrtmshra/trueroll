"""Rules CRUD and lifecycle endpoints."""
import json
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_roles
from app.models.rule import Rule, RuleVersion
from app.services import rules_service

router = APIRouter()


# ── Schemas ───────────────────────────────────────────────────────────────────

class RuleVersionOut(BaseModel):
    id: str
    rule_id: str
    version: int
    academic_year: str
    programme_level: str
    domain: str
    state: str
    institution_type: str
    bucket: str
    cap_basis: str
    cap_percent: Optional[float]
    cap_fixed: Optional[int]
    eligible_categories: str
    source_document: str
    source_clause: str
    source_url: Optional[str]
    effective_from: Optional[date]
    effective_to: Optional[date]
    status: str
    enabled: bool
    approvals: str
    illustrative_label: str = "Illustrative: to be confirmed against AICTE rules"

    model_config = {"from_attributes": True}


class ProposeBody(BaseModel):
    rule_id: str
    version: int
    academic_year: str
    programme_level: list[str]
    domain: str = "ALL"
    state: str = "ALL"
    institution_type: str = "ALL"
    bucket: str
    cap_basis: str
    cap_percent: Optional[float] = None
    cap_fixed: Optional[int] = None
    eligible_categories: list[str] = []
    source_document: str
    source_clause: str
    source_url: Optional[str] = None
    effective_from: Optional[date] = None
    effective_to: Optional[date] = None


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("")
def list_rules(
    academic_year: Optional[str] = None,
    db: Session = Depends(get_db),
    _: dict = Depends(require_roles("RULES_OWNER", "RULES_APPROVER", "NATIONAL_OFFICER", "SYSTEM_ADMIN")),
):
    q = db.query(RuleVersion)
    if academic_year:
        q = q.filter(RuleVersion.academic_year == academic_year)
    return [RuleVersionOut.model_validate(rv) for rv in q.order_by(RuleVersion.rule_id, RuleVersion.version).all()]


@router.post("", status_code=201)
def propose_rule(
    body: ProposeBody,
    db: Session = Depends(get_db),
    user: dict = Depends(require_roles("RULES_OWNER", "SYSTEM_ADMIN")),
):
    try:
        rv = rules_service.propose_rule(
            db,
            rule_id=body.rule_id,
            version=body.version,
            academic_year=body.academic_year,
            programme_level=body.programme_level,
            domain=body.domain,
            state=body.state,
            institution_type=body.institution_type,
            bucket=body.bucket,
            cap_basis=body.cap_basis,
            cap_percent=body.cap_percent,
            cap_fixed=body.cap_fixed,
            eligible_categories=body.eligible_categories,
            source_document=body.source_document,
            source_clause=body.source_clause,
            source_url=body.source_url,
            effective_from=body.effective_from,
            effective_to=body.effective_to,
            proposer_id=user["user_id"],
            proposer_email=user["email"],
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    return RuleVersionOut.model_validate(rv)


@router.get("/{rule_id}/versions")
def list_rule_versions(
    rule_id: str,
    db: Session = Depends(get_db),
    _: dict = Depends(require_roles("RULES_OWNER", "RULES_APPROVER", "NATIONAL_OFFICER", "SYSTEM_ADMIN")),
):
    rows = (
        db.query(RuleVersion)
        .filter(RuleVersion.rule_id == rule_id)
        .order_by(RuleVersion.version)
        .all()
    )
    return [RuleVersionOut.model_validate(rv) for rv in rows]


@router.post("/{rule_id}/versions/{version}/submit")
def submit_for_review(
    rule_id: str,
    version: int,
    db: Session = Depends(get_db),
    user: dict = Depends(require_roles("RULES_OWNER", "SYSTEM_ADMIN")),
):
    rv = db.query(RuleVersion).filter(
        RuleVersion.rule_id == rule_id,
        RuleVersion.version == version,
    ).first()
    if not rv:
        raise HTTPException(status_code=404, detail="Rule version not found")
    try:
        rv = rules_service.submit_for_review(db, rv, user["email"])
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    return RuleVersionOut.model_validate(rv)


@router.post("/{rule_id}/versions/{version}/approve")
def approve_rule(
    rule_id: str,
    version: int,
    db: Session = Depends(get_db),
    user: dict = Depends(require_roles("RULES_APPROVER", "SYSTEM_ADMIN")),
):
    rv = db.query(RuleVersion).filter(
        RuleVersion.rule_id == rule_id,
        RuleVersion.version == version,
    ).first()
    if not rv:
        raise HTTPException(status_code=404, detail="Rule version not found")
    try:
        rv = rules_service.approve_rule_version(db, rv, user["email"])
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    return RuleVersionOut.model_validate(rv)


@router.post("/{rule_id}/versions/{version}/activate")
def activate_rule(
    rule_id: str,
    version: int,
    db: Session = Depends(get_db),
    user: dict = Depends(require_roles("RULES_OWNER", "RULES_APPROVER", "SYSTEM_ADMIN")),
):
    rv = db.query(RuleVersion).filter(
        RuleVersion.rule_id == rule_id,
        RuleVersion.version == version,
    ).first()
    if not rv:
        raise HTTPException(status_code=404, detail="Rule version not found")
    try:
        rv = rules_service.activate_rule_version(db, rv, date.today())
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    return RuleVersionOut.model_validate(rv)
