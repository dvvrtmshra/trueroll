"""Create schema and seed all demo data. Run via: make seed"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.config import settings
from app.core.database import engine, SessionLocal
from app.core.audit import append_audit_entry
from app.models import Base
from app.models.setting import Setting


def create_schema() -> None:
    Base.metadata.create_all(bind=engine)
    print("[init_db] Schema created.")


def seed_settings(db) -> None:
    demo_clock = "2026-10-22T09:00:00+05:30"
    if not db.query(Setting).filter(Setting.key == "demo_clock").first():
        db.add(Setting(key="demo_clock", value=demo_clock))
        db.commit()
        print(f"[init_db] demo_clock → {demo_clock}")


def main() -> None:
    create_schema()
    db = SessionLocal()
    try:
        seed_settings(db)

        from seed import generate_users
        generate_users.run(db)

        from seed import generate_employers
        generate_employers.run(db)

        from seed import generate_institutions
        generate_institutions.run(db)

        from seed import generate_rules
        generate_rules.run(db)

        from seed import generate_students
        generate_students.run(db)

        from seed import generate_api_keys
        generate_api_keys.run(db)

        from seed import populate_seat_buckets
        populate_seat_buckets.run(db)

        from seed import generate_matching_pairs
        generate_matching_pairs.run(db)

        from seed import generate_anomaly_data
        generate_anomaly_data.run(db)

        from seed import generate_audit_history
        generate_audit_history.run(db)

        append_audit_entry(db, "system", "SYSTEM_ADMIN", "DB_INIT", "System", "init_db")
        print("[init_db] Done.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
