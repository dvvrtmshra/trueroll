from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.roles import Role, require_role

router = APIRouter()


@router.get("/chain/verify")
def chain_verify(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    _: None = Depends(require_role(Role.AUDITOR, Role.NATIONAL_OFFICER, Role.SYSTEM_ADMIN)),
):
    from app.core.audit import verify_chain
    return verify_chain(db)


@router.get("/entries")
def list_entries(
    object_type: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    _: None = Depends(require_role(
        Role.AUDITOR, Role.NATIONAL_OFFICER, Role.REGIONAL_OFFICER,
        Role.RULES_OWNER, Role.SYSTEM_ADMIN,
    )),
):
    from app.models.audit_entry import AuditEntry
    q = db.query(AuditEntry)
    if object_type:
        q = q.filter(AuditEntry.object_type == object_type)
    rows = q.order_by(AuditEntry.time.desc()).limit(limit).all()
    return [
        {
            "id": r.id,
            "actor": r.actor,
            "actor_role": r.actor_role,
            "action": r.action,
            "object_type": r.object_type,
            "object_id": r.object_id,
            "time": r.time.isoformat() if r.time else None,
            "extra": r.extra,
        }
        for r in rows
    ]
