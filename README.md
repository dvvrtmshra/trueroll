# TrueRoll — Prototype

**SIH 2026 · PS SIH26263 · Team StaplerX**

> SAMPLE DATA. Simulated integrations. Not an official AICTE system.

TrueRoll is a prototype web application for AICTE APAAR-based student data management and verification. Colleges upload student lists, a rule-governed Seat-Ledger checks every seat type, students control consent-bound verification, and every action is written to a tamper-evident audit log.

---

## What is real and what is simulated

| Real (working code) | Simulated (fake stand-ins) |
|---|---|
| Seat-Ledger engine and all checks | AICTE approval data (M1) |
| Rules Service, versioning, two-person approval | Student data (M3) |
| Validation, identity tiers, duplicate detection | APAAR / DigiLocker (M4) |
| Anomaly scoring (trained on synthetic data) | Anomaly training data (M6) |
| Consent, credentials, Ed25519 signatures, QR | OTP and demo users (M7) |
| Role-based access control, audit hash chain | Mail and SMS delivery (M9) |
| Upload API, reports, CSV/PDF exports | State admission data (M11) |

See `docs/SIMULATED.md` for the full list.

---

## Quick start (local, no Docker)

```bash
# 1. Python environment
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
# Unix:    source .venv/bin/activate
pip install -r requirements.txt

# 2. Environment
cp ../.env.example ../.env
# Edit .env if needed (defaults use SQLite)

# 3. Create schema and seed demo users
make seed          # from repo root
# or: cd backend && python -m scripts.init_db

# 4. Start backend
make run-backend   # http://localhost:8000  /docs for OpenAPI

# 5. Frontend (separate terminal)
cd frontend
npm install
make run-frontend  # http://localhost:5173
```

Demo OTP for every account: **123456**

Quick sign-in accounts (all use OTP 123456):

| Role | Email |
|---|---|
| AICTE National Officer | `officer.national@trueroll.demo` |
| AICTE Regional Officer (North) | `officer.north@trueroll.demo` |
| Rules Owner | `rules.owner@trueroll.demo` |
| Rules Approver | `rules.approver@trueroll.demo` |
| College Admin (INST-0001) | `admin.inst0001@trueroll.demo` |
| Student (verified) | `student.verified@trueroll.demo` |
| Employer | `employer.demotech@trueroll.demo` |
| Auditor | `auditor@trueroll.demo` |
| System Admin | `sysadmin@trueroll.demo` |

## Docker Compose

```bash
cp .env.example .env   # edit passwords if needed
docker compose up --build
```

Backend: http://localhost:8000 · Frontend: http://localhost:5173

## Make targets

| Command | What it does |
|---|---|
| `make seed` | Create schema and seed demo data |
| `make reset-demo` | Drop and recreate everything from seed |
| `make test` | Run pytest suite |
| `make run-backend` | Start FastAPI dev server |
| `make run-frontend` | Start Vite dev server |
| `make evaluate` | Run evaluation suite (Phase 9+) |

## Build phases

See `docs/SPEC.md` section 11. Current phase: **0 — Skeleton**.
