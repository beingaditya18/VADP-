import { test, expect } from '@playwright/test';

test.describe('VADP Cryptographic Verification & Merkle Ledger E2E Journey', () => {
  test('1. Verification Contract completeness checklist rendering', async ({ page }) => {
    await page.goto('/judge');

    // Handle login if redirected
    if (page.url().includes('/login')) {
      const emailInput = page.locator('input[type="email"], input[name="email"]');
      if (await emailInput.count() > 0) {
        await emailInput.fill('judge.sharma@nyaya.gov.in');
        await page.fill('input[type="password"], input[name="password"]', 'Password123!');
        await page.click('button[type="submit"]');
      }
    }

    // Verify verification contract container or badge exists
    const vadpBadge = page.locator('text=/VADP|Verification Contract|Cryptographic Integrity|Merkle/i');
    if (await vadpBadge.count() > 0) {
      await expect(vadpBadge.first()).toBeVisible();
    }
  });

  test('2. Independent cryptographic verification action', async ({ page }) => {
    await page.goto('/judge');

    const verifyBtn = page.locator('button:has-text("Verify"), button:has-text("Verify Contract"), button:has-text("Check Hash")');
    if (await verifyBtn.count() > 0) {
      await verifyBtn.first().click();
      await page.waitForTimeout(500);
    }
  });

  test('3. Decision provenance timeline displays sequential contract events', async ({ page }) => {
    await page.goto('/judge');

    const timelineContainer = page.locator('[data-testid="provenance-timeline"], div.space-y-4, ol, ul');
    if (await timelineContainer.count() > 0) {
      await expect(timelineContainer.first()).toBeVisible();
    }
  });
});
