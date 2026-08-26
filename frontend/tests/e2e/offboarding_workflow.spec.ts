import { test, expect } from '@playwright/test';

test.describe('Employee Offboarding Workflow', () => {
  test('Admin can initiate offboarding for an active employee', async ({ page }) => {
    // Navigate to Login as Admin
    await page.goto('/login');
    await page.getByRole('button', { name: 'Admin', exact: true }).click();
    await expect(page.getByRole('heading', { name: /Welcome back/i })).toBeVisible({ timeout: 10000 });

    // Navigate to Users
    await page.getByRole('link', { name: 'User Management' }).click();
    await expect(page.getByRole('heading', { name: 'User Management' })).toBeVisible();

    // Find the first active user's Offboard button
    // It's a button with text "Offboard"
    const offboardBtn = page.locator('button:has-text("Offboard"):not(:disabled)').first();

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
