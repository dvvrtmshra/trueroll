"""M2 — Seed the illustrative seat rule book."""
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.models.rule import Rule, RuleVersion

ILLUSTRATIVE_DOC = "Illustrative: to be confirmed against AICTE rules"
ILLUSTRATIVE_CLAUSE = "TO BE CONFIRMED"

_APPROVALS_TWO = (
    '[{"by":"rules.owner@trueroll.demo","role":"proposer","at":"2026-06-01"},'
    '{"by":"rules.approver@trueroll.demo","role":"approver","at":"2026-06-15"}]'
)
_APPROVALS_ONE = (
    '[{"by":"rules.owner@trueroll.demo","role":"proposer","at":"2026-06-01"}]'
)
_APPROVALS_NONE = "[]"

RULES: list[dict] = [
    # Rule canonical IDs
    {"id": "NRI-IN", "current_version": 1},
    {"id": "SN-A", "current_version": 2},
    {"id": "SN-B", "current_version": 1},
    {"id": "SN-PG", "current_version": 1},
    {"id": "SN-MGT", "current_version": 1},
    {"id": "EWS-ST", "current_version": 1},
]

VERSIONS: list[dict] = [
    # NRI-IN v1 — active
    {
        "id": "rv-nri-in-v1",
        "rule_id": "NRI-IN",
        "version": 1,
        "academic_year": "2026-27",
        "programme_level": '["UG"]',
        "domain": "Engineering and Technology",
        "state": "ALL",
        "institution_type": "ALL",
        "bucket": "NRI_IN",
        "cap_basis": "approved_intake",
        "cap_percent": 5.0,
        "cap_fixed": None,
        "eligible_categories": '["NRI"]',
        "source_document": ILLUSTRATIVE_DOC,
        "source_clause": ILLUSTRATIVE_CLAUSE,
        "source_url": None,
        "effective_from": date(2026, 7, 1),
        "effective_to": None,
        "status": "active",
        "enabled": True,
        "approvals": _APPROVALS_TWO,
        "test_suite": "seat_ledger_regression_v3",
        "proposed_by": None,
    },
    # SN-A v1 — retired (2025-26)
    {
        "id": "rv-sna-v1",
        "rule_id": "SN-A",
        "version": 1,
        "academic_year": "2025-26",
        "programme_level": '["UG"]',
        "domain": "Engineering and Technology",
        "state": "ALL",
        "institution_type": "ALL",
        "bucket": "OCI_FN_EXTRA",
        "cap_basis": "approved_intake",
        "cap_percent": 10.0,
        "cap_fixed": None,
        "eligible_categories": '["FN","OCI","PIO"]',
        "source_document": ILLUSTRATIVE_DOC,
        "source_clause": ILLUSTRATIVE_CLAUSE,
        "source_url": None,
        "effective_from": date(2025, 7, 1),
        "effective_to": date(2026, 6, 30),
        "status": "retired",
        "enabled": False,
        "approvals": _APPROVALS_TWO,
        "test_suite": "seat_ledger_regression_v3",
        "proposed_by": None,
    },
    # SN-A v2 — active (2026-27)
    {
        "id": "rv-sna-v2",
        "rule_id": "SN-A",
        "version": 2,
        "academic_year": "2026-27",
        "programme_level": '["UG"]',
        "domain": "Engineering and Technology",
        "state": "ALL",
        "institution_type": "ALL",
        "bucket": "OCI_FN_EXTRA",
        "cap_basis": "approved_intake",
        "cap_percent": 10.0,
        "cap_fixed": None,
        "eligible_categories": '["FN","OCI","PIO"]',
        "source_document": ILLUSTRATIVE_DOC,
        "source_clause": ILLUSTRATIVE_CLAUSE,
        "source_url": None,
        "effective_from": date(2026, 7, 1),
        "effective_to": None,
        "status": "active",
        "enabled": True,
        "approvals": _APPROVALS_TWO,
        "test_suite": "seat_ledger_regression_v3",
        "proposed_by": None,
    },
    # SN-B v1 — active (2026-27)
    {
        "id": "rv-snb-v1",
        "rule_id": "SN-B",
        "version": 1,
        "academic_year": "2026-27",
        "programme_level": '["UG"]',
        "domain": "Engineering and Technology",
        "state": "ALL",
        "institution_type": "ALL",
        "bucket": "CIWGC_EXTRA",
        "cap_basis": "approved_intake",
        "cap_percent": 5.0,
        "cap_fixed": None,
        "eligible_categories": '["CIWGC"]',
        "source_document": ILLUSTRATIVE_DOC,
        "source_clause": ILLUSTRATIVE_CLAUSE,
        "source_url": None,
        "effective_from": date(2026, 7, 1),
        "effective_to": None,
        "status": "active",
        "enabled": True,
        "approvals": _APPROVALS_TWO,
        "test_suite": "seat_ledger_regression_v3",
        "proposed_by": None,
    },
    # SN-PG v1 — pending approval
    {
        "id": "rv-snpg-v1",
        "rule_id": "SN-PG",
        "version": 1,
        "academic_year": "2026-27",
        "programme_level": '["PG"]',
        "domain": "Engineering and Technology",
        "state": "ALL",
        "institution_type": "ALL",
        "bucket": "INTL_PG_EXTRA",
        "cap_basis": "approved_intake",
        "cap_percent": 25.0,
        "cap_fixed": None,
        "eligible_categories": '["FN","OCI","PIO","CIWGC"]',
        "source_document": ILLUSTRATIVE_DOC,
        "source_clause": ILLUSTRATIVE_CLAUSE,
        "source_url": None,
        "effective_from": date(2026, 7, 1),
        "effective_to": None,
        "status": "pending_review",
        "enabled": False,
        "approvals": _APPROVALS_ONE,
        "test_suite": None,
        "proposed_by": None,
    },
    # SN-MGT v1 — pending approval
    {
        "id": "rv-snmgt-v1",
        "rule_id": "SN-MGT",
        "version": 1,
        "academic_year": "2026-27",
        "programme_level": '["MBA/PGDM","MCA","UG"]',
        "domain": "Management",
        "state": "ALL",
        "institution_type": "ALL",
        "bucket": "INTL_MGT_EXTRA",
        "cap_basis": "approved_intake",
        "cap_percent": 25.0,
        "cap_fixed": None,
        "eligible_categories": '["FN","OCI","PIO","CIWGC","NRI"]',
        "source_document": ILLUSTRATIVE_DOC,
        "source_clause": ILLUSTRATIVE_CLAUSE,
        "source_url": None,
        "effective_from": date(2026, 7, 1),
        "effective_to": None,
        "status": "pending_review",
        "enabled": False,
        "approvals": _APPROVALS_ONE,
        "test_suite": None,
        "proposed_by": None,
    },
    # EWS-ST v1 — draft, disabled (S4: unconfirmed rule)
    {
        "id": "rv-ewsst-v1",
        "rule_id": "EWS-ST",
        "version": 1,
        "academic_year": "2026-27",
        "programme_level": '["UG","Diploma"]',
        "domain": "Engineering and Technology",
        "state": "West Bengal",
        "institution_type": "ALL",
        "bucket": "EWS_EXTRA",
        "cap_basis": "approved_intake",
        "cap_percent": 10.0,
        "cap_fixed": None,
        "eligible_categories": '["EWS"]',
        "source_document": ILLUSTRATIVE_DOC,
        "source_clause": ILLUSTRATIVE_CLAUSE,
        "source_url": None,
        "effective_from": None,
        "effective_to": None,
        "status": "draft",
        "enabled": False,
        "approvals": _APPROVALS_NONE,
        "test_suite": None,
        "proposed_by": None,
    },
]


def run(db) -> None:
    if db.query(Rule).count() > 0:
        print("[gen_rules] Already seeded — skip")
        return

    for r in RULES:
        db.add(Rule(**r))

    for v in VERSIONS:
        db.add(RuleVersion(**v))

    db.commit()
    print(f"[gen_rules] {len(RULES)} rules, {len(VERSIONS)} versions")
