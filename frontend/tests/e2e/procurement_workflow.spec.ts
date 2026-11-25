import { test, expect } from '@playwright/test';

test.describe('Procurement Workflow', () => {
  test('Employee can create a new purchase requisition', async ({ page }) => {
    // Log in as Employee
    await page.goto('/login');
    await page.getByRole('button', { name: 'Rachel Foster' }).click();
    await expect(page.getByRole('heading', { name: /My Dashboard|Good day/i })).toBeVisible({ timeout: 10000 });

    // Navigate to PRs
    await page.getByRole('link', { name: 'My Requisitions' }).click();
    await expect(page.getByRole('heading', { name: 'My Requisitions' })).toBeVisible();

    // Open New PR Modal
    await page.getByRole('button', { name: 'New Requisition', exact: true }).click();
    
    // Fill form
    const prTitle = `MacBook Pro M3 Replacement ${Date.now()}`;
    await page.getByPlaceholder('e.g. MacBook Pro M3').fill(prTitle);
    await page.getByPlaceholder('Provide context for approval and actual problem being solved...').fill('Replacement laptop for development work.');
    await page.getByRole('button', { name: 'Submit Requisition' }).click();

    // Verify it appears
    await expect(page.getByText(prTitle).first()).toBeVisible({ timeout: 10000 });
  });
});
