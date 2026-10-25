"""Regression test runner — run S1–S5, S14, S18 scenarios as a service call.

Returns a list of {scenario, expected, actual, pass} dicts.
Uses an in-memory SQLite session so results never touch production data.
"""
from __future__ import annotations

import json
from datetime import date, datetime, timezone
from typing import Any
from uuid import uuid4

from sqlalchemy import create_engine, event as sa_event
from sqlalchemy.orm import Session, sessionmaker

from app.models.base import Base
from app.models.course import CourseApproval
from app.models.institution import Institution
from app.models.rule import Rule, RuleVersion
from app.models.admission_event import AdmissionEvent
from app.models.seat_bucket import SeatBucket
from app.services.ledger import evaluate, reconcile


def _build_session() -> Session:
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )

    @sa_event.listens_for(engine, "connect")
    def _set_wal(conn, _):
        conn.execute("PRAGMA foreign_keys=ON")

    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine)
    return factory()


def _add_rule(db: Session, rule_id: str, bucket: str, cap_percent: float,
              academic_year: str = "2026-27", level: str = "UG",
              eligible: list[str] | None = None) -> RuleVersion:
    if not db.query(Rule).filter(Rule.id == rule_id).first():
        db.add(Rule(id=rule_id, current_version=1))
    rv = RuleVersion(
        id=str(uuid4()),
        rule_id=rule_id,
        version=1,
        academic_year=academic_year,
        programme_level=json.dumps([level]),
        domain="ALL",
        state="ALL",
        institution_type="ALL",
        bucket=bucket,
        cap_basis="PERCENT_OF_INTAKE",
        cap_percent=cap_percent,
        eligible_categories=json.dumps(eligible or []),
        source_document="AICTE Handbook (Illustrative)",
        source_clause="Illustrative: to be confirmed against AICTE rules",
        status="active",
        enabled=True,
        approvals=json.dumps([]),
        proposed_at=datetime.now(timezone.utc),
    )
    db.add(rv)
    db.commit()
    return rv


def _add_course(db: Session, institution_id: str, course_id: str,
                intake: int = 240, academic_year: str = "2026-27",
                level: str = "UG", domain: str = "Engineering") -> CourseApproval:
    if not db.query(Institution).filter(Institution.id == institution_id).first():
        db.add(Institution(
            id=institution_id, name=f"Test Inst {institution_id}",
            region="Test", state="ALL", city="Test", type="Private",
        ))
    c = CourseApproval(
        id=course_id, institution_id=institution_id,
        name="B.Tech CSE", level=level, domain=domain,
        academic_year=academic_year, approved_intake=intake,
    )
    db.add(c)
    db.commit()
    return c


def _admit(db: Session, course_id: str, n: int, seat_category: str,
           nationality: str = "INDIAN") -> None:
    for _ in range(n):
        db.add(AdmissionEvent(
            id=str(uuid4()),
            student_id=str(uuid4()),
            course_approval_id=course_id,
            seat_category=seat_category,
            event_type="ADMIT",
            admission_round="ROUND_1",
            entry_type="REGULAR",
            nationality_status=nationality,
            event_time=datetime(2026, 7, 1, tzinfo=timezone.utc),
        ))
    db.commit()


def _withdraw(db: Session, course_id: str, student_id: str) -> None:
    db.add(AdmissionEvent(
        id=str(uuid4()),
        student_id=student_id,
        course_approval_id=course_id,
        seat_category="OCI_FN_EXTRA",
        event_type="WITHDRAW",
        admission_round="ROUND_1",
        entry_type="REGULAR",
        nationality_status="FOREIGN",
        event_time=datetime(2026, 9, 1, tzinfo=timezone.utc),
    ))
    db.commit()


def run_regression_tests() -> list[dict[str, Any]]:
    """Run S1–S5, S14, S18 regression checks and return results."""
    results = []
    as_of = date(2026, 10, 1)

    def _run(label: str, expected: str, fn) -> None:
        db = _build_session()
        try:
            actual = fn(db)
            results.append({
                "scenario": label,
                "expected": expected,
                "actual": actual,
                "pass": actual == expected,
            })
        except Exception as exc:
            results.append({
                "scenario": label,
                "expected": expected,
                "actual": f"ERROR: {exc}",
                "pass": False,
            })
        finally:
            db.close()

    # S1 — 276 admitted (lawful max), simple counter ALARM, Seat-Ledger OK
    def _s1(db):
        _add_rule(db, "SN-A", "OCI_FN_EXTRA", 10.0)
        _add_rule(db, "SN-B", "CIWGC_EXTRA", 5.0)
        _add_course(db, "INST-S1", "CRS-S1", intake=240)
        _admit(db, "CRS-S1", 240, "REGULAR")
        _admit(db, "CRS-S1", 24, "OCI_FN_EXTRA", "FOREIGN")
        _admit(db, "CRS-S1", 12, "CIWGC_EXTRA", "FOREIGN")
        reconcile(db, "CRS-S1")
        res = evaluate(db, "CRS-S1", as_of)
        return res.status
    _run("S1: Lawful 276 → Seat-Ledger", "OK", _s1)

    # S2 — 5 domestic students in OCI_FN_EXTRA bucket → C3 flag
    def _s2(db):
        _add_rule(db, "SN-A", "OCI_FN_EXTRA", 10.0)
        _add_rule(db, "SN-B", "CIWGC_EXTRA", 5.0)
        _add_course(db, "INST-S2", "CRS-S2", intake=240)
        _admit(db, "CRS-S2", 240, "REGULAR")
        _admit(db, "CRS-S2", 19, "OCI_FN_EXTRA", "FOREIGN")
        _admit(db, "CRS-S2", 5, "OCI_FN_EXTRA", "INDIAN")  # C3: domestic in extra
        _admit(db, "CRS-S2", 12, "CIWGC_EXTRA", "FOREIGN")
        reconcile(db, "CRS-S2")
        res = evaluate(db, "CRS-S2", as_of)
        checks = [f.check for f in res.flags]
        return "FLAG:C3" if "C3" in checks else res.status
    _run("S2: Domestic in OCI/FN extra → C3", "FLAG:C3", _s2)

    # S3 — 282 admitted (6 over lawful max 276) → C2 flag
    def _s3(db):
        _add_rule(db, "SN-A", "OCI_FN_EXTRA", 10.0)
        _add_rule(db, "SN-B", "CIWGC_EXTRA", 5.0)
        _add_course(db, "INST-S3", "CRS-S3", intake=240)
        _admit(db, "CRS-S3", 246, "REGULAR")  # includes 6 NRI_IN
        _admit(db, "CRS-S3", 24, "OCI_FN_EXTRA", "FOREIGN")
        _admit(db, "CRS-S3", 12, "CIWGC_EXTRA", "FOREIGN")
        reconcile(db, "CRS-S3")
        res = evaluate(db, "CRS-S3", as_of)
        checks = [f.check for f in res.flags]
        return "FLAG:C2" if "C2" in checks else res.status
    _run("S3: 282 admitted (over max 276) → C2", "FLAG:C2", _s3)

    # S4 — EWS students, draft rule → RULE_NOT_CONFIRMED
    def _s4(db):
        from app.models.rule import Rule, RuleVersion
        if not db.query(Rule).filter(Rule.id == "EWS-S4").first():
            db.add(Rule(id="EWS-S4", current_version=1))
        db.add(RuleVersion(
            id=str(uuid4()), rule_id="EWS-S4", version=1,
            academic_year="2026-27", programme_level=json.dumps(["UG"]),
            domain="ALL", state="ALL", institution_type="ALL",
            bucket="EWS", cap_basis="PERCENT_OF_INTAKE", cap_percent=10.0,
            eligible_categories=json.dumps([]),
            source_document="AICTE (Illustrative)",
            source_clause="Draft rule (Illustrative)",
            status="draft", enabled=False,
            approvals=json.dumps([]),
            proposed_at=datetime.now(timezone.utc),
        ))
        db.commit()
        _add_course(db, "INST-S4", "CRS-S4", intake=240)
        _admit(db, "CRS-S4", 230, "REGULAR")
        _admit(db, "CRS-S4", 10, "EWS")
        reconcile(db, "CRS-S4")
        res = evaluate(db, "CRS-S4", as_of)
        return res.status
    _run("S4: EWS with draft rule → RULE_NOT_CONFIRMED", "RULE_NOT_CONFIRMED", _s4)

    # S5 — approve EWS rule → re-evaluate → OK
    def _s5(db):
        from app.services.rules_service import approve_rule_version, activate_rule_version, submit_for_review
        if not db.query(Rule).filter(Rule.id == "EWS-S5").first():
            db.add(Rule(id="EWS-S5", current_version=1))
        rv = RuleVersion(
            id=str(uuid4()), rule_id="EWS-S5", version=1,
            academic_year="2026-27", programme_level=json.dumps(["UG"]),
            domain="ALL", state="ALL", institution_type="ALL",
            bucket="EWS", cap_basis="PERCENT_OF_INTAKE", cap_percent=10.0,
            eligible_categories=json.dumps([]),
            source_document="AICTE EWS Rules (Illustrative)",
            source_clause="Para 5 (Illustrative: to be confirmed against AICTE rules)",
            status="pending_review", enabled=False,
            approvals=json.dumps([{"by": "proposer@test", "role": "proposer",
                                   "at": datetime.now(timezone.utc).isoformat()}]),
            proposed_at=datetime.now(timezone.utc),
        )
        db.add(rv)
        db.commit()
        rv = approve_rule_version(db, rv, "approver@test")
        rv = activate_rule_version(db, rv, as_of)
        _add_course(db, "INST-S5", "CRS-S5", intake=240)
        _admit(db, "CRS-S5", 216, "REGULAR")
        _admit(db, "CRS-S5", 24, "EWS")
        reconcile(db, "CRS-S5")
        res = evaluate(db, "CRS-S5", as_of)
        return res.status
    _run("S5: Approve EWS rule → re-evaluate → OK", "OK", _s5)

    # S14 — withdrawal frees seat → OK
    def _s14(db):
        _add_rule(db, "SN-A", "OCI_FN_EXTRA", 10.0)
        _add_rule(db, "SN-B", "CIWGC_EXTRA", 5.0)
        _add_course(db, "INST-S14", "CRS-S14", intake=240)
        _admit(db, "CRS-S14", 204, "REGULAR")
        _admit(db, "CRS-S14", 12, "CIWGC_EXTRA", "FOREIGN")

        # Admit 24 OCI (at cap), then withdraw 3 → 21 left ≤ 24
        oci_ids = [str(uuid4()) for _ in range(24)]
        for sid in oci_ids:
            db.add(AdmissionEvent(
                id=str(uuid4()), student_id=sid,
                course_approval_id="CRS-S14",
                seat_category="OCI_FN_EXTRA",
                event_type="ADMIT", admission_round="ROUND_1",
                entry_type="REGULAR", nationality_status="FOREIGN",
                event_time=datetime(2026, 7, 1, tzinfo=timezone.utc),
            ))
        db.commit()
        for sid in oci_ids[:3]:
            _withdraw(db, "CRS-S14", sid)
        reconcile(db, "CRS-S14")
        res = evaluate(db, "CRS-S14", as_of)
        return res.status
    _run("S14: Withdrawal frees OCI seat → OK", "OK", _s14)

    # S18 — rule change → new Evaluation row; old row keeps old hash
    def _s18(db):
        _add_rule(db, "SN-A-S18", "OCI_FN_EXTRA", 10.0)
        _add_rule(db, "SN-B-S18", "CIWGC_EXTRA", 5.0)
        _add_course(db, "INST-S18", "CRS-S18", intake=240)
        _admit(db, "CRS-S18", 240, "REGULAR")
        _admit(db, "CRS-S18", 24, "OCI_FN_EXTRA", "FOREIGN")
        _admit(db, "CRS-S18", 12, "CIWGC_EXTRA", "FOREIGN")
        reconcile(db, "CRS-S18")
        res1 = evaluate(db, "CRS-S18", as_of)
        old_hash = res1.rule_set_hash

        # Add a new rule (changes the rule set hash)
        _add_rule(db, "EWS-S18", "EWS", 10.0)
        res2 = evaluate(db, "CRS-S18", as_of)
        new_hash = res2.rule_set_hash

        if old_hash == new_hash:
            return "ERROR: hash unchanged"

        # Check old Evaluation still has original hash
        from app.models.evaluation import Evaluation
        evals = db.query(Evaluation).filter(
            Evaluation.course_approval_id == "CRS-S18"
        ).order_by(Evaluation.evaluated_at).all()
        if len(evals) < 2:
            return f"ERROR: only {len(evals)} evaluation rows"
        if evals[0].rule_set_hash != old_hash:
            return "ERROR: old evaluation hash mutated"
        if evals[1].rule_set_hash != new_hash:
            return "ERROR: new evaluation hash wrong"
        return "OK"
    _run("S18: Rule change preserves old Evaluation hash", "OK", _s18)

    return results
