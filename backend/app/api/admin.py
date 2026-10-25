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
    return {"now": app_now(db).isoformat()}


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
