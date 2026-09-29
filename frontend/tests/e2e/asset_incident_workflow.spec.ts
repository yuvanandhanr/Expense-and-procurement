import { test, expect } from '@playwright/test';

test.describe('Asset Incident Workflow', () => {
  test('Employee can report a damaged asset', async ({ page }) => {
    // Log in as Employee
    await page.goto('/login');
    await page.getByRole('button', { name: 'Rachel Foster' }).click();
    await expect(page.getByRole('heading', { name: /Good day/i })).toBeVisible({ timeout: 10000 });

    // Navigate to My Assets
    await page.getByRole('link', { name: 'My Assets' }).click();
    await expect(page.getByRole('heading', { name: 'My Assets' })).toBeVisible();

    // Find the first assigned asset and click Report Issue
    // We assume there's at least one asset. If not, the test data needs seeding.
    const reportBtn = page.getByRole('button', { name: 'Report Issue' }).first();
    
    if (await reportBtn.isVisible()) {
      await reportBtn.click();

      // Ensure modal opens
      await expect(page.getByRole('heading', { name: 'Report Asset Issue' })).toBeVisible();

      // Select issue type
      await page.locator('main select').selectOption('Damage');

      // Fill description
      await page.getByPlaceholder('Please describe exactly what happened...').fill('Playwright Test Damage: Screen cracked during travel');

      // Submit report
      await page.getByRole('button', { name: 'Submit Report' }).click();

      // Verify success (Toast appears)
      await expect(page.getByText('Incident reported successfully')).toBeVisible({ timeout: 10000 });
    }
  });
});
