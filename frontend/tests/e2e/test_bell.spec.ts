import { test, expect } from '@playwright/test';

test('bell popup', async ({ page }) => {
  await page.goto('/login');
  await page.getByRole('button', { name: 'Alex Rivera' }).click();
  await expect(page.getByRole('heading', { name: /My Dashboard|Good day/i })).toBeVisible({ timeout: 10000 });
  
  // click bell
  const bellBtn = page.locator('button[title="Notifications"]');
  await expect(bellBtn).toBeVisible();
  await bellBtn.click();
  
  // Verify notification popover appears
  await expect(page.getByText('Notifications', { exact: true }).first()).toBeVisible();
});
