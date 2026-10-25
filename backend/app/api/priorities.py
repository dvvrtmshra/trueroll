"""Review priorities API (anomaly intelligence)."""
import json
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.security import require_roles
from app.models.institution import Institution
from app.models.course import CourseApproval
from app.models.review_priority import ReviewPriority

router = APIRouter()

OFFICER_ROLES = ("NATIONAL_OFFICER", "REGIONAL_OFFICER", "SYSTEM_ADMIN")


@router.get("")
def list_priorities(
    band: Optional[str] = None,
    institution_id: Optional[str] = None,
    academic_year: str = "2026-27",
    page: int = 1,
    page_size: int = 50,
    db: Session = Depends(get_db),
    user: dict = Depends(require_roles(*OFFICER_ROLES)),
):
    if not settings.ANOMALY_ENABLED:
        return {
            "items": [],
            "total": 0,
            "message": "Anomaly Intelligence not yet enabled. Run `make evaluate` then set ANOMALY_ENABLED=true.",
        }

    q = db.query(ReviewPriority).filter(ReviewPriority.period == academic_year)
    if band:
        q = q.filter(ReviewPriority.band == band)
    if institution_id:
        q = q.filter(ReviewPriority.institution_id == institution_id)
    # Regional officer scoping
    if user.get("role") == "REGIONAL_OFFICER" and user.get("region"):
        inst_ids = [
            i.id for i in db.query(Institution).filter(Institution.region == user["region"]).all()
        ]
        q = q.filter(ReviewPriority.institution_id.in_(inst_ids))

    total = q.count()
    items = q.order_by(ReviewPriority.score.desc()).offset((page - 1) * page_size).limit(page_size).all()

    result = []
    for rp in items:
        inst = db.query(Institution).filter(Institution.id == rp.institution_id).first()
        course = db.query(CourseApproval).filter(CourseApproval.id == rp.course_id).first() if rp.course_id else None
        result.append({
            "id": rp.id,
            "institution_id": rp.institution_id,
            "institution_name": inst.name if inst else rp.institution_id,
            "course_id": rp.course_id,
            "course_name": course.name if course else None,
            "period": rp.period,
            "score": rp.score,
            "band": rp.band,
            "reasons": json.loads(rp.reasons or "[]"),
            "peer_group": rp.peer_group,
            "model_version": rp.model_version,
            "status": rp.status,
            "officer_label": rp.officer_label,
            "created_at": rp.created_at.isoformat() if rp.created_at else None,
        })

    return {"items": result, "total": total}


@router.get("/{priority_id}")
def get_priority(
    priority_id: str,
    db: Session = Depends(get_db),
    _: dict = Depends(require_roles(*OFFICER_ROLES)),
):
    rp = db.query(ReviewPriority).filter(ReviewPriority.id == priority_id).first()
    if not rp:
        raise HTTPException(status_code=404, detail="Priority not found")

    inst = db.query(Institution).filter(Institution.id == rp.institution_id).first()
    course = db.query(CourseApproval).filter(CourseApproval.id == rp.course_id).first() if rp.course_id else None

    features = json.loads(rp.features_json or "{}")

    return {
        "id": rp.id,
        "institution_id": rp.institution_id,
        "institution_name": inst.name if inst else rp.institution_id,
        "course_id": rp.course_id,
        "course_name": course.name if course else None,
        "period": rp.period,
        "score": rp.score,
        "band": rp.band,
        "reasons": json.loads(rp.reasons or "[]"),
        "peer_group": rp.peer_group,
        "model_version": rp.model_version,
        "status": rp.status,
        "officer_label": rp.officer_label,
        "features": features,
        "advisory_notice": "Advisory only. Not a flag. Not a finding. Prototype model evaluated on synthetic data.",
        "created_at": rp.created_at.isoformat() if rp.created_at else None,
    }


class LabelBody(BaseModel):
    label: str  # useful | not_useful | need_more_info


@router.post("/{priority_id}/label")
def label_priority(
    priority_id: str,
    body: LabelBody,
    db: Session = Depends(get_db),
    _: dict = Depends(require_roles(*OFFICER_ROLES)),
):
    rp = db.query(ReviewPriority).filter(ReviewPriority.id == priority_id).first()
    if not rp:
        raise HTTPException(status_code=404, detail="Priority not found")

    valid_labels = {"useful", "not_useful", "need_more_info"}
    if body.label not in valid_labels:
        raise HTTPException(status_code=422, detail=f"label must be one of {valid_labels}")

    rp.officer_label = body.label
    db.commit()
    return {"id": rp.id, "officer_label": rp.officer_label}
