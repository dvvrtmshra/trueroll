"""Seat-Ledger Engine — checks C1-C5, evaluate, reconcile, simple_counter."""
import json
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from typing import Optional
from uuid import uuid4

from sqlalchemy.orm import Session

from app.models.admission_event import AdmissionEvent
from app.models.course import CourseApproval
from app.models.evaluation import Evaluation
from app.models.flag import Flag
from app.models.institution import Institution
from app.models.seat_bucket import SeatBucket
from app.services.rules_service import (
    active_rules_for,
    draft_or_pending_rules_for,
    rule_set_hash,
)

# ── Constants ─────────────────────────────────────────────────────────────────

# Maps seat_category from AdmissionEvent → SeatBucket.bucket_code.
# NRI_IN is inside approved_intake and therefore counts against REGULAR.
BUCKET_FOR_CATEGORY: dict[str, str] = {
    "REGULAR": "REGULAR",
    "NRI_IN": "REGULAR",
    "OCI_FN_EXTRA": "OCI_FN_EXTRA",
    "CIWGC_EXTRA": "CIWGC_EXTRA",
    "EWS": "EWS",
    "INTL_PG_EXTRA": "INTL_PG_EXTRA",
    "INTL_MGT_EXTRA": "INTL_MGT_EXTRA",
    "LATERAL": "LATERAL",
}

# Nationality required for seats that are extra/international
INTERNATIONAL_BUCKETS: set[str] = {
    "OCI_FN_EXTRA",
    "CIWGC_EXTRA",
    "INTL_PG_EXTRA",
    "INTL_MGT_EXTRA",
}

# Extra buckets that need an explicit rule
RULE_REQUIRED_BUCKETS: set[str] = INTERNATIONAL_BUCKETS | {"EWS"}


@dataclass
class FlagReason:
    check: str          # C1 | C2 | C3 | C4_REVERSION_APPLIED | W205
    bucket: Optional[str] = None
    cap: Optional[int] = None
    used: Optional[int] = None
    over_by: Optional[int] = None
    record_ids: list[str] = field(default_factory=list)
    rule_id: Optional[str] = None
    rule_version: Optional[int] = None
    note: Optional[str] = None


@dataclass
class EvalResult:
    status: str          # OK | FLAG | RULE_NOT_CONFIRMED
    course_id: str
    rule_set_hash: str
    rule_versions_used: list[str]
    flags: list[FlagReason]
    review_reason: Optional[str] = None
    caps: dict[str, int] = field(default_factory=dict)
    eff_caps: dict[str, int] = field(default_factory=dict)
    counts: dict[str, int] = field(default_factory=dict)


# ── Cap helpers ───────────────────────────────────────────────────────────────

def compute_caps(approved_intake: int, rules) -> dict[str, int]:
    """Return {bucket: cap} for all buckets given a set of active rules."""
    caps: dict[str, int] = {"REGULAR": approved_intake}
    for rv in rules:
        if rv.cap_basis == "PERCENT_OF_INTAKE" and rv.cap_percent is not None:
            cap = int(approved_intake * rv.cap_percent / 100)
        elif rv.cap_basis == "FIXED" and rv.cap_fixed is not None:
            cap = rv.cap_fixed
        else:
            cap = 0
        caps[rv.bucket] = cap
    return caps


def apply_reversion(caps: dict[str, int], counts: dict[str, int]) -> dict[str, int]:
    """C4 — surplus CIWGC capacity reverts to OCI_FN bucket."""
    eff = dict(caps)
    oci, ciwgc = "OCI_FN_EXTRA", "CIWGC_EXTRA"
    if oci in eff and ciwgc in eff:
        surplus = max(0, eff[ciwgc] - counts.get(ciwgc, 0))
        eff[oci] = eff[oci] + surplus
    return eff


def lawful_max(eff_caps: dict[str, int]) -> int:
    return sum(eff_caps.values())


# ── Event queries ─────────────────────────────────────────────────────────────

def _active_events(db: Session, course_id: str):
    """Events where event_type=ADMIT and no subsequent WITHDRAW for same student+course."""
    all_events = (
        db.query(AdmissionEvent)
        .filter(AdmissionEvent.course_approval_id == course_id)
        .order_by(AdmissionEvent.event_time)
        .all()
    )
    # Net: track admitted students; WITHDRAW cancels an ADMIT
    admitted: dict[str, AdmissionEvent] = {}
    for ev in all_events:
        if ev.event_type == "ADMIT":
            admitted[ev.student_id] = ev
        elif ev.event_type in ("WITHDRAW", "TRANSFER_OUT"):
            admitted.pop(ev.student_id, None)
    return list(admitted.values())


def bucket_counts(db: Session, course_id: str) -> dict[str, int]:
    """Count active admitted students per bucket."""
    counts: dict[str, int] = {}
    for ev in _active_events(db, course_id):
        bucket = BUCKET_FOR_CATEGORY.get(ev.seat_category, ev.seat_category)
        counts[bucket] = counts.get(bucket, 0) + 1
    return counts


# ── Core evaluation ───────────────────────────────────────────────────────────

def evaluate(
    db: Session,
    course_id: str,
    as_of: Optional[date] = None,
) -> EvalResult:
    """
    Run all checks C1-C5 for a course. Writes Evaluation and updates Flags.
    Returns an EvalResult (also persisted as Evaluation row).
    """
    if as_of is None:
        as_of = date.today()

    course = db.query(CourseApproval).filter(CourseApproval.id == course_id).first()
    if course is None:
        raise ValueError(f"Course {course_id!r} not found")
    institution = db.query(Institution).filter(Institution.id == course.institution_id).first()
    if institution is None:
        raise ValueError(f"Institution {course.institution_id!r} not found")

    active_rules = active_rules_for(db, course, institution, as_of)
    unconfirmed_rules = draft_or_pending_rules_for(db, course, institution, as_of)

    rs_hash = rule_set_hash(active_rules)
    rv_ids = [rv.id for rv in active_rules]

    active_buckets: set[str] = {rv.bucket for rv in active_rules}
    # Buckets covered by draft/pending rules
    unconfirmed_buckets: set[str] = {rv.bucket for rv in unconfirmed_rules}

    active_events = _active_events(db, course_id)

    # Which rule-required buckets have students?
    occupied: dict[str, list[AdmissionEvent]] = {}
    for ev in active_events:
        bucket = BUCKET_FOR_CATEGORY.get(ev.seat_category, ev.seat_category)
        occupied.setdefault(bucket, []).append(ev)

    # RULE_NOT_CONFIRMED check: any occupied rule-required bucket without active rule?
    missing_rule_buckets = [
        b for b in occupied
        if b in RULE_REQUIRED_BUCKETS and b not in active_buckets
    ]
    if missing_rule_buckets:
        # Distinguish "rule exists but unconfirmed" from "no rule at all"
        if any(b in unconfirmed_buckets for b in missing_rule_buckets):
            reason = f"Rule not confirmed: human review ({', '.join(missing_rule_buckets)})"
        else:
            reason = f"No rule defined for bucket(s): {', '.join(missing_rule_buckets)}"
        result = EvalResult(
            status="RULE_NOT_CONFIRMED",
            course_id=course_id,
            rule_set_hash=rs_hash,
            rule_versions_used=rv_ids,
            flags=[],
            review_reason=reason,
        )
        _persist(db, course_id, result)
        return result

    counts = {b: len(evs) for b, evs in occupied.items()}
    caps = compute_caps(course.approved_intake, active_rules)
    eff_caps = apply_reversion(caps, counts)
    lmax = lawful_max(eff_caps)

    flag_reasons: list[FlagReason] = []

    # C1 — bucket over effective cap
    for bucket, cap in eff_caps.items():
        used = counts.get(bucket, 0)
        if used > cap:
            rv = next((r for r in active_rules if r.bucket == bucket), None)
            flag_reasons.append(FlagReason(
                check="C1",
                bucket=bucket,
                cap=cap,
                used=used,
                over_by=used - cap,
                rule_id=rv.rule_id if rv else None,
                rule_version=rv.version if rv else None,
            ))

    # C2 — total over lawful max
    total_admitted = sum(counts.values())
    if total_admitted > lmax:
        flag_reasons.append(FlagReason(
            check="C2",
            bucket=None,
            cap=lmax,
            used=total_admitted,
            over_by=total_admitted - lmax,
        ))

    # C3 — domestic student in international extra seat
    for bucket in INTERNATIONAL_BUCKETS:
        if bucket not in occupied:
            continue
        ineligible = [ev for ev in occupied[bucket] if ev.nationality_status == "INDIAN"]
        if ineligible:
            rv = next((r for r in active_rules if r.bucket == bucket), None)
            flag_reasons.append(FlagReason(
                check="C3",
                bucket=bucket,
                used=len(ineligible),
                record_ids=[ev.student_id for ev in ineligible],
                rule_id=rv.rule_id if rv else None,
                rule_version=rv.version if rv else None,
                note=f"{len(ineligible)} ineligible holder(s)",
            ))

    status = "FLAG" if flag_reasons else "OK"
    result = EvalResult(
        status=status,
        course_id=course_id,
        rule_set_hash=rs_hash,
        rule_versions_used=rv_ids,
        flags=flag_reasons,
        caps=caps,
        eff_caps=eff_caps,
        counts=counts,
    )

    _persist(db, course_id, result)
    _update_flags(db, course, result, active_events)
    return result


def _flag_reason_to_dict(fr: FlagReason) -> dict:
    return {
        "check": fr.check,
        "bucket": fr.bucket,
        "cap": fr.cap,
        "used": fr.used,
        "over_by": fr.over_by,
        "record_ids": fr.record_ids,
        "rule_id": fr.rule_id,
        "rule_version": fr.rule_version,
        "note": fr.note,
    }


def _persist(db: Session, course_id: str, result: EvalResult) -> Evaluation:
    ev = Evaluation(
        id=str(uuid4()),
        course_approval_id=course_id,
        rule_set_hash=result.rule_set_hash,
        rule_versions_used=json.dumps(result.rule_versions_used),
        result=result.status,
        result_detail=json.dumps({
            "flags": [_flag_reason_to_dict(f) for f in result.flags],
            "review_reason": result.review_reason,
            "caps": result.caps,
            "eff_caps": result.eff_caps,
            "counts": result.counts,
        }),
        evaluated_at=datetime.now(timezone.utc),
    )
    db.add(ev)
    db.commit()
    return ev


def _update_flags(db: Session, course: CourseApproval, result: EvalResult, active_events) -> None:
    """One open flag per (course, bucket). Update if exists, create if new, clear if resolved."""
    existing_flags = (
        db.query(Flag)
        .filter(
            Flag.course_approval_id == course.id,
            Flag.status == "open",
        )
        .all()
    )
    existing_by_bucket: dict[str, Flag] = {f.bucket: f for f in existing_flags}

    new_flag_buckets: set[str] = set()
    for fr in result.flags:
        if fr.check in ("C1", "C2", "C3"):
            bucket_key = fr.bucket or "__total__"
            new_flag_buckets.add(bucket_key)

            if bucket_key in existing_by_bucket:
                f = existing_by_bucket[bucket_key]
                f.cap = fr.cap
                f.used = fr.used
                f.over_by = fr.over_by
                f.record_ids = json.dumps(fr.record_ids)
                f.updated_at = datetime.now(timezone.utc)
            else:
                db.add(Flag(
                    id=str(uuid4()),
                    institution_id=course.institution_id,
                    course_approval_id=course.id,
                    bucket=bucket_key,
                    rule_id=fr.rule_id,
                    rule_version=fr.rule_version,
                    cap=fr.cap,
                    used=fr.used,
                    over_by=fr.over_by,
                    record_ids=json.dumps(fr.record_ids),
                    status="open",
                    severity="high",
                    opened_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc),
                ))

    # Auto-clear flags that are no longer triggered
    for bucket_key, f in existing_by_bucket.items():
        if bucket_key not in new_flag_buckets:
            f.status = "auto_cleared"
            f.updated_at = datetime.now(timezone.utc)

    db.commit()


# ── Reconcile ─────────────────────────────────────────────────────────────────

def reconcile(db: Session, course_id: str) -> dict[str, int]:
    """
    Recompute SeatBucket.used from event history. Returns {bucket: drift} where
    drift = (stored used) - (computed used). Zero drift is the expected state.
    """
    course = db.query(CourseApproval).filter(CourseApproval.id == course_id).first()
    if course is None:
        raise ValueError(f"Course {course_id!r} not found")

    computed = bucket_counts(db, course_id)

    stored_buckets = (
        db.query(SeatBucket)
        .filter(SeatBucket.course_approval_id == course_id)
        .all()
    )
    stored: dict[str, SeatBucket] = {sb.bucket_code: sb for sb in stored_buckets}

    drift: dict[str, int] = {}
    all_buckets = set(computed) | set(stored)
    for bucket in all_buckets:
        comp_used = computed.get(bucket, 0)
        if bucket in stored:
            d = stored[bucket].used - comp_used
            drift[bucket] = d
            stored[bucket].used = comp_used
        else:
            drift[bucket] = -comp_used
            db.add(SeatBucket(
                id=str(uuid4()),
                course_approval_id=course_id,
                bucket_code=bucket,
                cap=course.approved_intake if bucket == "REGULAR" else 0,
                used=comp_used,
            ))

    db.commit()
    return drift


def reconcile_all(db: Session) -> dict[str, dict[str, int]]:
    """Reconcile every course. Returns {course_id: {bucket: drift}}."""
    courses = db.query(CourseApproval).all()
    results = {}
    for c in courses:
        results[c.id] = reconcile(db, c.id)
    return results


# ── Simple counter (compare mode) ─────────────────────────────────────────────

def simple_counter(course: CourseApproval, total_admitted: int) -> str:
    """
    Naïve headcount check: ALARM if total_admitted exceeds approved_intake.
    Used ONLY for the Compare view — does not know about extra seats.
    """
    if total_admitted > course.approved_intake:
        return "ALARM"
    return "OK"
