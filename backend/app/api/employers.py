"""Employer endpoints."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user, require_roles
from app.models.employer import Employer

router = APIRouter()


@router.get("")
def list_employers(
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    employers = db.query(Employer).filter(Employer.is_active == True).all()
    return [{"id": e.id, "name": e.name, "sector": e.sector} for e in employers]


@router.get("/{employer_id}")
def get_employer(
    employer_id: str,
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    e = db.query(Employer).filter(Employer.id == employer_id).first()
    if not e:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Employer not found")
    return {"id": e.id, "name": e.name, "sector": e.sector, "cin": e.cin, "api_tier": e.api_tier}
