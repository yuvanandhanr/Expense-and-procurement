import { test, expect } from '@playwright/test';

test('bell popup', async ({ page }) => {
  await page.goto('http://localhost:5173/login');
  await page.fill('input[type="email"]', 'y.raja@dataeko.ai');
  await page.fill('input[type="password"]', 'admin123');
  await page.click('button:has-text("Sign In")');
  await page.waitForURL('http://localhost:5173/');
  
  // click bell
  await page.click('button[title="Notifications"]');
  await page.waitForTimeout(1000);
  await page.screenshot({ path: '../scratch/bell_clicked.png' });
});
