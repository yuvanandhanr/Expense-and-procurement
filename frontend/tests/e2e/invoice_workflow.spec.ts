import { test, expect } from '@playwright/test';
import * as fs from 'fs';
import * as path from 'path';

test.describe('Vendor Invoice OCR and Data Integrity Workflow', () => {
  const datasetPath = process.env.OCR_DATASET_PATH || 'C:\\Yuvan\\Expense and procurement\\document_ocr_dataset_v2';
  
  test.beforeEach(async ({ page }) => {
    await page.addInitScript(() => {
      window.localStorage.clear();
    });
  });

  test('Upload Invoice and Verify Data Integrity', async ({ page, request }) => {
    test.setTimeout(90000); // OCR processing can be slow
    
    // 1. Admin/Finance Login
    await page.goto('/');
    await page.getByRole('button', { name: 'Alex Rivera' }).click();
    await expect(page.getByRole('heading', { name: /Good day/i })).toBeVisible({ timeout: 10000 });
    
    // Check initial dashboard invoice count/amount if possible
    
    // 2. Upload Invoice via API (Simulating AP/Vendor upload since UI might be missing)
    // We will use the first vendor invoice from the dataset
    const invoiceFilePath = path.join(datasetPath, 'images', 'vendor_invoice', 'vendor_invoice_0001.png');
    const imageBuffer = fs.readFileSync(invoiceFilePath);
    
    // We need the auth token
    const token = await page.evaluate(() => localStorage.getItem('access_token'));
    
    const response = await request.post('/api/v1/invoices/upload-batch', {
      headers: {
        'Authorization': `Bearer ${token}`
      },
      multipart: {
        files: {
          name: 'vendor_invoice_0001.png',
          mimeType: 'image/png',
          buffer: imageBuffer,
        }
      }
    });
    
    expect(response.status()).toBe(200);
    const invoiceData = await response.json();
    expect(invoiceData.length).toBeGreaterThan(0);
    const invoice = invoiceData[0];
    
    // 3. Verify in Invoices Page
    const invoicesResponsePromise = page.waitForResponse(response => response.url().includes('/api/v1/invoices') && response.status() === 200);
    await page.getByRole('link', { name: 'Vendor Invoices' }).click();
    await expect(page.getByRole('heading', { name: 'Vendor Invoices (3-Way Match)' })).toBeVisible();
    await invoicesResponsePromise;
    
    // Find the uploaded invoice in the list
    await expect(page.getByText(invoice.invoice_number)).toBeVisible({ timeout: 10000 });
    
    // 4. Check Data Integrity
    // E.g., The OCR extracted amount should match what is shown in the dashboard or invoice list
    const amountStr = `$${Number(invoice.grand_total).toLocaleString('en-US')}`;
    const row = page.locator('table tbody tr').filter({ hasText: invoice.invoice_number });
    await expect(row.getByText(amountStr)).toBeVisible();
    
    // Verify Dashboard Data Integrity
    await page.getByRole('link', { name: 'Dashboard', exact: true }).click();
    await expect(page.getByRole('heading', { name: /Good day/i })).toBeVisible();
    
    // Ensure the dashboard reflects the updated data (you could check for specific numbers or charts)
    // For now we just ensure no errors and it loads correctly
  });
});
