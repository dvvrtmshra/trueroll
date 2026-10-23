# TrueRoll — Claude Working Rules

Re-read the relevant section of `docs/SPEC.md` at the start of every phase.

---

## Git rules (hard, no exceptions)

- **Never** run: `git add`, `git commit`, `git push`, `git merge`, `git rebase`,
  `git reset`, `git checkout`, `git stash`. Not automatically, not "to save progress",
  not at the end of a phase.
- Never create branches, tags, or amend commits.
- Never add `Co-Authored-By`, "Generated with Claude Code", or any Claude attribution
  anywhere: commits, PR text, file headers, README, code comments, docs.
- Read-only git is allowed: `git status`, `git diff`, `git log`.
- At the end of every phase: list files changed and give a suggested commit message
  in plain imperative style with no attribution. The developer makes every commit.

---

## Working rules

- Build in the phase order of `docs/SPEC.md` section 11 (phases 0–10).
- After each phase: run acceptance tests, report pass/fail, list assumptions,
  remind the developer to commit, then **STOP** and wait for the go-ahead.
- Write Seat-Ledger and Rules regression tests before or together with the engine code.
- Use fixed random seed **26263** in every generator.
- Record every assumption in `docs/decisions.md`. Keep `docs/SIMULATED.md` current.
- Use the stack in spec section 3.2. Ask before changing it.
- Keep diffs small and code readable. Add tests with each feature, not after.
- Do not build anything from spec section 12 (extras) until asked after phase 10.
- If a requirement is unclear, record the decision in `docs/decisions.md` and continue.
  If the choice would be costly to reverse, ask first.

---

## Product honesty (non-negotiable)

1. Permanent **SAMPLE DATA** ribbon on every page.
   SIMULATED chip on every simulated source.
2. Fictional institutions and people only. No real Aadhaar, APAAR IDs, phone numbers
   or college names.
3. Never state any performance or accuracy number that a script has not produced.
4. No UI text containing the words **"violation"**, **"fraud"** or **"guilty"**.
   An automated test (`test_ui_strings.py`) checks the built frontend for these words.
5. Every seeded rule labelled **"Illustrative: to be confirmed against AICTE rules"**.
6. A missing or unverified ID **never rejects a student**. It produces a warning and
   the student stays counted.
7. The server decides, screens only show. Every route has a role check. Scope filters
   (region, institution, student) are applied **inside the query**, not after.

---

## Other non-negotiable spec rules

- Seat rules and percentages are never hard-coded. They live in the database,
  versioned, with source and status (spec 6.5).
- Every dashboard number comes from the database, not from a constant.
- An unconfirmed rule (Draft, Pending, disabled or missing) never raises an automatic
  flag. It creates a "Rule not confirmed: human review" item.
- Two **different** people must approve a rule — enforced server-side
  (`approver != proposer`).
- The audit log is append-only and hash-chained. The normal app DB user has no
  `UPDATE` or `DELETE` right on the `audit_entry` table.
- Raw phone numbers and guardian names are never stored — only keyed HMAC tokens.
- An employer only ever receives the minimal signed response in spec 6.7.
- Old evaluations are never edited. A rule change writes new evaluation rows and
  preserves the rule version each one used.
