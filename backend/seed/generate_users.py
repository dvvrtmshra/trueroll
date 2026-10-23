"""M7 — Generate all demo users per spec Section 5.1."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.models.user import User

DEMO_USERS = [
    # AICTE Officers
    {"id": "demo-nat-001", "email": "officer.national@trueroll.demo",
     "role": "NATIONAL_OFFICER", "region": None, "institution_id": None,
     "student_id": None, "employer_id": None, "is_active": True},
    {"id": "demo-reg-north-001", "email": "officer.north@trueroll.demo",
     "role": "REGIONAL_OFFICER", "region": "North", "institution_id": None,
     "student_id": None, "employer_id": None, "is_active": True},
    {"id": "demo-reg-south-001", "email": "officer.south@trueroll.demo",
     "role": "REGIONAL_OFFICER", "region": "South", "institution_id": None,
     "student_id": None, "employer_id": None, "is_active": True},
    {"id": "demo-reg-east-001", "email": "officer.east@trueroll.demo",
     "role": "REGIONAL_OFFICER", "region": "East", "institution_id": None,
     "student_id": None, "employer_id": None, "is_active": True},
    {"id": "demo-reg-west-001", "email": "officer.west@trueroll.demo",
     "role": "REGIONAL_OFFICER", "region": "West", "institution_id": None,
     "student_id": None, "employer_id": None, "is_active": True},
    # Rules
    {"id": "demo-ro-001", "email": "rules.owner@trueroll.demo",
     "role": "RULES_OWNER", "region": None, "institution_id": None,
     "student_id": None, "employer_id": None, "is_active": True},
    {"id": "demo-ra-001", "email": "rules.approver@trueroll.demo",
     "role": "RULES_APPROVER", "region": None, "institution_id": None,
     "student_id": None, "employer_id": None, "is_active": True},
    # College Admins — hero colleges
    {"id": "demo-ca-001", "email": "admin.inst0001@trueroll.demo",
     "role": "COLLEGE_ADMIN", "region": "North", "institution_id": "INST-0001",
     "student_id": None, "employer_id": None, "is_active": True},
    {"id": "demo-ca-002", "email": "admin.inst0002@trueroll.demo",
     "role": "COLLEGE_ADMIN", "region": "South", "institution_id": "INST-0002",
     "student_id": None, "employer_id": None, "is_active": True},
    {"id": "demo-ca-003", "email": "admin.inst0003@trueroll.demo",
     "role": "COLLEGE_ADMIN", "region": "West", "institution_id": "INST-0003",
     "student_id": None, "employer_id": None, "is_active": True},
    {"id": "demo-ca-004", "email": "admin.inst0004@trueroll.demo",
     "role": "COLLEGE_ADMIN", "region": "East", "institution_id": "INST-0004",
     "student_id": None, "employer_id": None, "is_active": True},
    {"id": "demo-ca-005", "email": "admin.inst0005@trueroll.demo",
     "role": "COLLEGE_ADMIN", "region": "North", "institution_id": "INST-0005",
     "student_id": None, "employer_id": None, "is_active": True},
    {"id": "demo-ca-006", "email": "admin.inst0006@trueroll.demo",
     "role": "COLLEGE_ADMIN", "region": "South", "institution_id": "INST-0006",
     "student_id": None, "employer_id": None, "is_active": True},
    # Students
    {"id": "demo-st-t1", "email": "student.verified@trueroll.demo",
     "role": "STUDENT", "region": None, "institution_id": None,
     "student_id": "STU-00001", "employer_id": None, "is_active": True},
    {"id": "demo-st-t2", "email": "student.unverified@trueroll.demo",
     "role": "STUDENT", "region": None, "institution_id": None,
     "student_id": "STU-00002", "employer_id": None, "is_active": True},
    {"id": "demo-st-t3", "email": "student.noid@trueroll.demo",
     "role": "STUDENT", "region": None, "institution_id": None,
     "student_id": "STU-00003", "employer_id": None, "is_active": True},
    {"id": "demo-st-t4", "email": "student.foreign@trueroll.demo",
     "role": "STUDENT", "region": None, "institution_id": None,
     "student_id": "STU-00004", "employer_id": None, "is_active": True},
    {"id": "demo-st-grad", "email": "student.graduating@trueroll.demo",
     "role": "STUDENT", "region": None, "institution_id": None,
     "student_id": "STU-00005", "employer_id": None, "is_active": True},
    # Employers
    {"id": "demo-em-001", "email": "employer.demotech@trueroll.demo",
     "role": "EMPLOYER", "region": None, "institution_id": None,
     "student_id": None, "employer_id": "EMP-0001", "is_active": True},
    {"id": "demo-em-002", "email": "employer.acme@trueroll.demo",
     "role": "EMPLOYER", "region": None, "institution_id": None,
     "student_id": None, "employer_id": "EMP-0002", "is_active": True},
    # Auditor and Admin
    {"id": "demo-aud-001", "email": "auditor@trueroll.demo",
     "role": "AUDITOR", "region": None, "institution_id": None,
     "student_id": None, "employer_id": None, "is_active": True},
    {"id": "demo-sys-001", "email": "sysadmin@trueroll.demo",
     "role": "SYSTEM_ADMIN", "region": None, "institution_id": None,
     "student_id": None, "employer_id": None, "is_active": True},
]


def run(db) -> None:
    added = 0
    for u in DEMO_USERS:
        existing = db.query(User).filter(User.email == u["email"]).first()
        if not existing:
            db.add(User(**u))
            added += 1
    db.commit()
    print(f"[gen_users] {added} new demo users")
