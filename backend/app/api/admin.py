from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.roles import Role, require_role
from app.models.setting import Setting

router = APIRouter()


class ClockBody(BaseModel):
    iso_datetime: str


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
    return {"now": app_now(db).isoformat()}
