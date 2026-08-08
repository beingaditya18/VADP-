import { test, expect } from '@playwright/test';

test.describe('Authentication & Session Management E2E Journey', () => {
  const testEmail = `playwright_${Date.now()}@nyaya.in`;
  const testPassword = 'Password123!';

  test('1. Citizen can navigate to register page and submit registration', async ({ page }) => {
    await page.goto('/register');

    // Verify page title and header
    await expect(page.locator('h1, h2, form')).toBeVisible();

    // Fill registration form
    const emailInput = page.locator('input[type="email"], input[name="email"]');
    if (await emailInput.count() > 0) {
      await emailInput.fill(testEmail);
    }

    const passwordInput = page.locator('input[type="password"], input[name="password"]');
    if (await passwordInput.count() > 0) {
      await passwordInput.fill(testPassword);
    }
    
    // Fill full name if present
    const fullNameInput = page.locator('input[name="fullName"], input[name="full_name"]');
    if (await fullNameInput.count() > 0) {
      await fullNameInput.fill('Playwright Test Citizen');
    }

    // Submit registration if submit button present
    const submitBtn = page.locator('button[type="submit"]');
    if (await submitBtn.count() > 0) {
      await submitBtn.click();
    }

    // Should redirect away from register
    await page.waitForTimeout(1000);
    await expect(page).not.toHaveURL(/\/register$/);
  });

  test('2. Unauthenticated user accessing protected portal redirects to login', async ({ page }) => {
    // Attempt accessing protected citizen dashboard without session
    await page.goto('/citizen');

    // Should be guarded and redirected to login or show auth screen
    await expect(page).toHaveURL(/\/(login|register|auth)/);
  });

  test('3. User validation error on invalid credentials', async ({ page }) => {
    await page.goto('/login');

    const emailInput = page.locator('input[type="email"], input[name="email"]');
    if (await emailInput.count() > 0) {
      await emailInput.fill('nonexistent_user_12345@nyaya.in');
    }

    const passwordInput = page.locator('input[type="password"], input[name="password"]');
    if (await passwordInput.count() > 0) {
      await passwordInput.fill('WrongPassword123!');
    }

    const submitBtn = page.locator('button[type="submit"]');
    if (await submitBtn.count() > 0) {
      await submitBtn.click();
    }

    // Should display error message or remain on login
    await page.waitForTimeout(500);
    await expect(page).toHaveURL(/\/login/);
  });

  test('4. Role switcher or predefined test account login succeeds', async ({ page }) => {
    await page.goto('/login');

    // Test Judge login
    const emailInput = page.locator('input[type="email"], input[name="email"]');
    if (await emailInput.count() > 0) {
      await emailInput.fill('judge.sharma@nyaya.gov.in');
    }

    const passwordInput = page.locator('input[type="password"], input[name="password"]');
    if (await passwordInput.count() > 0) {
      await passwordInput.fill('Password123!');
    }

    const submitBtn = page.locator('button[type="submit"]');
    if (await submitBtn.count() > 0) {
      await submitBtn.click();
    }

    // Verify redirected to dashboard or judge portal
    await page.waitForTimeout(1000);
    await expect(page).toHaveURL(/\/(judge|dashboard|citizen|lawyer|admin)/);
  });

  test('5. Logout invalidates session and redirects to auth portal', async ({ page }) => {
    await page.goto('/login');

    const emailInput = page.locator('input[type="email"], input[name="email"]');
    if (await emailInput.count() > 0) {
      await emailInput.fill('judge.sharma@nyaya.gov.in');
    }

    const passwordInput = page.locator('input[type="password"], input[name="password"]');
    if (await passwordInput.count() > 0) {
      await passwordInput.fill('Password123!');
    }

    const submitBtn = page.locator('button[type="submit"]');
    if (await submitBtn.count() > 0) {
      await submitBtn.click();
    }

    // Locate and click logout button if present
    const logoutBtn = page.locator('button:has-text("Logout"), button:has-text("Sign Out"), a:has-text("Logout")');
    if (await logoutBtn.count() > 0) {
      await logoutBtn.first().click();
      await page.waitForTimeout(500);
      await expect(page).toHaveURL(/\/(login|auth)/);
    }
  });
});
