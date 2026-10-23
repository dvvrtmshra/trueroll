"""M1 — Generate 48 fictional institutions and their courses."""
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from seed.common import (
    ACADEMIC_YEARS, DOMAINS, INST_TYPES, INTAKES,
    REGIONS, RNG, SEED, STATES_BY_REGION,
)
from app.models.institution import Institution
from app.models.course import CourseApproval

# Hero institutions — fixed per spec Section 10.1
HERO = [
    {
        "id": "INST-0001",
        "name": "Sample Institute of Technology",
        "region": "North",
        "state": "Delhi",
        "city": "New Delhi",
        "type": "Government",
        "status": "Open",
    },
    {
        "id": "INST-0002",
        "name": "Demo College of Engineering",
        "region": "South",
        "state": "Karnataka",
        "city": "Bengaluru",
        "type": "Private",
        "status": "Open",
    },
    {
        "id": "INST-0003",
        "name": "Model Institute of Engineering",
        "region": "West",
        "state": "Maharashtra",
        "city": "Pune",
        "type": "Autonomous",
        "status": "Open",
    },
    {
        "id": "INST-0004",
        "name": "Trial Institute of Technology",
        "region": "East",
        "state": "West Bengal",
        "city": "Kolkata",
        "type": "Private",
        "status": "Open",
    },
    {
        "id": "INST-0005",
        "name": "Example Institute of Management",
        "region": "North",
        "state": "Uttar Pradesh",
        "city": "Noida",
        "type": "Private",
        "status": "Open",
    },
    {
        "id": "INST-0006",
        "name": "Pilot College of Computer Applications",
        "region": "South",
        "state": "Tamil Nadu",
        "city": "Chennai",
        "type": "Autonomous",
        "status": "Open",
    },
]

# Hero courses — fixed for scenarios
HERO_COURSES: list[dict] = [
    # INST-0001: CSE 240 (main demo college, lawful 238 admitted)
    {"id": "CRS-0001-CSE", "institution_id": "INST-0001", "name": "B.Tech CSE",
     "level": "UG", "domain": "Engineering and Technology",
     "academic_year": "2026-27", "approved_intake": 240, "lateral_intake": 24},
    {"id": "CRS-0001-ECE", "institution_id": "INST-0001", "name": "B.Tech ECE",
     "level": "UG", "domain": "Engineering and Technology",
     "academic_year": "2026-27", "approved_intake": 120, "lateral_intake": 0},
    {"id": "CRS-0001-MTECH", "institution_id": "INST-0001", "name": "M.Tech CSE",
     "level": "PG", "domain": "Engineering and Technology",
     "academic_year": "2026-27", "approved_intake": 60, "lateral_intake": 0},
    # INST-0002: Engineering 240 (S2 — domestic in extra seats)
    {"id": "CRS-0002-CSE", "institution_id": "INST-0002", "name": "B.Tech CSE",
     "level": "UG", "domain": "Engineering and Technology",
     "academic_year": "2026-27", "approved_intake": 240, "lateral_intake": 0},
    {"id": "CRS-0002-MECH", "institution_id": "INST-0002", "name": "B.Tech Mechanical",
     "level": "UG", "domain": "Engineering and Technology",
     "academic_year": "2026-27", "approved_intake": 120, "lateral_intake": 0},
    # INST-0003: CSE 240 (S3 — 282 admitted)
    {"id": "CRS-0003-CSE", "institution_id": "INST-0003", "name": "B.Tech CSE",
     "level": "UG", "domain": "Engineering and Technology",
     "academic_year": "2026-27", "approved_intake": 240, "lateral_intake": 0},
    {"id": "CRS-0003-ECE", "institution_id": "INST-0003", "name": "B.Tech ECE",
     "level": "UG", "domain": "Engineering and Technology",
     "academic_year": "2026-27", "approved_intake": 120, "lateral_intake": 0},
    # INST-0004: Engineering with EWS (S4 — rule not confirmed)
    {"id": "CRS-0004-CSE", "institution_id": "INST-0004", "name": "B.Tech CSE",
     "level": "UG", "domain": "Engineering and Technology",
     "academic_year": "2026-27", "approved_intake": 180, "lateral_intake": 0},
    # INST-0005: Management (S5 — pending SN-MGT, S15 — anomaly)
    {"id": "CRS-0005-MBA", "institution_id": "INST-0005", "name": "MBA",
     "level": "MBA/PGDM", "domain": "Management",
     "academic_year": "2026-27", "approved_intake": 120, "lateral_intake": 0},
    {"id": "CRS-0005-BBA", "institution_id": "INST-0005", "name": "BBA",
     "level": "UG", "domain": "Management",
     "academic_year": "2026-27", "approved_intake": 60, "lateral_intake": 0},
    # INST-0006: Computer Applications (S6-S10)
    {"id": "CRS-0006-MCA", "institution_id": "INST-0006", "name": "MCA",
     "level": "MCA", "domain": "Computer Applications",
     "academic_year": "2026-27", "approved_intake": 60, "lateral_intake": 0},
    {"id": "CRS-0006-BCA", "institution_id": "INST-0006", "name": "BCA",
     "level": "UG", "domain": "Computer Applications",
     "academic_year": "2026-27", "approved_intake": 60, "lateral_intake": 0},
]

CITY_PREFIXES = [
    "Greenfield", "New", "Modern", "Central", "National", "State",
    "Progressive", "Advanced", "Premier", "Eastern", "Western", "Northern",
    "Southern", "Metro", "Capital", "District",
]

INST_SUFFIXES = [
    "Institute of Technology", "College of Engineering", "Institute of Engineering",
    "Technical College", "Engineering College", "College of Technology",
    "Polytechnic Institute", "Institute of Science and Technology",
]


def _gen_institution(rng: random.Random, idx: int, region: str) -> dict:
    state = rng.choice(STATES_BY_REGION[region])
    city = rng.choice(CITY_PREFIXES) + " City"
    prefix = rng.choice(CITY_PREFIXES)
    suffix = rng.choice(INST_SUFFIXES)
    return {
        "id": f"INST-{idx:04d}",
        "name": f"{prefix} {suffix}",
        "region": region,
        "state": state,
        "city": city,
        "type": rng.choice(INST_TYPES),
        "status": "Open",
    }


def _gen_courses(rng: random.Random, institution_id: str, base_idx: int) -> list[dict]:
    n = rng.randint(3, 6)
    courses = []
    seen_names: set[str] = set()
    domain = rng.choice(list(DOMAINS.keys()))
    domain_data = DOMAINS[domain]
    levels = list(domain_data.keys())
    for i, level in enumerate(rng.sample(levels, min(n, len(levels)))):
        names = domain_data[level]
        name = rng.choice(names)
        if name in seen_names:
            continue
        seen_names.add(name)
        intake = rng.choice(INTAKES)
        lateral = rng.choice([0, 0, 0, round(intake * 0.1)]) if level in ("UG", "Diploma") else 0
        for yr in ACADEMIC_YEARS:
            courses.append({
                "id": f"CRS-{base_idx:04d}-{i:02d}-{yr}",
                "institution_id": institution_id,
                "name": name,
                "level": level,
                "domain": domain,
                "academic_year": yr,
                "approved_intake": intake,
                "lateral_intake": lateral,
            })
    return courses


def run(db) -> None:
    from app.models.institution import Institution
    from app.models.course import CourseApproval

    if db.query(Institution).count() > 0:
        print("[gen_institutions] Already seeded — skip")
        return

    rng = random.Random(SEED)

    # Hero institutions
    for h in HERO:
        db.add(Institution(**h))

    # Hero courses
    for c in HERO_COURSES:
        db.add(CourseApproval(**c))

    # 42 random institutions distributed across 6 regions (7 each)
    idx = 7
    for region in REGIONS:
        for _ in range(7):
            inst = _gen_institution(rng, idx, region)
            db.add(Institution(**inst))
            courses = _gen_courses(rng, inst["id"], idx)
            for c in courses:
                db.add(CourseApproval(**c))
            idx += 1

    db.commit()
    inst_count = db.query(Institution).count()
    course_count = db.query(CourseApproval).count()
    print(f"[gen_institutions] {inst_count} institutions, {course_count} courses")
