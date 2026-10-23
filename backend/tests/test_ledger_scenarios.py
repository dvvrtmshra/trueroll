"""
Seat-Ledger regression tests — spec section 6.4 examples + scenarios S1-S5, S14, S18.

All six examples from 6.4 and scenarios S1-S5, S14, S18 must pass.
"""
import json
from datetime import date, datetime, timezone
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from app.models.institution import Institution
from app.models.course import CourseApproval
from app.models.rule import Rule, RuleVersion
from app.models.student import Student
from app.models.admission_event import AdmissionEvent
from app.services.ledger import evaluate, reconcile, simple_counter, bucket_counts
from app.services.rules_service import approve_rule_version, activate_rule_version, submit_for_review


# ── Test-data helpers ─────────────────────────────────────────────────────────

def _inst(db: Session, inst_id: str, state: str = "Delhi", inst_type: str = "Government") -> Institution:
    existing = db.query(Institution).filter(Institution.id == inst_id).first()
    if existing:
        return existing
    i = Institution(
        id=inst_id, name=f"Test Institution {inst_id}", region="North",
        state=state, city="Test City", type=inst_type, status="Open",
    )
    db.add(i)
    db.commit()
    return i


def _course(
    db: Session,
    course_id: str,
    inst_id: str,
    intake: int = 240,
    level: str = "UG",
    domain: str = "Engineering and Technology",
    academic_year: str = "2026-27",
) -> CourseApproval:
    existing = db.query(CourseApproval).filter(CourseApproval.id == course_id).first()
    if existing:
        return existing
    c = CourseApproval(
        id=course_id, institution_id=inst_id,
        name=f"Test {course_id}", level=level, domain=domain,
        academic_year=academic_year, approved_intake=intake, lateral_intake=0,
    )
    db.add(c)
    db.commit()
    return c


def _rule_version(
    db: Session,
    rule_id: str,
    version: int,
    bucket: str,
    cap_percent: float | None,
    status: str = "active",
    academic_year: str = "2026-27",
    level: str = "UG",
    domain: str = "Engineering and Technology",
    cap_basis: str = "PERCENT_OF_INTAKE",
) -> RuleVersion:
    rv_id = f"RV-{rule_id}-V{version}-TEST"
    existing = db.query(RuleVersion).filter(RuleVersion.id == rv_id).first()
    if existing:
        return existing
    rule = db.query(Rule).filter(Rule.id == rule_id).first()
    if not rule:
        db.add(Rule(id=rule_id, current_version=version))
        db.commit()
    rv = RuleVersion(
        id=rv_id,
        rule_id=rule_id,
        version=version,
        academic_year=academic_year,
        programme_level=json.dumps([level]),
        domain=domain,
        state="ALL",
        institution_type="ALL",
        bucket=bucket,
        cap_basis=cap_basis,
        cap_percent=cap_percent,
        cap_fixed=None,
        eligible_categories=json.dumps(["FN", "OCI", "PIO"]),
        source_document="AICTE Handbook (Illustrative)",
        source_clause="Para X (Illustrative: to be confirmed against AICTE rules)",
        status=status,
        enabled=(status == "active"),
        approvals=json.dumps([{"by": "proposer@test", "role": "proposer", "at": "2026-01-01T00:00:00+00:00"}]),
        proposed_by="test",
        proposed_at=datetime.now(timezone.utc),
    )
    db.add(rv)
    db.commit()
    return rv


def _student(db: Session, stu_id: str, nationality: str = "INDIAN") -> Student:
    existing = db.query(Student).filter(Student.id == stu_id).first()
    if existing:
        return existing
    s = Student(
        id=stu_id, full_name=f"Student {stu_id}",
        date_of_birth=date(2000, 1, 1), gender="M",
        apaar_id=None, identity_tier="T1",
        contact_token="tok1", guardian_token="tok2",
    )
    db.add(s)
    db.commit()
    return s


def _admit_n(
    db: Session,
    course_id: str,
    n: int,
    seat_category: str,
    nationality: str = "INDIAN",
    prefix: str = "S",
    start: int = 1,
    at: datetime | None = None,
) -> list[str]:
    """Admit n students; return list of student_ids."""
    if at is None:
        at = datetime(2026, 7, 15, 9, 0, 0, tzinfo=timezone.utc)
    ids = []
    for i in range(start, start + n):
        sid = f"{prefix}-{course_id}-{seat_category[:3]}-{i:04d}"
        _student(db, sid, nationality)
        db.add(AdmissionEvent(
            id=str(uuid4()),
            student_id=sid,
            course_approval_id=course_id,
            seat_category=seat_category,
            event_type="ADMIT",
            admission_round="ROUND_1",
            entry_type="REGULAR",
            nationality_status=nationality,
            event_time=at,
            upload_id=None,
        ))
        ids.append(sid)
    db.commit()
    return ids


def _withdraw_n(db: Session, course_id: str, student_ids: list[str], at: datetime) -> None:
    for sid in student_ids:
        db.add(AdmissionEvent(
            id=str(uuid4()),
            student_id=sid,
            course_approval_id=course_id,
            seat_category="REGULAR",
            event_type="WITHDRAW",
            admission_round="ROUND_1",
            entry_type="REGULAR",
            nationality_status="INDIAN",
            event_time=at,
            upload_id=None,
        ))
    db.commit()


# ── Setup fixtures ────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def ledger_setup(session_db):
    """Create shared institutions, rules, and courses for ledger tests."""
    inst_id = "INST-LT001"
    _inst(session_db, inst_id, state="Delhi")

    # Active SN-A and SN-B rules for UG Engineering
    _rule_version(session_db, "SN-A-TEST", 1, "OCI_FN_EXTRA", 10.0, status="active")
    _rule_version(session_db, "SN-B-TEST", 1, "CIWGC_EXTRA", 5.0, status="active")
    # Draft EWS rule (for S4)
    _rule_version(session_db, "EWS-TEST", 1, "EWS", 10.0, status="draft")
    # Pending SN-MGT rule for Management courses (S5)
    _rule_version(
        session_db, "SN-MGT-TEST", 1, "INTL_MGT_EXTRA", 25.0,
        status="pending_review",
        level="MBA/PGDM",
        domain="Management",
    )

    return {"inst_id": inst_id, "db": session_db}


# ── Example 1 / S1 — Lawful 276, no flag ─────────────────────────────────────

def test_example1_lawful_276(ledger_setup):
    """240 REGULAR + 24 OCI_FN + 12 CIWGC = 276 = lawful max → OK."""
    db = ledger_setup["db"]
    cid = "CRS-LT-E1"
    _course(db, cid, ledger_setup["inst_id"], intake=240)
    _admit_n(db, cid, 240, "REGULAR", "INDIAN")
    _admit_n(db, cid, 24, "OCI_FN_EXTRA", "FOREIGN", start=300)
    _admit_n(db, cid, 12, "CIWGC_EXTRA", "FOREIGN", start=400)

    result = evaluate(db, cid, as_of=date(2026, 10, 1))
    assert result.status == "OK", f"Expected OK, got {result.status}: {result.flags}"
    assert result.flags == []


def test_s1_simple_counter_alarm_vs_seat_ledger_ok(ledger_setup):
    """S1: simple_counter says ALARM (276 > 240), Seat-Ledger says OK."""
    db = ledger_setup["db"]
    cid = "CRS-LT-E1"
    course = db.query(CourseApproval).filter(CourseApproval.id == cid).first()
    counts = bucket_counts(db, cid)
    total = sum(counts.values())
    assert total == 276
    assert simple_counter(course, total) == "ALARM"
    result = evaluate(db, cid, as_of=date(2026, 10, 1))
    assert result.status == "OK"


# ── Example 2 / S2 — C3 domestic in extra seats ───────────────────────────────

def test_example2_c3_domestic_in_extra(ledger_setup):
    """S2: 5 domestic (INDIAN) students in OCI_FN_EXTRA → C3 flag, 5 ineligible."""
    db = ledger_setup["db"]
    cid = "CRS-LT-E2"
    _course(db, cid, ledger_setup["inst_id"], intake=240)
    _admit_n(db, cid, 240, "REGULAR", "INDIAN")
    # 19 foreign + 5 domestic in OCI_FN_EXTRA
    _admit_n(db, cid, 19, "OCI_FN_EXTRA", "FOREIGN", start=300)
    _admit_n(db, cid, 5, "OCI_FN_EXTRA", "INDIAN", start=400)   # ineligible
    _admit_n(db, cid, 12, "CIWGC_EXTRA", "FOREIGN", start=500)

    result = evaluate(db, cid, as_of=date(2026, 10, 1))
    assert result.status == "FLAG"
    c3_flags = [f for f in result.flags if f.check == "C3"]
    assert len(c3_flags) == 1
    assert c3_flags[0].bucket == "OCI_FN_EXTRA"
    assert c3_flags[0].used == 5
    assert len(c3_flags[0].record_ids) == 5


# ── Example 3 / S3 — C2 + C1 over max 282 ───────────────────────────────────

def test_example3_c2_c1_over_max(ledger_setup):
    """S3: 240 REGULAR + 6 NRI_IN = 246 in REGULAR bucket (>cap 240) + 24 OCI + 12 CIWGC = 282."""
    db = ledger_setup["db"]
    cid = "CRS-LT-E3"
    _course(db, cid, ledger_setup["inst_id"], intake=240)
    _admit_n(db, cid, 240, "REGULAR", "INDIAN")
    _admit_n(db, cid, 6, "NRI_IN", "INDIAN", start=250)       # inside intake, counted in REGULAR bucket
    _admit_n(db, cid, 24, "OCI_FN_EXTRA", "FOREIGN", start=300)
    _admit_n(db, cid, 12, "CIWGC_EXTRA", "FOREIGN", start=400)

    result = evaluate(db, cid, as_of=date(2026, 10, 1))
    assert result.status == "FLAG"
    checks = {f.check for f in result.flags}
    assert "C1" in checks, f"Expected C1 flag; got {[f.check for f in result.flags]}"
    assert "C2" in checks, f"Expected C2 flag; got {[f.check for f in result.flags]}"

    c1 = next(f for f in result.flags if f.check == "C1")
    assert c1.bucket == "REGULAR"
    assert c1.over_by == 6

    c2 = next(f for f in result.flags if f.check == "C2")
    assert c2.over_by == 6   # 282 - 276


# ── Example 4 — C4 reversion: CIWGC=4, OCI=30 → no flag ─────────────────────

def test_example4_c4_reversion_no_flag(ledger_setup):
    """CIWGC used 4 (cap 12), OCI used 30 (cap 24). Reversion: eff_OCI = 24+8 = 32. No flag."""
    db = ledger_setup["db"]
    cid = "CRS-LT-E4"
    _course(db, cid, ledger_setup["inst_id"], intake=240)
    _admit_n(db, cid, 240, "REGULAR", "INDIAN")
    _admit_n(db, cid, 30, "OCI_FN_EXTRA", "FOREIGN", start=300)
    _admit_n(db, cid, 4, "CIWGC_EXTRA", "FOREIGN", start=400)

    result = evaluate(db, cid, as_of=date(2026, 10, 1))
    # eff_OCI = 24 + max(0, 12 - 4) = 32; total = 240+30+4 = 274 ≤ 276
    assert result.status == "OK", f"Expected OK: {result.flags}"
    assert result.eff_caps.get("OCI_FN_EXTRA") == 32


# ── Example 5 — C4 reversion fails: CIWGC=12, OCI=30 → C1+C2 ─────────────────

def test_example5_c4_reversion_c1_flag(ledger_setup):
    """CIWGC full (12), OCI 30 > cap 24. No reversion surplus. C1 on OCI_FN, C2 on total."""
    db = ledger_setup["db"]
    cid = "CRS-LT-E5"
    _course(db, cid, ledger_setup["inst_id"], intake=240)
    _admit_n(db, cid, 240, "REGULAR", "INDIAN")
    _admit_n(db, cid, 30, "OCI_FN_EXTRA", "FOREIGN", start=300)
    _admit_n(db, cid, 12, "CIWGC_EXTRA", "FOREIGN", start=400)

    result = evaluate(db, cid, as_of=date(2026, 10, 1))
    assert result.status == "FLAG"
    checks = {f.check for f in result.flags}
    assert "C1" in checks
    assert "C2" in checks

    c1 = next(f for f in result.flags if f.check == "C1")
    assert c1.bucket == "OCI_FN_EXTRA"
    assert c1.over_by == 6   # 30 - 24 (no reversion when CIWGC is full)


# ── Example 6 / S4 — RULE_NOT_CONFIRMED ──────────────────────────────────────

def test_example6_s4_rule_not_confirmed(ledger_setup):
    """S4: EWS students present but EWS-TEST rule is draft → RULE_NOT_CONFIRMED."""
    db = ledger_setup["db"]
    cid = "CRS-LT-E6"
    _course(db, cid, ledger_setup["inst_id"], intake=180)
    _admit_n(db, cid, 165, "REGULAR", "INDIAN")
    _admit_n(db, cid, 15, "EWS", "INDIAN", start=200)

    result = evaluate(db, cid, as_of=date(2026, 10, 1))
    assert result.status == "RULE_NOT_CONFIRMED"
    assert result.flags == []
    assert result.review_reason is not None
    assert "EWS" in result.review_reason


# ── S5 — Approve SN-MGT-TEST, re-evaluate → changes from NOT_CONFIRMED to OK ─

def test_s5_approve_rule_and_reevaluate(ledger_setup):
    """S5: Management course with INTL_MGT seats. SN-MGT-TEST is pending.
    After approval + activation by a second person, re-evaluation clears NOT_CONFIRMED."""
    db = ledger_setup["db"]
    _inst(db, "INST-LT002", state="Uttar Pradesh")
    cid = "CRS-LT-MGT"
    _course(db, cid, "INST-LT002", intake=120, level="MBA/PGDM", domain="Management")
    _admit_n(db, cid, 100, "REGULAR", "INDIAN")
    _admit_n(db, cid, 10, "INTL_MGT_EXTRA", "FOREIGN", start=200)

    # Before approval: RULE_NOT_CONFIRMED (pending rule)
    result_before = evaluate(db, cid, as_of=date(2026, 10, 1))
    assert result_before.status == "RULE_NOT_CONFIRMED"

    # Approve as a different person and activate
    rv = db.query(RuleVersion).filter(RuleVersion.id == "RV-SN-MGT-TEST-V1-TEST").first()
    assert rv is not None, "SN-MGT-TEST rule version not found"
    rv = approve_rule_version(db, rv, "approver@trueroll.test")
    rv = activate_rule_version(db, rv, date(2026, 9, 1))

    # After activation: re-evaluate → OK
    result_after = evaluate(db, cid, as_of=date(2026, 10, 1))
    assert result_after.status == "OK", f"Expected OK after rule activation: {result_after.flags}"


# ── S14 — Withdrawal frees seat ───────────────────────────────────────────────

def test_s14_withdrawal_frees_seat(ledger_setup):
    """Withdrawing a student reduces bucket count; evaluation stays OK.

    Use intake=240 with all CIWGC seats filled so C4 reversion adds no surplus.
    Admit exactly 24 OCI_FN; withdraw 3 → used=21, cap=24 → no flag.
    """
    db = ledger_setup["db"]
    cid = "CRS-LT-S14"
    _course(db, cid, ledger_setup["inst_id"], intake=240)
    admitted = _admit_n(db, cid, 24, "OCI_FN_EXTRA", "FOREIGN", start=600)
    _admit_n(db, cid, 12, "CIWGC_EXTRA", "FOREIGN", start=650)   # fills CIWGC cap → no reversion
    _admit_n(db, cid, 204, "REGULAR", "INDIAN", start=700)

    counts_before = bucket_counts(db, cid)
    assert counts_before.get("OCI_FN_EXTRA", 0) == 24

    # Withdraw 3 OCI students
    early_withdraw = datetime(2026, 9, 1, tzinfo=timezone.utc)
    _withdraw_n(db, cid, admitted[:3], at=early_withdraw)

    counts_after = bucket_counts(db, cid)
    assert counts_after.get("OCI_FN_EXTRA", 0) == 21

    result = evaluate(db, cid, as_of=date(2026, 10, 1))
    assert result.status == "OK", f"Expected OK after withdrawal: {result.flags}"


# ── S18 — Rule change mid-year preserves old evaluations ─────────────────────

def test_s18_rule_change_preserves_history(ledger_setup):
    """S18: Activating a new rule version retires the old one.
    Old Evaluation rows keep their original rule_set_hash (immutable)."""
    import json as _json
    db = ledger_setup["db"]
    from app.models.evaluation import Evaluation

    cid = "CRS-LT-S18"
    _course(db, cid, ledger_setup["inst_id"], intake=240)
    _admit_n(db, cid, 200, "REGULAR", "INDIAN", start=800)
    _admit_n(db, cid, 20, "OCI_FN_EXTRA", "FOREIGN", start=900)
    _admit_n(db, cid, 10, "CIWGC_EXTRA", "FOREIGN", start=950)

    # First evaluation with current active rules
    r1 = evaluate(db, cid, as_of=date(2026, 9, 1))
    hash1 = r1.rule_set_hash

    # Add and activate a new version of SN-A-TEST
    new_rv_id = "RV-SN-A-TEST-V2-TEST"
    if not db.query(RuleVersion).filter(RuleVersion.id == new_rv_id).first():
        new_rv = RuleVersion(
            id=new_rv_id, rule_id="SN-A-TEST", version=2,
            academic_year="2026-27",
            programme_level=_json.dumps(["UG"]),
            domain="Engineering and Technology",
            state="ALL", institution_type="ALL",
            bucket="OCI_FN_EXTRA",
            cap_basis="PERCENT_OF_INTAKE", cap_percent=12.0,
            eligible_categories=_json.dumps(["FN", "OCI"]),
            source_document="AICTE Update (Illustrative)",
            source_clause="Para Y (Illustrative: to be confirmed against AICTE rules)",
            status="approved", enabled=False,
            approvals=_json.dumps([
                {"by": "proposer@trueroll.test", "role": "proposer", "at": "2026-01-01T00:00:00+00:00"},
                {"by": "approver2@trueroll.test", "role": "approver", "at": "2026-01-02T00:00:00+00:00"},
            ]),
            proposed_by="test",
            proposed_at=datetime.now(timezone.utc),
        )
        db.add(new_rv)
        db.commit()
    new_rv = db.query(RuleVersion).filter(RuleVersion.id == new_rv_id).first()
    if new_rv.status == "approved":
        activate_rule_version(db, new_rv, date(2026, 10, 1))

    # Second evaluation now uses the new rule version
    r2 = evaluate(db, cid, as_of=date(2026, 10, 2))
    hash2 = r2.rule_set_hash

    assert hash1 != hash2, "Rule set hash must change when rule is updated"

    # The original evaluation in the DB still has its original hash (immutable)
    e1_db = db.query(Evaluation).filter(Evaluation.rule_set_hash == hash1).first()
    assert e1_db is not None, "Original evaluation with old hash must still exist"
    assert e1_db.rule_set_hash == hash1


# ── Reconcile ─────────────────────────────────────────────────────────────────

def test_reconcile_zero_drift(ledger_setup):
    """After reconcile(), a second reconcile() call reports zero drift on all buckets."""
    db = ledger_setup["db"]
    cid = "CRS-LT-E1"
    # First call populates (or corrects) SeatBucket from events.
    reconcile(db, cid)
    # Second call should report no drift.
    drift = reconcile(db, cid)
    assert all(v == 0 for v in drift.values()), f"Non-zero drift after second reconcile: {drift}"
