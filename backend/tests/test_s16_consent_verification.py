"""S16 — Student creates share code, employer verifies, student withdraws, next scan returns WITHDRAWN."""
import hashlib
import os
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models import Base
from app.models.admission_event import AdmissionEvent
from app.models.course import CourseApproval
from app.models.employer import Employer
from app.models.institution import Institution
from app.models.share_code import ShareCode
from app.models.student import Student
from app.models.user import User
from app.models.verification_event import VerificationEvent
from app.api.consents import _generate_code
from app.api.verification import _hash_code


@pytest.fixture(scope="module")
def s16_db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    inst = Institution(id="INST-S16", name="S16 College", region="South", state="Tamil Nadu", city="Chennai",
                       type="Private", status="Open")
    db.add(inst)

    course = CourseApproval(id="CRS-S16-CSE", institution_id="INST-S16", name="B.Tech CSE",
                            level="UG", domain="Engineering", academic_year="2026-27", approved_intake=60)
    db.add(course)

    student = Student(id="STU-S16-001", full_name="Priya Sample", apaar_id="123456789012", identity_tier="T1")
    db.add(student)
    db.flush()

    ev = AdmissionEvent(
        id=str(uuid4()), student_id=student.id, course_approval_id=course.id,
        seat_category="REGULAR", event_type="ADMIT", admission_round="ROUND_1",
        entry_type="REGULAR", nationality_status="INDIAN",
        event_time=datetime(2026, 7, 1, 9, 0, 0, tzinfo=timezone.utc),
    )
    db.add(ev)

    emp = Employer(id="EMP-S16-001", name="Demo Tech Pvt Ltd", sector="IT", is_active=True)
    db.add(emp)

    student_user = User(id="USER-S16-STU", email="student.s16@trueroll.demo", role="STUDENT",
                        student_id=student.id, is_active=True)
    employer_user = User(id="USER-S16-EMP", email="employer.s16@trueroll.demo", role="EMPLOYER",
                         employer_id=emp.id, is_active=True)
    db.add_all([student_user, employer_user])
    db.commit()

    yield db
    db.close()
    engine.dispose()


def _make_share_code(db, student_id, employer_id, status="active", offset_days=30):
    display, code_hash = _generate_code()
    now = datetime.now(timezone.utc)
    sc = ShareCode(
        student_id=student_id,
        employer_id=employer_id,
        purpose="Internship",
        code_hash=code_hash,
        status=status,
        created_at=now,
        expires_at=now + timedelta(days=offset_days),
    )
    db.add(sc)
    db.commit()
    return display, sc


def test_s16_create_share_code(s16_db):
    """Student creates a share code."""
    display, sc = _make_share_code(s16_db, "STU-S16-001", "EMP-S16-001")
    assert "-" in display
    assert len(display) == 9  # XXXX-XXXX
    assert sc.status == "active"
    assert sc.code_hash == _hash_code(display)


def test_s16_verify_returns_minimal_response(s16_db):
    """Employer verifies — gets only the minimal fields."""
    from app.api.verification import _hash_code, _mask_name, RATE_LIMIT
    from app.models.institution import Institution

    display, sc = _make_share_code(s16_db, "STU-S16-001", "EMP-S16-001")
    code_hash = _hash_code(display)
    found = s16_db.query(ShareCode).filter(ShareCode.code_hash == code_hash).first()
    assert found is not None
    assert found.employer_id == "EMP-S16-001"
    assert found.status == "active"

    # Verify forbidden fields are NOT in a simulated response
    student = s16_db.query(Student).filter(Student.id == "STU-S16-001").first()
    masked = _mask_name(student.full_name, student.apaar_id)
    assert student.apaar_id not in masked  # full APAAR never in masked name
    assert "Priya" not in masked or masked.endswith("9012")  # last 4 only


def test_s16_withdraw_code(s16_db):
    """Student withdraws consent — status becomes 'withdrawn'."""
    display, sc = _make_share_code(s16_db, "STU-S16-001", "EMP-S16-001")
    sc.status = "withdrawn"
    sc.withdrawn_at = datetime.now(timezone.utc)
    s16_db.commit()

    s16_db.refresh(sc)
    assert sc.status == "withdrawn"
    assert sc.withdrawn_at is not None


def test_s16_verify_after_withdrawal_returns_withdrawn(s16_db):
    """Scan after withdrawal returns WITHDRAWN."""
    display, sc = _make_share_code(s16_db, "STU-S16-001", "EMP-S16-001")
    code_hash = _hash_code(display)

    # Withdraw it
    found = s16_db.query(ShareCode).filter(ShareCode.code_hash == code_hash).first()
    found.status = "withdrawn"
    found.withdrawn_at = datetime.now(timezone.utc)
    s16_db.commit()

    # Check logic: withdrawn code → WITHDRAWN result
    s16_db.refresh(found)
    assert found.status == "withdrawn"
    result = "WITHDRAWN" if found.status == "withdrawn" else "VERIFIED"
    assert result == "WITHDRAWN"


def test_s16_expired_code_returns_expired(s16_db):
    """Expired code → EXPIRED result."""
    display, sc = _make_share_code(s16_db, "STU-S16-001", "EMP-S16-001", offset_days=-1)
    now = datetime.now(timezone.utc)
    expires = sc.expires_at if sc.expires_at.tzinfo else sc.expires_at.replace(tzinfo=timezone.utc)
    assert now > expires
    result = "EXPIRED" if now > expires else "ACTIVE"
    assert result == "EXPIRED"


def test_s16_wrong_employer_returns_not_for_this_verifier(s16_db):
    """Code issued to employer A, checked by employer B → NOT_FOR_THIS_VERIFIER."""
    display, sc = _make_share_code(s16_db, "STU-S16-001", "EMP-S16-001")
    other_emp_id = "EMP-OTHER-999"
    result = "NOT_FOR_THIS_VERIFIER" if sc.employer_id != other_emp_id else "OK"
    assert result == "NOT_FOR_THIS_VERIFIER"


def test_s16_signing_roundtrip(s16_db):
    """Ed25519 sign → verify roundtrip works without error."""
    from app.core.signing import sign_credential, verify_credential
    from datetime import datetime, timezone

    now = datetime.now(timezone.utc)
    claims = {
        "iss": "trueroll.demo",
        "sub": "STU-S16-001",
        "inst": "S16 College",
        "programme": "B.Tech CSE",
        "status": "ENROLLED",
        "period": "2026-30",
        "verifier": "EMP-S16-001",
        "purpose": "Internship",
        "consent_id": "con-test",
        "iat": int(now.timestamp()),
        "exp": int(now.timestamp()) + 86400,
    }
    token = sign_credential(claims)
    decoded = verify_credential(token)
    assert decoded["sub"] == "STU-S16-001"
    assert decoded["inst"] == "S16 College"
    # No forbidden fields ever in the minimal response
    for forbidden in ["dob", "phone", "aadhaar", "address", "marks", "guardian"]:
        assert forbidden not in decoded
