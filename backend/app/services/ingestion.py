"""Upload pipeline — parse, validate, tier, deduplicate, write events, evaluate."""
import csv
import hashlib
import io
import json
from datetime import date, datetime, timezone
from typing import Optional
from uuid import uuid4

from sqlalchemy.orm import Session

from app.core.security import hmac_token
from app.models.admission_event import AdmissionEvent
from app.models.course import CourseApproval
from app.models.duplicate_case import DuplicateCase
from app.models.student import Student
from app.models.upload import Upload
from app.models.upload_error import UploadError
from app.services.fuzzy_matcher import score as fuzzy_score, duplicate_class as dup_class
from app.services.ledger import evaluate, reconcile


REQUIRED_COLS = {
    "student_ref", "full_name", "date_of_birth",
    "nationality_status", "seat_category", "course_code", "admission_date",
    "mode",
}

VALID_SEAT_CATS = {
    "REGULAR", "NRI_IN", "OCI_FN_EXTRA", "CIWGC_EXTRA", "EWS",
    "INTL_PG_EXTRA", "INTL_MGT_EXTRA", "LATERAL",
}

VALID_NATIONALITIES = {
    "INDIAN", "NRI", "OCI", "PIO", "FN", "CIWGC",
}

FOREIGN_NATIONALITIES = {"NRI", "OCI", "PIO", "FN", "CIWGC"}


def _make_student_id(institution_id: str, academic_year: str, student_ref: str) -> str:
    key = f"{institution_id}:{academic_year}:{student_ref}"
    h = hashlib.md5(key.encode()).hexdigest()[:12]
    return f"STU-{h}"


def _validate_row(
    row: dict,
    course_ids: set,
    row_num: int,
    seen_refs: set,
    demo_date: date,
) -> list[dict]:
    errs = []

    def err(field, code, msg):
        errs.append({"row_number": row_num, "field": field, "error_code": code, "message": msg})

    for col in REQUIRED_COLS:
        if not row.get(col, "").strip():
            err(col, "E101", f"Missing required field: {col}")

    if errs:
        return errs

    apaar = row.get("apaar_id", "").strip()
    if apaar and (len(apaar) != 12 or not apaar.isdigit()):
        err("apaar_id", "E102", "APAAR ID must be exactly 12 digits")

    dob_str = row["date_of_birth"].strip()
    dob = None
    try:
        dob = date.fromisoformat(dob_str)
        age = (demo_date - dob).days // 365
        if not (15 <= age <= 60):
            err("date_of_birth", "E103", f"Age {age} is outside the valid range 15-60")
    except ValueError:
        err("date_of_birth", "E103", f"Invalid date format: {dob_str!r} (expected YYYY-MM-DD)")

    admit_str = row["admission_date"].strip()
    try:
        admit_date = date.fromisoformat(admit_str)
        if admit_date > demo_date:
            err("admission_date", "E103", "Admission date is in the future")
    except ValueError:
        err("admission_date", "E103", f"Invalid date format: {admit_str!r} (expected YYYY-MM-DD)")

    course_code = row["course_code"].strip()
    if course_code not in course_ids:
        err("course_code", "E104", f"Unknown course code {course_code!r} for this institution and year")

    if row["seat_category"].strip() not in VALID_SEAT_CATS:
        err("seat_category", "E105", f"Invalid seat_category {row['seat_category']!r}")

    if row["nationality_status"].strip() not in VALID_NATIONALITIES:
        err("nationality_status", "E105", f"Invalid nationality_status {row['nationality_status']!r}")

    ref = row["student_ref"].strip()
    if ref in seen_refs:
        err("student_ref", "E106", f"Duplicate student_ref {ref!r} in this file (class D1)")
    else:
        seen_refs.add(ref)

    return errs


def _assign_tier(row: dict, registry_result: Optional[str]) -> str:
    nationality = row.get("nationality_status", "INDIAN").strip()
    apaar = row.get("apaar_id", "").strip()
    opted_out = row.get("opted_out", "").strip().lower() in ("true", "yes", "1")
    if nationality in FOREIGN_NATIONALITIES or opted_out:
        return "T4"
    if not apaar:
        return "T3"
    if registry_result == "VERIFIED":
        return "T1"
    return "T2"


def _nationality_status(row: dict) -> str:
    ns = row.get("nationality_status", "INDIAN").strip().upper()
    return "FOREIGN" if ns in FOREIGN_NATIONALITIES else "INDIAN"


def _ensure_dup_case(
    db: Session,
    sid_a: str, sid_b: str,
    dup_cls: str,
    confidence: float,
    inst_a: str,
    inst_b: Optional[str],
    apaar: Optional[str],
) -> None:
    exists = db.query(DuplicateCase).filter(
        ((DuplicateCase.student_id_a == sid_a) & (DuplicateCase.student_id_b == sid_b)) |
        ((DuplicateCase.student_id_a == sid_b) & (DuplicateCase.student_id_b == sid_a))
    ).first()
    if not exists:
        db.add(DuplicateCase(
            id=str(uuid4()),
            student_id_a=sid_a,
            student_id_b=sid_b,
            duplicate_class=dup_cls,
            match_basis="apaar" if apaar else "name_dob",
            confidence=confidence,
            institution_id_a=inst_a,
            institution_id_b=inst_b,
            evidence=json.dumps({"apaar": apaar, "class": dup_cls}),
            status="suspected",
        ))


def process_upload(
    db: Session,
    upload_id: str,
    institution_id: str,
    academic_year: str,
    csv_bytes: bytes,
    uploader_id: str,
    demo_date: Optional[date] = None,
) -> dict:
    """Full pipeline. Returns a summary dict (also stored in Upload row)."""
    if demo_date is None:
        demo_date = date.today()

    upload = db.query(Upload).filter(Upload.id == upload_id).first()
    if upload is None:
        raise ValueError(f"Upload {upload_id!r} not found")

    upload.status = "processing"
    db.commit()

    try:
        text = csv_bytes.decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(text))
        rows = list(reader)
    except Exception as exc:
        upload.status = "failed"
        db.commit()
        return {"error": str(exc)}

    # Build course lookup for this institution+year
    course_map: dict[str, CourseApproval] = {}
    for c in db.query(CourseApproval).filter(
        CourseApproval.institution_id == institution_id,
        CourseApproval.academic_year == academic_year,
    ).all():
        course_map[c.id] = c
        parts = c.id.split("-")
        if len(parts) >= 3:
            short = parts[-1]
            course_map[short] = c
        # Also index by just the course code portion (e.g. CSE, MCA)
        course_map[c.id] = c

    course_ids = set(course_map.keys())

    errors: list[dict] = []
    warnings: list[dict] = []
    valid_rows: list[tuple[dict, CourseApproval]] = []
    seen_refs: set = set()
    tier_counts = {"T1": 0, "T2": 0, "T3": 0, "T4": 0}
    dup_counts = {"D1": 0, "D2": 0, "D3": 0, "D4": 0, "D5": 0}

    existing_students = db.query(Student).all()

    for row_num, row in enumerate(rows, start=2):
        row_errs = _validate_row(row, course_ids, row_num, seen_refs, demo_date)
        if row_errs:
            errors.extend(row_errs)
            continue
        apaar = row.get("apaar_id", "").strip()
        if not apaar:
            warnings.append({"row_number": row_num, "field": None,
                              "error_code": "W201", "message": "No APAAR ID — student assigned tier T3"})
        course_code = row["course_code"].strip()
        course = course_map.get(course_code)
        valid_rows.append((row, course))

    for e in errors:
        db.add(UploadError(
            upload_id=upload_id,
            row_number=e.get("row_number"),
            field=e.get("field"),
            error_code=e["error_code"],
            message=e["message"],
        ))
    for w in warnings:
        db.add(UploadError(
            upload_id=upload_id,
            row_number=w.get("row_number"),
            field=w.get("field"),
            error_code=w["error_code"],
            message=w["message"],
        ))

    courses_affected: set = set()
    accepted = 0
    warned_count = len(warnings)

    from app.simulators.registry_sim import verify as reg_verify

    for row, course in valid_rows:
        if course is None:
            continue

        student_ref = row["student_ref"].strip()
        apaar = row.get("apaar_id", "").strip() or None
        full_name = row["full_name"].strip()
        dob_str = row["date_of_birth"].strip()
        dob = date.fromisoformat(dob_str)
        seat_cat = row["seat_category"].strip()
        nationality = row.get("nationality_status", "INDIAN").strip()
        admission_date = date.fromisoformat(row["admission_date"].strip())
        mode = row.get("mode", "FULL_TIME").strip()
        admission_round = row.get("admission_round", "ROUND_1").strip() or "ROUND_1"
        entry_type = row.get("entry_type", "REGULAR").strip() or "REGULAR"
        gender = row.get("gender", "").strip() or None
        phone_raw = row.get("contact_phone", "").strip()
        guardian_raw = row.get("guardian_name", "").strip()

        registry_result = None
        if apaar:
            reg_resp = reg_verify(db, apaar)
            registry_result = reg_resp.get("result")
            if registry_result == "UNAVAILABLE":
                db.add(UploadError(
                    upload_id=upload_id, row_number=None, field="apaar_id",
                    error_code="W203",
                    message=f"Registry unavailable for APAAR {apaar}; student stays T2",
                ))
                warned_count += 1

        tier = _assign_tier(row, registry_result)
        tier_counts[tier] = tier_counts.get(tier, 0) + 1

        student_id = _make_student_id(institution_id, academic_year, student_ref)

        existing_student = db.query(Student).filter(Student.id == student_id).first()
        if existing_student:
            if tier == "T1" and existing_student.identity_tier != "T1":
                existing_student.identity_tier = tier
            student = existing_student
        else:
            student = Student(
                id=student_id,
                full_name=full_name,
                date_of_birth=dob,
                gender=gender,
                apaar_id=apaar,
                identity_tier=tier,
                contact_token=hmac_token(phone_raw) if phone_raw else None,
                guardian_token=hmac_token(guardian_raw) if guardian_raw else None,
            )
            db.add(student)

        existing_admit = db.query(AdmissionEvent).filter(
            AdmissionEvent.student_id == student_id,
            AdmissionEvent.course_approval_id == course.id,
            AdmissionEvent.event_type.in_(["ADMIT", "CORRECTION"]),
        ).order_by(AdmissionEvent.event_time.desc()).first()

        if existing_admit and existing_admit.seat_category != seat_cat:
            # Same student re-uploaded with a different seat_category → CORRECTION event
            corr_ev = AdmissionEvent(
                id=str(uuid4()),
                student_id=student_id,
                course_approval_id=course.id,
                seat_category=seat_cat,
                event_type="CORRECTION",
                admission_round=admission_round,
                entry_type=entry_type,
                nationality_status=_nationality_status(row),
                event_time=datetime(
                    admission_date.year, admission_date.month, admission_date.day,
                    9, 0, 0, tzinfo=timezone.utc,
                ),
                upload_id=upload_id,
            )
            db.add(corr_ev)
            courses_affected.add(course.id)
            accepted += 1
        elif not existing_admit:
            # Duplicate detection against all existing DB students
            for other in existing_students:
                if other.id == student_id:
                    continue
                if apaar and other.apaar_id == apaar:
                    other_event = db.query(AdmissionEvent).filter(
                        AdmissionEvent.student_id == other.id,
                        AdmissionEvent.event_type == "ADMIT",
                    ).first()
                    if other_event:
                        other_course = db.query(CourseApproval).filter(
                            CourseApproval.id == other_event.course_approval_id
                        ).first()
                        if other_course and other_course.institution_id != institution_id:
                            dc = "D2"
                            _ensure_dup_case(db, student_id, other.id, dc, 1.0,
                                             institution_id, other_course.institution_id, apaar)
                            dup_counts[dc] += 1
                elif not apaar and other.full_name and other.date_of_birth:
                    s = fuzzy_score(full_name, dob, other.full_name, other.date_of_birth)
                    dc = dup_class(s)
                    if dc:
                        _ensure_dup_case(db, student_id, other.id, dc, s,
                                         institution_id, None, None)
                        dup_counts[dc] += 1

            admit_ev = AdmissionEvent(
                id=str(uuid4()),
                student_id=student_id,
                course_approval_id=course.id,
                seat_category=seat_cat,
                event_type="ADMIT",
                admission_round=admission_round,
                entry_type=entry_type,
                nationality_status=_nationality_status(row),
                event_time=datetime(
                    admission_date.year, admission_date.month, admission_date.day,
                    9, 0, 0, tzinfo=timezone.utc,
                ),
                upload_id=upload_id,
            )
            db.add(admit_ev)
            courses_affected.add(course.id)
            accepted += 1

    db.flush()

    for cid in courses_affected:
        try:
            reconcile(db, cid)
        except Exception:
            pass

    db.flush()

    ledger_results = []
    for cid in courses_affected:
        try:
            result = evaluate(db, cid, as_of=demo_date)
            c = db.query(CourseApproval).filter(CourseApproval.id == cid).first()
            ledger_results.append({
                "course": c.name if c else cid,
                "approved": c.approved_intake if c else 0,
                "result": result.status,
                "flags": len(result.flags),
            })
        except Exception as exc:
            ledger_results.append({"course": cid, "error": str(exc)})

    summary = {
        "rows_total": len(rows),
        "rows_accepted": accepted,
        "rows_warning": warned_count,
        "rows_error": len(errors),
        "identity_tiers": tier_counts,
        "duplicates": dup_counts,
        "ledger": ledger_results,
    }

    upload.status = "done"
    upload.row_count = len(rows)
    upload.error_count = len(errors)
    upload.rows_accepted = accepted
    upload.rows_warning = warned_count
    upload.rows_errors = len(errors)
    upload.identity_tiers = json.dumps(tier_counts)
    upload.duplicates_summary = json.dumps(dup_counts)
    upload.ledger_results = json.dumps(ledger_results)
    upload.completed_at = datetime.now(timezone.utc)
    db.commit()

    return summary
