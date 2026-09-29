import { test, expect } from '@playwright/test';

test.describe('Authentication Flow', () => {
  test('User can log in as Employee', async ({ page }) => {
    // Navigate to the app root (will redirect to /login)
    await page.goto('/');

    // Wait for the login page to load
    await expect(page.getByRole('heading', { name: /ProcureSync/i })).toBeVisible();

    // Click the Employee mock login button
    const employeeLoginBtn = page.getByRole('button', { name: 'Rachel Foster' });
    await employeeLoginBtn.click();

    // Wait for successful redirection to Dashboard
    await expect(page.getByRole('heading', { name: /Good day/i })).toBeVisible({ timeout: 10000 });

    // Verify the URL is not /login
    expect(page.url()).not.toContain('/login');
  });

  test('User can log in as Admin', async ({ page }) => {
    await page.goto('/login');

    const adminLoginBtn = page.getByRole('button', { name: 'Alex Rivera' });
    await adminLoginBtn.click();

    await expect(page.getByRole('heading', { name: /Good day/i })).toBeVisible({ timeout: 10000 });
  });
});
