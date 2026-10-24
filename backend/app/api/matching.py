"""Matching evaluation endpoint — fuzzy matcher on M16 pairs."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_roles

router = APIRouter()


@router.get("/evaluation")
def matching_evaluation(
    db: Session = Depends(get_db),
    _: dict = Depends(require_roles("NATIONAL_OFFICER", "REGIONAL_OFFICER", "SYSTEM_ADMIN")),
):
    from app.services.matching_eval import run_evaluation
    return run_evaluation(db)
