# TrueRoll — Simulated Services and Datasets

Every item in this file is a **fake stand-in** for a real outside system or real data.
Each is clearly labelled in the UI with a **SIMULATED** chip.

| ID | What we create | Why | Status |
|---|---|---|---|
| M1 | AICTE approval records (48 institutions, 214 courses, intake) | No AICTE DB access | **Seeded (Phase 1)** — `seed/generate_institutions.py`, fake read-only API stub at `/sim/aicte/` |
| M2 | Seat rule book (6 rules, 7 versions — NRI-IN, SN-A v1/v2, SN-B, SN-PG, SN-MGT, EWS-ST) | Official rules unconfirmed | **Engine live (Phase 2)** — rules loaded by `rules_service.active_rules_for()`; lifecycle enforced (draft→pending→approved→active); two-person approval; retire on supersede |
| M3 | Synthetic student admission records (12,855 students, 2026-27) | No real student data | **Seeded (Phase 1)** — `seed/generate_students.py`, hero scenario data planted |
| M4 | APAAR / DigiLocker-ABC simulator | No API Setu approval; live access needs registered requester onboarding | Simulated — fake service at `/sim/registry/` behind `RegistryAdapter` interface |
| M5 | Sample upload files (CSV/XLSX) in `seed/uploads/` | Needed to demo uploads | Fake files, real validation |
| M6 | Anomaly training and evaluation dataset | No labelled anomaly data | Fake data, real model (Phase 8) |
| M7 | Demo users (22 accounts across all roles) and mock OTP (always `123456`) | No real identity provider | **Seeded (Phase 1)** — `seed/generate_users.py`. Real role checks |
| M8 | Employer organisations (8 fictional) | Demo only | **Seeded (Phase 1)** — `seed/generate_employers.py` |
| M9 | Mock mail and SMS outbox (table `outbox`) | No real email/SMS delivery | Fake delivery, real message content |
| M10 | Certificate template and sample PDFs | Needed for PS item 10 | Real PDF generation, fake data |
| M11 | State admission data | Future integration | Static display only — no logic |
| M12 | Demo clock (`setting` table, `app_now()`) | To demo effective dates and deadlines | Fake time control, real date logic |
| M13 | Signing keys in `vault/` | Real HSM out of scope | Real Ed25519 keys, documented as a stand-in |
| M14 | Pre-seeded audit history (2,000 entries, April–October 2026) | To show a lived-in chain | **Seeded (Phase 1)** — `seed/generate_audit_history.py`. Real hash chain |
| M15 | Institution API keys (48, one per institution) | Demo of API upload | **Seeded (Phase 1)** — `seed/generate_api_keys.py`. Real API key check |
| M16 | Typo-injected duplicate set (400 true pairs + 400 near-misses) | No real duplicate data | Fake data, real matcher (Phase 3) |

---

## Adapter interfaces (proof of integration design)

These interfaces exist so real implementations can replace simulators without changing other code:

- `backend/app/adapters/registry.py` — `RegistryAdapter` ABC + `SimulatedRegistry`
- `backend/app/adapters/aicte.py` — `AicteAdapter` ABC + `SimulatedAicte`

---

## Integration register

| System | Status | Notes |
|---|---|---|
| AICTE approval database | SIMULATED | `SimulatedAicte` behind `AicteAdapter` |
| DigiLocker / APAAR registry | SIMULATED | `SimulatedRegistry` behind `RegistryAdapter`. Live access needs API Setu approval |
| State admission data | FUTURE | Placeholder tile only |
| Mail / SMS delivery | SIMULATED | `outbox` table shown in Mock Mail page |
| Signing key vault (HSM) | SIMULATED | Ed25519 keys in `vault/` |
