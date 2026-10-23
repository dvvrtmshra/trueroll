"""M15 — Generate one demo API key per institution."""
import hashlib
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from seed.common import SEED
from app.models.api_key import ApiKey
from app.models.institution import Institution


def _key_hash(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


def run(db) -> None:
    if db.query(ApiKey).count() > 0:
        print("[gen_api_keys] Already seeded — skip")
        return

    rng = random.Random(SEED + 1)
    institutions = db.query(Institution).all()
    added = 0
    for inst in institutions:
        raw_key = f"demo_key_{inst.id.lower().replace('-', '')}_{rng.randint(100000, 999999)}"
        db.add(ApiKey(
            id=f"ak-{inst.id.lower().replace('-', '')}",
            employer_id="system",  # institution keys reuse ApiKey with employer_id="system"
            key_hash=_key_hash(raw_key),
            name=f"Demo API key for {inst.id}",
            is_active=True,
        ))
        added += 1
    db.commit()
    print(f"[gen_api_keys] {added} institution API keys")
