# TrueRoll — Architecture Decisions

Assumptions and non-obvious decisions. Ordered by phase.

---

## Phase 0 — Skeleton

### D1. Seat-rule model: two separate buckets (SN-A + SN-B)

**Decision:** Model OCI/FN extra seats and CIWGC extra seats as two separate buckets
(`OCI_FN_EXTRA` and `CIWGC_EXTRA`), not as a single pool.

**Rationale:** Spec sections M2, 6.4 seed them separately. The C4 reversion rule
(`effective_cap[OCI_FN] += max(0, cap[CIWGC] - used[CIWGC])`) makes them functionally
equivalent to a 36-seat pool with a 12-seat Gulf-worker sub-limit for intake 240, while
keeping the rule text honest and traceable.

**Numbers (intake 240, illustrative):**
- Regular: 240 (includes NRI-IN 12)
- OCI_FN_EXTRA cap: 24 (SN-A v2, 10 %)
- CIWGC_EXTRA cap: 12 (SN-B v1, 5 %)
- Lawful maximum: 276

All rules remain marked "Illustrative: to be confirmed against AICTE rules".

---

### D2. Audit tamper demo — two-tier DB roles

**Decision:** Use a second PostgreSQL role `trueroll_tamper` with `UPDATE` rights
only on `audit_entry`, activated only when `DEMO_MODE=true`.

**Rationale:** Spec 6.8 requires the normal app user to have no UPDATE/DELETE on
`audit_entry`. Spec 5.10 requires a tamper button for the demo. A privileged role
used exclusively by the tamper/restore endpoints resolves the conflict.

**Implementation:**
- Normal role: `trueroll_app` — no UPDATE/DELETE on `audit_entry`.
- Tamper role: `trueroll_tamper` — UPDATE on `audit_entry` only.
- Tamper and restore endpoints are double-gated: `DEMO_MODE=true` AND System Admin JWT.
- SQLite (dev): tamper uses a direct SQLAlchemy `text()` statement; the DB-level
  permission separation applies only to PostgreSQL.

---

### D3. Anomaly layer isolation

**Decision:** The anomaly service is fully self-contained in
`backend/app/services/anomaly/`, gated by `ANOMALY_ENABLED=true` (default: false),
and built in Phase 8 only.

**When off:** `GET /priorities` returns an empty list; the Model evaluation page
shows "Anomaly Intelligence not yet enabled".

---

### D4. Phase 9 report count

**Decision:** Build 12 reports (R1–R12) per spec v1.1. Spec phase 9 text says "11
reports" but v1.1 added R12 (Prototype evaluation summary). Use 12.

---

### D5. User table — institution_id is not a DB-level FK

**Decision:** `user.institution_id` is a plain String column without a foreign key
constraint. The application enforces the relationship.

**Rationale:** In Phase 0 the schema is created before institution rows exist (those
are seeded in Phase 1). A DB-level FK would fail on PostgreSQL. Application-level
enforcement is sufficient for the prototype.

---

### D6. SQLite for local dev; PostgreSQL for Docker

**Decision:** `DATABASE_URL=sqlite:///./trueroll.db` is the default in `.env.example`.
Docker Compose uses PostgreSQL. All application code must work on both. The
`check_same_thread=False` SQLite argument is set conditionally.

---

### D7. Schema management: create_all for Phase 0, Alembic later

**Decision:** Phase 0 uses `Base.metadata.create_all(engine)` in `scripts/init_db.py`
for simplicity. Alembic migrations will be added in Phase 1 when seeded data
structures stabilise.

---

## Phase 1 — Data

### D8. Student count: 12,855 (above spec ~9,000)

**Decision:** Accept 12,855 students. Spec says "about 9,000"; the generator fills
courses at 70–98% of approved intake across 214 courses for 2026-27 plus hero
institutions with planted scenario counts. The higher count comes from random fill
of 42 non-hero institutions and is consistent with the spec's "about".

### D9. SQLAlchemy FK ordering: flush-before-events pattern

**Decision:** In `generate_students.py`, all `Student` rows are added and
`db.flush()` is called before any `AdmissionEvent` rows for the same batch.

**Rationale:** SQLite's FK enforcement (`PRAGMA foreign_keys = ON`) checks constraints
at INSERT time during a bulk `executemany`. Without flushing students first, SQLAlchemy's
unit-of-work may attempt to insert admission events before the referenced students are
visible, causing `IntegrityError`. The flush pattern ensures correct insert ordering.

---

## Phase 2 — Rules + Seat-Ledger Engine

### D11. NRI_IN mapped to REGULAR bucket in Seat-Ledger

**Decision:** `BUCKET_FOR_CATEGORY["NRI_IN"] = "REGULAR"`. NRI seats count against `approved_intake` (the REGULAR cap), not as an extra bucket.

**Rationale:** Spec D1 states "NRI seats are inside the approved intake". Counting NRI_IN in its own bucket would allow it to exceed the 240-seat cap. Mapping it to REGULAR ensures the cap is honoured.

---

### D12. Multiple active rules for same bucket resolved by last-wins

**Decision:** If two `RuleVersion` rows are both `active` for the same bucket and scope, `compute_caps` takes the last one returned by the query. This is a misconfiguration; the activation step retires the previous version of the **same rule_id** only.

**Rationale:** Two rules of different rule_ids covering the same bucket in the same year is a governance error. The engine does not prevent it but the last-wins behaviour means a superceeding rule always overrides. Test isolation uses year `2025-26` for rules that must not interfere with year `2026-27` ledger tests.

---

### D13. SeatBucket.used not updated by evaluate(); requires reconcile()

**Decision:** `evaluate()` reads counts directly from `AdmissionEvent` history. `SeatBucket.used` is populated only by `reconcile()` (or `reconcile_all()` in `init_db`).

**Rationale:** Phase 2 doesn't yet have an admission-event write path (that's Phase 3). Using event history directly avoids dual-write complexity in tests and initial seed. Phase 3 will add the inline SeatBucket update.

---

---

## Phase 3 — Ingestion, identity, duplicates, simulators

### D14. Student ID derived from institution+year+student_ref hash

**Decision:** Student IDs in the upload pipeline use `STU-{md5(institution_id:academic_year:student_ref)[:12]}` rather than the full concatenation.

**Rationale:** The full `STU-{institution_id}-{academic_year}-{student_ref}` string can exceed the 36-character ID column limit. A short MD5 prefix is deterministic and collision-resistant for prototype scale.

---

### D15. opted_out flag in CSV upload

**Decision:** The upload CSV accepts an optional `opted_out` column (true/yes/1). Students with this set are assigned tier T4 without APAAR check.

**Rationale:** Spec section 6.2 states opted-out students are T4. Since APAAR is not mandatory and rejection is never allowed for missing/unverified IDs, opted-out students are counted normally with no penalty.

---

### D16. Fuzzy score formula thresholds

**Decision:** Score = 0.50 * name_sim + 0.35 * dob_sim + 0.15 * course_year_sim. Threshold ≥ 0.93 → D4 review case; 0.85–0.93 → D5 watch list. Without same_course, identical name+DOB = 0.85 = D5 boundary (D5). With same_course, it = 1.0 = D4.

**Rationale:** When same_course is not known (cross-institution), the 0.85 boundary correctly puts identical-name-DOB into D5 (watch list, not auto-review) unless the same course is confirmed. Nothing is auto-flagged regardless of score.

---

### D10. ApiKey table reused for institution keys

**Decision:** The `api_key` table (designed for employer API keys) is reused for
institution API keys in Phase 1, setting `employer_id = "system"` as a sentinel.

**Rationale:** Phase 1 only needs the key hash stored; a separate table was not worth
adding. In Phase 3 (ingestion), if a cleaner separation is needed, a dedicated
`institution_api_key` column on the `Institution` model can be added.
