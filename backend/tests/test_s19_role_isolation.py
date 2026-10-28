"""S19 — Role isolation: 403 when accessing cross-institution/region resources."""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.models.institution import Institution
from app.models.course import CourseApproval
from app.models.flag import Flag
from uuid import uuid4
from datetime import datetime, timezone


@pytest.fixture()
def two_colleges(db):
    for i in (1, 2):
        if not db.query(Institution).filter(Institution.id == f"ISO-INST-{i:02d}").first():
            db.add(Institution(
                id=f"ISO-INST-{i:02d}",
                name=f"Isolation College {i}",
                region="North" if i == 1 else "South",
                state="Delhi" if i == 1 else "Tamil Nadu",
                city="Delhi" if i == 1 else "Chennai",
                type="Private",
                status="Open",
            ))
        if not db.query(CourseApproval).filter(CourseApproval.id == f"ISO-COURSE-{i:02d}").first():
            db.add(CourseApproval(
                id=f"ISO-COURSE-{i:02d}",
                institution_id=f"ISO-INST-{i:02d}",
                name="B.Tech CSE",
                level="UG",
                domain="Engineering and Technology",
                academic_year="2026-27",
                approved_intake=120,
            ))
    db.commit()
    yield db


def _login(email: str) -> str:
    client = TestClient(app)
    resp = client.post("/auth/verify-otp", json={"email": email, "otp": "123456"})
    assert resp.status_code == 200, f"Login failed for {email!r}: {resp.text}"
    return resp.json()["access_token"]


def test_s19_college_admin_cannot_see_other_college(two_colleges):
    """COLLEGE_ADMIN gets 403/404 accessing an institution they don't own."""
    token = _login("admin.inst0001@trueroll.demo")
    client = TestClient(app)
    client.headers.update({"Authorization": f"Bearer {token}"})

    resp = client.get("/institutions/ISO-INST-02/dashboard")
    assert resp.status_code in (403, 404), f"Expected 403/404, got {resp.status_code}"


def test_s19_regional_officer_ledger_accessible(two_colleges):
    """NATIONAL_OFFICER can access any ledger course."""
    token = _login("officer.national@trueroll.demo")
    client = TestClient(app)
    client.headers.update({"Authorization": f"Bearer {token}"})

    resp = client.get("/ledger/course/ISO-COURSE-01")
    assert resp.status_code in (200, 404), f"Expected 200/404, got {resp.status_code}"


def test_s19_employer_cannot_access_admin(two_colleges):
    """EMPLOYER cannot access restricted admin endpoints."""
    token = _login("employer.demotech@trueroll.demo")
    client = TestClient(app)
    client.headers.update({"Authorization": f"Bearer {token}"})

    resp = client.get("/admin/jobs")
    assert resp.status_code == 403, f"Expected 403, got {resp.status_code}: {resp.text}"


def test_s19_student_cannot_access_flags(two_colleges):
    """STUDENT cannot access the flags queue."""
    token = _login("student.verified@trueroll.demo")
    client = TestClient(app)
    client.headers.update({"Authorization": f"Bearer {token}"})

    resp = client.get("/flags")
    assert resp.status_code == 403, f"Expected 403, got {resp.status_code}"


def test_s19_unauthenticated_returns_401():
    """Unauthenticated requests are rejected."""
    client = TestClient(app)
    resp = client.get("/flags")
    assert resp.status_code == 401
