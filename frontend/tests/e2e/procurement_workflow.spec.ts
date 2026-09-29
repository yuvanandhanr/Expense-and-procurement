import { test, expect } from '@playwright/test';

test.describe('Procurement Workflow', () => {
  test('Employee can create a new purchase requisition', async ({ page }) => {
    // Log in as Employee
    await page.goto('/login');
    await page.getByRole('button', { name: 'Rachel Foster' }).click();
    await expect(page.getByRole('heading', { name: /Good day/i })).toBeVisible({ timeout: 10000 });

    // Navigate to PRs
    await page.getByRole('link', { name: 'My Requisitions' }).click();
    await expect(page.getByRole('heading', { name: 'My Requisitions' })).toBeVisible();

    // Open New PR Modal
    await page.getByRole('button', { name: 'New Requisition' }).click();
    
    // Fill form
    await page.getByLabel('Requisition Title').fill('MacBook Pro M3 Replacement');
    await page.getByLabel('Estimated Cost (USD)').fill('1500');
    await page.getByRole('button', { name: 'Submit Requisition' }).click();

    // Verify it appears
    await expect(page.getByText('MacBook Pro M3 Replacement').first()).toBeVisible({ timeout: 10000 });
  });
});
