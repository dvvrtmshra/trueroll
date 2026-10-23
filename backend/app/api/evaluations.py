"""Evaluation endpoints — trigger and retrieve Seat-Ledger evaluations."""
import json
from datetime import date, datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_roles
from app.models.evaluation import Evaluation
from app.services.ledger import evaluate, reconcile, simple_counter

router = APIRouter()


class EvaluationOut(BaseModel):
    id: str
    course_approval_id: str
    rule_set_hash: str
    rule_versions_used: str
    result: str
    result_detail: Optional[str]
    evaluated_at: datetime

    model_config = {"from_attributes": True}


class EvalTrigger(BaseModel):
    as_of: Optional[date] = None


@router.post("/courses/{course_id}", status_code=201)
def trigger_evaluation(
    course_id: str,
    body: EvalTrigger = EvalTrigger(),
    db: Session = Depends(get_db),
    _: dict = Depends(require_roles(
        "NATIONAL_OFFICER", "REGIONAL_OFFICER", "RULES_OWNER",
        "RULES_APPROVER", "SYSTEM_ADMIN",
    )),
):
    try:
        result = evaluate(db, course_id, as_of=body.as_of)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return {"status": result.status, "flags": len(result.flags), "review_reason": result.review_reason}


@router.get("/courses/{course_id}")
def get_evaluations(
    course_id: str,
    limit: int = 20,
    db: Session = Depends(get_db),
    _: dict = Depends(require_roles(
        "NATIONAL_OFFICER", "REGIONAL_OFFICER", "RULES_OWNER",
        "RULES_APPROVER", "SYSTEM_ADMIN",
    )),
):
    rows = (
        db.query(Evaluation)
        .filter(Evaluation.course_approval_id == course_id)
        .order_by(Evaluation.evaluated_at.desc())
        .limit(limit)
        .all()
    )
    return [EvaluationOut.model_validate(r) for r in rows]


@router.post("/courses/{course_id}/reconcile")
def trigger_reconcile(
    course_id: str,
    db: Session = Depends(get_db),
    _: dict = Depends(require_roles("NATIONAL_OFFICER", "SYSTEM_ADMIN")),
):
    try:
        drift = reconcile(db, course_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return {"drift": drift}
