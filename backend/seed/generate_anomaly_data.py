"""M6 — Plant synthetic anomalies in seeded institutions and store ground-truth labels."""
import random
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).parent.parent))

from seed.common import SEED, hmac_token
from app.models.admission_event import AdmissionEvent
from app.models.anomaly_label import AnomalyLabel
from app.models.course import CourseApproval
from app.models.student import Student

ANOMALY_YEAR = "2026-27"

# Which institution gets which planted anomaly
PLANTED = {
    "INST-0005": "LATE_SURGE",
    "INST-0006": "CATEGORY_MIX",
    "INST-0007": "SHARED_ATTRIBUTE_CLUSTER",
    "INST-0008": "FULL_STREAK",
    "INST-0012": "POST_AUDIT_WITHDRAWALS",
}

CYCLE_END = date(2026, 11, 30)
AUDIT_DATE = date(2026, 9, 30)


def run(db) -> None:
    if db.query(AnomalyLabel).count() > 0:
        print("[gen_anomaly] Already seeded — skip")
        return

    rng = random.Random(SEED + 8)

    for inst_id, anomaly_type in PLANTED.items():
        course = (
            db.query(CourseApproval)
            .filter(
                CourseApproval.institution_id == inst_id,
                CourseApproval.academic_year == ANOMALY_YEAR,
            )
            .first()
        )
        if not course:
            print(f"[gen_anomaly] No course for {inst_id} — skip label")
            db.add(AnomalyLabel(
                institution_id=inst_id,
                course_id=None,
                academic_year=ANOMALY_YEAR,
                anomaly_type=anomaly_type,
                planted=True,
            ))
            continue

        if anomaly_type == "LATE_SURGE":
            # Add extra admissions in last 14 days of cycle
            cutoff = CYCLE_END - timedelta(days=14)
            for i in range(20):
                stu_id = f"ANOM-{inst_id}-LS-{i:03d}"
                if not db.query(Student).filter(Student.id == stu_id).first():
                    db.add(Student(
                        id=stu_id,
                        full_name=f"Late Student {i}",
                        date_of_birth=date(2002, rng.randint(1, 12), rng.randint(1, 28)),
                        identity_tier="T3",
                    ))
                db.flush()
                admit_date = cutoff + timedelta(days=rng.randint(0, 13))
                if not db.query(AdmissionEvent).filter(
                    AdmissionEvent.student_id == stu_id,
                    AdmissionEvent.course_approval_id == course.id,
                ).first():
                    db.add(AdmissionEvent(
                        id=str(uuid4()),
                        student_id=stu_id,
                        course_approval_id=course.id,
                        seat_category="REGULAR",
                        event_type="ADMIT",
                        admission_round="ROUND_3",
                        entry_type="REGULAR",
                        nationality_status="INDIAN",
                        event_time=datetime(
                            admit_date.year, admit_date.month, admit_date.day,
                            10, 0, 0, tzinfo=timezone.utc,
                        ),
                    ))

        elif anomaly_type == "CATEGORY_MIX":
            # Add OCI/FN students far above normal
            for i in range(15):
                stu_id = f"ANOM-{inst_id}-CM-{i:03d}"
                if not db.query(Student).filter(Student.id == stu_id).first():
                    db.add(Student(
                        id=stu_id,
                        full_name=f"Foreign Student {i}",
                        date_of_birth=date(2001, rng.randint(1, 12), rng.randint(1, 28)),
                        identity_tier="T4",
                    ))
                db.flush()
                if not db.query(AdmissionEvent).filter(
                    AdmissionEvent.student_id == stu_id,
                    AdmissionEvent.course_approval_id == course.id,
                ).first():
                    db.add(AdmissionEvent(
                        id=str(uuid4()),
                        student_id=stu_id,
                        course_approval_id=course.id,
                        seat_category="OCI_FN_EXTRA",
                        event_type="ADMIT",
                        admission_round="ROUND_1",
                        entry_type="REGULAR",
                        nationality_status="FOREIGN",
                        event_time=datetime(2026, 7, 15, 10, 0, 0, tzinfo=timezone.utc),
                    ))

        elif anomaly_type == "SHARED_ATTRIBUTE_CLUSTER":
            # 8 students share the same guardian token
            shared_token = hmac_token("shared-guardian-anom-0007")
            for i in range(8):
                stu_id = f"ANOM-{inst_id}-SA-{i:03d}"
                if not db.query(Student).filter(Student.id == stu_id).first():
                    db.add(Student(
                        id=stu_id,
                        full_name=f"Cluster Student {i}",
                        date_of_birth=date(2003, 5, rng.randint(1, 28)),
                        identity_tier="T3",
                        contact_token=shared_token,
                    ))
                db.flush()
                if not db.query(AdmissionEvent).filter(
                    AdmissionEvent.student_id == stu_id,
                    AdmissionEvent.course_approval_id == course.id,
                ).first():
                    db.add(AdmissionEvent(
                        id=str(uuid4()),
                        student_id=stu_id,
                        course_approval_id=course.id,
                        seat_category="REGULAR",
                        event_type="ADMIT",
                        admission_round="ROUND_1",
                        entry_type="REGULAR",
                        nationality_status="INDIAN",
                        event_time=datetime(2026, 7, 20, 10, 0, 0, tzinfo=timezone.utc),
                    ))

        elif anomaly_type == "POST_AUDIT_WITHDRAWALS":
            # 5 withdrawals after audit date
            events = (
                db.query(AdmissionEvent)
                .filter(
                    AdmissionEvent.course_approval_id == course.id,
                    AdmissionEvent.event_type == "ADMIT",
                )
                .limit(5)
                .all()
            )
            for ev in events:
                withdraw_date = AUDIT_DATE + timedelta(days=rng.randint(1, 20))
                if not db.query(AdmissionEvent).filter(
                    AdmissionEvent.student_id == ev.student_id,
                    AdmissionEvent.course_approval_id == course.id,
                    AdmissionEvent.event_type == "WITHDRAW",
                ).first():
                    db.add(AdmissionEvent(
                        id=str(uuid4()),
                        student_id=ev.student_id,
                        course_approval_id=course.id,
                        seat_category=ev.seat_category,
                        event_type="WITHDRAW",
                        admission_round=ev.admission_round,
                        entry_type=ev.entry_type,
                        nationality_status=ev.nationality_status,
                        event_time=datetime(
                            withdraw_date.year, withdraw_date.month, withdraw_date.day,
                            10, 0, 0, tzinfo=timezone.utc,
                        ),
                    ))

        db.add(AnomalyLabel(
            institution_id=inst_id,
            course_id=course.id,
            academic_year=ANOMALY_YEAR,
            anomaly_type=anomaly_type,
            planted=True,
        ))

    db.commit()
    print(f"[gen_anomaly] Planted {len(PLANTED)} anomaly labels")
