"""Simulated registry endpoints (M4)."""
from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.simulators.registry_sim import verify, start_consent_session

router = APIRouter()


class VerifyRequest(BaseModel):
    apaar_id: str
    name_token: str = ""
    dob_token: str = ""


class ConsentRequest(BaseModel):
    apaar_id: str


class ModeRequest(BaseModel):
    mode: str  # up | slow | flaky | down


@router.post("/mode")
def set_registry_mode(
    body: ModeRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    from app.models.setting import Setting
    allowed = {"up", "slow", "flaky", "down"}
    mode = body.mode.lower()
    if mode not in allowed:
        from fastapi import HTTPException
        raise HTTPException(status_code=422, detail=f"mode must be one of {allowed}")
    row = db.query(Setting).filter(Setting.key == "registry_mode").first()
    if row:
        row.value = mode
    else:
        db.add(Setting(key="registry_mode", value=mode))
    db.commit()
    return {"registry_mode": mode}


@router.get("/mode")
def get_registry_mode(db: Session = Depends(get_db)):
    from app.models.setting import Setting
    row = db.query(Setting).filter(Setting.key == "registry_mode").first()
    return {"registry_mode": row.value if row else "up"}


@router.post("/registry/verify")
def registry_verify(body: VerifyRequest, db: Session = Depends(get_db)):
    return verify(db, body.apaar_id, body.name_token, body.dob_token)


@router.post("/registry/consent-session")
def registry_consent_session(body: ConsentRequest, db: Session = Depends(get_db)):
    return start_consent_session(db, body.apaar_id)


@router.get("/registry/consent", response_class=HTMLResponse)
def mock_consent_page(session: str = "", apaar: str = ""):
    masked = apaar[:8] + "****" if len(apaar) >= 8 else apaar
    return HTMLResponse(f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><title>Consent — Simulated</title></head>
<body style="font-family:sans-serif;max-width:420px;margin:60px auto;padding:20px;border:2px solid #D9730D">
<div style="background:#FDF0DE;padding:8px;text-align:center;font-weight:bold;color:#B45309">
  SIMULATED CONSENT SCREEN — PROTOTYPE ONLY
</div>
<h2 style="color:#0B2545">TrueRoll requests to verify your APAAR ID</h2>
<p>This allows TrueRoll to confirm your enrolment status with your educational institution.</p>
<p>APAAR: <code>{masked}</code></p>
<div style="margin-top:24px">
  <button onclick="window.close()" style="background:#1B8A3E;color:#fff;padding:10px 24px;border:none;cursor:pointer">Allow</button>
  &nbsp;
  <button onclick="window.close()" style="background:#D62828;color:#fff;padding:10px 24px;border:none;cursor:pointer">Deny</button>
</div>
<p style="font-size:12px;color:#475569;margin-top:24px">SAMPLE DATA — No real data is transmitted. Simulated for prototype.</p>
</body></html>""")
