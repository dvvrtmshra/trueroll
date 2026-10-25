"""Anomaly model evaluation and scoring endpoints."""
import json
from pathlib import Path

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_roles

router = APIRouter()

EVAL_PATH = Path(__file__).parent.parent.parent.parent / "models" / "anomaly_eval.json"

OFFICER_ROLES = ("NATIONAL_OFFICER", "REGIONAL_OFFICER", "SYSTEM_ADMIN")


@router.get("/evaluation")
def get_evaluation(
    _: dict = Depends(require_roles(*OFFICER_ROLES)),
):
    if not EVAL_PATH.exists():
        return {
            "status": "not_run",
            "message": "Run `make evaluate` (cd backend && python -m scripts.evaluate_anomaly) to generate evaluation results.",
            "honesty_notice": "Evaluated on synthetic labelled data. Real accuracy requires an AICTE pilot with officer-labelled outcomes.",
            "simulated": True,
        }
    data = json.loads(EVAL_PATH.read_text())
    return data


@router.post("/score")
def run_scoring(
    academic_year: str = "2026-27",
    db: Session = Depends(get_db),
    _: dict = Depends(require_roles("SYSTEM_ADMIN")),
):
    from app.services.anomaly_scorer import score_all
    results = score_all(db, academic_year)
    return {"scored": len(results), "academic_year": academic_year}
