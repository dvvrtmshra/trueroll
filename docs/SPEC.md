# TrueRoll Prototype: Complete Build Specification

**For:** the teammate who will build the prototype (with Claude).
**Project:** TrueRoll, SIH 2026 PS **SIH26263** (AICTE: APAAR ID-based student data management and verification platform).
**Team:** StaplerX · **Status:** build specification **v1.1** · **Matches:** architecture v2 (locked)

> **How to read this.** Section 1 is the most important: it lists every dataset and every fake service we must create. Section 5 describes exactly what each user role sees. Sections 6 and 7 hold the rules and logic. Section 9 is the demo script. Section 11 is the order to build in.

---

## 0. Read this first

### 0.1 What we are building (in simple words)

TrueRoll is a website where **colleges upload their student lists**, a **checking engine** tests every record and every seat, **AICTE officers** see a live screen of problems with the exact rule behind each one, **students** control who can verify them, and **employers** get a safe yes/no answer.

The prototype is a **working web application** with a real backend and real logic, running on **made-up (synthetic) data** and **fake versions of outside government systems**. It is not a mock-up of pictures. When you upload a file, the numbers really change, flags really appear, and a verification code really checks a digital signature.

### 0.2 What must impress in the first round (our USP, in order of importance)

| # | Moment | What the judge sees | Why it wins |
|---|---|---|---|
| 1 | **Seat-Ledger "Compare mode"** | The same college data shown twice: a simple counter that panics, and our Seat-Ledger that stays quiet when the college is right and, when it is wrong, names the rule, version and records | This is our core idea, made visible in 20 seconds |
| 2 | **Rule governance** | A Rules Owner proposes a rule, a second person approves it, tests run, it goes live for one academic year only. An unconfirmed rule never raises an automatic flag | Answers the hardest judge question ("who says your rules are right?") |
| 3 | **Consent-bound verification** | Student creates a share code, employer scans it, gets only "Enrolled: yes/no", student then withdraws consent and the next scan fails | Privacy done properly, live |
| 4 | **Anomaly Intelligence with honest evaluation** | A ranked "Review priorities" queue with reason codes, and a "Model evaluation" page showing precision/recall on synthetic labelled data against a simple baseline | Covers the PS's "intelligent anomaly detection" without false claims |
| 5 | **Tamper test** | Someone edits a past audit entry in the database, the Auditor clicks "Verify chain", and the break is detected | Shows tamper-evident audit, memorable |

### 0.3 Golden rules (honesty and safety)

1. **Everything is labelled.** A permanent **"SAMPLE DATA"** ribbon on every page. Simulated systems show a **SIMULATED** chip. Nothing is shown as live.
2. **No real people, no real colleges.** Use fictional names for institutions and students. Never use real Aadhaar numbers, real APAAR IDs, real phone numbers or real college names.
3. **We never claim accuracy on real data.** The anomaly model's numbers come only from the synthetic evaluation and are labelled that way.
4. **A flag is not a finding.** No screen may say "violation", "fraud" or "guilty". Use "flag", "needs review", "concern".
5. **Rules are illustrative.** Every seeded rule shows "Illustrative: to be confirmed against AICTE rules".
6. **A missing or unverified ID never rejects a student.** It produces a Warning and the student stays counted.
7. **Servers decide, screens only show.** All permission checks happen on the server. Hiding a button is not security.

### 0.4 Priority tags used in this document

| Tag | Meaning |
|---|---|
| **[MUST]** | Needed for the demo and for covering the PS deliverables |
| **[SHOULD]** | Makes the demo clearly stronger |
| **[EXTRA]** | Bonus that adds polish or answers likely judge questions |

There is no time limit, so build everything, but build in the order of Section 11.

### 0.5 Instructions for Claude (paste this at the start of the build chat)

- Treat this file as the single source of truth. If something is unclear, write the assumption in `docs/decisions.md` and continue.
- Build in the phase order of Section 11. After each phase, run the acceptance tests listed there.
- Create all seed data with a **fixed random seed (26263)** so the demo is identical every time.
- Never hard-code seat rules inside code. All rules live in the rule book (database), versioned (Section 6.5).
- Every number on a dashboard must come from the database, not from constants.
- Keep one file `docs/SIMULATED.md` listing every fake service and every dataset, and keep it up to date.

### 0.6 What changed in v1.1 (driven by a stress test of the slides)

| # | Change | Where |
|---|---|---|
| 1 | **Fuzzy matching for students without an APAAR ID**, with a typo-injected test set (M16) and a "Matching evaluation" page. Low-confidence matches go to review and are never auto-flagged | 6.3, M16, N7 |
| 2 | **Corrections, spot rounds and lateral entry** handled, with a **reconcile** function proving the counters equal the event history | 6.4, S21, S22 |
| 3 | **Evaluation results panel**: the prototype measures its own numbers (breaches caught, false alarms against a simple counter, time from upload to flag, matching and anomaly precision and recall) so the slides can quote **our** results | 6.14, S24 |
| 4 | Certificates explicitly carry **APAAR ID + student ID + QR**; admission round and entry type added as fields | 6.1, 6.10 |
| 5 | Registry simulator gets a **latency and failure profile** and a consent redirect; the Admin page states that live access needs registered approval | M4, 5.10 |
| 6 | **Rules ownership** stated as a deployment assumption | 6.5 |


---

## 1. MOCK DATA AND SIMULATED INTERFACES (everything we must create)

**This is the list of things that do not exist in the real world for us, so we must create them.** Each item has an ID (M1, M2, ...) used throughout this document.

### 1.1 Summary

| ID | What we create | Why it is mocked | Real or fake in the prototype | Used by |
|---|---|---|---|---|
| **M1** | AICTE approval records (institutions, courses, approved intake) | We have no access to AICTE's database | Fake data + fake read-only API | Seat-Ledger (source of the caps), dashboards |
| **M2** | Seat rule book (rules, versions, statuses) | Official rules must be confirmed by AICTE | Illustrative rules, **real engine** | Rules Service, Seat-Ledger |
| **M3** | Synthetic student admission records | No real student data | Fake data, **real processing** | Everything |
| **M4** | **APAAR / DigiLocker-ABC simulator** (identity check + consent page) | No registry access or API Setu approval | Fake service with a **real adapter contract** | Identity tiers, student onboarding |
| **M5** | Sample upload files (CSV/XLSX) | Needed to demo uploads | Fake files, real validation | Institution upload |
| **M6** | Anomaly training and evaluation dataset (with planted, labelled anomalies) | No labelled fraud data exists | Fake data, **real model** | Anomaly Intelligence |
| **M7** | Demo users, roles and mock OTP | No real identity provider | Fake accounts, **real role checks** | Login |
| **M8** | Employer organisations | Demo only | Fake | Verification |
| **M9** | Mock mail and SMS outbox | We do not send real messages | Fake delivery, real message content | Notifications |
| **M10** | Certificate template and sample certificates | Needed for PS item 10 | Real PDF generation, fake data | Certificates |
| **M11** | State admission data placeholder | Future integration only | Static display, **no logic** | "Future" tile |
| **M12** | Demo clock (movable "today") | To demo deadlines and effective dates | Fake time control, real date logic | Rules, reminders |
| **M13** | Signing keys and mock key vault | A real HSM is out of scope | **Real** Ed25519 keys stored in a folder called "vault" | Credentials |
| **M14** | Pre-seeded audit history | To show a long, valid chain | Fake history, **real hash chain** | Audit |
| **M15** | Institution API keys (demo) | Demo of API upload | Fake keys, real API check | Upload API |
| **M16** | **Typo-injected duplicate set** (for matching evaluation) | No real duplicate data exists | Fake data, **real matcher** | Duplicate resolver, Matching evaluation page |

### 1.2 Details of each item

#### M1. AICTE approval records (simulated AICTE feed)

| Property | Specification |
|---|---|
| Purpose | The **only source of approved intake**. Colleges can never type or change it |
| Volume | **48 fictional institutions**, 6 demo regions (North, South, East, West, Central, North-East) |
| Institution fields | `institution_id` (INST-0001...), `name` (fictional), `region`, `state`, `city`, `type` (Private / Government / Autonomous), `status` (Open) |
| Courses per institution | 3 to 6 |
| Course fields | `course_id`, `institution_id`, `name`, `level` (Diploma, UG, PG, MBA/PGDM, MCA), `domain` (Engineering and Technology, Management, Computer Applications), `academic_year` (2025-26 and 2026-27), `approved_intake` (60, 90, 120, 180 or 240), `lateral_intake` (optional, default 0) |
| API | `GET /sim/aicte/institutions`, `GET /sim/aicte/approvals?year=2026-27`. Read-only. Marked SIMULATED |
| Naming rule | Names like "Sample Institute of Technology", "Demo College of Engineering". **Never** a real college name |
| Hero institutions | A few fixed institutions (listed in Section 10) carry the demo scenarios |

#### M2. Seat rule book (illustrative)

Seed these rule records. All are **illustrative** and show the banner "to be confirmed against AICTE rules".

| Rule ID | Version | Meaning (illustrative) | Scope | Status |
|---|---|---|---|---|
| **NRI-IN** | v1 | NRI seats are **inside** the approved intake, 5% of intake (12 of 240) | UG Engineering, 2026-27 | Active |
| **SN-A** | v1 | Extra seats for OCI/FN students: 10% of approved intake (24 of 240) | UG Engineering, 2025-26 | Retired |
| **SN-A** | v2 | Same, effective 2026-27 | UG Engineering, 2026-27 | **Active** |
| **SN-B** | v1 | Extra seats for CIWGC students: 5% of approved intake (12 of 240). A vacant CIWGC seat may be filled by OCI/FN students | UG Engineering, 2026-27 | **Active** |
| **SN-PG** | v1 | Extra seats for international students in PG: 25% of intake | PG Engineering, 2026-27 | **Pending approval** (proposed, no approver yet) |
| **SN-MGT** | v1 | Extra seats, management and computer applications: 25% | Management/MCA, 2026-27 | **Pending approval** |
| **EWS-ST** | v1 | State-specific extra EWS seats: 10% | One state | **Draft, disabled** (used to demo "unconfirmed rule goes to human review") |

Rule record fields are in Section 6.5. Each rule also stores: `source_document`, `source_clause` ("TO BE CONFIRMED"), `effective_from`, `effective_to`, `approvals[]`, `test_suite_id`, `enabled`.

#### M3. Synthetic student admission records

| Property | Specification |
|---|---|
| Volume | About **9,000 students** across the 48 institutions, 2026-27 admissions, plus a smaller 2025-26 history |
| Generator | Python script `seed/generate_students.py` using Faker (`en_IN` locale) with fixed seed 26263 |
| Fields | `student_id` (internal), `full_name` (fake), `date_of_birth` (fake), `gender` (optional), `apaar_id` (12 digits or empty), `identity_tier` (T1-T4), `course_id`, `seat_category` (REGULAR, NRI_IN, OCI_FN_EXTRA, CIWGC_EXTRA, EWS), `admission_date`, `admission_round` (ROUND_1, ROUND_2, ROUND_3, SPOT), `entry_type` (REGULAR or LATERAL), `status` (ADMITTED, WITHDRAWN, TRANSFERRED), `withdrawal_date`, `contact_token` (hashed fake phone), `guardian_token` (hashed fake name) |
| Identity tier mix (illustrative) | T1 about 55%, T2 about 12%, T3 about 25%, T4 about 8% |
| Never include | Aadhaar numbers, real phone numbers, real photos, marks, addresses |
| Planted scenarios | The generator must plant the scenarios in Section 10 exactly (for example College A with 276 admitted) |

#### M4. APAAR / DigiLocker-ABC simulator (the biggest fake)

We have no access to the real registry. We build a **separate small service** that behaves like one, so our real adapter can be switched to the live service later.

| Property | Specification |
|---|---|
| What it is | A separate FastAPI app (or a route group `/sim/registry`) clearly labelled SIMULATED |
| Registry data | About **14,000 fake APAAR IDs** (12 digits) with a hashed name and hashed date of birth. Covers every T1 student |
| Endpoint 1 | `POST /sim/registry/verify` with `apaar_id` and name/date-of-birth tokens. Returns `VERIFIED`, `NOT_FOUND`, `MISMATCH` (ID exists, details differ) or `UNAVAILABLE` (HTTP 503) |
| Endpoint 2 | `POST /sim/registry/consent-session` returns a session id for the mock consent page |
| **Mock consent page** | A page that looks like a government consent screen: "TrueRoll requests to verify your APAAR ID. Allow / Deny". Banner: **"Simulated consent screen for prototype"** |
| Failure controls | An **Admin toggle "Registry: Up / Slow / Flaky / Down"**. *Slow* adds 3 to 8 seconds of delay. *Flaky* returns HTTP 503 for about 10% of calls. *Down* always fails. Also special IDs ending in `999` always time out. Used to demo "registry unavailable → student stays Unverified (T2) and is retried, never rejected" |
| Adapter contract | The TrueRoll backend calls the registry only through `RegistryAdapter` (an interface with `verify()` and `start_consent()`). The simulator is one implementation. A live one would be a second implementation. **Write this interface clearly**, because it is the proof that integration is designed |

#### M5. Sample upload files

Create these files in `seed/uploads/` (CSV, plus one XLSX):

| File | Content | Purpose |
|---|---|---|
| `A_lawful_276.csv` | 276 students in valid seat types for a 240-intake course | Seat-Ledger: no flag (the false-alarm case) |
| `B_domestic_in_extra.csv` | 276 admitted, 5 domestic students placed in extra international seats | Flag 5, ineligible seat holders |
| `C_over_max_282.csv` | 282 admitted | Flag 6, over the lawful maximum |
| `D_bad_format.csv` | Wrong column names, a 10-digit APAAR, blank required fields, bad dates | Validation errors and error report |
| `E_duplicates.csv` | Rows covering every duplicate class D1 to D5 | Duplicate resolver |
| `F_missing_apaar.csv` | 40% rows with no APAAR, some opted-out, some foreign nationals | Tiers T3 and T4, "nobody is rejected" |
| `G_large_5000.csv` | 5,000 clean rows | Performance target (under 60 seconds) |
| `H_resubmit_fixed.csv` | The corrected version of D | Resubmit flow, idempotency |
| `I_registry_down.csv` | Rows containing `...999` IDs | Registry unavailable behaviour |
| `template.csv` and `template.xlsx` | Header row and one example row | Download template |

#### M6. Anomaly training and evaluation dataset

| Property | Specification |
|---|---|
| Generator | `seed/generate_anomaly_data.py`, fixed seed 26263 |
| Size | **300 fictional institutions x 5 academic years**, with monthly admission counts and category mix per course |
| Planted anomaly types (labelled) | (1) **Late surge**: a large share of admissions in the last 14 days. (2) **Category-mix drift**: OCI/FN or NRI share far above peers. (3) **Shared-attribute cluster**: many students sharing one hashed contact or guardian token. (4) **100% streak**: every bucket exactly full for years. (5) **Post-audit withdrawals**: bulk withdrawals recorded after an audit date |
| Prevalence | About 6% to 10% of institution-years carry a planted anomaly |
| Labels | A column `is_anomaly` and `anomaly_type`. **The model never sees the labels during training** |
| Split | Held-out test set (for example 30% of institutions) |
| Baseline | A simple rule: flag if any single feature has a robust z-score above 3 |
| Output files | `models/anomaly_eval.json` with precision, recall, false-positive rate and PR-AUC per anomaly type, for the model and for the baseline |
| Honesty line shown in the app | "Evaluated on synthetic labelled data. Real accuracy requires an AICTE pilot with officer-labelled outcomes." |

#### M7. Demo users and mock OTP

| Property | Specification |
|---|---|
| Login | Email plus a **mock OTP: always `123456`** (clearly shown on the demo login page) |
| Accounts | One per role plus extras (see Section 5.1) |
| Role switcher | On the demo login page, big buttons: "Sign in as AICTE Officer", "...as College Admin", etc., so judges can switch roles in one click |

#### M8. Employer organisations

Eight fictional employers (for example "Demo Tech Pvt Ltd") with a verifier login each, used when a student creates a share code.

#### M9. Mock mail and SMS outbox

All "emails" and "SMS" are written to a table `outbox` and shown on a **"Mock Mail"** page (visible to every role for their own messages, and to Admin for all). Types: upload result, flag raised, clarification requested, ID reminder, consent created, consent withdrawn, verification performed.

#### M10. Certificate template and samples

A PDF template with the college name, student name, programme, **APAAR ID**, **student ID**, issue date and a **QR code** that opens the public verification page. Generate real PDFs from seeded graduating students.

#### M11. State admission data (placeholder)

Only a tile in the integration register labelled **FUTURE**. Optionally one static CSV displayed read-only. **No logic is built.**

#### M12. Demo clock

An Admin control "Set demo date". All date logic (rule effective dates, ID reminder deadlines, consent expiry, "audit date" for withdrawals) uses `app_now()` which reads the demo clock. Defaults to the real date.

#### M13. Signing keys and mock key vault

Generate a real **Ed25519** key pair at first start. Store it in `vault/` (clearly documented as a stand-in for a managed key store). Support "Rotate key" (new key id, old key kept for verifying old credentials).

#### M14. Pre-seeded audit history

Create about **2,000 audit entries** with a valid hash chain, covering earlier uploads, reviews, rule changes and consents, so the auditor screen looks lived-in.

#### M15. Institution API keys

Each seeded institution gets a demo API key (shown on the Institution API page) so the **upload API** can be demonstrated with `curl`.

#### M16. Typo-injected duplicate set (matching evaluation)

| Property | Specification |
|---|---|
| Generator | `seed/generate_matching_pairs.py`, fixed seed 26263 |
| Size | **400 true duplicate pairs** (the same fake person recorded at two colleges) and **400 near-miss pairs** (different people with similar names or the same date of birth) |
| Typo types injected into true pairs | Spelling variants (Kumar / Kumaar, Mohammad / Md), initials versus full names, middle name present or absent, extra spaces and case changes, transliteration variants (Aayush / Ayush), **day and month swapped** in the date of birth, **one wrong digit** in the date of birth |
| Labels | `is_true_duplicate` on every pair. The matcher never sees it |
| Used by | The fuzzy matcher (6.3) and the **Matching evaluation** page (precision, recall, F1, share sent to review) |

### 1.3 What is real and what is fake

| Real in the prototype (working code) | Fake in the prototype |
|---|---|
| Seat-Ledger engine and all checks | AICTE approval data (M1) |
| Rules Service, approval workflow, versioning, regression tests | Student data (M3) |
| Validation, identity tiers, duplicate classes | APAAR/DigiLocker (M4) |
| Anomaly scoring models (trained on synthetic data) | Anomaly training data (M6) |
| Consent, credentials, signatures, QR, revocation | OTP and demo users (M7) |
| Role-based access control and audit hash chain | Mail and SMS delivery (M9) |
| Upload API, reports, exports, dashboards | State data (M11) |

### 1.4 Reset and determinism

- `make seed` builds the whole database from scratch using seed 26263.
- `make reset-demo` restores the demo to its starting state in under 30 seconds (also available as an Admin button).
- A **"Scenario loader"** (Admin) can load any single scenario from Section 10 on its own.

---

## 2. The product in one page

### 2.1 Users and what each wants

| User | Wants | TrueRoll gives |
|---|---|---|
| AICTE National / Regional Officer | To know which colleges break seat rules, early, with proof | Live ledger, flag queue, review priorities, reports |
| Rules Owner (AICTE policy cell) | To keep rules correct and traceable | Rule book with provenance, two-person approval, tests |
| College Admin | To submit data once and fix errors easily | Upload wizard, fix list, seat usage, clarification replies |
| Student | To control their data and prove enrolment | Own record, consent manager, signed verified record |
| Employer / Verifier | A trustworthy yes/no | Scan-and-verify page |
| Auditor | To prove nothing was tampered with | Hash-chained audit trail, chain check |
| System Admin | To keep the demo healthy | Health, simulators, scenario loader, clock |

### 2.2 The flow (matches the PS flow)

```
Institution -> Upload -> APAAR validation -> Verification -> AICTE repository -> Analytics -> Authorised verification
```

In TrueRoll: **Upload** (college) -> **Validate** (clean, identity tier, duplicates) -> **Seat-Ledger** (caps from AICTE record) -> **Accepted / Warning / Flag** -> **Review queues** (rule flags and anomaly priorities) -> **Officer decision** -> **Student consent** -> **Employer verification** -> **Audit log** (every step).

### 2.3 The USP in plain words

**The Seat-Ledger Engine** keeps a separate counter for each seat type, takes caps from AICTE's own record, applies rules that are governed and versioned, and when something is wrong it says **which rule, which version and which students**. A simple "admitted > approved" counter cannot do this: it raises false alarms on lawful extra seats and cannot say why when it is right.

---

## 3. Architecture and technology

### 3.1 Layers (same as the locked architecture)

```
Users: officers, college admins, students, employers, rules owner, auditor, admin
Access: React web app + public REST API (OpenAPI) + login and roles
Core services: Ingestion | Identity + Duplicates | Seat-Ledger | Reporting
               Consent + Verification | Rules Service | Anomaly Intelligence
Data: database | audit log (hash chain) | file storage | key vault
Outside systems (all SIMULATED or FUTURE): AICTE records | DigiLocker/ABC | State data
```

### 3.2 Recommended stack

| Layer | Choice | Note |
|---|---|---|
| Frontend | **React + TypeScript + Vite**, Tailwind CSS, Recharts for charts, React Router, TanStack Query | Desktop first. Student view is mobile-friendly |
| Backend | **Python 3.12 + FastAPI**, Pydantic v2, SQLAlchemy 2 | Auto-generated OpenAPI docs at `/docs` |
| Database | **PostgreSQL** (SQLite is acceptable for the first run) | Use transactions for ledger updates |
| Background work | FastAPI background tasks or RQ/Celery with Redis | For large uploads |
| Live updates | **Server-Sent Events** (or polling every 5 s) | Officer dashboard updates when a college uploads |
| Auth | Token (JWT) login, role-based access control, mock OTP | Server checks every call |
| Signing | Python `cryptography` (Ed25519) | Real signatures |
| QR | `qrcode` library | |
| PDF | `reportlab` or `weasyprint` | Certificates and report exports |
| Anomaly | `scikit-learn`, `pandas`, `numpy` | Isolation forest plus robust baselines |
| Matching | `hmac`/`hashlib` plus `rapidfuzz` | Keyed tokens for T3/T4 |
| Tests | `pytest` (backend), Playwright (end-to-end) | Scenario suite is mandatory |
| Packaging | Docker Compose | One command to run everything |

### 3.3 Repository layout

```
trueroll/
  backend/
    app/
      api/            # routes per module
      core/           # config, security, roles, clock, audit
      models/         # database models
      services/
        ingestion/ identity/ duplicates/ ledger/ rules/ anomaly/ verification/ consent/ reporting/ notifications/
      adapters/       # RegistryAdapter, AicteAdapter (simulator implementations)
      simulators/     # registry, aicte, mock consent page
    tests/
  frontend/
    src/
      app/ components/ pages/<role>/ lib/ styles/
  seed/               # generators, rules, csv uploads, anomaly data
  models/             # anomaly_eval.json, trained model files
  vault/              # demo signing keys
  docs/               # SIMULATED.md, decisions.md, API.md
  docker-compose.yml  Makefile
```

### 3.4 Database tables (core)

| Table | Key fields |
|---|---|
| `institution` | id, name, region, state, city, type |
| `course_approval` | id, institution_id, name, level, domain, academic_year, approved_intake |
| `student` | id, full_name, dob, apaar_id (nullable), identity_tier, contact_token, guardian_token |
| `admission_event` | id, student_id, course_approval_id, seat_category, event_type (ADMIT / WITHDRAW / TRANSFER / CORRECTION), admission_round, event_time, upload_id |
| `seat_bucket` | id, course_approval_id, bucket_code, cap, used, updated_at |
| `rule` / `rule_version` | rule_id, version, scope fields, bucket, cap basis and percent, eligible categories, sub-buckets, source_document, source_clause, effective_from/to, status, enabled, approvals, test_suite_id |
| `evaluation` | id, subject (course approval), rule_set_hash, rule_versions_used, result, evaluated_at |
| `flag` | id, institution_id, course_approval_id, bucket, rule_id, rule_version, cap, used, over_by, record_ids, status, severity, opened_at, assigned_officer, decision, decision_reason |
| `flag_event` | id, flag_id, actor, action, note, time (the timeline) |
| `review_priority` | id, entity, period, score, band, reasons (json), model_version, status, officer_label |
| `duplicate_case` | id, class (D1 to D5), student_ids, evidence (json), status |
| `upload` | id, institution_id, file_name, file_hash, rows_total, rows_accepted, rows_warning, rows_error, status, started_at, finished_at, idempotency_key |
| `upload_error` | id, upload_id, row_number, code, message, field |
| `consent` | id, student_id, verifier_id, purpose, expires_at, status (ACTIVE / WITHDRAWN / EXPIRED), code_hash |
| `credential` | id, student_id, claims (json), signature, key_id, expires_at, revoked |
| `verification_log` | id, consent_id, verifier_id, result, checked_at |
| `audit_entry` | id, actor, role, action, object_type, object_id, time, prev_hash, hash |
| `user` | id, email, role, region, institution_id, student_id, employer_id |
| `employer` | id, name |
| `outbox` | id, to_user, channel, subject, body, time, type |
| `api_key` | institution_id, key_hash, created_at |
| `setting` | key, value (demo clock, registry mode, active key id) |

---

## 4. Design system

### 4.1 Colours (same palette as the slides)

| Token | Hex | Use |
|---|---|---|
| Navy | `#0B2545` | Headers, text, top bar |
| Blue | `#1F4E8C` | Primary buttons, links, structure |
| Green | `#1B8A3E` | Accepted, success, consent |
| Saffron | `#D9730D` | USP highlights (Seat-Ledger, Rules), warnings |
| Burnt orange | `#B45309` | Orange text on light backgrounds |
| Red | `#D62828` | Flags, problems, destructive actions |
| Slate | `#475569` | Secondary text |
| Tints | blue `#EAF0F9`, green `#E6F4EA`, orange `#FDF0DE`, red `#FCE7E7`, neutral `#F3F6FA` | Card backgrounds |

### 4.2 Typography and layout

- **Font:** Calibri (fallback Arial). Page titles 24px bold, section headings 16px bold in solid bars, body 14px, small labels 12px.
- **Layout:** top bar (logo "TrueRoll", role name, user menu, demo clock, language switch) and a left navigation per role. Content area on a 12-column grid.
- **Permanent ribbon:** a thin orange bar under the top bar: **"SAMPLE DATA. Simulated integrations. Not an official AICTE system."**

### 4.3 Shared components

| Component | Behaviour |
|---|---|
| **Status chip** | Accepted (green), Warning (orange), Flag (red), Advisory (blue outline) |
| **Tier badge** | T1 Verified (green), T2 Unverified (blue), T3 Pending (orange), T4 Opted-out or no route (slate). Tooltip explains each |
| **Seat bucket bar** | A progress bar per bucket, "238 / 240", turns orange at 95% and red when over |
| **Rule chip** | `SN-A v2` with a link to the rule record and the text "Illustrative" |
| **SIMULATED chip** | On every simulated source |
| **Evidence drawer** | A side panel listing the exact records behind a flag |
| **Timeline** | Vertical list of events (flag opened, clarification asked, college replied, decision) |
| **Empty, loading, error states** | Every table and chart has all three, with friendly text |
| **Toasts** | "Upload accepted: 1,188 of 1,204 records" |

### 4.4 Accessibility and responsiveness

Keyboard navigable, visible focus, colour never the only signal (chips have text), contrast checked, **student and employer pages work on a phone**, officer pages are desktop first.

### 4.5 Language (EXTRA)

A language switch with English and Hindi for the **student** screens only (labels and help text). Keep strings in a translation file.

---

## 5. Login, roles and every screen

### 5.1 Demo accounts (all use mock OTP `123456`) [MUST]

| Role | Demo email | Scope |
|---|---|---|
| AICTE National Officer | `officer.national@trueroll.demo` | All regions |
| AICTE Regional Officer (North) | `officer.north@trueroll.demo` | North region only |
| AICTE Regional Officer (South) | `officer.south@trueroll.demo` | South region only |
| Rules Owner (proposer) | `rules.owner@trueroll.demo` | Rule book |
| Rules Owner (second approver) | `rules.approver@trueroll.demo` | Rule book (a **different person**, required for two-person approval) |
| College Admin, hero college 1 | `admin.inst0001@trueroll.demo` | INST-0001 only |
| College Admin, hero colleges 2 to 6 | `admin.inst0002@...` to `admin.inst0006@...` | One college each |
| Student, verified | `student.verified@trueroll.demo` | Own record, tier T1 |
| Student, unverified | `student.unverified@...` | Tier T2 |
| Student, no ID | `student.noid@...` | Tier T3 |
| Student, foreign national | `student.foreign@...` | Tier T4 |
| Student, graduating | `student.graduating@...` | Has a certificate |
| Employer | `employer.demotech@trueroll.demo`, `employer.acme@...` | Verifier |
| Auditor | `auditor@trueroll.demo` | Read-only audit |
| System Admin | `sysadmin@trueroll.demo` | Prototype controls |

**Demo login page.** Email field, "Send OTP" button (mock: shows "Mock OTP is 123456"), plus a row of **"Quick sign-in as..."** buttons for every role so judges can switch in one click. A **"Switch role"** control stays in the top bar.

**Server rules for every screen below:** a role can only call its own routes. A wrong-role or wrong-scope request returns HTTP 403 and the screen shows "You do not have access to this." Add **one visible demo of this**: a College Admin pasting another college's URL gets the 403 page. [MUST]

### 5.2 Public pages (no login) [MUST]

| Page | Content |
|---|---|
| **Landing page** | One-line promise, three pictures (Upload, Check, Verify), a "Verify a certificate" box, "Open the demo" button, the SAMPLE DATA notice |
| **Certificate verification page** (the QR destination) | Shows: "Certificate is authentic / revoked / not found", institution, programme, issue date, student initials and last four of the APAAR ID. **Never shows** marks, address, DOB or phone. Every scan is logged. A student can switch this off from their account |
| **API documentation page** | The auto-generated OpenAPI page (`/docs`) with a short guide "Upload students with one request" and a `curl` example |
| **About and honesty page** | What is real, what is simulated (copy of Section 1.3), and the legend of status chips |

### 5.3 AICTE National Officer [MUST]

Left navigation: **Dashboard · Seat-Ledger · Flags · Review priorities · Institutions · Identity and duplicates · Reports · Rules (read-only) · My activity · Mock mail**

#### N1. Dashboard

Purpose: one live picture of the country.

```
+--------------------------------------------------------------------------------------------+
| TrueRoll   AICTE National Officer                       Demo date: 22 Oct 2026   [Switch] |
| SAMPLE DATA. Simulated integrations. Not an official AICTE system.                         |
+--------------------------------------------------------------------------------------------+
| [48 colleges: 44 reported] [8,973 students] [14 open flags] [9 high priorities] [93% IDs]  |
+--------------------------------------------+-----------------------------------------------+
| SEAT USAGE BY REGION (bar chart)           | LIVE ACTIVITY (updates by itself)             |
|  North  ████████████░  91%                 |  10:41  Sample Inst. of Tech. uploaded 1,204  |
|  South  ██████████░░░  84%                 |  10:41  Seat-Ledger: 1 flag raised (INST-0003)|
|  ...                                       |  10:38  Rule SN-PG v1 awaiting 2nd approval   |
+--------------------------------------------+-----------------------------------------------+
| NEEDS ATTENTION (top 5)                    | IDENTITY MIX (donut)  T1 55% T2 12% T3 25% T4 8%|
|  College A  CSE   +6 over   FLAG           |                                               |
|  College E  MCA   score 82  PRIORITY       | FLAG AGEING (bar)  0-3d  4-7d  8-14d  >14d    |
+--------------------------------------------+-----------------------------------------------+
```

Details:
- KPI cards come from live queries. Clicking a card opens the filtered list.
- **Live activity** uses server-sent events (or 5-second polling). When a college uploads in another browser window, a new row appears **without refresh**. This is the "real-time dashboard" requirement [MUST].
- Region chart: a bar per region, clicking drills into that region's institutions.
- "Needs attention" mixes flags and anomaly priorities and says which it is.

#### N2. Seat-Ledger monitor (the USP screen)

Filters: region, state, level, domain, academic year, status (All, Within limit, Near cap, Flag, Rule unconfirmed). Table:

| Column | Meaning |
|---|---|
| Institution, Course, Level | Identity of the row |
| Approved intake | From M1 (AICTE) |
| Lawful maximum | Computed from the **active** rules, with the rule chips (for example `SN-A v2`, `SN-B v1`) |
| Admitted | Current count |
| Regular / Extra used | Bucket counts |
| Status | Within limit, Near cap (95%), Flag (+N), **Rule unconfirmed** |

Clicking a row opens a **side drawer** with every bucket as a bar (`238 / 240`), the rules applied with their sources and versions, and links to flags.

**Compare mode toggle (top right): "Show simple counter vs Seat-Ledger"** [MUST]

```
+---------------------------------------------------------------------------------------------+
| COMPARE MODE: why a simple counter fails                                       [ON]  [OFF]  |
+---------------------------------+----------------------------+------------------------------+
| Course / admitted               | Simple counter (>240)      | Seat-Ledger                  |
+---------------------------------+----------------------------+------------------------------+
| College A / CSE      276        | ALARM (false alarm)        | No flag. Lawful under SN-A   |
|                                 |                            | v2 + SN-B v1 (276 = 240+24+12)|
| College B / CSE      276        | ALARM (cannot say why)     | FLAG 5. Extra seats held by  |
|                                 |                            | domestic students. SN-A v2   |
| College C / CSE      282        | ALARM (no detail)          | FLAG 6 over max 276          |
| College D / CSE      250        | ALARM                      | Rule unconfirmed: human      |
|                                 |                            | review, no automatic flag    |
+---------------------------------+----------------------------+------------------------------+
| Note: "Simple counter alarm" is not a regulatory finding. Numbers illustrative.            |
+---------------------------------------------------------------------------------------------+
```

The simple-counter column is computed by a tiny function (`admitted > approved`). The Seat-Ledger column calls the real engine. Both run on the same live data. A caption under the table states that the numbers are illustrative.

#### N3. Flags queue (Rule flags)

- Tabs: **Open · Under review · Clarification requested · Resolved · Escalated**.
- Columns: Flag ID, Institution, Course, Bucket, Over-by, Rule and version, Age, Assigned to, Status.
- Actions: assign to me, bulk assign (National only), sort by age or size, export CSV.
- A banner on top: "A flag is not a finding. An officer decides."

#### N4. Flag detail

```
+--------------------------------------------------------------------------------------------+
| FLAG #114   [Under review]   Rule: SN-A v2 (Illustrative)       Opened 22 Oct 09:58        |
| College C, B.Tech CSE, 2026-27: admitted 282 against an assumed maximum of 276 (6 above)   |
+------------------------------------------+-------------------------------------------------+
| SEAT LEDGER                              | WHY THIS FLAG                                   |
|  Regular        240 / 240  ██████████   |  Rule SN-A v2: OCI/FN extra seats = 10% of      |
|  OCI/FN extra    24 /  24  ██████████   |  approved intake (24 of 240)                    |
|  CIWGC extra     12 /  12  ██████████   |  Source: handbook addendum 2026-27              |
|  Over max         6                      |  Clause: TO BE CONFIRMED. Status: Active        |
|  Lawful max 276   Admitted 282          |  Effective 1 Jul 2026. Approved by two people.  |
+------------------------------------------+-------------------------------------------------+
| EVIDENCE: 6 records (277 to 282)  [Open list]  [Export]                                     |
|  Student ID | Admitted on | Seat category | Identity tier | Note                            |
+--------------------------------------------------------------------------------------------+
| TIMELINE  09:58 Flag raised (Seat-Ledger) > 10:12 Opened by Officer R. > ...               |
+--------------------------------------------------------------------------------------------+
| [Request clarification]   [Accept explanation]   [Escalate]            (reason required)    |
+--------------------------------------------------------------------------------------------+
```

- **Request clarification** opens a modal: message, optional deadline. The college sees it in its Flags page and gets a mock email. Status becomes *Clarification requested*.
- **Accept explanation** and **Escalate** require a written reason. The reason is saved in the timeline.
- "Escalate" shows "Handed to AICTE's formal process outside this platform." The platform never records a finding.
- Linked items: related duplicate cases, the college's earlier flags, the rule record.

#### N5. Review priorities (Anomaly Intelligence)

Table of ranked entities with columns **Entity (college or course), Period, Score (0-100 gauge), Band (Low/Medium/High), Top reasons (chips), Model version, Status**.

Detail drawer for a row:
- **Reason codes** with plain text: `LATE_SURGE: admissions in the last 14 days are 3.4 MAD above the peer median`, `CATEGORY_MIX: OCI/FN share is 2.1x the peer median`.
- **Charts:** (a) the college's monthly admissions with the surge highlighted, (b) a box plot of the peer group with this college as a dot, (c) category mix against peers.
- **Peer group description:** "Peers: same state, UG, intake 200-300 (n=14)".
- **Officer feedback buttons:** *Useful / Not useful / Need more information* (these are stored as labels for the future pilot).
- A fixed notice: **"Advisory only. Not a flag. Not a finding. Prototype model evaluated on synthetic data."**
- Link to **Model evaluation** (Section 6.6): a page with precision, recall, false-positive rate per anomaly type, model vs baseline. [MUST]

#### N6. Institution detail

Tabs: **Overview · Courses and ledger · Uploads · Flags · Identity · Duplicates · Anomaly history**. Overview shows profile, region, last upload, open flags, and identity mix. Courses tab shows every bucket bar. Uploads tab lists each upload with counts and a download of its error report.

#### N7. Identity and duplicates

- **Identity coverage:** donut of T1 to T4 nationally, bar by region, table by institution with "ID pending past deadline" highlighted.
- **Duplicate cases:** list with class chip D1 to D5, students involved (masked), evidence summary, status. Row opens a panel that shows the evidence and the **classification reason**, for example D3: "Same APAAR, one physical and one online programme. Possibly permitted under UGC dual-programme guidelines. Default: verify, no penalty."
- Actions: Mark as data error, Mark as permitted, Send for clarification, Keep on watch list (D5).
- **Matching evaluation tab:** precision, recall, F1 and share sent to review on the typo-injected set (6.3, M16).

#### N8. Reports [MUST]

A page listing at least these reports. Each has parameters, an on-screen preview, and **Export CSV** and **Export PDF**:

| # | Report | For |
|---|---|---|
| R1 | Seat utilisation by course | Monitoring |
| R2 | Over-cap and rule-flag summary | Monitoring |
| R3 | Identity coverage by tier, region, college | Policy |
| R4 | Duplicate case summary | Monitoring |
| R5 | Flag lifecycle and ageing | Monitoring |
| R6 | College compliance scorecard | **Accreditation** |
| R7 | Withdrawals and transfers | Monitoring |
| R8 | Review priority ranking | Monitoring |
| R9 | Regional summary | Policy |
| R10 | Category mix by state | Policy |
| R11 | Rule versions used in evaluations | Audit |
| R12 | Prototype evaluation summary (6.14) | Evidence for judges |

#### N9. Rules (read-only), My activity, Mock mail

Officers can read rules and their sources but cannot edit. **My activity** lists the officer's own actions. **Mock mail** shows messages they would have received.

### 5.4 AICTE Regional Officer [MUST]

Same screens as the National Officer with these differences:
- A fixed **region badge** in the top bar ("Region: North").
- Every list and chart is filtered to that region **on the server**.
- Pasting a flag URL from another region shows the 403 page.
- Bulk assign is hidden. "Escalate to National" is available.

### 5.5 Rules Owner and second approver [MUST]

Navigation: **Rule book · Propose · Approvals · Tests and backtest · Changelog · Unconfirmed-rule watch**

#### R1. Rule book

Table of all rules: Rule ID, Version, Scope (year, level, domain, state), Bucket, Cap, Effective from, **Status chip** (Draft, Pending approval, Approved, Active, Retired), Enabled toggle (only Active rules may be enabled).

#### R2. Rule detail (provenance page)

```
+--------------------------------------------------------------------------------------------+
| RULE SN-A   Version 2   [Active]   Illustrative: to be confirmed against AICTE rules        |
+--------------------------------------------+-----------------------------------------------+
| WHAT IT SAYS                               | WHERE IT COMES FROM                           |
|  Bucket: OCI/FN extra seats                |  Document: Handbook addendum 2026-27 [attach] |
|  Cap: 10% of approved intake               |  Clause: TO BE CONFIRMED                      |
|  Eligible: FN, OCI, PIO                    |  Source URL / uploaded PDF                    |
|  Scope: UG Engineering, 2026-27, all states|                                               |
|  Effective 1 Jul 2026 to open-ended        |                                               |
+--------------------------------------------+-----------------------------------------------+
| APPROVALS  Proposed by rules.owner  >  Approved by rules.approver (22 Oct 17:20)            |
| TESTS      Regression suite seat_ledger_v3: 14/14 passed   Backtest on 2025-26: 3 changes  |
| USED BY    1,240 evaluations (rule version stored with each one)                            |
| HISTORY    v1 Retired (2025-26)  >  v2 Active (2026-27)        [Compare v1 and v2]          |
+--------------------------------------------------------------------------------------------+
```

#### R3. Propose a rule or a new version

Form: rule ID, scope fields, bucket, cap basis (percent of intake or fixed number), eligible categories, sub-buckets and reversion, effective dates, **source document (required)**, **clause (required)**, attachment. Saves as **Draft**. Cannot be submitted without a source.

#### R4. Approval queue

Lists rules in *Pending approval*. The second approver sees **Approve** and **Reject** (comment required). The proposer sees the buttons **disabled** with the tooltip "A different person must approve." [MUST] (This is the two-person demo.)

#### R5. Tests and backtest [MUST]

- **Regression suite:** a table of scenarios (A, B, C and edge cases) with expected and actual results and a pass/fail chip. A **Run tests** button executes them live against the proposed rule.
- **Backtest:** choose a previous academic year. The page lists **which institutions would change status** under the proposed rule, with before and after. A rule cannot be approved until its tests pass.

#### R6. Activation

On the effective date (read from the demo clock) an Approved rule becomes Active. Show a button **"Advance demo clock to effective date"** for the demo. After activation the Ledger re-runs **only for the rule's academic year**, writing **new** evaluation records. Old evaluations keep the rule version they used. [MUST]

#### R7. Changelog and unconfirmed-rule watch

- Changelog: who changed what, when, on which source.
- **Unconfirmed-rule watch:** lists courses whose evaluation depends on a Draft, Pending or disabled rule. For these the Ledger does **not** raise an automatic flag; it shows **"Rule not confirmed: human review."** [MUST]

### 5.6 College Admin [MUST]

Navigation: **Dashboard · Upload · My seats · Students · Flags and clarifications · Certificates · API · Mock mail · Help**

#### C1. Dashboard

Cards for each course: name, approved intake, a bucket bar set, status chip. Below: last upload result, open clarification requests, **ID reminders** (number of T3 students with deadline), notifications.

#### C2. Upload wizard (the main college journey)

```
 Step 1 CHOOSE        Step 2 CHECKING          Step 3 RESULTS            Step 4 FIX
 [Course v]           Reading rows ...         1,204 read                [Download error list]
 [Drop a file here]   ████████░░ 82%           1,188 accepted            [Upload corrected rows]
 [Download template]  1,000 / 1,204            9 warnings
 Mode: ( ) full list  Identity tiers ...       7 need your action        "Re-uploading the same
       ( ) round      Duplicate check ...                                 file changes nothing."
```

Step 3 tabs:
- **Errors:** table with Row, Field, Code, Message and a **fix hint** (for example "APAAR must be 12 digits"). Download as CSV.
- **Warnings:** for example "9 students have no APAAR ID yet: marked ID pending, add by 31 Jan."
- **Identity tiers:** counts T1 to T4.
- **Duplicates:** cases found, with class chips.
- **Seat check (live result):** the course's buckets after the upload, bars, and any flag.
- **Failure messages:** "Registry unavailable: students shown as unverified and retried. Nobody was rejected."

Behaviour [MUST]: valid rows are kept even if some rows fail. The same file uploaded twice creates **no duplicates** (idempotency). Large files process in the background with a progress bar. The officer dashboard updates live when the upload finishes.

#### C3. My seats

For each course: every bucket as a bar, the **lawful maximum with rule chips and sources**, a warning at 95% ("OCI/FN extra seats are nearly full"), and a plain-language explanation of each rule. **What-if tool [EXTRA]:** "If I admit 5 more OCI/FN students, will I stay within limits?" (a read-only calculation using the same engine).

#### C4. Students

Searchable table (name, APAAR, tier badge, course, seat category, status). A student's detail page offers: **Add or correct APAAR ID**, **Send reminder**, **Record opt-out** (the student must confirm in their own account), **Foreign national route** (explains the alternative identifier), **Record withdrawal or transfer** (with date; releases a seat). Withdrawals recorded after an "audit date" show a note that they will be reviewed.

#### C5. Flags and clarifications

Only this college's flags. Each opens a thread: officer message, the college's reply box with attachments, status chips. Buttons **Submit explanation** and **Submit corrected data** (which goes to the upload wizard). The college can never see other colleges.

#### C6. Certificates

For graduating students: generate a **certificate PDF** containing college, student name, programme, **APAAR ID and student ID**, issue date and a **QR code**. List, download, and **Revoke** (with reason).

#### C7. API

Shows the college's demo API key (masked, with Reveal), the endpoint, a ready-to-copy `curl` for uploading a CSV, expected responses and error codes, the rate limit, and a **"Test connection (simulated)"** button. [MUST]

#### C8 and C9. Mock mail and Help

Messages the college would receive. Help explains tiers, rules, flags and how to fix errors in simple words.

### 5.7 Student [MUST]

Mobile-first. Navigation: **My record · Identity · Consent · Access log · Certificates · Data and privacy · Mock mail**

#### S0. Sign-in

Phone or email plus mock OTP. A first-time screen explains in three lines what TrueRoll holds and why.

#### S1. My record

```
+--------------------------------------+
| Priya (sample)                       |
| Sample Institute of Technology       |
| B.Tech Computer Science, 2026-30     |
| [Enrolled]   [T1 Verified]           |
| APAAR ID: linked (ends 4271)         |
|                                      |
| [Download my verified record]        |
+--------------------------------------+
```

"Download my verified record" produces a signed JSON and a PDF with a QR.

#### S2. Identity (and what to do)

Shows the tier and its meaning in plain words.
- **T1:** "Your APAAR ID is verified."
- **T2:** "Your APAAR number was entered but not verified yet." Button **Verify now** (opens the **mock consent page**, then returns T1).
- **T3:** "You have no APAAR ID yet. **You are still counted and nothing is held against you.**" Button *How to get one* (information only).
- **T4:** "You opted out or have no route to an APAAR ID. **You are counted. No penalty.**"
- Buttons: **Link my APAAR ID**, **I do not have one**, **I want to opt out**, **I am a foreign national**.

#### S3. Consent manager (key USP screen) [MUST]

```
+--------------------------------------------------+
| WHO CAN VERIFY ME                                |
|  Demo Tech Pvt Ltd   Internship   until 30 Nov   |
|  [ACTIVE]                          [Withdraw]    |
|--------------------------------------------------|
| [+ Create a share code]                          |
|  1 Choose verifier  [Demo Tech Pvt Ltd v]        |
|  2 Purpose          [Internship v]               |
|  3 Valid for        (7) (30) (90) days           |
|  4 What they will see:                           |
|      Enrolled: yes/no, college, programme        |
|      They will NOT see: marks, address, DOB...   |
|  [Create]  ->  QR + code  K7F2-9XQD              |
+--------------------------------------------------+
```

- A share code is bound to **one verifier, one purpose and an expiry**.
- The preview shows exactly the minimal response the employer will get.
- **Withdraw** is immediate: the next scan fails with "Consent withdrawn." A confirmation dialog explains this.
- A timeline shows created, used, withdrawn.

#### S4. Access log

Every verification: who, when, result, which consent. Also shows reads by college admins or officers of the student's record, where those happened.

#### S5. Certificates

Download certificate PDFs. Toggle **"Allow the certificate QR to be scanned publicly"** (default on).

#### S6. Data and privacy

A plain list: "TrueRoll stores: name, APAAR (if any), programme, seat category, status. TrueRoll never stores: marks, address, Aadhaar number." Buttons: **Request a correction** (creates a message to the college admin) and **Notification preferences**.

### 5.8 Employer / Verifier [MUST]

Navigation: **Verify · My checks · Organisation**. First login requires accepting the **purpose-limitation terms**.

#### E1. Verify

```
+--------------------------------------------------------------------+
| VERIFY A STUDENT                                                   |
| [ Paste code or link ]  [Scan QR]  [Upload QR image]   [Verify]   |
+--------------------------------------------------------------------+
| RESULT                                                             |
|  [OK] VERIFIED: signature valid                                    |
|  Student       A.K.M. ...4271                                      |
|  Institution   Sample Institute of Technology                      |
|  Programme     B.Tech Computer Science                             |
|  Status        Enrolled (2026-30)                                  |
|  Checked on    22 Oct 2026 10:41   Valid until 30 Nov 2026         |
|  Shared by     the student, for Demo Tech Pvt Ltd (Internship)     |
+------------------------------+-------------------------------------+
| NEVER SHOWN                  | Marks, address, DOB, phone, Aadhaar,|
|                              | other colleges, college flags       |
+------------------------------+-------------------------------------+
```

Result states, each with its own colour and message [MUST]:

| State | Message |
|---|---|
| Verified | As above |
| Expired | "This code has expired. Ask the student for a new one." |
| Withdrawn | "The student has withdrawn consent." |
| Not for this verifier | "This code was issued to a different verifier." |
| Invalid signature | "This credential failed the signature check." |
| Not found | "No such code." |

The camera scan uses the browser camera (QR library). If the camera is not allowed, the paste and upload options still work.

#### E2 and E3. My checks and Organisation

A history table of the employer's own checks, and organisation details. A visible rate-limit notice ("20 checks per hour in this prototype").

### 5.9 Auditor [MUST]

Navigation: **Audit trail · Access log · Rule history · Exports**

#### A1. Audit trail with chain check

```
+--------------------------------------------------------------------------------------------+
| AUDIT TRAIL     48,210 entries        Chain: [ VALID ]            [Verify chain now]        |
+--------+--------------+--------------------+----------------------+------------------------+
| Time   | Actor        | Action             | Object               | Hash (first 8) | Link  |
| 10:41  | Employer ABC | Verified enrolment | Student ...4271      | 9fa3c1d2       |  OK   |
| 10:12  | Officer R.   | Opened flag #114   | College A / CSE      | 41be07aa       |  OK   |
+--------+--------------+--------------------+----------------------+------------------------+
```

**Verify chain now** recomputes every hash and shows a progress bar and a result:
- Valid: "No entry changed or removed."
- Broken: "Chain broken at entry 31,204. Expected 9fa3c1d2, found 00aa11bb." with the entry highlighted red.

Filters: actor, role, action, object, date range. **Export CSV.**

#### A2 to A4

**Access log** (every read or verification of student data), **Rule history** (every rule change), **Exports** (CSV of any of these). The Auditor is **read-only** and cannot see student details by default (names are masked).

### 5.10 System Admin (prototype controls) [MUST]

Navigation: **Health · Simulators · Scenarios · Clock · Keys · Jobs · Backups · Tamper demo**

| Screen | What it does |
|---|---|
| **Health** | Green or red status for API, database, queue, registry simulator, AICTE simulator |
| **Simulators** | Registry **Up / Slow / Flaky / Down** switch, AICTE feed on or off, request counters. A note states: **"Live APAAR and DigiLocker access needs registered approval (API Setu requester onboarding). This prototype uses a simulator behind the same adapter."** Also a **Reconcile now** button (section 6.4). Shows the **integration register** with chips LIVE (none), SIMULATED, FUTURE |
| **Scenarios** | A button per scenario from Section 10 (load only that one) and **Reset demo** |
| **Clock** | Set the demo date, with "Advance one day" and "Advance to rule effective date" |
| **Keys** | Active signing key id, **Rotate key** (old key kept to verify old credentials) |
| **Jobs** | Uploads in progress, retry queue, failed items (dead letter) with a **Retry** button |
| **Backups** | **Create backup** and a list. Labelled: **"Backups are planned for production and not yet tested."** |
| **Tamper demo** | Prototype-only. **"Edit an old audit entry"** changes one stored row directly in the database so the Auditor's chain check fails; **"Restore"** repairs it. Clearly labelled "Prototype demonstration only" |

### 5.11 Cross-role features [SHOULD]

- **Global search** (officers): find a college, course or flag by name or ID.
- **Notification bell** with unread count for every role.
- **Keyboard shortcut** `?` opens help.
- **Print-friendly** flag detail and reports.

---

## 6. Engines and logic (how each feature really works)

### 6.1 Ingestion and validation [MUST]

**Accepted inputs:** CSV and XLSX through the web wizard, and CSV through the upload API. Maximum file size 10 MB.

**Required columns (the template):**

| Column | Rule |
|---|---|
| `student_ref` | The college's own ID. Used for the idempotency key |
| `full_name` | Required |
| `date_of_birth` | `YYYY-MM-DD`, age 15 to 60 |
| `apaar_id` | Optional. If present, exactly 12 digits |
| `nationality_status` | `INDIAN`, `NRI`, `OCI`, `PIO`, `FN`, `CIWGC` |
| `seat_category` | `REGULAR`, `NRI_IN`, `OCI_FN_EXTRA`, `CIWGC_EXTRA`, `EWS` |
| `course_code` | Must exist in the AICTE approval record (M1) for the college and year |
| `admission_date` | `YYYY-MM-DD`, not in the future (uses the demo clock) |
| `mode` | `FULL_TIME` or `ONLINE` (used for duplicate classes) |
| `timing_slot` | Optional: `MORNING`, `EVENING`, `WEEKEND` |
| `admission_round` | Optional, default `ROUND_1`. Values `ROUND_1`, `ROUND_2`, `ROUND_3`, `SPOT` |
| `entry_type` | Optional, default `REGULAR`. `LATERAL` for lateral entry |
| `gender` | Optional |
| `contact_phone`, `guardian_name` | Optional. **Converted to keyed hash tokens on receipt. The raw values are never stored** |

**Validation codes (data format only; seat problems are flags, not validation errors):**

| Code | Type | Meaning |
|---|---|---|
| E101 | Error | Missing required column or value |
| E102 | Error | APAAR is not exactly 12 digits |
| E103 | Error | Invalid or impossible date |
| E104 | Error | Unknown course code for this college and year |
| E105 | Error | Invalid seat category or nationality value |
| E106 | Error | Same student twice in the same file (duplicate class D1) |
| W201 | Warning | No APAAR ID (tier T3) |
| W202 | Warning | APAAR present but not verified (tier T2) |
| W203 | Warning | Registry unavailable, retry scheduled |
| W204 | Warning | Possible duplicate across colleges (class D2 to D5, see 6.3) |
| W205 | Warning | Withdrawal recorded after an audit date |

**Processing steps (one background job per upload):**

1. Compute `file_hash`. If the same `(institution, year, file_hash)` was already processed, return the earlier result (**idempotent**).
2. Parse rows and validate. Collect errors and warnings per row.
3. For every valid row create or update the student by the **idempotency key** `(institution, academic_year, student_ref)`. Re-uploading never duplicates.
4. Assign the identity tier (6.2) and classify duplicates (6.3).
5. In **one database transaction per course**, write admission events and update seat buckets.
6. Run the Seat-Ledger for each affected course (6.4).
7. Write the upload summary, send mock notifications, write audit entries, and push a live event (6.12).

**Partial success:** valid rows are kept. Failed rows are returned in an error report (CSV) that the college can fix and re-upload as `H_resubmit_fixed.csv` does.

**Progress:** the job table stores `rows_processed` and the wizard polls it every second.

### 6.2 Identity tiers [MUST]

Identity verification status and admission validity are **separate**. A tier never rejects a student.

| Tier | How assigned | Treatment |
|---|---|---|
| **T1 Verified** | APAAR present and the registry adapter returned `VERIFIED` (after the student's consent on the mock consent page) | Strongest key for duplicates |
| **T2 Unverified** | APAAR present with valid format but not yet verified, **or** the registry was unavailable | Verification queue. Retried. Shown as "Unverified" |
| **T3 Pending** | No APAAR ID | Provisional ID created by the college. Reminder with a deadline. **Counted** |
| **T4 Opted-out or no route** | Student opted out, or foreign national with no route | Alternative identifier token. **Counted. No penalty** |

**Verification flow:** a college upload creates tier T2. The student (or a "Verify now" action) starts the **mock consent page**. On Allow, the backend calls `RegistryAdapter.verify()`. Result `VERIFIED` moves the student to T1, `MISMATCH` shows "Details do not match, contact your college", `UNAVAILABLE` leaves T2 and schedules a retry (retry button for the demo).

### 6.3 Duplicate resolver [MUST]

Matching uses, in order: exact APAAR, then keyed tokens (`contact_token`, `guardian_token`), then a name and date-of-birth fuzzy match (`rapidfuzz`, threshold 92) as a **weak** signal only.

| Class | Detection | Action | Confidence |
|---|---|---|---|
| **D1** | Same student, same course, same college (same file or earlier) | **Auto-reject the second row** as a data error. The only automatic action | High |
| **D2** | Same APAAR in two colleges, both `FULL_TIME`, **overlapping timing slots** | Create a review case | Medium-high |
| **D3** | Same APAAR, one `FULL_TIME` and one `ONLINE`, **or** non-overlapping timing slots | "Possibly permitted." Verify. **No penalty by default** | Low as a violation |
| **D4** | No APAAR, strong match across colleges: keyed-token match, **or fuzzy score of 0.93 or more** | Review case | Medium |
| **D5** | No APAAR, fuzzy score from 0.85 to 0.93 | Watch list only. **Not a flag** | Low |

Every case stores its **evidence and reason** in plain words. The case screen shows the note: "Dual enrolment can be permitted under UGC rules. AICTE's position for technical programmes must be confirmed. Default: verify, do not penalise."

#### Matching without an APAAR ID (fuzzy) [MUST]

Exact keyed tokens break on typos, so students **without** an APAAR ID are matched in two steps.

1. **Exact first:** if both records carry an APAAR ID, match exactly on it. Otherwise try the keyed contact and guardian tokens.
2. **Fuzzy second** on the normalised record:
   - **Normalise:** lower-case, strip honorifics and punctuation, collapse spaces, expand common abbreviations (Md to Mohammad), apply a small transliteration map (Aayush / Ayush, Kumaar / Kumar).
   - **Name similarity** = the higher of `rapidfuzz` token-sort ratio and Jaro-Winkler, plus a bonus if the Double Metaphone keys match.
   - **Date of birth:** exact = 1.0, day and month swapped = 0.9, one wrong digit = 0.8, otherwise 0.
   - **Course and year:** bonus if the same course family and year.
   - **Score** = `0.50 * name + 0.35 * dob + 0.15 * course_year`.
3. **Thresholds:** score of **0.93 or more** creates a **D4 review case**. **0.85 to 0.93** goes to the **D5 watch list**. Below 0.85 nothing happens. **Nothing is ever auto-flagged or auto-rejected on a fuzzy match.**

**Privacy note:** in the prototype the matcher runs inside the secured service on normalised stored values. A production version would use privacy-preserving, Bloom-filter style encoding as in published linkage studies, which must be **re-evaluated by us** because their reported 99.3% agreement came from a different method and data.

**Matching evaluation page [MUST]** (Officer, Identity and duplicates, tab "Matching evaluation"): run the matcher on M16 and show **precision, recall, F1, and the share of true pairs sent to review**, by typo type. Headline wording: "Measured on synthetic typo-injected data. Real accuracy needs a pilot."

### 6.4 The Seat-Ledger Engine (the USP) [MUST]

#### Inputs

- **Approved intake** from the AICTE record (M1), never from the college.
- The **active rule set** for the course (6.5), chosen by academic year, level, domain, state.
- All admission events (admit, withdraw, transfer) with seat category, nationality, tier and time.

#### State

Counters per `(course_approval, bucket)`: `cap` and `used`. They are updated **in the same transaction** as the admission event, so every check is a constant-time lookup.

#### Buckets used in the demo

`REGULAR` (includes `NRI_IN`, which is inside the intake), `OCI_FN_EXTRA`, `CIWGC_EXTRA`, `EWS` (only if an active rule exists).

#### Checks

| Check | Test | Result if it fails |
|---|---|---|
| **C1 Bucket cap** | `used[bucket] > effective_cap[bucket]` | Flag with bucket, cap, used, over-by |
| **C2 Total maximum** | `sum(used) > approved_intake + sum(extra caps)` | Flag "over the lawful maximum" |
| **C3 Eligibility** | A student in an extra bucket whose `nationality_status` is not eligible for it (for example a domestic student in `OCI_FN_EXTRA`) | Flag listing the **ineligible holders** |
| **C4 Reversion** | If `CIWGC_EXTRA` has vacant seats, `OCI_FN_EXTRA` may use them: `effective_cap[OCI_FN] = cap[OCI_FN] + max(0, cap[CIWGC] - used[CIWGC])` | Applied **before** C1 so a lawful reversion is not flagged |
| **C5 Timing** | Bulk withdrawals recorded after an "audit date" | Warning W205 and a review note |

#### Rule-not-confirmed path [MUST]

If the course needs a rule that is **Draft, Pending, disabled or missing**, the engine returns `RULE_NOT_CONFIRMED`. It raises **no automatic flag**. It creates a **review item** with the reason "Rule not confirmed" and shows it in the Rules Owner's watch list and the officer's Seat-Ledger status column.

#### Pseudo-code

```python
def evaluate(course, as_of):
    rules = rules_service.active_for(course, as_of)          # Active, enabled, in date, in scope
    if rules.missing_or_unconfirmed:
        return Result(status="RULE_NOT_CONFIRMED", flags=[], review_reason="Rule not confirmed")
    caps = compute_caps(course.approved_intake, rules)        # per bucket, e.g. REGULAR 240, OCI_FN 24, CIWGC 12
    used = ledger.counts(course)                              # per bucket, active admissions only
    eff = apply_reversion(caps, used, rules)                  # C4
    reasons = []
    for b in buckets:
        if used[b] > eff[b]: reasons.append(Reason("C1", b, cap=eff[b], used=used[b]))
    if sum(used.values()) > lawful_max(course.approved_intake, rules):
        reasons.append(Reason("C2", total_used=sum(used.values()), maximum=lawful_max(...)))
    bad = ineligible_holders(course, rules)                   # C3
    if bad: reasons.append(Reason("C3", students=[s.id for s in bad]))
    ev = Evaluation(course, rule_versions=rules.versions(), rule_set_hash=rules.hash(), result=...)
    store(ev)                                                  # never overwritten
    return upsert_flag_if_needed(course, reasons, ev)          # one open flag per course and bucket
```

#### Flag rules

- One **open flag per course and bucket**. A new evaluation **updates** it (new evaluation id, new numbers). It does not create a flood.
- A flag stores `rule_id`, `rule_version`, `cap`, `used`, `over_by`, `record_ids`, `first_breach_at`.
- When the numbers return within limits the flag moves to **"Auto-cleared pending officer review"**; only an officer closes it.

#### Examples the code must reproduce (approved intake 240)

| Case | Result |
|---|---|
| Regular 240, OCI/FN 24, CIWGC 12 (276 total, valid categories) | No flag |
| Regular 240, OCI/FN 24, CIWGC 12, but 5 of the extra seats held by `INDIAN` students | C3 flag, 5 ineligible holders |
| 282 total | C2 flag, 6 over, plus C1 on the bucket that overflowed |
| CIWGC used 4 of 12, OCI/FN used 30 | C4: effective OCI/FN cap = 24 + 8 = 32. **No flag** |
| CIWGC used 12, OCI/FN used 30 | C1 flag on OCI/FN: 6 over |
| Course whose rule is Draft | `RULE_NOT_CONFIRMED`, no flag |

#### Reconciliation and edge cases [MUST]

- **Counters are derived from the event history.** The event types are `ADMIT`, `WITHDRAW`, `TRANSFER` and `CORRECTION`. A **correction** (for example fixing a seat category or a course) is a new event that supersedes the old one. History is never edited.
- **`reconcile(course)`** recomputes every bucket from the events and compares it with the stored counters. The result must be **zero drift**. It runs after every withdrawal, correction and re-upload, and an Admin button **"Reconcile now"** runs it for all courses and shows the result.
- **Spot rounds** use the same buckets and are tagged by `admission_round`. They add no new cap.
- **Lateral entry:** if the AICTE record (M1) gives a `lateral_intake` for the course, lateral students count against a separate `LATERAL` bucket with that cap. If it gives none, the course returns `RULE_NOT_CONFIRMED` for lateral students (human review).
- **Re-uploads** are idempotent (6.1), so they never inflate a counter.

#### The simple counter (for Compare mode only)

```python
def simple_counter(course): return "ALARM" if course.admitted > course.approved_intake else "OK"
```

### 6.5 Rules Service, governance and versioning [MUST]

#### Rule record

```yaml
rule_id: SN-A
version: 2
scope: { academic_year: "2026-27", programme_level: [UG], domain: "Engineering and Technology", state: ALL, institution_type: ALL }
bucket: OCI_FN_EXTRA
cap: { basis: approved_intake, percent: 10 }
eligible_categories: [FN, OCI, PIO]
sub_buckets: {}
source: { document: "AICTE handbook addendum 2026-27 (illustrative)", clause: "TO BE CONFIRMED", url: "attach PDF" }
effective_from: "2026-07-01"
effective_to: null
status: active              # draft | pending_review | approved | active | retired
enabled: true               # only 'active' may be true
approvals: [ { by: rules.owner, role: proposer }, { by: rules.approver, role: approver, at: "..." } ]
test_suite: seat_ledger_regression_v3
```

#### Lifecycle (enforced by the server)

| Step | Gate |
|---|---|
| Draft | Source document and clause are required to leave Draft |
| Pending review | A **different** user than the proposer must approve (`approver != proposer`, enforced server-side) |
| Regression | The suite must pass 100% |
| Backtest | Computed and shown. Informational but recorded |
| Approved | Two distinct people recorded |
| Active | On the effective date by the demo clock, **only for its scope and academic year** |
| Retired | Superseded. Kept for history |

**Who owns the rules (deployment assumption).** In a real deployment AICTE would nominate a rules team that holds the Rules Owner and approver roles. In the prototype this is two demo users. The slides present this as an assumption.

#### Historical decisions [MUST]

- Every evaluation stores `rule_versions_used` and `rule_set_hash`.
- Activating a new version **re-evaluates only courses in its academic year** and writes **new** evaluation rows. Old rows are never edited.
- The Rules Owner screen "Compare v1 and v2" and the Flag detail "Rule used" must always show the version that evaluation used.

#### Regression suite (must exist as automated tests)

At minimum the six examples in 6.4, plus: lawful 276, ineligible holders, 282, reversion lawful, reversion exceeded, draft rule, withdrawal frees a seat, transfer between buckets, rule change applies only to its year.

### 6.6 Anomaly Intelligence [MUST]

Strictly separate from the policy checks. It produces **Review priorities**, never flags.

#### Features (per institution, course and academic year)

| Feature | Meaning |
|---|---|
| `late_share_14d` | Share of admissions in the last 14 days of the cycle |
| `surge_ratio` | Last-14-day admissions divided by the college's own historical median |
| `mix_ocifn`, `mix_nri`, `mix_ciwgc`, `mix_ews` | Category shares compared with the peer median |
| `fill_streak` | Consecutive years every bucket was exactly full |
| `withdraw_rate` and `post_audit_withdrawals` | Withdrawal behaviour |
| `max_cluster` | Largest group of students sharing one hashed contact or guardian token (graph connected components) |
| `dob_concentration` | Share of the most common date of birth |

#### Peer groups

Same state, same level, intake band (for example 200 to 300). If a group has fewer than 8 members, widen to the same region and level. Show the peer group and its size in the UI.

#### Method (standard and explainable)

1. **Robust baseline:** for each feature compute a robust z-score `z = (x - median) / (1.4826 * MAD)` against the peer group.
2. **Isolation forest** on the standardised feature vector (`n_estimators=200`, `contamination=0.08`, `random_state=26263`).
3. **Graph clustering** for shared tokens (cluster size 5 or more).
4. **Score:** `s_if` = percentile rank of the isolation-forest score within the peer group, `s_rz = min(1, max|z| / 6)`, `score = round(100 * (0.5*s_if + 0.5*s_rz))`.
5. **Band:** below 40 Low, 40 to 69 Medium, 70 and above High (threshold tuned on a validation split and recorded).
6. **Reasons:** the top three features by `|z|`, mapped to plain-language reason codes (`LATE_SURGE`, `CATEGORY_MIX`, `SHARED_ATTRIBUTE_CLUSTER`, `FULL_STREAK`, `POST_AUDIT_WITHDRAWALS`).

#### Output record

```json
{ "entity": "INST-0005", "course": "MBA", "period": "2026-27", "review_priority": 82, "band": "HIGH",
  "reasons": [ {"code": "LATE_SURGE", "detail": "Admissions in the last 14 days are 3.4 MAD above peer median"},
               {"code": "CATEGORY_MIX", "detail": "OCI/FN share is 2.1x the peer median"} ],
  "peer_group": "Same state, PG, intake 90-150 (n=11)", "model": "robust_baseline + isolation_forest v0.1",
  "status": "advisory" }
```

#### Evaluation (script `scripts/evaluate_anomaly.py`, results to `models/anomaly_eval.json`)

- Train on the non-held-out institutions without labels. Score the held-out set.
- Report **precision, recall, false-positive rate and PR-AUC per anomaly type**, for the model and for the **baseline**, plus precision at top-k.
- If the model does not beat the baseline on a type, the page **shows that honestly**.

#### "Model evaluation" page [MUST]

Table of the metrics above, a precision-recall chart, a confusion matrix, and the honesty notice: *"Evaluated on synthetic labelled data. Real accuracy requires an AICTE pilot with officer-labelled outcomes."* **[EXTRA]** A threshold slider that recomputes precision and recall from the stored test scores.

### 6.7 Consent and verification [MUST]

#### Share code

1. The student picks a verifier (employer), a purpose and an expiry (7, 30 or 90 days).
2. The server creates a `consent` row and a **random 40-bit code** (displayed as `K7F2-9XQD`). Only a **hash** of the code is stored.
3. The QR contains `https://<host>/v/<code>`.

#### Credential format (real signatures)

A compact **JWS signed with Ed25519** (`alg: EdDSA`):

```json
{ "iss": "trueroll.demo", "sub": "stu_9c1f...", "inst": "Sample Institute of Technology",
  "programme": "B.Tech Computer Science", "status": "ENROLLED", "period": "2026-30",
  "verifier": "emp_demotech", "purpose": "Internship", "consent_id": "con_4417",
  "iat": 1792665660, "exp": 1795344060, "kid": "key-2026-10-a" }
```

The student's own **downloadable verified record** is the same format with a longer expiry and no verifier.

#### Verification algorithm

1. Employer submits a code (typed, scanned, or from a link).
2. Server hashes it and finds the consent. Not found returns `NOT_FOUND`.
3. If the consent is `WITHDRAWN` return `WITHDRAWN`. If past expiry return `EXPIRED`.
4. If the logged-in employer is not the consent's verifier return `NOT_FOR_THIS_VERIFIER`.
5. Read the student's **current** enrolment status. Build fresh claims and **sign** them.
6. **Verify the signature** with the public key for that `kid` (this is the visible "signature valid").
7. Return the **minimal response** (below). Write a `verification_log` row, an audit entry, and a mock notification to the student.

**Minimal response (the only fields an employer ever gets):**

```json
{ "verification_id": "vf_1029", "result": "VERIFIED", "student_display": "A.K.M. ...4271",
  "institution": "Sample Institute of Technology", "programme": "B.Tech Computer Science",
  "status": "ENROLLED", "valid_as_of": "2026-10-22T10:41:00+05:30", "consent_expires": "2026-11-30",
  "signature_valid": true }
```

**Never returned:** marks, address, date of birth, phone, Aadhaar, other institutions, any college flag or duplicate case.

**Withdrawal and revocation:** `POST /consents/{id}/withdraw` sets `WITHDRAWN` and takes effect on the very next scan. A public **revocation list** (`/v1/revocations`) lists revoked certificates and credentials by id.

**Rate limit:** 20 verifications per hour per employer, shown in the UI.

### 6.8 Audit log (hash chain) [MUST]

- `hash = SHA-256( prev_hash || canonical_json(actor, role, action, object_type, object_id, time) )`. The first entry uses `prev_hash = "GENESIS"`.
- **Append-only:** no update or delete endpoint exists. The database user for the app has no UPDATE or DELETE right on this table.
- **Logged actions:** logins, uploads and their results, flag creation and every status change, officer decisions, rule changes and approvals, consent creation and withdrawal, every verification, certificate issue and revoke, every read of a student's detail by a college or officer, admin actions, key rotation.
- **Verify chain** recomputes every hash in order and reports the first mismatch.

### 6.9 Notifications and mock mail [SHOULD]

Event to message mapping: upload finished (college), flag raised (officer), clarification requested (college), college replied (officer), ID reminder (student and college, with the demo-clock deadline), consent created and withdrawn (student), verification performed (student), rule approved or rejected (rules owner). Each is an `outbox` row shown in the Mock mail page.

### 6.10 Certificates [MUST]

- Certificate id format `TRC-2026-000123`.
- PDF content: college, student, programme, **APAAR ID**, **student ID**, issue date, certificate id, **QR** to `https://<host>/c/<certificate_id>`. The College Certificates screen has a **Preview** button, and an institution can print or display the PDF. Take one screenshot of a generated certificate for the slides.
- The public page `/c/<id>` shows authentic, revoked or not found with minimal details, and logs the scan.
- A revoked certificate shows "Revoked" and appears in the revocation list.

### 6.11 Reports (definitions) [MUST]

Each report is a parameterised query returning rows plus a title, filters and a "generated on" stamp. Exports: **CSV** (with spreadsheet-injection protection: prefix any cell starting with `=`, `+`, `-`, `@` with a quote) and **PDF** (table with header, footer and the SAMPLE DATA notice). See Section 5.3 N8 for the list.

### 6.12 Live updates [MUST]

A single stream endpoint `GET /v1/stream` (Server-Sent Events) sends events: `upload_finished`, `flag_created`, `flag_updated`, `priority_created`, `rule_status_changed`, `consent_changed`. The frontend subscribes once and updates the dashboard, queues and notification bell **without refreshing**. If SSE fails, fall back to polling every 5 seconds.

### 6.13 Security checklist [MUST]

| Area | Requirement |
|---|---|
| Authentication | JWT with short expiry (30 minutes) and refresh. Mock OTP in the prototype |
| Authorisation | A role dependency on **every** route. Scope filters (region, institution, student) applied **inside the query**, not after |
| Passwords and secrets | Secrets in environment variables. No secret in the repository |
| Personal data | `contact_phone` and `guardian_name` stored only as HMAC tokens. No raw personal data in logs |
| Input | Schema validation on every request. File size and type checks. Reject formulas in CSV cells |
| Output | CSV injection protection on exports |
| Transport | HTTPS in any deployed demo. Secure headers. CORS limited to the frontend origin |
| Rate limits | Login attempts, verification (20 per hour per employer), upload (5 per minute per college) |
| Keys | Ed25519 keys in `vault/` with file permission 600. Rotation supported |
| Audit | Section 6.8 |

### 6.14 Evaluation results panel (our own measured numbers) [MUST]

Judges ask for results, not just features. The prototype therefore measures itself. One command, `make evaluate`, runs the checks below, writes `models/evaluation_summary.json`, and the **"Evaluation results"** page (Officer and Admin) displays it. These are the numbers that go on the slides, **labelled "measured on synthetic data in our prototype"**.

| Metric | How it is measured |
|---|---|
| **Planted breaches caught on upload** | Generate 200 course uploads with known planted breaches (over the maximum, or ineligible holders) and 200 lawful ones. Report breaches caught out of planted |
| **False alarms: simple counter vs Seat-Ledger** | On the lawful courses that use extra seats, count alarms from `admitted > approved` and flags from the Seat-Ledger. Report both |
| **Time from upload to flag** | Server timestamps `upload.finished_at` to `flag.opened_at` over 50 runs. Report median and 95th percentile |
| **Upload throughput** | Seconds to process `G_large_5000.csv` |
| **Matching precision and recall** | On M16 (6.3) at the stated thresholds, by typo type |
| **Anomaly precision and recall** | On M6, model versus baseline (6.6) |
| **Reconciliation drift** | Counters versus event history across all scenarios. Must be zero |

The page also offers **Copy as a slide table**. Until `make evaluate` has run, the page shows "Not yet measured".


---

## 7. API reference and data contracts

All routes are under `/v1` unless stated. Every route returns JSON with a consistent error shape `{ "error": { "code": "...", "message": "..." } }`. The full interactive documentation is generated at `/docs`. [MUST]

### 7.1 Endpoints

| Area | Method and path | Who |
|---|---|---|
| Auth | `POST /auth/request-otp`, `POST /auth/verify-otp`, `GET /me` | All |
| Simulated AICTE | `GET /sim/aicte/institutions`, `GET /sim/aicte/approvals?year=` | Backend only |
| Simulated registry | `POST /sim/registry/verify`, `POST /sim/registry/consent-session` | Adapter only |
| Upload | `POST /institutions/{id}/uploads` (multipart, `Idempotency-Key` header, bearer token or `X-API-Key`) | College Admin |
| Upload status | `GET /uploads/{id}`, `GET /uploads/{id}/errors.csv` | College Admin, Officers |
| Ledger | `GET /ledger`, `GET /ledger/course/{id}`, `GET /ledger/compare` | Officers, College (own) |
| Flags | `GET /flags`, `GET /flags/{id}`, `POST /flags/{id}/assign`, `/clarify`, `/accept`, `/escalate`, `/reply` | Officers (reply: College) |
| Priorities | `GET /priorities`, `GET /priorities/{id}`, `POST /priorities/{id}/label`, `GET /anomaly/evaluation` | Officers |
| Rules | `GET /rules`, `POST /rules`, `GET /rules/{id}/versions/{v}`, `POST .../submit`, `/approve`, `/reject`, `/tests/run`, `/backtest`, `/activate`, `GET /rules/unconfirmed` | Rules Owner (read: Officers) |
| Students | `GET /students`, `GET /students/{id}`, `POST /students/{id}/apaar`, `/withdraw`, `/opt-out` | College Admin (own) |
| Identity | `POST /identity/verify`, `POST /identity/consent-session` | Student, College |
| Duplicates | `GET /duplicates`, `POST /duplicates/{id}/resolve` | Officers |
| Consent | `POST /consents`, `GET /consents`, `POST /consents/{id}/withdraw`, `GET /access-log` | Student |
| Verify | `POST /verify` body `{ "code": "K7F2-9XQD" }` | Employer |
| Credentials | `GET /credentials/me`, `GET /revocations` | Student, public |
| Certificates | `POST /certificates`, `GET /certificates`, `POST /certificates/{id}/revoke`, public `GET /public/certificates/{id}` | College, public |
| Reports | `GET /reports`, `GET /reports/{id}?format=` json, csv or pdf | Officers |
| Audit | `GET /audit`, `POST /audit/verify-chain` | Auditor |
| Admin | `POST /admin/scenario/{id}`, `/reset`, `/clock`, `/registry-mode`, `/rotate-key`, `/tamper`, `/restore` | System Admin |
| Corrections | `POST /students/{id}/correct` (new event, history kept) | College Admin (own) |
| Evaluation | `GET /evaluation/summary`, `GET /matching/evaluation`, `POST /admin/reconcile` | Officers, Admin |
| Notifications | `GET /outbox` | All (own) |
| Stream | `GET /stream` (SSE) | All |

### 7.2 Example: upload response

```json
{ "upload_id": "upl_0091", "status": "COMPLETED", "rows_total": 1204, "rows_accepted": 1188,
  "rows_warning": 9, "rows_error": 7, "identity_tiers": {"T1": 640, "T2": 120, "T3": 380, "T4": 48},
  "duplicates": {"D1": 3, "D2": 1, "D3": 2, "D4": 1, "D5": 4},
  "ledger": [ { "course": "B.Tech CSE", "approved": 240, "lawful_max": 276, "admitted": 276, "result": "OK" } ],
  "errors_csv": "/v1/uploads/upl_0091/errors.csv" }
```

### 7.3 Example: flag

```json
{ "flag_id": 114, "status": "UNDER_REVIEW", "institution": "INST-0003", "course": "B.Tech CSE", "year": "2026-27",
  "bucket": "TOTAL", "rule": { "id": "SN-A", "version": 2, "status": "active" },
  "cap": 276, "used": 282, "over_by": 6, "record_ids": ["stu_8811", "stu_8812", "..."],
  "first_breach_at": "2026-10-22T09:58:00+05:30",
  "timeline": [ { "t": "09:58", "actor": "system", "action": "FLAG_RAISED" } ],
  "disclaimer": "A flag is not a finding." }
```

### 7.4 Upload API example (for the demo)

```bash
curl -X POST https://<host>/v1/institutions/INST-0001/uploads \
  -H "X-API-Key: demo_key_inst0001" -H "Idempotency-Key: 2026-27-cse-batch-1" \
  -F "course_code=CSE" -F "file=@B_domestic_in_extra.csv"
```

---

## 8. PS deliverables coverage (every item mapped)

| # | PS requirement | Where in the prototype | Real or simulated |
|---|---|---|---|
| 1 | Secure platform/API for student-level upload keyed by APAAR ID | College Upload wizard (C2) and the Upload API with API key (C7, `POST /institutions/{id}/uploads`) | Real |
| 2 | Fields: approved intake, actual enrolment, supernumerary, NRI, OCI, FN, other | Student upload columns (6.1), seat buckets (6.4), My seats (C3), Ledger monitor (N2). Approved intake comes from M1. Fields include admission round and entry type | Real logic, simulated data |
| 3 | Automated validation: duplicates, invalid or missing APAAR, intake exceeded, inconsistencies, cross-institution duplicates | Validation codes (6.1), identity tiers (6.2), duplicate classes (6.3), Seat-Ledger (6.4) | Real |
| 4 | Real-time dashboards for AICTE and institutions | Officer dashboard with live activity (N1), Ledger monitor (N2), College dashboard (C1), live stream (6.12) | Real |
| 5 | Secure verification for AICTE, institutions, employers, regulators | Verify page (E1), consent manager (S3), officer evidence views, role-based access | Real |
| 6 | Verifiable student records linked to academic identity | Signed verified record (S1), credential format (6.7), tier badge and APAAR link | Real signatures, simulated identity source |
| 7 | API integration with institutional and AICTE systems | Open API with docs (Section 7), adapters (`RegistryAdapter`, `AicteAdapter`), Admin integration register | API real, integrations **simulated** |
| 8 | Security, privacy, authentication, RBAC, audit, consent | Role system (5.1), scope filters, consent (6.7), hash-chained audit (6.8), security checklist (6.13), 403 demo | Real |
| 9 | Reports for policy, accreditation, monitoring | Reports page (N8) with 12 reports including excess-intake, duplicate-enrolment and the accreditation scorecard, with CSV/PDF export | Real |
| 10 | APAAR ID with student ID on certificates | Certificate generator (C6, 6.10) carrying APAAR ID, student ID and QR, with a public check page | Real |
| Flow | Institution to Upload to APAAR Validation to Verification to AICTE repository to Analytics to Authorised Verification | Section 2.2 shows the same flow; each step is a screen | Real |
| Outcome | Authentic records, real-time monitoring, excess detection, data-driven governance | Ledger, flags, dashboards, reports, rules governance | Real |
| Innovation | Automated validation, **intelligent anomaly detection**, real-time monitoring, secure verification, analytics | Seat-Ledger, **Anomaly Intelligence with evaluation page (6.6)**, SSE live updates, consent-bound verification, analytics and reports | Real (model on synthetic data) |

---

## 9. Demo script (about 8 minutes)

Keep the SAMPLE DATA ribbon visible. State the honesty line once at the start: "Everything is synthetic and the outside systems are simulated."

| # | Role | Action | What to say | Time |
|---|---|---|---|---|
| 1 | Landing page | Open the home page | "TrueRoll checks admissions, rule by rule, and lets students prove enrolment safely." | 0:20 |
| 2 | **Officer** | Open the dashboard | "One live picture. 48 colleges, open flags, identity coverage." | 0:30 |
| 3 | **Officer** | Seat-Ledger, switch **Compare mode ON** | "A simple counter panics at 241. We know that 276 is lawful here, and we flag the real problems with the rule and version." **(Our USP)** | 1:00 |
| 4 | **College Admin** (second browser window) | Upload `B_domestic_in_extra.csv` for INST-0002 | "Upload a student list. It checks itself." Show progress and results, errors and warnings | 1:00 |
| 5 | **Officer** | Dashboard updates by itself; open the new flag | "No refresh. The flag says which rule, which version, which students. A flag is not a finding." Request clarification | 1:00 |
| 6 | **College Admin** | Open Flags, reply with an explanation | "The college explains or fixes and resubmits." | 0:30 |
| 7 | **Rules Owner** then **second approver** | Open the pending `SN-MGT` rule, run tests and backtest, approve as the second person | "Rules are governed: sourced, versioned, two people, tested before activation. Unconfirmed rules never auto-flag." | 1:15 |
| 8 | **Officer** | Review priorities, open one, then **Model evaluation** | "Anomaly scoring is advisory and shown with reasons. Evaluated on synthetic data against a baseline, and we say so." | 1:00 |
| 9 | **Student** (phone view) | Consent manager, create a share code | "The student decides who can verify, for what, until when." | 0:45 |
| 10 | **Employer** | Verify the code | "A signed yes/no. Never marks or address." | 0:30 |
| 11 | **Student** | Withdraw consent, **Employer** scans again | "Withdrawn means withdrawn, instantly." | 0:30 |
| 12 | **Admin** then **Auditor** | Tamper demo, then Verify chain | "Any edit to history is detected." | 0:45 |

**Backup plan:** keep a screen recording of this exact run, and keep the seeded state reachable with **Reset demo**. If the registry simulator misbehaves, set it to Up from Admin.

---

## 10. Scenario catalogue and acceptance tests

### 10.1 Hero institutions (fixed IDs so tests are repeatable)

| ID | Name (fictional) | Carries |
|---|---|---|
| INST-0001 | Sample Institute of Technology | Main demo college. CSE course intake 240, 238 admitted, lawful. Used for uploads |
| INST-0002 | Demo College of Engineering | Scenario S2 (domestic students in extra seats) |
| INST-0003 | Model Institute of Engineering | Scenario S3 (282 admitted) |
| INST-0004 | Trial Institute of Technology | Scenario S4 (rule not confirmed, EWS draft rule applies) |
| INST-0005 | Example Institute of Management | Scenarios S5 (pending rule SN-MGT) and S15 (late surge anomaly) |
| INST-0006 | Pilot College of Computer Applications | Scenarios S6 to S10 (identity gaps, duplicates) |

### 10.2 Scenarios and expected results (each must be an automated test)

| ID | Scenario | Steps | Expected |
|---|---|---|---|
| **S1** | Lawful 276 | Load `A_lawful_276.csv` | **No flag.** Compare mode shows simple counter ALARM vs Seat-Ledger OK |
| **S2** | Domestic students in extra seats | Load `B_domestic_in_extra.csv` | **One flag, 5 ineligible holders (C3)**, rule and version cited |
| **S3** | 282 admitted | Load `C_over_max_282.csv` | **Flag 6 over the maximum (C2)**, with the overflowing bucket (C1) |
| **S4** | Unconfirmed rule | Evaluate INST-0004 | `RULE_NOT_CONFIRMED`. **No automatic flag.** Appears in the Unconfirmed-rule watch |
| **S5** | Pending rule becomes active | Approve `SN-MGT` as a second person, tests pass, advance the demo clock | Status Active. Only 2026-27 courses re-evaluated. Old evaluations keep their rule version |
| **S6** | Missing APAAR | Load `F_missing_apaar.csv` | Warnings W201, tier T3, **all students counted**, none rejected |
| **S7** | Foreign national | Include `FN` rows | Tier T4, counted in the eligible extra bucket, no penalty |
| **S8** | Opted-out student | Student records opt-out | Tier T4. No penalty. Still counted |
| **S9** | Registry down | Admin sets Registry Down, load `I_registry_down.csv` | W203. Students stay T2. Retry works after Registry Up, becoming T1. **Nobody rejected** |
| **S10** | Duplicate classes | Load `E_duplicates.csv` | D1 auto-rejected. D2 and D4 create review cases. D3 verified, no penalty. D5 watch list only |
| **S11** | Bad file | Load `D_bad_format.csv` | Error report with codes. Valid rows kept. Corrected file `H_resubmit_fixed.csv` completes |
| **S12** | Idempotency | Load the same file twice | **Zero new records** the second time |
| **S13** | Large file | Load `G_large_5000.csv` | Completes in **under 60 seconds** (target). Progress bar works |
| **S14** | Withdrawal | Record a withdrawal, then another after an audit date | Seat freed. The late one adds W205 and a review note |
| **S15** | Anomaly | Open INST-0005 priorities | **High priority with reasons** `LATE_SURGE` and `CATEGORY_MIX` |
| **S16** | Consent lifecycle | Create code, verify, withdraw, verify again | Verified, then `WITHDRAWN`. Also test expired and wrong verifier |
| **S17** | Tamper | Admin tamper, Auditor verify | Chain **broken** at the exact entry. Restore returns it to valid |
| **S18** | Rule change mid-year | New version for the same year | Applies to its year only. History unchanged |
| **S19** | Role isolation | College Admin opens another college URL. Regional officer opens another region | **403** page |
| **S20** | Live update | Upload in one window | Officer dashboard shows the new row **without refresh** |
| **S21** | Correction and reconciliation | Correct one student's seat category and re-upload a file | A `CORRECTION` event is stored. Counters change accordingly. **`reconcile` reports zero drift** |
| **S22** | Spot round and lateral entry | Upload a `SPOT` round file and a `LATERAL` file | Spot admissions use the same buckets. Lateral counts against `lateral_intake`, or the course returns `RULE_NOT_CONFIRMED` if none exists |
| **S23** | Fuzzy matching with typos | Run the matcher on M16 | Precision, recall and F1 appear on the Matching evaluation page. Matches at 0.93 or more create D4 review cases, 0.85 to 0.93 the D5 watch list. **Nothing is auto-flagged** |
| **S24** | Evaluation summary | Run `make evaluate` | `evaluation_summary.json` exists. The Evaluation results page shows every metric in 6.14 |

Also test: the minimal response never contains forbidden fields (S16), CSV export neutralises formulas, and the proposer cannot approve their own rule (S5).

---

## 11. Build order and definition of done

| Phase | Build | Done when |
|---|---|---|
| **0. Skeleton** | Repo, Docker Compose, database models, auth with mock OTP, role dependencies, audit chain, design system, SAMPLE ribbon, `/docs` | A user can sign in as each role and see an empty home page. Audit entries chain correctly |
| **1. Data** | Generators and seeds for M1, M2, M3, M7, M8, M14, M15. `make seed` | Database holds 48 institutions, about 9,000 students, rules, demo users. Same output every run |
| **2. Rules and Seat-Ledger (backend first)** | Rules Service with lifecycle, Seat-Ledger with checks C1 to C5, evaluations, flags, regression suite | All six examples in 6.4 and scenarios S1 to S5, S14, S18 pass as automated tests |
| **3. Ingestion, identity, duplicates, simulators** | Upload pipeline, validation codes, tiers, duplicate classes, **fuzzy matcher and M16**, registry simulator and mock consent page, adapters | Scenarios S6 to S13 and **S23** pass |
| **4. Officer screens** | Dashboard, Ledger monitor with Compare mode, Flags queue and detail, live stream | Scenario S20 works. Compare mode matches S1 to S3 |
| **5. College screens** | Dashboard, Upload wizard, My seats, Students, Flags and clarifications, API page | A full college round trip works (upload, fix, resubmit, reply) |
| **6. Rules Owner screens** | Rule book, detail, propose, approvals, tests and backtest, activation, watch list | Two-person approval enforced. S5 and S18 work in the UI |
| **7. Consent and verification** | Student screens, consent manager, credentials, employer verify page, certificates, public certificate page | Scenario S16 works. Forbidden fields never appear |
| **8. Anomaly Intelligence** | Anomaly generator (M6), training and evaluation script, Review priorities queue and detail, Model evaluation page | Scenario S15 works. `anomaly_eval.json` exists and the page displays it |
| **9. Reports, Auditor, Admin** | 11 reports with exports, Auditor screens with Verify chain, Admin tools including Tamper demo, scenario loader, clock, mock mail | Scenarios S17, S19, **S21, S22 and S24** work. All exports download. `make evaluate` writes the summary |
| **10. Polish** | Empty, loading and error states, accessibility pass, mobile pass for student and employer, Hindi student labels, README, `docs/SIMULATED.md`, Playwright run of the demo script | The full Section 9 script runs end to end, twice in a row, from **Reset demo** |

**Definition of done for the whole prototype:**
1. All 24 scenarios pass as automated tests.
2. The Section 9 demo runs in under 9 minutes with no manual database edits.
3. Every simulated source shows a SIMULATED chip and appears in `docs/SIMULATED.md`.
4. No screen text (UI copy) contains the words "violation", "fraud" or "guilty".
5. `make seed` and `make reset-demo` work from a clean machine in one command each.

---

## 12. Extras worth adding (beyond the PS) [EXTRA]

| Extra | Why it helps |
|---|---|
| **Guided tour mode** | A "Start demo tour" button that highlights each step of Section 9 with a tooltip, so a judge can self-navigate |
| **What-if tool for colleges** | "If I admit 5 more OCI/FN students, am I still within limits?" |
| **Rule impact simulator** | Change a cap percentage and see how many colleges change status before proposing it |
| **Upload data-quality score** | A 0-100 score per upload with the top three fixes |
| **Explain this flag** | A plain-language paragraph generated from the flag data (templated, not AI): "This course has 6 more students than the lawful maximum of 276..." |
| **Threshold slider on Model evaluation** | Lets a judge move the threshold and watch precision and recall change |
| **Webhooks for colleges** | A college registers a URL and receives an event when a flag is opened (simulated delivery shown in Mock mail) |
| **Student PWA** | Installable on a phone, with the QR available offline |
| **Public transparency page** | Aggregate, non-identifying statistics (coverage, number of colleges reporting) |
| **Hindi for student screens** | Accessibility and relevance |
| **Print-ready flag dossier** | One-click PDF of a flag with ledger, evidence and timeline |
| **Data lineage panel** | On any number, "Where does this come from?" shows the query and the source table |

---

## 13. Likely judge questions and where the prototype answers them

| Question | Show this |
|---|---|
| How do you know your seat rules are legally right? | Rules Owner screens: provenance, two-person approval, tests, **unconfirmed rules route to human review** (S4, S5) |
| What about students without an APAAR ID? | Student Identity screen, S6, S7, S8: counted, never rejected |
| Is every duplicate a violation? | Duplicate classes D1 to D5, S10, with the UGC note |
| Do you have access to APAAR, DigiLocker, AICTE APIs? | Admin integration register: **None live. SIMULATED**, with the adapter interface. Registry Down demo (S9) |
| Why can an employer see anything about a student? | Minimal signed yes/no, consent, withdrawal (S16) |
| Can you change a cap without corrupting past decisions? | S18 and the rule version shown on every flag |
| What is the accuracy of your AI detection? | Model evaluation page: synthetic data, baseline, honest wording |
| Can it handle bulk uploads and outages? | S13 (large file), S12 (idempotent retry), S9 (registry down), Jobs screen, "backups planned, not tested" |
| How do I know the log has not been edited? | Tamper demo (S17) |
| How do you match students who have no APAAR ID, given typos? | Fuzzy matching with a typo-injected test and the **Matching evaluation** page. Low confidence goes to review, never auto-flag (S23) |
| What about corrections, spot rounds and lateral entry? | `CORRECTION` events and the **reconcile** proof of zero drift (S21, S22) |
| Where do your impact numbers come from? | The **Evaluation results** page: our own measured numbers on synthetic data (S24) |

---

## 14. Appendix

### 14.1 Glossary (simple words)

| Term | Meaning |
|---|---|
| **APAAR ID** | A 12-digit national student ID. Voluntary |
| **Approved intake** | The seats AICTE allows a college to fill in a course for a year |
| **Supernumerary / extra seats** | Seats allowed beyond the approved intake for specific groups, such as international students |
| **NRI, OCI, PIO, FN, CIWGC** | Non-Resident Indian, Overseas Citizen of India, Person of Indian Origin, Foreign National, Children of Indian Workers in the Gulf |
| **Bucket** | A separate counter for one seat type |
| **Lawful maximum** | Approved intake plus all allowed extra seats under the active rules |
| **Flag** | A rule-cited concern awaiting an officer. **Not a finding** |
| **Review priority** | An advisory ranking from the anomaly model. Not a flag |
| **Identity tier** | How strongly a student's identity is verified: T1 to T4 |
| **Consent** | A student's permission for one verifier, one purpose, until a date. Can be withdrawn |
| **Hash chain** | A log where each entry carries a fingerprint of the previous one, so edits are detectable |
| **Idempotent** | Doing the same thing twice has the same effect as doing it once |
| **SIMULATED** | A fake stand-in for a real outside system |

### 14.2 Files the teammate should create first

```
seed/generate_institutions.py   seed/generate_students.py   seed/generate_anomaly_data.py
seed/rules.json                 seed/uploads/*.csv          seed/users.json
backend/app/adapters/registry.py (RegistryAdapter interface + SimulatedRegistry)
backend/app/adapters/aicte.py    (AicteAdapter interface + SimulatedAicte)
backend/app/services/ledger/engine.py   backend/app/services/rules/lifecycle.py
backend/tests/test_ledger_scenarios.py  (S1 to S5, S14, S18)
scripts/evaluate_anomaly.py     docs/SIMULATED.md   docs/decisions.md
```

### 14.3 One-paragraph summary to give the team

TrueRoll is a working web application on synthetic data. Colleges upload student lists. A rule-governed Seat-Ledger checks every seat type, citing the rule and version behind every flag, and a separate anomaly layer ranks where officers should look, with reasons and an honest evaluation. Students control who can verify them, employers receive only a signed yes/no, and every action is written to a tamper-evident log. The outside systems (AICTE records, APAAR/DigiLocker) are simulated behind real adapter interfaces and clearly labelled as such.
