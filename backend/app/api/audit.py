"""Audit trail API — A1 to A4. Read-only. Student details masked for AUDITOR role."""
import csv
import io
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.roles import Role, require_role

router = APIRouter()


def _mask_object_id(actor_role: str, object_type: str, object_id: Optional[str], viewer_role: str) -> Optional[str]:
    """AUDITOR cannot see student IDs by default — mask the last 4 chars."""
    if viewer_role == "AUDITOR" and object_type in ("student", "Student") and object_id:
        return "…" + object_id[-4:]
    return object_id


def _entry_to_dict(entry, viewer_role: str) -> dict:
    return {
        "id": entry.id,
        "actor": entry.actor,
        "actor_role": entry.actor_role,
        "action": entry.action,
        "object_type": entry.object_type,
        "object_id": _mask_object_id(entry.actor_role, entry.object_type, entry.object_id, viewer_role),
        "time": entry.time.isoformat() if entry.time else None,
        "hash_prefix": entry.entry_hash[:8] if entry.entry_hash else None,
        "prev_hash_prefix": entry.prev_hash[:8] if entry.prev_hash else None,
        "extra": entry.extra,
    }


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
    actor: Optional[str] = None,
    actor_role: Optional[str] = None,
    action: Optional[str] = None,
    object_type: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    limit: int = Query(50, ge=1, le=500),
    format: str = Query("json", pattern="^(json|csv)$"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    _: None = Depends(require_role(
        Role.AUDITOR, Role.NATIONAL_OFFICER, Role.REGIONAL_OFFICER,
        Role.RULES_OWNER, Role.SYSTEM_ADMIN,
    )),
):
    from app.models.audit_entry import AuditEntry

    q = db.query(AuditEntry)
    if actor:
        q = q.filter(AuditEntry.actor.ilike(f"%{actor}%"))
    if actor_role:
        q = q.filter(AuditEntry.actor_role == actor_role)
    if action:
        q = q.filter(AuditEntry.action.ilike(f"%{action}%"))
    if object_type:
        q = q.filter(AuditEntry.object_type == object_type)
    if date_from:
        try:
            dt = datetime.fromisoformat(date_from)
            q = q.filter(AuditEntry.time >= dt)
        except ValueError:
            pass
    if date_to:
        try:
            dt = datetime.fromisoformat(date_to)
            q = q.filter(AuditEntry.time <= dt)
        except ValueError:
            pass

    rows = q.order_by(AuditEntry.id.desc()).limit(limit).all()
    viewer_role = current_user.get("role", "")
    total = q.count()
    items = [_entry_to_dict(r, viewer_role) for r in rows]

    if format == "csv":
        buf = io.StringIO()
        w = csv.writer(buf)
        w.writerow(["ID", "Time", "Actor", "Role", "Action", "Object type", "Object ID", "Hash (8)"])
        for item in items:
            w.writerow([
                item["id"], item["time"], item["actor"], item["actor_role"],
                item["action"], item["object_type"], item["object_id"], item["hash_prefix"],
            ])
        buf.seek(0)
        return StreamingResponse(
            iter([buf.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": 'attachment; filename="audit-trail.csv"'},
        )

    return {"total": total, "items": items, "limit": limit}
