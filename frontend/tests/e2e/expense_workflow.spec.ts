import { test, expect } from '@playwright/test';
import { getRandomTestImage, getImagePath } from './utils/ocrHelper';

test.describe('Expense Workflow & Reimbursement OCR', () => {
  test('Employee creates expense, uploads receipt (OCR), Manager approves', async ({ page }) => {
    test.setTimeout(120000);
    // 1. Log in as Employee
    await page.goto('/login');
    await page.getByRole('button', { name: 'Rachel Foster' }).click();
    await expect(page.getByRole('heading', { name: /My Dashboard|Good day/i })).toBeVisible({ timeout: 10000 });

    // 2. Navigate to Expenses
    await page.getByRole('link', { name: 'My Reimbursements' }).click();
    await expect(page.getByRole('heading', { name: 'My Reimbursements' })).toBeVisible();

    // 3. Create New Reimbursement
    await page.getByRole('button', { name: /New Reimbursement/i }).click();
    
    // Select the category and submit
    const uniqueId = Date.now();
    const reportTitle = `Q3 Sales Offsite in NYC ${uniqueId}`;
    await page.getByPlaceholder('e.g. Q3 Sales Offsite in NYC').fill(reportTitle);
    await page.getByPlaceholder('Provide a detailed justification for this expense claim...').fill('Travel and client dinner expenses for the Q3 enterprise sales offsite.');
    await page.getByRole('button', { name: /Create Report|Save & Add Receipts/i }).click();

    // Verify it appears in the list and is auto-selected in details
    await expect(page.getByText(reportTitle).first()).toBeVisible({ timeout: 20000 });
    await expect(page.getByRole('heading', { name: reportTitle, exact: true })).toBeVisible({ timeout: 20000 });
    
    // 4. Upload Receipt using OCR dataset helper
    const testDoc = getRandomTestImage('reimbursement');
    const imagePath = getImagePath(testDoc.file);
    
    console.log(`Testing OCR with ${testDoc.file} - Expected Amount: ${testDoc.grand_total}`);

    // Set input files
    const fileInput = page.locator('input#receipt-upload');
    await fileInput.setInputFiles(imagePath);

    // Wait for OCR to complete (success toast)
    await expect(page.getByText('Receipts uploaded & OCR completed')).toBeVisible({ timeout: 20000 });
    await page.waitForTimeout(2000); // Wait for data refetch

    // 5. Verify amount if required by OCR confidence threshold
    const verifyBtn = page.getByText('VERIFY AMOUNT', { exact: true }).or(page.getByText('Verify Amount', { exact: true }));
    if (await verifyBtn.count() > 0 && await verifyBtn.first().isVisible()) {
      await verifyBtn.first().click();
      await page.locator('input[type="number"]').fill(testDoc.grand_total.toString());
      await page.locator('button').filter({ has: page.locator('svg.lucide-check-circle') }).first().click();
    }

    // 6. Submit for Approval
    await page.getByRole('button', { name: 'Review & Submit' }).click();
    
    // Declaration modal
    await page.getByRole('checkbox').check();
    await page.getByRole('button', { name: 'Confirm & Submit' }).click();

    // Wait for status to change to Pending Approval
    await expect(page.getByText(/Submitted|Pending Manager Approval|Pending Approval/i).first()).toBeVisible({ timeout: 10000 });

    // 7. Log out Employee
    await page.evaluate(() => localStorage.clear());

    // 8. Log in as Manager
    await page.goto('/login');
    await page.getByRole('button', { name: 'David Kim' }).click();
    await expect(page.getByRole('heading', { name: /My Dashboard|Good day/i })).toBeVisible({ timeout: 10000 });

    // 9. Navigate to Team Approvals or Expenses
    await page.getByRole('link', { name: 'Pending Approvals' }).click();
    
    // Find the report and approve it
    const row = page.locator('tr', { hasText: reportTitle }).first();
    await expect(row).toBeVisible({ timeout: 15000 });
    await row.getByRole('button', { name: 'Review & Action' }).click();

    // In detail modal, click Approve
    await page.getByRole('button', { name: 'Approve', exact: true }).click();

    // In confirm modal, click Confirm Approval
    await page.getByRole('button', { name: 'Confirm Approval' }).click();
    
    // Check toast or status update
    await expect(page.getByText(/successfully approved/i)).toBeVisible({ timeout: 10000 });
  });
});
