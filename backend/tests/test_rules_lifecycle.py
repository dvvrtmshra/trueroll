"""Rules lifecycle and governance tests."""
import json
from datetime import date, datetime, timezone

import pytest
from sqlalchemy.orm import Session

from app.models.rule import Rule, RuleVersion
from app.services.rules_service import (
    propose_rule,
    submit_for_review,
    approve_rule_version,
    activate_rule_version,
)


def test_propose_requires_source(db):
    """Cannot propose a rule without source_document and source_clause."""
    with pytest.raises(ValueError, match="source_document"):
        propose_rule(
            db,
            rule_id="TEST-RL-X",
            version=1,
            academic_year="2026-27",
            programme_level=["UG"],
            domain="ALL",
            state="ALL",
            institution_type="ALL",
            bucket="OCI_FN_EXTRA",
            cap_basis="PERCENT_OF_INTAKE",
            cap_percent=10.0,
            cap_fixed=None,
            eligible_categories=["FN"],
            source_document="",
            source_clause="Para 1",
            source_url=None,
            effective_from=None,
            effective_to=None,
            proposer_id="user-001",
            proposer_email="proposer@test",
        )


def test_propose_creates_draft(db):
    """propose_rule creates a RuleVersion in draft status."""
    rv = propose_rule(
        db,
        rule_id="TEST-RL-PROPOSE",
        version=1,
        academic_year="2026-27",
        programme_level=["UG"],
        domain="ALL",
        state="ALL",
        institution_type="ALL",
        bucket="CIWGC_EXTRA",
        cap_basis="PERCENT_OF_INTAKE",
        cap_percent=5.0,
        cap_fixed=None,
        eligible_categories=["CIWGC"],
        source_document="AICTE Handbook (Illustrative)",
        source_clause="Para 3 (Illustrative: to be confirmed against AICTE rules)",
        source_url=None,
        effective_from=None,
        effective_to=None,
        proposer_id="user-propose",
        proposer_email="proposer@trueroll.test",
    )
    assert rv.status == "draft"
    assert rv.enabled is False
    approvals = json.loads(rv.approvals)
    assert approvals[0]["role"] == "proposer"


def test_submit_for_review(db):
    """submit_for_review moves draft → pending_review."""
    rv = propose_rule(
        db,
        rule_id="TEST-RL-SUBMIT",
        version=1,
        academic_year="2026-27",
        programme_level=["UG"],
        domain="ALL",
        state="ALL",
        institution_type="ALL",
        bucket="OCI_FN_EXTRA",
        cap_basis="PERCENT_OF_INTAKE",
        cap_percent=10.0,
        cap_fixed=None,
        eligible_categories=["FN"],
        source_document="AICTE Handbook (Illustrative)",
        source_clause="Para 2 (Illustrative: to be confirmed against AICTE rules)",
        source_url=None,
        effective_from=None,
        effective_to=None,
        proposer_id="user-001",
        proposer_email="p@test",
    )
    rv = submit_for_review(db, rv, "p@test")
    assert rv.status == "pending_review"


def test_proposer_cannot_approve(db):
    """The person who proposed a rule cannot also approve it."""
    rv = propose_rule(
        db,
        rule_id="TEST-RL-SELFAPPROVE",
        version=1,
        academic_year="2026-27",
        programme_level=["UG"],
        domain="ALL",
        state="ALL",
        institution_type="ALL",
        bucket="EWS",
        cap_basis="PERCENT_OF_INTAKE",
        cap_percent=10.0,
        cap_fixed=None,
        eligible_categories=[],
        source_document="AICTE Handbook (Illustrative)",
        source_clause="Para 5 (Illustrative: to be confirmed against AICTE rules)",
        source_url=None,
        effective_from=None,
        effective_to=None,
        proposer_id="user-001",
        proposer_email="proposer@trueroll.test",
    )
    rv = submit_for_review(db, rv, "proposer@trueroll.test")
    with pytest.raises(ValueError, match="Proposer cannot approve"):
        approve_rule_version(db, rv, "proposer@trueroll.test")


def test_two_person_approval_activates(db):
    """A different approver can approve → approve → activate lifecycle."""
    rv = propose_rule(
        db,
        rule_id="TEST-RL-TWOPERS",
        version=1,
        academic_year="2026-27",
        programme_level=["UG"],
        domain="ALL",
        state="ALL",
        institution_type="ALL",
        bucket="CIWGC_EXTRA",
        cap_basis="PERCENT_OF_INTAKE",
        cap_percent=5.0,
        cap_fixed=None,
        eligible_categories=["CIWGC"],
        source_document="AICTE Handbook (Illustrative)",
        source_clause="Para 4 (Illustrative: to be confirmed against AICTE rules)",
        source_url=None,
        effective_from=None,
        effective_to=None,
        proposer_id="user-proposer",
        proposer_email="p1@trueroll.test",
    )
    rv = submit_for_review(db, rv, "p1@trueroll.test")
    rv = approve_rule_version(db, rv, "p2@trueroll.test")
    assert rv.status == "approved"
    rv = activate_rule_version(db, rv, date(2026, 10, 1))
    assert rv.status == "active"
    assert rv.enabled is True


def test_activate_retires_older_version(db):
    """Activating a new version retires the previous active version for the same rule+year."""
    rule_id = "TEST-RL-RETIRE"

    # Activate v1 manually (simulates already-active state)
    rule = Rule(id=rule_id, current_version=1)
    db.add(rule)
    rv1 = RuleVersion(
        id="RV-RETIRE-V1",
        rule_id=rule_id,
        version=1,
        academic_year="2025-26",        # isolated year — won't touch 2026-27 ledger tests
        programme_level=json.dumps(["UG"]),
        domain="ALL",
        state="ALL",
        institution_type="ALL",
        bucket="OCI_FN_EXTRA",
        cap_basis="PERCENT_OF_INTAKE",
        cap_percent=10.0,
        eligible_categories=json.dumps(["FN"]),
        source_document="AICTE (Illustrative)",
        source_clause="Para 1 (Illustrative: to be confirmed against AICTE rules)",
        status="active",
        enabled=True,
        approvals=json.dumps([]),
        proposed_at=datetime.now(timezone.utc),
    )
    db.add(rv1)
    db.commit()

    # Now propose and activate v2
    rv2 = propose_rule(
        db,
        rule_id=rule_id,
        version=2,
        academic_year="2025-26",        # must match v1 year for retirement to work
        programme_level=["UG"],
        domain="ALL",
        state="ALL",
        institution_type="ALL",
        bucket="OCI_FN_EXTRA",
        cap_basis="PERCENT_OF_INTAKE",
        cap_percent=12.0,
        cap_fixed=None,
        eligible_categories=["FN"],
        source_document="AICTE Update (Illustrative)",
        source_clause="Para 1B (Illustrative: to be confirmed against AICTE rules)",
        source_url=None,
        effective_from=None,
        effective_to=None,
        proposer_id="u1",
        proposer_email="a@trueroll.test",
    )
    rv2 = submit_for_review(db, rv2, "a@trueroll.test")
    rv2 = approve_rule_version(db, rv2, "b@trueroll.test")
    rv2 = activate_rule_version(db, rv2, date(2026, 10, 1))

    db.refresh(rv1)
    assert rv1.status == "retired"
    assert rv2.status == "active"
