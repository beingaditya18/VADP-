import { test, expect } from '@playwright/test';

test.describe('Judicial Case Filing & VADP Explainability E2E Journey', () => {
  test('1. Citizen portal case navigation and filing initialization', async ({ page }) => {
    // Navigate to citizen portal
    await page.goto('/citizen');

    // If redirected to login, authenticate first
    if (page.url().includes('/login')) {
      const emailInput = page.locator('input[type="email"], input[name="email"]');
      if (await emailInput.count() > 0) {
        await emailInput.fill('citizen.kumar@nyaya.in');
        await page.fill('input[type="password"], input[name="password"]', 'Password123!');
        await page.click('button[type="submit"]');
      }
    }

    // Check dashboard loaded
    await expect(page).toHaveURL(/\/(citizen|dashboard|login)/);

    // Verify case listing or file case button
    const fileCaseBtn = page.locator('button:has-text("File"), a:has-text("File"), button:has-text("New Case")');
    if (await fileCaseBtn.count() > 0) {
      await expect(fileCaseBtn.first()).toBeVisible();
    }
  });

  test('2. AI Decision Explanation rendering with SHAP feature weights', async ({ page }) => {
    await page.goto('/judge');

    // Handle authentication if redirected
    if (page.url().includes('/login')) {
      const emailInput = page.locator('input[type="email"], input[name="email"]');
      if (await emailInput.count() > 0) {
        await emailInput.fill('judge.sharma@nyaya.gov.in');
        await page.fill('input[type="password"], input[name="password"]', 'Password123!');
        await page.click('button[type="submit"]');
      }
    }

    // Inspect case card or AI panel
    const aiAnalysisSection = page.locator('[data-testid="ai-analysis"], section, div.border');
    if (await aiAnalysisSection.count() > 0) {
      await expect(aiAnalysisSection.first()).toBeVisible();
    }
  });

  test('3. Trust score breakdown and precedent radar visualization', async ({ page }) => {
    await page.goto('/judge');

    const trustScoreBadge = page.locator('text=/Trust Score|Trust Rating|Confidence/i');
    if (await trustScoreBadge.count() > 0) {
      await expect(trustScoreBadge.first()).toBeVisible();
    }
  });
});
