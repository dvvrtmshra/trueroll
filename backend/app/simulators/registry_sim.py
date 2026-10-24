"""M4 — APAAR/DigiLocker registry simulator.

Mode: Up | Slow | Flaky | Down — read from Setting table key "registry_mode".
Special: APAAR IDs ending in "999" always return UNAVAILABLE (to demo registry-down path).
"""
import random
import time

from sqlalchemy.orm import Session

from app.models.setting import Setting
from app.models.student import Student


MODES = ("up", "slow", "flaky", "down")


def _get_mode(db: Session) -> str:
    s = db.query(Setting).filter(Setting.key == "registry_mode").first()
    return (s.value if s else "up").lower()


def verify(
    db: Session,
    apaar_id: str,
    name_token: str = "",
    dob_token: str = "",
) -> dict:
    """Return {"result": "VERIFIED"|"NOT_FOUND"|"MISMATCH"|"UNAVAILABLE", "simulated": True}."""
    # IDs ending in 999 always time out (demo registry-down path)
    if apaar_id.endswith("999"):
        return {"result": "UNAVAILABLE", "simulated": True}

    mode = _get_mode(db)

    if mode == "down":
        return {"result": "UNAVAILABLE", "simulated": True}

    if mode == "slow":
        time.sleep(0.05)

    if mode == "flaky":
        if random.random() < 0.1:
            return {"result": "UNAVAILABLE", "simulated": True}

    if not (len(apaar_id) == 12 and apaar_id.isdigit()):
        return {"result": "NOT_FOUND", "simulated": True}

    student = db.query(Student).filter(Student.apaar_id == apaar_id).first()
    if not student:
        return {"result": "NOT_FOUND", "simulated": True}

    return {"result": "VERIFIED", "simulated": True, "student_id": student.id}


def start_consent_session(db: Session, apaar_id: str) -> dict:
    from uuid import uuid4
    session_id = str(uuid4())
    return {
        "session_id": session_id,
        "mock_consent_url": f"/sim/registry/consent?session={session_id}&apaar={apaar_id}",
        "simulated": True,
    }
