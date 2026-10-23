"""M14 — Seed ~2,000 pre-history audit entries with a valid hash chain."""
import hashlib
import json
import random
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from seed.common import SEED
from app.models.audit_entry import AuditEntry

ACTIONS = [
    ("LOGIN", "User", "NATIONAL_OFFICER"),
    ("LOGIN", "User", "COLLEGE_ADMIN"),
    ("UPLOAD_SUBMITTED", "Upload", "COLLEGE_ADMIN"),
    ("UPLOAD_COMPLETED", "Upload", "SYSTEM"),
    ("FLAG_RAISED", "Flag", "SYSTEM"),
    ("FLAG_REVIEWED", "Flag", "NATIONAL_OFFICER"),
    ("RULE_PROPOSED", "RuleVersion", "RULES_OWNER"),
    ("RULE_APPROVED", "RuleVersion", "RULES_APPROVER"),
    ("RULE_ACTIVATED", "RuleVersion", "SYSTEM"),
    ("EVALUATION_RUN", "Evaluation", "SYSTEM"),
    ("CONSENT_CREATED", "Consent", "STUDENT"),
    ("CONSENT_WITHDRAWN", "Consent", "STUDENT"),
    ("CREDENTIAL_ISSUED", "Credential", "SYSTEM"),
    ("VERIFICATION_PERFORMED", "VerificationLog", "EMPLOYER"),
    ("DB_INIT", "System", "SYSTEM_ADMIN"),
    ("STUDENT_REGISTERED", "Student", "COLLEGE_ADMIN"),
    ("ADMISSION_RECORDED", "AdmissionEvent", "COLLEGE_ADMIN"),
    ("WITHDRAWAL_RECORDED", "AdmissionEvent", "COLLEGE_ADMIN"),
    ("AUDIT_CHAIN_VERIFIED", "AuditEntry", "AUDITOR"),
]

ACTORS = {
    "NATIONAL_OFFICER": "officer.national@trueroll.demo",
    "COLLEGE_ADMIN": "admin.inst0001@trueroll.demo",
    "SYSTEM": "system",
    "RULES_OWNER": "rules.owner@trueroll.demo",
    "RULES_APPROVER": "rules.approver@trueroll.demo",
    "STUDENT": "student.verified@trueroll.demo",
    "EMPLOYER": "employer.demotech@trueroll.demo",
    "SYSTEM_ADMIN": "sysadmin@trueroll.demo",
    "AUDITOR": "auditor@trueroll.demo",
}


def _canonical_json(data: dict) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), default=str)


def _compute_hash(prev_hash: str, entry_data: dict) -> str:
    payload = prev_hash + _canonical_json(entry_data)
    return hashlib.sha256(payload.encode()).hexdigest()


def _naive_isoformat(t: datetime) -> str:
    if t.tzinfo is not None:
        t = t.astimezone(timezone.utc).replace(tzinfo=None)
    return t.isoformat()


def run(db) -> None:
    existing = db.query(AuditEntry).count()
    if existing >= 100:
        print(f"[gen_audit] Already has {existing} entries — skip")
        return

    rng = random.Random(SEED + 2)
    # Start from ~6 months ago
    start = datetime(2026, 4, 1, 8, 0, 0)
    prev_hash = "GENESIS"

    # Find the actual last entry (from init_db SYSTEM entries)
    last = db.query(AuditEntry).order_by(AuditEntry.id.desc()).first()
    if last:
        prev_hash = last.entry_hash

    added = 0
    current_time = start

    for _ in range(2000):
        action, obj_type, role = rng.choice(ACTIONS)
        actor = ACTORS[role]
        obj_id = f"obj-{rng.randint(1, 9999):04d}"
        current_time = current_time + timedelta(seconds=rng.randint(30, 3600))

        entry_data = {
            "actor": actor,
            "actor_role": role,
            "action": action,
            "object_type": obj_type,
            "object_id": obj_id,
            "time": _naive_isoformat(current_time),
        }
        new_hash = _compute_hash(prev_hash, entry_data)

        db.add(AuditEntry(
            actor=actor,
            actor_role=role,
            action=action,
            object_type=obj_type,
            object_id=obj_id,
            time=current_time,
            prev_hash=prev_hash,
            entry_hash=new_hash,
        ))
        prev_hash = new_hash
        added += 1

        if added % 200 == 0:
            db.flush()

    db.commit()
    print(f"[gen_audit] {added} audit history entries")
