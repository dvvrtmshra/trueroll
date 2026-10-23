"""M2 — APAAR / DigiLocker adapter (simulated)."""
from app.adapters.registry import register


class APAARAdapter:
    service_id = "M2"
    service_name = "APAAR DigiLocker API"

    def ping(self) -> bool:
        return True

    def verify_apaar(self, apaar_id: str) -> dict:
        """Simulated APAAR verification — always returns verified for well-formed IDs."""
        valid = len(apaar_id) == 12 and apaar_id.isdigit()
        return {"apaar_id": apaar_id, "verified": valid, "simulated": True}


apaar = APAARAdapter()
register(apaar)
