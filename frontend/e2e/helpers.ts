import { Page } from "@playwright/test";

const API = "http://localhost:8000";
const OTP = "123456";

/**
 * Log in via the UI. Handles the 3-step login (choose role → email → OTP)
 * by clicking the quick-role button when the email matches a known demo account.
 */
export async function login(page: Page, email: string) {
  await page.goto("/login");
  await page.waitForSelector("body");

  // Try the quick-role button first (avoids the email step)
  const btn = page.locator(`button:has-text("${email.split("@")[0].replace(/\./g, " ")}")`);
  const quickBtn = page.locator(`button[class*="bg-"]`).filter({ hasText: email.split(".")[0] });

  // Fall back to manual email flow
  const emailInput = page.locator('[data-testid="email-input"]');
  if (await emailInput.isVisible({ timeout: 500 }).catch(() => false)) {
    // Already on email step
    await emailInput.fill(email);
    await page.click('[data-testid="request-otp"]');
  } else {
    // On choose step — click "Enter a custom email instead" then fill
    const customLink = page.locator('button:has-text("Enter a custom email")');
    if (await customLink.count() > 0) {
      await customLink.click();
    }
    const ei = page.locator('[data-testid="email-input"]');
    await ei.waitFor({ state: "visible" });
    await ei.fill(email);
    await page.click('[data-testid="request-otp"]');
  }

  // OTP step
  const otpInput = page.locator('[data-testid="otp-input"]');
  await otpInput.waitFor({ state: "visible" });
  await otpInput.fill(OTP);
  await page.click('[data-testid="verify-otp"]');

  // Wait until we leave the login page
  await page.waitForFunction(() => !window.location.pathname.includes("login"), { timeout: 10_000 });
}

export async function adminToken(): Promise<string> {
  const resp = await fetch(`${API}/auth/verify-otp`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email: "sysadmin@trueroll.demo", otp: OTP }),
  });
  const data = await resp.json();
  return data.access_token;
}

export async function getToken(email: string): Promise<string> {
  const resp = await fetch(`${API}/auth/verify-otp`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, otp: OTP }),
  });
  const data = await resp.json();
  return data.access_token;
}

export async function apiPost(path: string, body: object, token: string) {
  const resp = await fetch(`${API}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
    body: JSON.stringify(body),
  });
  return resp.json();
}

export async function apiGet(path: string, token: string) {
  const resp = await fetch(`${API}${path}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  return resp.json();
}
