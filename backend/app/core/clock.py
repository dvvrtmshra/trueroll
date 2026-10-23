from datetime import datetime, timezone
from sqlalchemy.orm import Session


def app_now(db: Session | None = None) -> datetime:
    """
    Return the application's notion of "now".
    If a demo clock is set in the settings table, return that.
    Otherwise return the real UTC time.
    """
    if db is not None:
        try:
            from app.models.setting import Setting
            row = db.query(Setting).filter(Setting.key == "demo_clock").first()
            if row and row.value:
                return datetime.fromisoformat(row.value).replace(tzinfo=timezone.utc)
        except Exception:
            pass
    return datetime.now(timezone.utc)
