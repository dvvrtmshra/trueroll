"""Activity feed — recent events formatted as human-readable items."""
import json
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_roles
from app.models.audit_entry import AuditEntry
from app.models.institution import Institution

router = APIRouter()

_OFFICER_ROLES = ("NATIONAL_OFFICER", "REGIONAL_OFFICER", "SYSTEM_ADMIN")

_ACTION_MESSAGES = {
    "UPLOAD_DONE": lambda extra, inst: f"{inst} uploaded {extra.get('rows_accepted', '?')} students",
    "FLAG_CREATED": lambda extra, inst: f"Flag raised for {inst}: {extra.get('bucket', '?')} bucket",
    "FLAG_UPDATED": lambda extra, inst: f"Flag updated for {inst}: {extra.get('status', '?')}",
    "RULE_ACTIVATED": lambda extra, inst: f"Rule {extra.get('rule_id', '?')} v{extra.get('version', '?')} activated",
    "LOGIN": lambda extra, inst: f"{extra.get('email', '?')} signed in",
    "EVALUATE": lambda extra, inst: f"Seat-Ledger evaluated for {inst}",
}


def _format_entry(entry: AuditEntry, db: Session, user_region: Optional[str]) -> Optional[dict]:
    extra = {}
    if entry.extra:
        try:
            extra = json.loads(entry.extra)
        except Exception:
            pass

    inst_id = extra.get("institution_id") or entry.object_id
    inst_name = inst_id or "system"
    if inst_id and inst_id.startswith("INST-"):
        inst = db.query(Institution).filter(Institution.id == inst_id).first()
        if inst:
            if user_region and inst.region != user_region:
                return None
            inst_name = inst.name

    msg_fn = _ACTION_MESSAGES.get(entry.action)
    if msg_fn:
        message = msg_fn(extra, inst_name)
    else:
        message = f"{entry.action.lower().replace('_', ' ')} — {inst_name}"

    return {
        "id": entry.id,
        "time": entry.time.isoformat(),
        "message": message,
        "action": entry.action,
        "institution_id": inst_id,
        "institution_name": inst_name,
        "actor": entry.actor,
    }


@router.get("")
def list_activity(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    user: dict = Depends(require_roles(*_OFFICER_ROLES)),
):
    user_region = user.get("region") if user.get("role") == "REGIONAL_OFFICER" else None
    entries = (
        db.query(AuditEntry)
        .order_by(AuditEntry.time.desc())
        .limit(limit * 3)
        .all()
    )
    items = []
    for e in entries:
        item = _format_entry(e, db, user_region)
        if item:
            items.append(item)
        if len(items) >= limit:
            break
    return items
