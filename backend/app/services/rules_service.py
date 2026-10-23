"""Rules Service — scope lookup, lifecycle gates, governance."""
import hashlib
import json
from datetime import date, datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.models.rule import Rule, RuleVersion
from app.models.institution import Institution
from app.models.course import CourseApproval


def _parse_levels(rv: RuleVersion) -> list[str]:
    try:
        return json.loads(rv.programme_level)
    except Exception:
        return [rv.programme_level]


def _scope_matches(rv: RuleVersion, course: CourseApproval, institution: Institution, as_of: date) -> bool:
    if rv.academic_year != course.academic_year:
        return False
    if course.level not in _parse_levels(rv):
        return False
    if rv.domain not in ("ALL", course.domain):
        return False
    if rv.state not in ("ALL", institution.state):
        return False
    if rv.institution_type not in ("ALL", institution.type):
        return False
    if rv.effective_from and as_of < rv.effective_from:
        return False
    if rv.effective_to and as_of > rv.effective_to:
        return False
    return True


def active_rules_for(
    db: Session,
    course: CourseApproval,
    institution: Institution,
    as_of: date,
) -> list[RuleVersion]:
    """Return all active, enabled, in-scope RuleVersions for a given course."""
    candidates = db.query(RuleVersion).filter(
        RuleVersion.status == "active",
        RuleVersion.enabled == True,  # noqa: E712
        RuleVersion.academic_year == course.academic_year,
    ).all()
    return [rv for rv in candidates if _scope_matches(rv, course, institution, as_of)]


def draft_or_pending_rules_for(
    db: Session,
    course: CourseApproval,
    institution: Institution,
    as_of: date,
) -> list[RuleVersion]:
    """Return non-active (draft/pending) rules that would otherwise match scope."""
    candidates = db.query(RuleVersion).filter(
        RuleVersion.status.in_(["draft", "pending_review"]),
        RuleVersion.academic_year == course.academic_year,
    ).all()
    return [rv for rv in candidates if _scope_matches(rv, course, institution, as_of)]


def rule_set_hash(rules: list[RuleVersion]) -> str:
    ids = sorted(rv.id for rv in rules)
    return hashlib.sha256("|".join(ids).encode()).hexdigest()


# ── Lifecycle ──────────────────────────────────────────────────────────────────

def _require_role(user: dict, *roles: str) -> None:
    if user.get("role") not in roles:
        raise PermissionError(f"Requires one of {roles}")


def propose_rule(
    db: Session,
    *,
    rule_id: str,
    version: int,
    academic_year: str,
    programme_level: list[str],
    domain: str,
    state: str,
    institution_type: str,
    bucket: str,
    cap_basis: str,
    cap_percent: Optional[float],
    cap_fixed: Optional[int],
    eligible_categories: list[str],
    source_document: str,
    source_clause: str,
    source_url: Optional[str],
    effective_from: Optional[date],
    effective_to: Optional[date],
    proposer_id: str,
    proposer_email: str,
) -> RuleVersion:
    if not source_document or source_document.strip() == "":
        raise ValueError("source_document is required to propose a rule")
    if not source_clause or source_clause.strip() == "":
        raise ValueError("source_clause is required to propose a rule")

    # Ensure parent Rule exists
    rule = db.query(Rule).filter(Rule.id == rule_id).first()
    if not rule:
        rule = Rule(id=rule_id, current_version=1)
        db.add(rule)

    from uuid import uuid4
    rv = RuleVersion(
        id=str(uuid4()),
        rule_id=rule_id,
        version=version,
        academic_year=academic_year,
        programme_level=json.dumps(programme_level),
        domain=domain,
        state=state,
        institution_type=institution_type,
        bucket=bucket,
        cap_basis=cap_basis,
        cap_percent=cap_percent,
        cap_fixed=cap_fixed,
        eligible_categories=json.dumps(eligible_categories),
        source_document=source_document,
        source_clause=source_clause,
        source_url=source_url,
        effective_from=effective_from,
        effective_to=effective_to,
        status="draft",
        enabled=False,
        approvals=json.dumps([{"by": proposer_email, "role": "proposer", "at": datetime.now(timezone.utc).isoformat()}]),
        proposed_by=proposer_id,
        proposed_at=datetime.now(timezone.utc),
    )
    db.add(rv)
    db.commit()
    db.refresh(rv)
    return rv


def submit_for_review(db: Session, rv: RuleVersion, submitter_email: str) -> RuleVersion:
    if rv.status != "draft":
        raise ValueError(f"Rule is {rv.status}, not draft")
    if not rv.source_document or rv.source_document == "TO BE CONFIRMED":
        raise ValueError("source_document required to leave Draft")
    if not rv.source_clause or rv.source_clause == "TO BE CONFIRMED":
        raise ValueError("source_clause required to leave Draft")
    rv.status = "pending_review"
    db.commit()
    db.refresh(rv)
    return rv


def approve_rule_version(db: Session, rv: RuleVersion, approver_email: str) -> RuleVersion:
    if rv.status != "pending_review":
        raise ValueError(f"Rule is {rv.status}, not pending_review")
    existing = json.loads(rv.approvals)
    for a in existing:
        if a.get("by") == approver_email:
            raise ValueError("Proposer cannot approve their own rule")
    existing.append({"by": approver_email, "role": "approver", "at": datetime.now(timezone.utc).isoformat()})
    rv.approvals = json.dumps(existing)
    rv.status = "approved"
    db.commit()
    db.refresh(rv)
    return rv


def activate_rule_version(db: Session, rv: RuleVersion, as_of: date) -> RuleVersion:
    if rv.status != "approved":
        raise ValueError(f"Rule is {rv.status}, not approved")
    rv.status = "active"
    rv.enabled = True
    # Retire any older version of the same rule with the same scope
    older = db.query(RuleVersion).filter(
        RuleVersion.rule_id == rv.rule_id,
        RuleVersion.academic_year == rv.academic_year,
        RuleVersion.status == "active",
        RuleVersion.id != rv.id,
    ).all()
    for old in older:
        old.status = "retired"
        old.enabled = False
    db.commit()
    db.refresh(rv)
    return rv
