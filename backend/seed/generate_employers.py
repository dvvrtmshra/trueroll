"""M8 — Generate 8 fictional employer organisations."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.models.employer import Employer

EMPLOYERS = [
    {"id": "EMP-0001", "name": "Demo Tech Pvt Ltd", "cin": "U72200DL2015PTC280001",
     "sector": "Information Technology", "is_active": True, "api_tier": "standard"},
    {"id": "EMP-0002", "name": "Acme Solutions Ltd", "cin": "U74999MH2010PLC200002",
     "sector": "Consulting", "is_active": True, "api_tier": "standard"},
    {"id": "EMP-0003", "name": "Sample Infosystems Pvt Ltd", "cin": "U72200KA2012PTC300003",
     "sector": "Information Technology", "is_active": True, "api_tier": "standard"},
    {"id": "EMP-0004", "name": "Model Manufacturing Co Ltd", "cin": "U28100GJ2008PLC400004",
     "sector": "Manufacturing", "is_active": True, "api_tier": "standard"},
    {"id": "EMP-0005", "name": "Trial Finance Services", "cin": "U65100TN2014PLC500005",
     "sector": "Financial Services", "is_active": True, "api_tier": "standard"},
    {"id": "EMP-0006", "name": "Pilot Healthcare Ltd", "cin": "U85100WB2016PLC600006",
     "sector": "Healthcare", "is_active": True, "api_tier": "standard"},
    {"id": "EMP-0007", "name": "Generic Research Foundation", "cin": None,
     "sector": "Research", "is_active": True, "api_tier": "standard"},
    {"id": "EMP-0008", "name": "Example Analytics Pvt Ltd", "cin": "U72200UP2019PTC800008",
     "sector": "Analytics", "is_active": True, "api_tier": "standard"},
]


def run(db) -> None:
    from app.models.employer import Employer

    added = 0
    for e in EMPLOYERS:
        if not db.query(Employer).filter(Employer.id == e["id"]).first():
            db.add(Employer(**e))
            added += 1
    db.commit()
    print(f"[gen_employers] {added} employers")
