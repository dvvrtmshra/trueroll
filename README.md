# TrueRoll — Prototype

**SIH 2026 · Problem Statement SIH26263 · Team StaplerX**

> **All data is synthetic. No real students, colleges, or government systems are used.
> Every outside system (AICTE, APAAR, DigiLocker) is simulated and clearly labelled.**

TrueRoll is a working web application that checks college admissions rule-by-rule, lets students control who can verify them, and writes every action to a tamper-evident audit log.

---

## How to run it (local, ~5 minutes from scratch)

You need **Python 3.11+** and **Node.js 18+** installed. Nothing else.

### Step 1 — Backend

```bash
cd backend

# Create a virtual environment
python -m venv .venv

# Activate it
# Windows:
.venv\Scripts\activate
# Mac/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy the default config (SQLite, no passwords needed)
cd ..
cp .env.example .env

# Create the database and load all demo data
make seed

# Start the backend server
make run-backend
# → http://localhost:8000
# → http://localhost:8000/docs  (interactive API explorer)
```

### Step 2 — Frontend (new terminal)

```bash
cd frontend
npm install
```

Back in the repo root:

```bash
make run-frontend
# → http://localhost:5173
```

Open **http://localhost:5173** in your browser. Done.

---

## Demo login

Every account uses OTP **`123456`** — just type it when prompted.

| Who | Email | What they can do |
|---|---|---|
| AICTE National Officer | `officer.national@trueroll.demo` | Dashboard, Seat-Ledger Compare mode, Flags, Reports |
| AICTE Regional Officer (North) | `officer.north@trueroll.demo` | Same as above, scoped to North |
| Rules Owner | `rules.owner@trueroll.demo` | Propose and manage seat rules |
| Rules Approver | `rules.approver@trueroll.demo` | Second-person approval (two-person rule) |
| College Admin — INST-0001 | `admin.inst0001@trueroll.demo` | Upload students, see flags, reply to queries |
| College Admin — INST-0002 | `admin.inst0002@trueroll.demo` | Different college (tests cross-institution isolation) |
| Student (verified, has APAAR) | `student.verified@trueroll.demo` | My record, consent manager, certificates |
| Student (no APAAR) | `student.noid@trueroll.demo` | Shows identity warning — student still counted |
| Employer | `employer.demotech@trueroll.demo` | Verify a student share code |
| Auditor | `auditor@trueroll.demo` | Audit trail, chain verify, Tamper demo |
| System Admin | `sysadmin@trueroll.demo` | Admin tools, clock, scenarios, Tamper demo |

---

## 8-minute demo (judge walkthrough)

Reset to a clean state first:

```bash
# With the backend running, click "Reset demo" in Admin → System Admin
# Or from the terminal:
make reset-demo
```

Then follow the 12 steps below (full script in `docs/SPEC.md` Section 9):

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
| 9 | Student (phone view) | Consent → Create share code | "Student decides who can verify, for what, until when." |
| 10 | Employer | Verify the code | "Signed yes/no. No marks, address, or Aadhaar." |
| 11 | Student | Withdraw consent → Employer scans again | "Withdrawn means withdrawn, instantly." |
| 12 | System Admin → Auditor | Admin → Tamper demo → Auditor → Verify chain | "Any edit to history is detected." |

---

## Run the tests

```bash
# Backend tests (71 tests, ~35 seconds)
make test

# TypeScript type check
cd frontend && npx tsc --noEmit

# Evaluation script (writes models/evaluation_summary.json)
make evaluate

# End-to-end Playwright tests (requires both servers running in other terminals)
make e2e
```

---

## Docker Compose (alternative)

```bash
cp .env.example .env
docker compose up --build
# Backend: http://localhost:8000
# Frontend: http://localhost:5173
```

---

## Make targets

| Command | What it does |
|---|---|
| `make seed` | Create schema and seed all demo data (idempotent) |
| `make reset-demo` | Drop everything and reseed from scratch |
| `make test` | Run the full pytest suite |
| `make run-backend` | Start FastAPI dev server on :8000 |
| `make run-frontend` | Start Vite dev server on :5173 |
| `make evaluate` | Run anomaly + master evaluation, write summary JSON |
| `make e2e` | Run Playwright demo-script tests |
| `make e2e-ui` | Open Playwright interactive UI |

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
  src/components/    Shared: Layout, SimulatedChip, TierBadge, LoadingSpinner, EmptyState…
  e2e/               Playwright tests (demo-script.spec.ts)

docs/
  SPEC.md            Full build specification
  SIMULATED.md       Every simulated system and dataset
  decisions.md       Architecture decisions D1–D28

seed/
  uploads/           Sample CSV files (A–I scenarios + large file) — created by make seed
```

---

## Scenarios covered by automated tests

All 24 scenarios from `docs/SPEC.md` Section 10:

S1 Lawful 276 · S2 Domestic in extra seats · S3 Over maximum · S4 Unconfirmed rule · S5 Pending rule · S6 Missing APAAR · S7 Foreign national · S8 Opted-out · S9 Registry down · S10 Duplicate classes · S11 Bad file · S12 Idempotency · S13 Large file · S14 Withdrawal · **S15 Anomaly** · S16 Consent lifecycle · **S17 Tamper** · S18 Rule change mid-year · **S19 Role isolation** · S20 Live update · **S21 Correction + reconcile** · **S22 Spot + lateral** · S23 Fuzzy matching · **S24 Evaluation summary**

---

## Troubleshooting

**`make seed` fails with "no module named app"**
→ Make sure your virtual environment is activated before running `make seed`.

**Port 8000 already in use**
→ `lsof -i :8000` (Mac/Linux) or `netstat -ano | findstr 8000` (Windows), then kill the process.

**Frontend shows blank page / 401 everywhere**
→ The backend is not running. Start it with `make run-backend` first.

**"Invalid OTP"**
→ The OTP is always `123456`. Make sure you are using an email from the table above.

**Want to start fresh**
→ `make reset-demo` drops and recreates everything.
