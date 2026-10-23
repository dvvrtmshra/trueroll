import hashlib
import json
from datetime import datetime, timezone
from sqlalchemy.orm import Session


def _canonical_json(data: dict) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), default=str)


def _compute_hash(prev_hash: str, entry_data: dict) -> str:
    payload = prev_hash + _canonical_json(entry_data)
    return hashlib.sha256(payload.encode()).hexdigest()


def _time_for_hash(t: datetime) -> str:
    """Consistent UTC naive ISO string for hashing regardless of DB backend."""
    if t.tzinfo is not None:
        t = t.astimezone(timezone.utc).replace(tzinfo=None)
    return t.isoformat()


def append_audit_entry(
    db: Session,
    actor: str,
    role: str,
    action: str,
    object_type: str,
    object_id: str,
    time: datetime | None = None,
) -> "AuditEntry":  # noqa: F821
    from app.models.audit_entry import AuditEntry

    if time is None:
        time = datetime.now(timezone.utc)

    last = db.query(AuditEntry).order_by(AuditEntry.id.desc()).first()
    prev_hash = last.entry_hash if last else "GENESIS"

    entry_data = {
        "actor": actor,
        "actor_role": role,
        "action": action,
        "object_type": object_type,
        "object_id": object_id,
        "time": _time_for_hash(time),
    }
    new_hash = _compute_hash(prev_hash, entry_data)

    entry = AuditEntry(
        actor=actor,
        actor_role=role,
        action=action,
        object_type=object_type,
        object_id=object_id,
        time=time,
        prev_hash=prev_hash,
        entry_hash=new_hash,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def verify_chain(db: Session) -> dict:
    from app.models.audit_entry import AuditEntry

    entries = db.query(AuditEntry).order_by(AuditEntry.id.asc()).all()
    if not entries:
        return {"valid": True, "entries_checked": 0}

    prev_hash = "GENESIS"
    for i, entry in enumerate(entries):
        entry_data = {
            "actor": entry.actor,
            "actor_role": entry.actor_role,
            "action": entry.action,
            "object_type": entry.object_type,
            "object_id": entry.object_id,
            "time": _time_for_hash(entry.time) if entry.time else "",
        }
        expected = _compute_hash(prev_hash, entry_data)
        if expected != entry.entry_hash:
            return {
                "valid": False,
                "broken_at_id": entry.id,
                "expected": expected,
                "found": entry.entry_hash,
                "entries_checked": i + 1,
            }
        prev_hash = entry.entry_hash

    return {"valid": True, "entries_checked": len(entries)}
