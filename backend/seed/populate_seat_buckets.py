"""Compute initial SeatBucket rows from seeded admission events."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.models.course import CourseApproval
from app.models.seat_bucket import SeatBucket


def run(db) -> None:
    if db.query(SeatBucket).count() > 0:
        print("[pop_seat_buckets] Already populated — skip")
        return

    from app.services.ledger import reconcile_all
    results = reconcile_all(db)

    total_courses = len(results)
    total_buckets = sum(len(v) for v in results.values())
    print(f"[pop_seat_buckets] {total_buckets} SeatBucket rows across {total_courses} courses")
