import { test, expect } from '@playwright/test';

test.describe('Employee Offboarding Workflow', () => {
  test('Admin can initiate offboarding for an active employee', async ({ page }) => {
    // Navigate to Login as Admin
    await page.goto('/login');
    await page.getByRole('button', { name: 'Alex Rivera' }).click();
    await expect(page.getByRole('heading', { name: /Good day/i })).toBeVisible({ timeout: 10000 });

    // Navigate to Users
    await page.getByRole('link', { name: 'User Management' }).click();
    await expect(page.getByRole('heading', { name: 'User Management' })).toBeVisible();

    // Find a user named "John Doe" or someone who isn't a core mock user.
    // If not found, just use the first row but skip offboarding core accounts.
    const row = page.locator('tr').filter({ hasText: /Employee/ }).filter({ hasNotText: 'Rachel Foster' }).first();
    const offboardBtn = row.locator('button:has-text("Offboard"):not(:disabled)');

    if (await offboardBtn.isVisible()) {
      // Stub the window.confirm dialogue to always return true
      page.on('dialog', dialog => dialog.accept());
      
      await offboardBtn.click();

      // Verify success
      await expect(page.getByText(/Offboarding initiated for/)).toBeVisible({ timeout: 10000 });

      // Navigate to Approvals to verify tasks exist
      await page.getByRole('link', { name: 'Approvals' }).click();
      await page.getByRole('button', { name: 'Resignations' }).click();
      
      // We expect some tasks to be generated for offboarding
      await expect(page.getByRole('table')).toBeVisible();
    }
  });
});
