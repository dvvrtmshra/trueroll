"""Master evaluation script — writes models/evaluation_summary.json.

Usage:
    cd backend && python -m scripts.evaluate

Measures:
  1. Planted breaches caught on upload
  2. False alarms: simple counter vs Seat-Ledger
  3. Upload throughput (G_large_5000.csv if present)
  4. Matching precision and recall (from matching_pairs seed)
  5. Anomaly precision and recall (from anomaly_eval.json if present)
  6. Reconciliation drift
"""
import json
import os
import sys
import time
from datetime import date, datetime, timezone

# Allow running as `python -m scripts.evaluate` from the backend directory
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def run():
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app.core.config import settings
    from app.models import Base

    engine = create_engine(settings.DATABASE_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "note": "Measured on synthetic data in our prototype.",
    }

    # ── 1. Planted breaches caught ────────────────────────────────────────────
    from app.models.evaluation import Evaluation
    from app.models.flag import Flag
    from sqlalchemy import func

    total_evals = db.query(func.count(Evaluation.id)).scalar() or 0
    total_flags = db.query(func.count(Flag.id)).filter(
        Flag.status.in_(["open", "auto_cleared", "under_review", "resolved"])
    ).scalar() or 0
    open_flags = db.query(func.count(Flag.id)).filter(
        Flag.status.in_(["open", "under_review"])
    ).scalar() or 0

    # Count FLAG evaluations vs OK evaluations
    flag_evals = db.query(func.count(Evaluation.id)).filter(Evaluation.result == "FLAG").scalar() or 0
    ok_evals = db.query(func.count(Evaluation.id)).filter(Evaluation.result == "OK").scalar() or 0

    summary["breaches"] = {
        "total_evaluations": total_evals,
        "flag_evaluations": flag_evals,
        "ok_evaluations": ok_evals,
        "open_flags": open_flags,
        "note": "Based on seeded scenario data (S1-S5). Known planted breaches for S2, S3.",
    }

    # ── 2. False alarms: simple counter vs Seat-Ledger ────────────────────────
    from app.models.course import CourseApproval
    from app.models.institution import Institution
    from app.models.seat_bucket import SeatBucket
    from app.services.ledger import simple_counter

    simple_alarms = 0
    ledger_flags = 0
    extra_seat_courses = 0

    for course in db.query(CourseApproval).filter(CourseApproval.academic_year == "2026-27").all():
        buckets = db.query(SeatBucket).filter(SeatBucket.course_approval_id == course.id).all()
        admitted = sum(b.used for b in buckets)
        lawful_max = sum(b.cap for b in buckets) if buckets else course.approved_intake

        if lawful_max > course.approved_intake:
            extra_seat_courses += 1
            sc = simple_counter(course, admitted)
            if sc == "ALARM":
                simple_alarms += 1
            last_eval = (
                db.query(Evaluation)
                .filter(Evaluation.course_approval_id == course.id)
                .order_by(Evaluation.evaluated_at.desc())
                .first()
            )
            if last_eval and last_eval.result == "FLAG":
                ledger_flags += 1

    summary["false_alarms"] = {
        "extra_seat_courses": extra_seat_courses,
        "simple_counter_alarms": simple_alarms,
        "seat_ledger_flags": ledger_flags,
        "false_alarm_rate": round((simple_alarms - ledger_flags) / max(extra_seat_courses, 1), 3),
        "note": "Simple counter does not know about extra seats; Seat-Ledger does.",
    }

    # ── 3. Upload throughput ──────────────────────────────────────────────────
    from app.models.upload import Upload

    uploads = db.query(Upload).filter(
        Upload.status.in_(["done", "completed"]),
        Upload.completed_at.isnot(None),
        Upload.uploaded_at.isnot(None),
    ).all()

    processing_times = []
    for u in uploads:
        if u.row_count and u.row_count >= 1000:
            t = (u.completed_at - u.uploaded_at).total_seconds()
            if t > 0:
                processing_times.append(t)

    if processing_times:
        processing_times.sort()
        median = processing_times[len(processing_times) // 2]
        p95 = processing_times[int(len(processing_times) * 0.95)]
    else:
        median = p95 = None

    summary["throughput"] = {
        "large_uploads_measured": len(processing_times),
        "median_seconds": round(median, 2) if median else None,
        "p95_seconds": round(p95, 2) if p95 else None,
        "note": "Large upload = 1000+ rows. Run G_large_5000.csv scenario for real measurement.",
    }

    # ── 4. Matching evaluation ────────────────────────────────────────────────
    from app.models.matching_pair import MatchingPair
    from app.services.fuzzy_matcher import score as fuzzy_score, duplicate_class as dup_class

    pairs = db.query(MatchingPair).all()
    tp = fp = fn = tn = 0
    for pair in pairs:
        from datetime import date as date_type
        score = fuzzy_score(pair.name_a, pair.dob_a, pair.name_b, pair.dob_b)
        detected = score >= 0.85  # D4 or D5 threshold
        actual = pair.is_true_duplicate
        if actual and detected:
            tp += 1
        elif not actual and detected:
            fp += 1
        elif actual and not detected:
            fn += 1
        else:
            tn += 1

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

    summary["matching"] = {
        "pairs_evaluated": len(pairs),
        "true_positives": tp,
        "false_positives": fp,
        "false_negatives": fn,
        "true_negatives": tn,
        "precision": round(precision, 3),
        "recall": round(recall, 3),
        "f1": round(f1, 3),
        "threshold": 0.85,
        "note": "D4 threshold 0.93, D5 watch 0.85. Nothing auto-flagged.",
    }

    # ── 5. Anomaly evaluation ─────────────────────────────────────────────────
    anomaly_eval_path = os.path.join(os.path.dirname(__file__), "..", "models", "anomaly_eval.json")
    if os.path.exists(anomaly_eval_path):
        with open(anomaly_eval_path) as f:
            summary["anomaly"] = json.load(f)
    else:
        summary["anomaly"] = {
            "status": "not_run",
            "note": "Run `python -m scripts.evaluate_anomaly` first.",
        }

    # ── 6. Reconciliation drift ───────────────────────────────────────────────
    from app.services.ledger import reconcile_all

    drift_results = reconcile_all(db)
    total_drift = sum(abs(v) for bd in drift_results.values() for v in bd.values())
    summary["reconciliation"] = {
        "courses_checked": len(drift_results),
        "total_drift": total_drift,
        "clean": total_drift == 0,
        "note": "Zero drift means event history matches stored counters exactly.",
    }

    db.close()

    # Write the summary
    models_dir = os.path.join(os.path.dirname(__file__), "..", "models")
    os.makedirs(models_dir, exist_ok=True)
    out_path = os.path.join(models_dir, "evaluation_summary.json")
    with open(out_path, "w") as f:
        json.dump(summary, f, indent=2)

    print(f"OK: Evaluation summary written to {out_path}")
    print(f"  Breaches: {flag_evals} FLAG evals")
    print(f"  Matching: precision={precision:.3f}, recall={recall:.3f}, F1={f1:.3f}")
    print(f"  Reconciliation drift: {total_drift}")
    return summary


if __name__ == "__main__":
    run()
