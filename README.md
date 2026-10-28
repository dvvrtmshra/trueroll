# TrueRoll — Prototype

**SIH 2026 · Problem Statement SIH26263 · Team StaplerX**

> **All data is synthetic. No real students, colleges, or government systems are used.
> Every outside system (AICTE, APAAR, DigiLocker) is simulated and clearly labelled.**

TrueRoll is a working web application that checks college admissions rule-by-rule, lets students control who can verify them, and writes every action to a tamper-evident audit log.

---

## Requirements

- **Python 3.11+**
- **Node.js 18+**

Nothing else. SQLite is bundled with Python — no database server needed.

---

## How to run it (Windows — PowerShell)

You need **two terminal windows** open at the same time.

### Terminal 1 — one-time setup + backend

```powershell
cd E:\gitdv\trueroll

# Create and activate virtual environment (once)
cd backend
python -m venv .venv
.venv\Scripts\activate
cd ..

# Install all dependencies (once)
.\run.ps1 install

# Copy config — SQLite, no passwords needed (once)
copy .env.example .env

# Seed the database (once, or after reset-demo)
.\run.ps1 seed

# Start the backend — KEEP THIS WINDOW OPEN
.\run.ps1 run-backend
```

Backend is ready at **http://localhost:8000** (API explorer: http://localhost:8000/docs)

### Terminal 2 — frontend

Open a **new** PowerShell window:

```powershell
cd E:\gitdv\trueroll
cd backend && .venv\Scripts\activate && cd ..

# Start the frontend — KEEP THIS WINDOW OPEN
.\run.ps1 run-frontend
```

Open **http://localhost:5173** in your browser. Done.

---

## How to run it (Mac / Linux)

```bash
cd trueroll
cd backend
python -m venv .venv && source .venv/bin/activate
cd ..
cp .env.example .env
make seed
make run-backend        # keep open
# new terminal:
make run-frontend       # http://localhost:5173
```

---

## Direct commands (no make or run.ps1 needed)

```bash
# From repo root with venv active:
cd backend && python -m scripts.init_db          # seed
cd backend && uvicorn app.main:app --reload --port 8000   # backend
cd frontend && npm install && npm run dev         # frontend
cd backend && python -m pytest tests/ -v          # tests
cd backend && python -m scripts.init_db --reset   # reset demo
```

---

## Demo login

Every account uses OTP **`123456`** — just type it when prompted.

| Who | Email | What they can do |
|---|---|---|
| AICTE National Officer | `officer.national@trueroll.demo` | Dashboard, Seat-Ledger Compare mode, Flags, Reports |
| AICTE Regional Officer (North) | `officer.north@trueroll.demo` | Same, scoped to North region |
| Rules Owner | `rules.owner@trueroll.demo` | Propose and manage seat rules |
| Rules Approver | `rules.approver@trueroll.demo` | Second-person rule approval (two-person rule) |
| College Admin — INST-0001 | `admin.inst0001@trueroll.demo` | Upload students, see flags, reply to queries |
| College Admin — INST-0002 | `admin.inst0002@trueroll.demo` | Different college — tests cross-institution isolation |
| Student (verified, has APAAR) | `student.verified@trueroll.demo` | My record, consent manager, certificates |
| Student (no APAAR) | `student.noid@trueroll.demo` | Shows identity warning — student still counted |
| Employer | `employer.demotech@trueroll.demo` | Verify a student share code |
| Auditor | `auditor@trueroll.demo` | Audit trail, chain verify, Tamper demo |
| System Admin | `sysadmin@trueroll.demo` | Admin tools, clock, scenarios, Tamper demo |

---

## 8-minute demo (judge walkthrough)

Reset to a clean state first:

```powershell
# Windows
.\run.ps1 reset-demo
```
```bash
# Mac / Linux
make reset-demo
```

Then follow these 12 steps (full script in `docs/SPEC.md` Section 9):

| # | Sign in as | What to do | What to say |
|---|---|---|---|
| 1 | — | Open http://localhost:5173 | "Everything is synthetic. SAMPLE DATA ribbon is always visible." |
| 2 | National Officer | Open Dashboard | "48 colleges, live flag count, identity coverage." |
| 3 | National Officer | Seat-Ledger → turn **Compare mode ON** | "Simple counter panics at 241. Seat-Ledger knows 276 is lawful here." ← **our USP** |
| 4 | College Admin (INST-0001) | Upload → choose `B_domestic_in_extra.csv` | "Upload triggers real rule checks." |
| 5 | National Officer | Dashboard updates; open the new flag | "Rule cited, version cited. A flag is not a finding." |
| 6 | College Admin (INST-0001) | Flags → reply | "College explains or resubmits." |
| 7 | Rules Owner → Rules Approver | Open pending `SN-MGT` rule, run tests, approve as second person | "Two people, sourced, tested. Unconfirmed rules never auto-flag." |
| 8 | National Officer | Review priorities → Model evaluation | "Advisory scoring with reasons. Honest numbers on synthetic data." |
| 9 | Student | Consent → Create share code | "Student decides who can verify, for what, until when." |
| 10 | Employer | Verify the share code | "Signed yes/no. No marks, address, or Aadhaar." |
| 11 | Student | Withdraw consent → Employer scans again | "Withdrawn means withdrawn, instantly." |
| 12 | System Admin → Auditor | Admin → Tamper demo → Auditor → Verify chain | "Any edit to history is detected." |

---

## Run the tests

```powershell
# Windows
.\run.ps1 test

# TypeScript type check (from repo root)
cd frontend && npx tsc --noEmit && cd ..

# Evaluation script
.\run.ps1 evaluate
```

```bash
# Mac / Linux
make test
cd frontend && npx tsc --noEmit
make evaluate
```

---

## run.ps1 commands (Windows)

| Command | What it does |
|---|---|
| `.\run.ps1 install` | Install Python + Node dependencies |
| `.\run.ps1 seed` | Create schema and seed all demo data (idempotent) |
| `.\run.ps1 reset-demo` | Drop everything and reseed from scratch |
| `.\run.ps1 run-backend` | Start FastAPI dev server on :8000 |
| `.\run.ps1 run-frontend` | Start Vite dev server on :5173 |
| `.\run.ps1 test` | Run all 71 backend tests |
| `.\run.ps1 evaluate` | Run anomaly + master evaluation |
| `.\run.ps1 e2e` | Run Playwright demo tests (needs both servers running) |

---

## Docker Compose (alternative)

```bash
cp .env.example .env
docker compose up --build
# Backend: http://localhost:8000
# Frontend: http://localhost:5173
```

---

## What is real and what is simulated

| Real (working logic) | Simulated (clearly labelled in UI) |
|---|---|
| Seat-Ledger engine, checks C1–C5 | AICTE approval data (fictional colleges) |
| Rules Service: versioning, two-person approval | Student records (fictional people) |
| Validation, identity tiers T1–T4, duplicate detection | APAAR / DigiLocker registry |
| Anomaly scoring (trained on synthetic labels) | Anomaly training labels |
| Consent, Ed25519 signatures, QR codes | OTP delivery (always `123456`) |
| Role-based access control, audit hash chain | Mail / SMS delivery |
| Upload pipeline, reports, CSV exports | State admission data |

Full list: [`docs/SIMULATED.md`](docs/SIMULATED.md)

---

## Key files

```
backend/
  app/api/           FastAPI routers (one file per domain)
  app/services/      Business logic: ledger, rules, ingestion, matcher
  app/models/        SQLAlchemy models
  scripts/           init_db, evaluate, evaluate_anomaly
  tests/             71 pytest tests covering all 24 scenarios

frontend/
  src/pages/         One folder per role: officer, college, student, employer, rules, admin, auditor
  src/components/    Shared: Layout, SimulatedChip, TierBadge, LoadingSpinner, EmptyState...
  e2e/               Playwright tests (demo-script.spec.ts)

docs/
  SPEC.md            Full build specification
  SIMULATED.md       Every simulated system and dataset
  decisions.md       Architecture decisions D1-D28

seed/
  uploads/           Sample CSV files (A-I scenarios + large file) — created by seed command
```

---

## Scenarios covered by automated tests

All 24 scenarios from `docs/SPEC.md` Section 10:

S1 Lawful 276 · S2 Domestic in extra seats · S3 Over maximum · S4 Unconfirmed rule · S5 Pending rule · S6 Missing APAAR · S7 Foreign national · S8 Opted-out · S9 Registry down · S10 Duplicate classes · S11 Bad file · S12 Idempotency · S13 Large file · S14 Withdrawal · **S15 Anomaly** · S16 Consent lifecycle · **S17 Tamper** · S18 Rule change mid-year · **S19 Role isolation** · S20 Live update · **S21 Correction + reconcile** · **S22 Spot + lateral** · S23 Fuzzy matching · **S24 Evaluation summary**

---

## Troubleshooting

**`make` is not recognised (Windows)**
Use `.\run.ps1 <command>` instead. All `make` commands have a `run.ps1` equivalent (see table above).

**`.\run.ps1` is not recognised / CommandNotFoundException**
You are in the wrong directory. Run `cd E:\gitdv\trueroll` first. `run.ps1` lives in the repo root.

**`.\run.ps1 seed` fails with "No module named scripts"**
Your virtual environment is not active. Run `cd backend && .venv\Scripts\activate && cd ..` then try again.

**`copy .env.example .env` — file not found**
Run this from the repo root (`E:\gitdv\trueroll`), not from inside `backend\` or `frontend\`.

**Port 8000 already in use**
`netstat -ano | findstr 8000` (Windows) or `lsof -i :8000` (Mac/Linux), then kill that process.

**Frontend shows blank page or 401 on every request**
The backend is not running. Start it with `.\run.ps1 run-backend` (Windows) or `make run-backend` (Mac/Linux) first.

**"Invalid OTP"**
The OTP is always `123456`. Use an email from the demo login table above.

**Want to start completely fresh**
`.\run.ps1 reset-demo` (Windows) or `make reset-demo` (Mac/Linux) — drops and recreates everything.
