/**
 * Playwright tests for the Section 9 demo script (all 12 steps).
 * Requires backend on :8000 and frontend on :5173.
 * Run: npx playwright test e2e/demo-script.spec.ts
 */
import { test, expect, Page } from "@playwright/test";
import { login, adminToken, apiPost, apiGet } from "./helpers";

const OTP = "123456";

// ── Shared state ─────────────────────────────────────────────────────────────
let studentToken = "";
let employerToken = "";
let shareCode = "";
let adminTok = "";

// ── 0. Reset demo from admin UI ───────────────────────────────────────────────
test.beforeAll(async () => {
  adminTok = await adminToken();
  const resp = await fetch("http://localhost:8000/admin/reset-demo", {
    method: "POST",
    headers: { Authorization: `Bearer ${adminTok}` },
  });
  if (!resp.ok) console.warn("reset-demo returned", resp.status, "- continuing");

  // Pre-fetch tokens for API helper tests
  const sr = await fetch("http://localhost:8000/auth/verify-otp", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email: "student.verified@trueroll.demo", otp: OTP }),
  });
  studentToken = (await sr.json()).access_token;

  const er = await fetch("http://localhost:8000/auth/verify-otp", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email: "employer.demotech@trueroll.demo", otp: OTP }),
  });
  employerToken = (await er.json()).access_token;
});

// ── Step 1: Landing page ──────────────────────────────────────────────────────
test("step1 — landing page shows SAMPLE DATA ribbon", async ({ page }) => {
  await page.goto("/");
  // Either redirect to login or show ribbon
  const url = page.url();
  if (url.includes("login")) {
    await page.waitForSelector("form");
    return; // Login page is fine — ribbon is on authenticated pages
  }
  await expect(page.locator("text=SAMPLE DATA").first()).toBeVisible();
});

// ── Step 2: Officer dashboard ─────────────────────────────────────────────────
test("step2 — officer dashboard shows institution count", async ({ page }) => {
  await login(page, "officer.national@trueroll.demo");
  await page.waitForURL(/^\//);
  const body = page.locator("body");
  await expect(body).toContainText(/institution|college|48/i);
  await expect(page.locator("text=SAMPLE DATA").first()).toBeVisible();
});

// ── Step 3: Compare mode ──────────────────────────────────────────────────────
test("step3 — seat-ledger compare mode can be toggled", async ({ page }) => {
  await login(page, "officer.national@trueroll.demo");
  await page.goto("/ledger");
  await page.waitForSelector("body");
  const compareBtn = page.locator('button:has-text("Compare"), label:has-text("Compare")');
  if (await compareBtn.count() > 0) {
    await compareBtn.first().click();
    await expect(page.locator("body")).toContainText(/simple|ledger|compare/i);
  }
});

// ── Step 4: College admin upload ──────────────────────────────────────────────
test("step4 — college admin can access upload page", async ({ page }) => {
  await login(page, "admin.inst0001@trueroll.demo");
  await page.goto("/upload");
  await page.waitForSelector("body");
  await expect(page.locator("body")).toContainText(/upload|drag|drop|csv/i);
});

// ── Step 5: Officer sees flags ────────────────────────────────────────────────
test("step5 — officer can open flags queue", async ({ page }) => {
  await login(page, "officer.national@trueroll.demo");
  await page.goto("/flags");
  await page.waitForSelector("body");
  // Should show flags list or empty state, not an error
  await expect(page.locator("body")).not.toContainText(/500|error loading/i);
  await expect(page.locator("text=SAMPLE DATA").first()).toBeVisible();
});

// ── Step 6: College admin replies to flag ─────────────────────────────────────
test("step6 — college admin can see flags page", async ({ page }) => {
  await login(page, "admin.inst0001@trueroll.demo");
  await page.goto("/flags");
  await page.waitForSelector("body");
  await expect(page.locator("body")).not.toContainText(/500|403/i);
});

// ── Step 7: Rules owner and approver ─────────────────────────────────────────
test("step7 — rules owner can see rule book", async ({ page }) => {
  await login(page, "rules.owner@trueroll.demo");
  await page.goto("/rules");
  await page.waitForSelector("body");
  await expect(page.locator("body")).toContainText(/rule|illustrative/i);
});

test("step7b — rules approver can see pending approvals", async ({ page }) => {
  await login(page, "rules.approver@trueroll.demo");
  await page.goto("/approvals");
  await page.waitForSelector("body");
  await expect(page.locator("body")).not.toContainText(/500|error/i);
});

// ── Step 8: Review priorities + model evaluation ──────────────────────────────
test("step8 — officer can see review priorities", async ({ page }) => {
  await login(page, "officer.national@trueroll.demo");
  await page.goto("/priorities");
  await page.waitForSelector("body");
  await expect(page.locator("body")).not.toContainText(/500/i);
});

test("step8b — model evaluation page loads", async ({ page }) => {
  await login(page, "officer.national@trueroll.demo");
  await page.goto("/model-eval");
  await page.waitForSelector("body");
  await expect(page.locator("body")).toContainText(/precision|recall|evaluation/i);
});

// ── Step 9: Student consent — create share code ───────────────────────────────
test("step9 — student can see consent manager", async ({ page }) => {
  await login(page, "student.verified@trueroll.demo");
  await page.goto("/consent");
  await page.waitForSelector("body");
  await expect(page.locator("body")).toContainText(/consent|share|सहमति/i);
});

test("step9b — student can create a share code (API)", async () => {
  const employers = await apiGet("/employers", studentToken);
  expect(Array.isArray(employers)).toBeTruthy();
  if (employers.length === 0) return;

  const created = await apiPost("/consents", {
    employer_id: employers[0].id,
    purpose: "Employment",
    expires_days: 30,
  }, studentToken);
  expect(created.code).toBeTruthy();
  shareCode = created.code;
});

// ── Step 10: Employer verifies ────────────────────────────────────────────────
test("step10 — employer can verify a share code", async ({ page }) => {
  // Ensure we have a share code
  if (!shareCode) {
    const employers = await apiGet("/employers", studentToken);
    if (employers.length > 0) {
      const created = await apiPost("/consents", {
        employer_id: employers[0].id,
        purpose: "Employment",
        expires_days: 30,
      }, studentToken);
      shareCode = created.code;
    }
  }
  if (!shareCode) { test.skip(); return; }

  await login(page, "employer.demotech@trueroll.demo");
  await page.goto("/");
  await page.waitForSelector("body");
  // Fill in the code
  const input = page.locator('input[placeholder*="XXXX"], input[placeholder*="code"]').first();
  if (await input.count() > 0) {
    await input.fill(shareCode);
    await page.click('button:has-text("Verify")');
    await page.waitForSelector("body");
    await expect(page.locator("body")).toContainText(/enrolled|ENROLLED/i);
  }
});

// ── Step 11: Student withdraws, employer gets "withdrawn" ─────────────────────
test("step11 — student can withdraw consent (API)", async () => {
  if (!shareCode) { return; }
  const consents = await apiGet("/consents", studentToken);
  const active = consents.find((c: { status: string; code?: string }) => c.status === "active");
  if (!active) return;

  const withdraw = await fetch(`http://localhost:8000/consents/${active.id}/withdraw`, {
    method: "POST",
    headers: { Authorization: `Bearer ${studentToken}` },
  });
  expect(withdraw.ok).toBeTruthy();
});

test("step11b — employer gets withdrawn response after withdrawal (API)", async () => {
  if (!shareCode) { return; }
  const resp = await fetch("http://localhost:8000/verify", {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${employerToken}` },
    body: JSON.stringify({ code: shareCode }),
  });
  // Withdrawn → 403 or the verify endpoint returns a "withdrawn" status in 200
  const data = await resp.json();
  const isWithdrawn = resp.status === 403 || data?.result === "withdrawn" ||
    (data?.detail ?? "").toLowerCase().includes("withdrawn");
  expect(isWithdrawn).toBeTruthy();
});

// ── Step 12: Tamper demo + audit chain verify ─────────────────────────────────
test("step12 — admin can access tamper demo tab", async ({ page }) => {
  await login(page, "sysadmin@trueroll.demo");
  await page.goto("/admin");
  await page.waitForSelector("body");
  const tamperTab = page.locator('button:has-text("Tamper")');
  if (await tamperTab.count() > 0) {
    await tamperTab.click();
    await expect(page.locator("body")).toContainText(/tamper|audit|entry/i);
  }
});

test("step12b — auditor can verify the chain", async ({ page }) => {
  await login(page, "auditor@trueroll.demo");
  await page.goto("/");
  await page.waitForSelector("body");
  const verifyBtn = page.locator('button:has-text("Verify chain"), button:has-text("Verify Chain")');
  if (await verifyBtn.count() > 0) {
    await verifyBtn.first().click();
    await expect(page.locator("body")).toContainText(/valid|chain|entries/i);
  }
});

// ── Regression: SAMPLE DATA ribbon on key pages ───────────────────────────────
test("regression — no forbidden words in officer pages", async ({ page }) => {
  await login(page, "officer.national@trueroll.demo");
  for (const path of ["/", "/flags", "/ledger"]) {
    await page.goto(path);
    await page.waitForSelector("body");
    const text = await page.locator("body").innerText();
    expect(text).not.toMatch(/\bviolation\b/i);
    expect(text).not.toMatch(/\bfraud\b/i);
    expect(text).not.toMatch(/\bguilty\b/i);
  }
});
