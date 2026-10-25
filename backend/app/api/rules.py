"""Rules CRUD and lifecycle endpoints."""
import json
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_roles
from app.models.course import CourseApproval
from app.models.evaluation import Evaluation
from app.models.institution import Institution
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
    proposed_by: Optional[str] = None
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


class RejectBody(BaseModel):
    reason: str


class BacktestBody(BaseModel):
    version: int
    academic_year: str = "2026-27"


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("")
def list_rules(
    academic_year: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    _: dict = Depends(require_roles("RULES_OWNER", "RULES_APPROVER", "NATIONAL_OFFICER", "REGIONAL_OFFICER", "SYSTEM_ADMIN")),
):
    q = db.query(RuleVersion)
    if academic_year:
        q = q.filter(RuleVersion.academic_year == academic_year)
    if status:
        q = q.filter(RuleVersion.status == status)
    return [RuleVersionOut.model_validate(rv) for rv in q.order_by(RuleVersion.rule_id, RuleVersion.version).all()]


@router.get("/unconfirmed")
def list_unconfirmed(
    db: Session = Depends(get_db),
    _: dict = Depends(require_roles("RULES_OWNER", "NATIONAL_OFFICER", "REGIONAL_OFFICER", "SYSTEM_ADMIN")),
):
    """Courses whose most recent Evaluation has status RULE_NOT_CONFIRMED."""
    # Find most recent evaluation per course
    from sqlalchemy import func
    subq = (
        db.query(
            Evaluation.course_approval_id,
            func.max(Evaluation.evaluated_at).label("max_at"),
        )
        .group_by(Evaluation.course_approval_id)
        .subquery()
    )
    latest = (
        db.query(Evaluation)
        .join(subq, (Evaluation.course_approval_id == subq.c.course_approval_id) &
              (Evaluation.evaluated_at == subq.c.max_at))
        .filter(Evaluation.result == "RULE_NOT_CONFIRMED")
        .all()
    )
    result = []
    for ev in latest:
        course = db.query(CourseApproval).filter(CourseApproval.id == ev.course_approval_id).first()
        if not course:
            continue
        inst = db.query(Institution).filter(Institution.id == course.institution_id).first()
        detail = json.loads(ev.result_detail or "{}")
        result.append({
            "course_id": ev.course_approval_id,
            "institution_id": course.institution_id,
            "institution_name": inst.name if inst else course.institution_id,
            "course_name": course.name,
            "evaluation_id": ev.id,
            "evaluated_at": ev.evaluated_at.isoformat(),
            "missing_rule_buckets": detail.get("review_reason", ""),
        })
    return result


@router.post("/tests/run")
def run_regression_tests(
    db: Session = Depends(get_db),
    _: dict = Depends(require_roles("RULES_OWNER", "SYSTEM_ADMIN")),
):
    from app.services.regression import run_regression_tests as _run
    return _run()


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
    _: dict = Depends(require_roles("RULES_OWNER", "RULES_APPROVER", "NATIONAL_OFFICER", "REGIONAL_OFFICER", "SYSTEM_ADMIN")),
):
    rows = (
        db.query(RuleVersion)
        .filter(RuleVersion.rule_id == rule_id)
        .order_by(RuleVersion.version)
        .all()
    )
    return [RuleVersionOut.model_validate(rv) for rv in rows]


@router.get("/{rule_id}/versions/{version}")
def get_rule_version(
    rule_id: str,
    version: int,
    db: Session = Depends(get_db),
    _: dict = Depends(require_roles("RULES_OWNER", "RULES_APPROVER", "NATIONAL_OFFICER", "REGIONAL_OFFICER", "SYSTEM_ADMIN")),
):
    rv = db.query(RuleVersion).filter(
        RuleVersion.rule_id == rule_id,
        RuleVersion.version == version,
    ).first()
    if not rv:
        raise HTTPException(status_code=404, detail="Rule version not found")
    # Count evaluations that used this rule version
    eval_count = db.query(Evaluation).filter(
        Evaluation.rule_versions_used.contains(rv.id)
    ).count()
    out = RuleVersionOut.model_validate(rv)
    return {**out.model_dump(), "evaluation_count": eval_count}


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
    user: dict = Depends(require_roles("RULES_APPROVER", "RULES_OWNER", "SYSTEM_ADMIN")),
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


@router.post("/{rule_id}/versions/{version}/reject")
def reject_rule(
    rule_id: str,
    version: int,
    body: RejectBody,
    db: Session = Depends(get_db),
    user: dict = Depends(require_roles("RULES_APPROVER", "RULES_OWNER", "SYSTEM_ADMIN")),
):
    rv = db.query(RuleVersion).filter(
        RuleVersion.rule_id == rule_id,
        RuleVersion.version == version,
    ).first()
    if not rv:
        raise HTTPException(status_code=404, detail="Rule version not found")
    if rv.status not in ("pending_review", "approved"):
        raise HTTPException(status_code=422, detail=f"Rule is {rv.status}, cannot reject")
    existing = json.loads(rv.approvals)
    for a in existing:
        if a.get("by") == user["email"] and a.get("role") == "proposer":
            raise HTTPException(status_code=422, detail="Proposer cannot reject their own rule")
    from datetime import datetime, timezone
    existing.append({
        "by": user["email"], "role": "rejector",
        "at": datetime.now(timezone.utc).isoformat(),
        "reason": body.reason,
    })
    rv.approvals = json.dumps(existing)
    rv.status = "rejected"
    db.commit()
    db.refresh(rv)
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
    from app.core.clock import app_now
    as_of = app_now(db).date()
    try:
        rv = rules_service.activate_rule_version(db, rv, as_of)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    # Re-run Seat-Ledger for all courses in this academic year
    courses = db.query(CourseApproval).filter(
        CourseApproval.academic_year == rv.academic_year
    ).all()
    from app.services.ledger import evaluate, reconcile
    rerun_count = 0
    for c in courses:
        try:
            reconcile(db, c.id)
            evaluate(db, c.id, as_of)
            rerun_count += 1
        except Exception:
            pass
    return {**RuleVersionOut.model_validate(rv).model_dump(), "courses_reevaluated": rerun_count}


@router.post("/{rule_id}/backtest")
def backtest_rule(
    rule_id: str,
    body: BacktestBody,
    db: Session = Depends(get_db),
    _: dict = Depends(require_roles("RULES_OWNER", "SYSTEM_ADMIN")),
):
    """Compare current evaluation status vs hypothetical status with this rule version active."""
    rv = db.query(RuleVersion).filter(
        RuleVersion.rule_id == rule_id,
        RuleVersion.version == body.version,
    ).first()
    if not rv:
        raise HTTPException(status_code=404, detail="Rule version not found")

    courses = db.query(CourseApproval).filter(
        CourseApproval.academic_year == body.academic_year
    ).all()

    from app.services.ledger import (
        _active_events, compute_caps, apply_reversion, lawful_max,
        BUCKET_FOR_CATEGORY, INTERNATIONAL_BUCKETS, RULE_REQUIRED_BUCKETS,
    )
    from app.services.rules_service import active_rules_for
    as_of = date.today()

    result = []
    for course in courses:
        inst = db.query(Institution).filter(Institution.id == course.institution_id).first()
        if not inst:
            continue

        active_rules = active_rules_for(db, course, inst, as_of)

        # Last stored evaluation status
        last_eval = (
            db.query(Evaluation)
            .filter(Evaluation.course_approval_id == course.id)
            .order_by(Evaluation.evaluated_at.desc())
            .first()
        )
        old_status = last_eval.result if last_eval else "NOT_EVALUATED"

        # Hypothetical: add the new rule version to active rules (replace same rule_id if present)
        hyp_rules = [r for r in active_rules if r.rule_id != rule_id]
        hyp_rules.append(rv)

        active_events = _active_events(db, course.id)
        occupied: dict[str, list] = {}
        for ev in active_events:
            bucket = BUCKET_FOR_CATEGORY.get(ev.seat_category, ev.seat_category)
            occupied.setdefault(bucket, []).append(ev)

        missing = [
            b for b in occupied
            if b in RULE_REQUIRED_BUCKETS and b not in {r.bucket for r in hyp_rules}
        ]
        if missing:
            new_status = "RULE_NOT_CONFIRMED"
        else:
            counts = {b: len(evs) for b, evs in occupied.items()}
            caps = compute_caps(course.approved_intake, hyp_rules)
            eff_caps = apply_reversion(caps, counts)
            lmax = lawful_max(eff_caps)
            total = sum(counts.values())
            flagged = False
            for bucket, cap in eff_caps.items():
                if counts.get(bucket, 0) > cap:
                    flagged = True
                    break
            if total > lmax:
                flagged = True
            new_status = "FLAG" if flagged else "OK"

        if old_status != new_status:
            result.append({
                "institution_id": course.institution_id,
                "institution_name": inst.name,
                "course_id": course.id,
                "course_name": course.name,
                "old_status": old_status,
                "new_status": new_status,
            })

    return {"changes": result, "total_courses": len(courses), "changed": len(result)}
