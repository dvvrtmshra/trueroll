"""Reports — N8 screen. 12 reports, JSON and CSV export."""
import csv
import io
import json
import os
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.roles import require_role, Role
from app.core.security import get_current_user

router = APIRouter()

_OFFICER_ROLES = (Role.NATIONAL_OFFICER, Role.REGIONAL_OFFICER, Role.SYSTEM_ADMIN, Role.AUDITOR)


def _require_officer(current_user=Depends(get_current_user)):
    from fastapi import HTTPException
    if current_user.get("role") not in (
        "NATIONAL_OFFICER", "REGIONAL_OFFICER", "SYSTEM_ADMIN", "AUDITOR",
    ):
        raise HTTPException(status_code=403, detail="Officers only")
    return current_user


REPORT_CATALOGUE = [
    {"id": "national-summary", "title": "National summary", "description": "Aggregate counts across all institutions"},
    {"id": "regional-breakdown", "title": "Regional breakdown", "description": "Per-region institution and flag counts"},
    {"id": "institution-compliance", "title": "Institution compliance", "description": "Per-institution evaluation status"},
    {"id": "seat-utilisation", "title": "Seat utilisation", "description": "Bucket fill rates per course"},
    {"id": "flag-ageing", "title": "Flag ageing", "description": "Open flags by age and severity"},
    {"id": "rule-coverage", "title": "Rule coverage", "description": "Rules active vs pending vs unconfirmed"},
    {"id": "duplicate-rate", "title": "Duplicate rate", "description": "Duplicate classes D1-D5 across institutions"},
    {"id": "vc-issuance", "title": "Credential issuance", "description": "Signed credentials issued and verified"},
    {"id": "employer-usage", "title": "Employer usage", "description": "Verification requests by employer"},
    {"id": "audit-integrity", "title": "Audit integrity", "description": "Hash-chain chain verify result"},
    {"id": "student-demographics", "title": "Student demographics", "description": "Identity tier and category breakdown"},
    {"id": "anomaly-summary", "title": "Anomaly summary", "description": "Review priority distribution by band"},
    {"id": "evaluation-summary", "title": "Evaluation results (6.14)", "description": "Prototype self-measured metrics"},
]


@router.get("")
def list_reports(current_user=Depends(_require_officer)):
    return {"reports": REPORT_CATALOGUE}


def _csv_response(headers: list[str], rows: list[list], filename: str):
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(headers)
    for r in rows:
        # Neutralise formula injection
        safe = [str(v).lstrip("=+@-\t\r") if isinstance(v, str) else v for v in r]
        w.writerow(safe)
    buf.seek(0)
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/national-summary")
def national_summary(
    format: str = Query("json", pattern="^(json|csv)$"),
    db: Session = Depends(get_db),
    current_user=Depends(_require_officer),
):
    from app.models.institution import Institution
    from app.models.student import Student
    from app.models.flag import Flag
    from app.models.course import CourseApproval
    from app.models.upload import Upload

    inst_count = db.query(func.count(Institution.id)).scalar() or 0
    student_count = db.query(func.count(Student.id)).scalar() or 0
    open_flags = db.query(func.count(Flag.id)).filter(
        Flag.status.in_(["open", "under_review", "clarification_requested"])
    ).scalar() or 0
    course_count = db.query(func.count(CourseApproval.id)).scalar() or 0
    upload_count = db.query(func.count(Upload.id)).scalar() or 0

    t1 = db.query(func.count(Student.id)).filter(Student.identity_tier == "T1").scalar() or 0
    t2 = db.query(func.count(Student.id)).filter(Student.identity_tier == "T2").scalar() or 0
    t3 = db.query(func.count(Student.id)).filter(Student.identity_tier == "T3").scalar() or 0
    t4 = db.query(func.count(Student.id)).filter(Student.identity_tier == "T4").scalar() or 0

    data = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "institutions": inst_count,
        "courses": course_count,
        "students": student_count,
        "uploads": upload_count,
        "open_flags": open_flags,
        "identity_tiers": {"T1": t1, "T2": t2, "T3": t3, "T4": t4},
        "note": "SAMPLE DATA — synthetic only",
    }
    if format == "csv":
        rows = [
            ["Metric", "Value"],
            ["Institutions", inst_count],
            ["Courses", course_count],
            ["Students", student_count],
            ["Uploads", upload_count],
            ["Open flags", open_flags],
            ["T1 Verified", t1],
            ["T2 Unverified", t2],
            ["T3 No APAAR", t3],
            ["T4 Opted-out/FN", t4],
        ]
        return _csv_response(["Metric", "Value"], rows, "national-summary.csv")
    return data


@router.get("/seat-utilisation")
def seat_utilisation(
    format: str = Query("json", pattern="^(json|csv)$"),
    academic_year: str = "2026-27",
    db: Session = Depends(get_db),
    current_user=Depends(_require_officer),
):
    from app.models.course import CourseApproval
    from app.models.institution import Institution
    from app.models.seat_bucket import SeatBucket

    rows = []
    for course in db.query(CourseApproval).filter(
        CourseApproval.academic_year == academic_year
    ).all():
        inst = db.query(Institution).filter(Institution.id == course.institution_id).first()
        buckets = db.query(SeatBucket).filter(SeatBucket.course_approval_id == course.id).all()
        total_cap = sum(b.cap for b in buckets) or course.approved_intake
        total_used = sum(b.used for b in buckets)
        fill_pct = round(100 * total_used / total_cap, 1) if total_cap else 0
        rows.append({
            "institution": inst.name if inst else course.institution_id,
            "course": course.name,
            "academic_year": academic_year,
            "approved_intake": course.approved_intake,
            "lawful_max": total_cap,
            "admitted": total_used,
            "fill_pct": fill_pct,
        })

    if format == "csv":
        headers = ["Institution", "Course", "Year", "Approved intake", "Lawful max", "Admitted", "Fill %"]
        csv_rows = [[r["institution"], r["course"], academic_year,
                     r["approved_intake"], r["lawful_max"], r["admitted"], r["fill_pct"]] for r in rows]
        return _csv_response(headers, csv_rows, "seat-utilisation.csv")
    return {"items": rows, "count": len(rows), "academic_year": academic_year}


@router.get("/flag-ageing")
def flag_ageing(
    format: str = Query("json", pattern="^(json|csv)$"),
    db: Session = Depends(get_db),
    current_user=Depends(_require_officer),
):
    from app.models.flag import Flag
    from app.models.institution import Institution

    now = datetime.now(timezone.utc)
    flags = db.query(Flag).filter(Flag.status.in_(["open", "under_review", "clarification_requested"])).all()
    buckets = {"0-3d": 0, "4-7d": 0, "8-30d": 0, "30+d": 0}
    rows = []
    for f in flags:
        age = (now - f.opened_at.replace(tzinfo=timezone.utc if f.opened_at.tzinfo is None else f.opened_at.tzinfo)).days
        if age <= 3:
            b = "0-3d"
        elif age <= 7:
            b = "4-7d"
        elif age <= 30:
            b = "8-30d"
        else:
            b = "30+d"
        buckets[b] += 1
        inst = db.query(Institution).filter(Institution.id == f.institution_id).first()
        rows.append({
            "flag_id": f.id,
            "institution": inst.name if inst else f.institution_id,
            "bucket": f.bucket,
            "severity": f.severity,
            "status": f.status,
            "age_days": age,
            "age_bucket": b,
            "opened_at": f.opened_at.isoformat(),
        })

    if format == "csv":
        headers = ["Flag ID", "Institution", "Bucket", "Severity", "Status", "Age (days)", "Age bucket"]
        csv_rows = [[r["flag_id"], r["institution"], r["bucket"], r["severity"],
                     r["status"], r["age_days"], r["age_bucket"]] for r in rows]
        return _csv_response(headers, csv_rows, "flag-ageing.csv")
    return {"summary": buckets, "items": rows, "total": len(rows)}


@router.get("/audit-integrity")
def audit_integrity(
    db: Session = Depends(get_db),
    current_user=Depends(_require_officer),
):
    from app.core.audit import verify_chain
    result = verify_chain(db)
    return result


@router.get("/anomaly-summary")
def anomaly_summary(
    format: str = Query("json", pattern="^(json|csv)$"),
    db: Session = Depends(get_db),
    current_user=Depends(_require_officer),
):
    from app.models.review_priority import ReviewPriority
    items = db.query(ReviewPriority).order_by(ReviewPriority.score.desc()).limit(200).all()
    band_counts = {"High": 0, "Medium": 0, "Low": 0}
    rows = []
    for rp in items:
        band_counts[rp.band] = band_counts.get(rp.band, 0) + 1
        rows.append({
            "id": rp.id,
            "institution_id": rp.institution_id,
            "course_id": rp.course_id,
            "period": rp.period,
            "score": rp.score,
            "band": rp.band,
            "model_version": rp.model_version,
            "status": rp.status,
        })

    if format == "csv":
        headers = ["ID", "Institution", "Course", "Period", "Score", "Band", "Model", "Status"]
        csv_rows = [[r["id"], r["institution_id"], r["course_id"], r["period"],
                     r["score"], r["band"], r["model_version"], r["status"]] for r in rows]
        return _csv_response(headers, csv_rows, "anomaly-summary.csv")
    return {"band_counts": band_counts, "items": rows, "total": len(rows)}


@router.get("/evaluation-summary")
def evaluation_summary(
    current_user=Depends(_require_officer),
):
    """Reads models/evaluation_summary.json. Returns not_run status if file missing."""
    summary_path = os.path.join(
        os.path.dirname(__file__), "..", "..", "models", "evaluation_summary.json"
    )
    if not os.path.exists(summary_path):
        return {
            "status": "not_run",
            "message": "Run `make evaluate` to generate the evaluation summary.",
        }
    with open(summary_path) as f:
        return json.load(f)


@router.get("/regional-breakdown")
def regional_breakdown(
    format: str = Query("json", pattern="^(json|csv)$"),
    db: Session = Depends(get_db),
    current_user=Depends(_require_officer),
):
    from app.models.institution import Institution
    from app.models.flag import Flag

    regions = db.query(Institution.region, func.count(Institution.id)).group_by(Institution.region).all()
    rows = []
    for region, count in regions:
        flags = db.query(func.count(Flag.id)).join(
            Institution, Flag.institution_id == Institution.id
        ).filter(
            Institution.region == region,
            Flag.status.in_(["open", "under_review"]),
        ).scalar() or 0
        rows.append({"region": region, "institutions": count, "open_flags": flags})

    if format == "csv":
        return _csv_response(["Region", "Institutions", "Open flags"],
                              [[r["region"], r["institutions"], r["open_flags"]] for r in rows],
                              "regional-breakdown.csv")
    return {"items": rows}


@router.get("/institution-compliance")
def institution_compliance(
    format: str = Query("json", pattern="^(json|csv)$"),
    academic_year: str = "2026-27",
    db: Session = Depends(get_db),
    current_user=Depends(_require_officer),
):
    from app.models.institution import Institution
    from app.models.evaluation import Evaluation
    from app.models.course import CourseApproval
    from app.models.flag import Flag

    rows = []
    for inst in db.query(Institution).order_by(Institution.name).limit(100).all():
        courses = db.query(CourseApproval).filter(
            CourseApproval.institution_id == inst.id,
            CourseApproval.academic_year == academic_year,
        ).all()
        for c in courses:
            last_eval = (
                db.query(Evaluation)
                .filter(Evaluation.course_approval_id == c.id)
                .order_by(Evaluation.evaluated_at.desc())
                .first()
            )
            open_flags = db.query(func.count(Flag.id)).filter(
                Flag.course_approval_id == c.id,
                Flag.status.in_(["open", "under_review"]),
            ).scalar() or 0
            rows.append({
                "institution": inst.name,
                "course": c.name,
                "last_result": last_eval.result if last_eval else "NOT_EVALUATED",
                "open_flags": open_flags,
                "last_evaluated": last_eval.evaluated_at.isoformat() if last_eval else None,
            })

    if format == "csv":
        return _csv_response(
            ["Institution", "Course", "Last result", "Open flags", "Last evaluated"],
            [[r["institution"], r["course"], r["last_result"], r["open_flags"], r["last_evaluated"]] for r in rows],
            "institution-compliance.csv",
        )
    return {"items": rows, "count": len(rows)}


@router.get("/rule-coverage")
def rule_coverage(
    db: Session = Depends(get_db),
    current_user=Depends(_require_officer),
):
    from app.models.rule import RuleVersion
    statuses = db.query(RuleVersion.status, func.count(RuleVersion.id)).group_by(RuleVersion.status).all()
    return {"rule_status_counts": {s: c for s, c in statuses}}


@router.get("/duplicate-rate")
def duplicate_rate(
    format: str = Query("json", pattern="^(json|csv)$"),
    db: Session = Depends(get_db),
    current_user=Depends(_require_officer),
):
    from app.models.duplicate_case import DuplicateCase
    classes = db.query(DuplicateCase.duplicate_class, func.count(DuplicateCase.id)).group_by(
        DuplicateCase.duplicate_class
    ).all()
    rows = [{"duplicate_class": dc, "count": cnt} for dc, cnt in classes]
    if format == "csv":
        return _csv_response(["Class", "Count"], [[r["duplicate_class"], r["count"]] for r in rows], "duplicate-rate.csv")
    return {"items": rows}


@router.get("/vc-issuance")
def vc_issuance(
    db: Session = Depends(get_db),
    current_user=Depends(_require_officer),
):
    from app.models.share_code import ShareCode
    total = db.query(func.count(ShareCode.id)).scalar() or 0
    active = db.query(func.count(ShareCode.id)).filter(ShareCode.status == "active").scalar() or 0
    withdrawn = db.query(func.count(ShareCode.id)).filter(ShareCode.status == "withdrawn").scalar() or 0
    return {"total_codes": total, "active": active, "withdrawn": withdrawn}


@router.get("/employer-usage")
def employer_usage(
    db: Session = Depends(get_db),
    current_user=Depends(_require_officer),
):
    from app.models.verification_event import VerificationEvent
    total = db.query(func.count(VerificationEvent.id)).scalar() or 0
    return {"total_verifications": total}


@router.get("/student-demographics")
def student_demographics(
    format: str = Query("json", pattern="^(json|csv)$"),
    db: Session = Depends(get_db),
    current_user=Depends(_require_officer),
):
    from app.models.student import Student
    from app.models.admission_event import AdmissionEvent

    tiers = db.query(Student.identity_tier, func.count(Student.id)).group_by(Student.identity_tier).all()
    categories = db.query(AdmissionEvent.seat_category, func.count(AdmissionEvent.id)).filter(
        AdmissionEvent.event_type == "ADMIT"
    ).group_by(AdmissionEvent.seat_category).all()

    tier_data = [{"tier": t, "count": c} for t, c in tiers]
    cat_data = [{"category": cat, "count": cnt} for cat, cnt in categories]

    if format == "csv":
        rows = [["Tier", t, c] for t, c in tiers] + [["Category", cat, cnt] for cat, cnt in categories]
        return _csv_response(["Type", "Value", "Count"], rows, "student-demographics.csv")
    return {"identity_tiers": tier_data, "seat_categories": cat_data}
