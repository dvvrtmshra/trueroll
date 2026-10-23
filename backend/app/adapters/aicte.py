"""M1 — AICTE approval adapter (simulated)."""
from app.adapters.registry import register


class AICTEAdapter:
    service_id = "M1"
    service_name = "AICTE Approval API"

    def ping(self) -> bool:
        return True

    def get_approval(self, institution_id: str, academic_year: str) -> dict:
        """Returns simulated approval data; no real network call."""
        return {
            "institution_id": institution_id,
            "academic_year": academic_year,
            "simulated": True,
            "status": "approved",
        }


aicte = AICTEAdapter()
register(aicte)
