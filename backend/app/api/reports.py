from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter()

REPORT_STUBS = [
    "national-summary", "regional-breakdown", "institution-compliance",
    "seat-utilisation", "flag-ageing", "rule-coverage", "duplicate-rate",
    "vc-issuance", "employer-usage", "audit-integrity",
    "student-demographics", "anomaly-summary",
]

for _r in REPORT_STUBS:
    def _make(name: str):
        @router.get(f"/{name}")
        def _report():
            return JSONResponse(status_code=501, content={"detail": f"Report {name} — Phase 9"})
        return _report
    _make(_r)
