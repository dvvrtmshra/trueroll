from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user, require_roles
from app.core.roles import Role, require_role
from app.models.setting import Setting

router = APIRouter()


class ClockBody(BaseModel):
    iso_datetime: str


class AdvanceClockBody(BaseModel):
    to_date: str  # YYYY-MM-DD


@router.post("/clock")
def set_demo_clock(
    body: ClockBody,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    _: None = Depends(require_role(Role.SYSTEM_ADMIN)),
):
    row = db.query(Setting).filter(Setting.key == "demo_clock").first()
    if row:
        row.value = body.iso_datetime
    else:
        row = Setting(key="demo_clock", value=body.iso_datetime)
        db.add(row)
    db.commit()
    return {"demo_clock": body.iso_datetime}


@router.get("/clock")
def get_demo_clock(db: Session = Depends(get_db)):
    from app.core.clock import app_now
    dt = app_now(db)
    return {"now": dt.isoformat(), "demo_date": dt.date().isoformat()}


@router.post("/clock/advance")
def advance_demo_clock(
    body: AdvanceClockBody,
    db: Session = Depends(get_db),
    user: dict = Depends(require_roles("SYSTEM_ADMIN", "RULES_OWNER")),
):
    """Advance the demo clock to a specific date; auto-activate any approved rules whose effective_from <= new_date."""
    try:
        new_date = date.fromisoformat(body.to_date)
    except ValueError:
        from fastapi import HTTPException
        raise HTTPException(status_code=422, detail="to_date must be YYYY-MM-DD")

    new_dt = datetime(new_date.year, new_date.month, new_date.day, 9, 0, 0, tzinfo=timezone.utc)

    row = db.query(Setting).filter(Setting.key == "demo_clock").first()
    if row:
        row.value = new_dt.isoformat()
    else:
        row = Setting(key="demo_clock", value=new_dt.isoformat())
        db.add(row)
    db.commit()

    # Auto-activate approved rules whose effective_from <= new_date
    from app.models.rule import RuleVersion
    from app.services.rules_service import activate_rule_version

    candidates = db.query(RuleVersion).filter(
        RuleVersion.status == "approved",
        RuleVersion.effective_from <= new_date,
    ).all()

    activated = []
    for rv in candidates:
        try:
            activate_rule_version(db, rv, new_date)
            activated.append({"rule_id": rv.rule_id, "version": rv.version, "bucket": rv.bucket})
        except Exception:
            pass

    # Re-run Seat-Ledger for affected years
    if activated:
        from app.models.course import CourseApproval
        from app.services.ledger import evaluate, reconcile
        years = {rv["rule_id"] for rv in activated}
        # Get unique academic years from activated rules
        act_rvs = db.query(RuleVersion).filter(
            RuleVersion.rule_id.in_(years),
            RuleVersion.status == "active",
        ).all()
        academic_years = {rv.academic_year for rv in act_rvs}
        for ay in academic_years:
            courses = db.query(CourseApproval).filter(
                CourseApproval.academic_year == ay
            ).all()
            for c in courses:
                try:
                    reconcile(db, c.id)
                    evaluate(db, c.id, new_date)
                except Exception:
                    pass

    return {"new_date": new_dt.isoformat(), "rules_activated": activated}


# ── Health ────────────────────────────────────────────────────────────────────

@router.get("/health")
def health_check(db: Session = Depends(get_db)):
    """Green/red for each service component."""
    from app.simulators.registry_sim import _get_mode as registry_mode
    import os

    services = {}

    # API itself
    services["api"] = {"status": "ok"}

    # Database
    try:
        db.execute(__import__("sqlalchemy").text("SELECT 1"))
        services["database"] = {"status": "ok"}
    except Exception as e:
        services["database"] = {"status": "error", "detail": str(e)}

    # Registry simulator
    try:
        mode = registry_mode(db)
        services["registry_simulator"] = {"status": "ok" if mode != "down" else "degraded", "mode": mode}
    except Exception:
        services["registry_simulator"] = {"status": "unknown"}

    # Audit chain
    try:
        from app.core.audit import verify_chain
        chain = verify_chain(db)
        services["audit_chain"] = {"status": "ok" if chain.get("valid") else "broken", "entries": chain.get("entries_checked", 0)}
    except Exception:
        services["audit_chain"] = {"status": "unknown"}

    overall = "ok" if all(s.get("status") == "ok" for s in services.values()) else "degraded"
    return {"overall": overall, "services": services}


# ── Jobs ──────────────────────────────────────────────────────────────────────

@router.get("/jobs")
def list_jobs(
    db: Session = Depends(get_db),
    user: dict = Depends(require_roles("SYSTEM_ADMIN", "NATIONAL_OFFICER")),
):
    from app.models.upload import Upload
    uploads = db.query(Upload).order_by(Upload.created_at.desc()).limit(50).all()
    return {
        "items": [
            {
                "id": u.id,
                "institution_id": u.institution_id,
                "academic_year": u.academic_year,
                "status": u.status,
                "rows_total": u.row_count,
                "rows_accepted": u.rows_accepted,
                "rows_error": u.rows_errors,
                "created_at": u.uploaded_at.isoformat() if u.uploaded_at else None,
                "finished_at": u.completed_at.isoformat() if u.completed_at else None,
            }
            for u in uploads
        ]
    }


# ── Tamper demo ───────────────────────────────────────────────────────────────

class TamperBody(BaseModel):
    entry_id: int


@router.post("/tamper")
def tamper_audit_entry(
    body: TamperBody,
    db: Session = Depends(get_db),
    user: dict = Depends(require_roles("SYSTEM_ADMIN")),
):
    """Prototype demo only. Corrupts one audit entry hash so chain verify fails."""
    from fastapi import HTTPException
    from sqlalchemy import text
    from app.models.audit_entry import AuditEntry

    entry = db.query(AuditEntry).filter(AuditEntry.id == body.entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Audit entry not found")

    # Save original hash so we can restore
    orig_hash = entry.entry_hash
    row = db.query(Setting).filter(Setting.key == "tamper_original_hash").first()
    if row:
        row.value = orig_hash
    else:
        db.add(Setting(key="tamper_original_hash", value=orig_hash))

    id_row = db.query(Setting).filter(Setting.key == "tamper_entry_id").first()
    if id_row:
        id_row.value = str(body.entry_id)
    else:
        db.add(Setting(key="tamper_entry_id", value=str(body.entry_id)))

    db.commit()

    # Corrupt the hash (bypass ORM to simulate a rogue DB write)
    bogus_hash = "00000000" + orig_hash[8:]
    db.execute(text("UPDATE audit_entry SET entry_hash = :h WHERE id = :i"),
               {"h": bogus_hash, "i": body.entry_id})
    db.commit()

    return {
        "tampered": True,
        "entry_id": body.entry_id,
        "note": "Prototype demonstration only. Run Verify chain in the Auditor screen to see the broken chain.",
    }


@router.post("/restore")
def restore_audit_entry(
    db: Session = Depends(get_db),
    user: dict = Depends(require_roles("SYSTEM_ADMIN")),
):
    """Restore the tampered audit entry. Prototype demo only."""
    from fastapi import HTTPException
    from sqlalchemy import text

    orig_row = db.query(Setting).filter(Setting.key == "tamper_original_hash").first()
    id_row = db.query(Setting).filter(Setting.key == "tamper_entry_id").first()

    if not orig_row or not id_row:
        raise HTTPException(status_code=400, detail="No tampered entry on record")

    db.execute(text("UPDATE audit_entry SET entry_hash = :h WHERE id = :i"),
               {"h": orig_row.value, "i": int(id_row.value)})
    db.commit()

    entry_id = int(id_row.value)
    db.delete(orig_row)
    db.delete(id_row)
    db.commit()

    return {"restored": True, "entry_id": entry_id}


# ── Scenarios ─────────────────────────────────────────────────────────────────

@router.post("/scenarios/{scenario_id}")
def load_scenario(
    scenario_id: str,
    db: Session = Depends(get_db),
    user: dict = Depends(require_roles("SYSTEM_ADMIN")),
):
    """Load a named scenario (re-evaluates the relevant institutions). Prototype demo."""
    from fastapi import HTTPException

    SCENARIO_INST = {
        "S1": "INST-0001",
        "S2": "INST-0002",
        "S3": "INST-0003",
        "S4": "INST-0004",
        "S5": "INST-0005",
    }
    inst_id = SCENARIO_INST.get(scenario_id.upper())
    if not inst_id:
        raise HTTPException(status_code=404, detail=f"Scenario {scenario_id!r} not found")

    from app.models.course import CourseApproval
    from app.services.ledger import evaluate
    from app.core.clock import app_now

    as_of = app_now(db).date()
    courses = db.query(CourseApproval).filter(CourseApproval.institution_id == inst_id).all()
    evaluated = []
    for c in courses:
        try:
            result = evaluate(db, c.id, as_of=as_of)
            evaluated.append({"course": c.id, "result": result.status})
        except Exception as e:
            evaluated.append({"course": c.id, "error": str(e)})

    return {"scenario": scenario_id, "institution": inst_id, "evaluated": evaluated}


@router.post("/reset-demo")
def reset_demo(
    db: Session = Depends(get_db),
    user: dict = Depends(require_roles("SYSTEM_ADMIN")),
):
    """Re-run the seed generators to restore demo state. Prototype only."""
    try:
        from seed.generate_uploads import run as run_uploads
        from seed.generate_matching_pairs import run as run_pairs
        from seed.generate_anomaly_data import run as run_anomaly
        run_uploads(db)
        run_pairs(db)
        run_anomaly(db)
        return {"reset": True, "message": "Demo data re-seeded. Restart the server for full effect."}
    except Exception as e:
        return {"reset": False, "error": str(e)}


# ── Integration register ──────────────────────────────────────────────────────

@router.get("/integration-register")
def integration_register():
    return {
        "note": "Live APAAR and DigiLocker access needs registered approval (API Setu requester onboarding). This prototype uses a simulator behind the same adapter.",
        "integrations": [
            {"name": "APAAR Registry", "purpose": "Identity verification", "status": "SIMULATED",
             "adapter": "app.adapters.registry.SimulatedRegistry"},
            {"name": "DigiLocker", "purpose": "Document fetch", "status": "FUTURE"},
            {"name": "AICTE Approvals Feed", "purpose": "Course intake data", "status": "SIMULATED",
             "adapter": "app.adapters.aicte.SimulatedAicte"},
            {"name": "SMTP / email gateway", "purpose": "Notifications", "status": "SIMULATED",
             "mock_mail_route": "/mock-mail"},
            {"name": "Ed25519 key store", "purpose": "Signing credentials", "status": "SIMULATED",
             "note": "Keys stored in vault/ — production would use a KMS"},
        ],
    }


# ── Keys ──────────────────────────────────────────────────────────────────────

@router.get("/keys")
def list_keys(user: dict = Depends(require_roles("SYSTEM_ADMIN"))):
    return {"active_key_id": "key-2026-10-a", "note": "Old keys kept for verification of issued credentials"}


@router.post("/keys/rotate")
def rotate_key(user: dict = Depends(require_roles("SYSTEM_ADMIN"))):
    """Rotate the Ed25519 signing key. Old key is kept to verify old credentials."""
    import os, json, datetime
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    from cryptography.hazmat.primitives.serialization import (
        Encoding, PrivateFormat, PublicFormat, NoEncryption,
    )

    vault_dir = os.path.join(os.path.dirname(__file__), "..", "..", "vault")
    os.makedirs(vault_dir, exist_ok=True)

    new_key = Ed25519PrivateKey.generate()
    kid = datetime.datetime.now(datetime.timezone.utc).strftime("key-%Y%m%d%H%M%S")

    priv_bytes = new_key.private_bytes(Encoding.PEM, PrivateFormat.PKCS8, NoEncryption())
    pub_bytes = new_key.public_key().public_bytes(Encoding.PEM, PublicFormat.SubjectPublicKeyInfo)

    with open(os.path.join(vault_dir, f"{kid}.pem"), "wb") as f:
        f.write(priv_bytes)
    with open(os.path.join(vault_dir, f"{kid}.pub"), "wb") as f:
        f.write(pub_bytes)

    # Update the active key pointer
    meta_path = os.path.join(vault_dir, "keys.json")
    meta = {}
    if os.path.exists(meta_path):
        with open(meta_path) as f:
            meta = json.load(f)
    meta["active"] = kid
    meta.setdefault("all", []).append(kid)
    with open(meta_path, "w") as f:
        json.dump(meta, f)

    return {"rotated": True, "new_key_id": kid}


# ── Reconcile all (admin action) ──────────────────────────────────────────────

@router.post("/reconcile")
def reconcile_all(
    db: Session = Depends(get_db),
    user: dict = Depends(require_roles("SYSTEM_ADMIN", "NATIONAL_OFFICER")),
):
    from app.services.ledger import reconcile_all as ra
    results = ra(db)
    total_drift = sum(abs(v) for bucket_map in results.values() for v in bucket_map.values())
    return {"courses_reconciled": len(results), "total_drift": total_drift, "results": results}


