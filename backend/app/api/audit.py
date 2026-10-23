from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.roles import Role, require_role
from app.core.audit import verify_chain

router = APIRouter()


@router.get("/chain/verify")
def chain_verify(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    _: None = Depends(require_role(Role.AUDITOR, Role.NATIONAL_OFFICER, Role.SYSTEM_ADMIN)),
):
    return verify_chain(db)


@router.get("/entries")
def list_entries():
    from fastapi.responses import JSONResponse
    return JSONResponse(status_code=501, content={"detail": "Not implemented — Phase 7"})
