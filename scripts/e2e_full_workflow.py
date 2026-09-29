import asyncio
from playwright.async_api import async_playwright

BASE_URL = "http://localhost:3001"

async def test_full_workflows():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={'width': 1280, 'height': 720})
        page = await context.new_page()
        
        # Test 1: Vendor Login
        print("Testing Vendor Login...")
        await page.goto(BASE_URL)
        # Click the vendor tab
        await page.wait_for_selector("button:has-text('Supplier Partner')", timeout=10000)
        await page.click("button:has-text('Supplier Partner')")
        
        await page.fill("input[placeholder='vendor@company.com']", "vendor@example.com")
        await page.click("button:has-text('Continue')")
        
        # Wait for OTP input
        await page.wait_for_selector("input[placeholder='000000']", timeout=10000)
        await page.fill("input[placeholder='000000']", "123456")
        await page.click("button:has-text('Verify & Login')")
        
        # Verify Vendor Dashboard
        try:
            await page.wait_for_selector("text=Vendor Operations", timeout=10000)
            print("✅ Vendor login successful!")
        except Exception as e:
            print("❌ Vendor login failed.")
            print(e)
            
        await page.click("button:has-text('Log out')")
        await page.wait_for_timeout(1000)

        # Test 2: Expense Creation and Approval
        print("Testing Expense Creation -> Approval flow...")
        # 2a. Employee Login
        await page.goto(BASE_URL)
        await page.click("button:has-text('Corporate Network')") # switch back to employee tab if needed
        await page.wait_for_selector("text=Rachel Foster", timeout=10000)
        await page.click("text=Rachel Foster") # Employee
        await page.wait_for_url("**/", timeout=15000)
        
        # 2b. Create and Submit Expense
        await page.goto(f"{BASE_URL}/#/expenses")
        await page.wait_for_selector("button:has-text('New Reimbursement')", timeout=15000)
        await page.click("button:has-text('New Reimbursement')")
        
        await page.fill("input[placeholder='e.g., Client Lunch']", "E2E Test Expense")
        await page.fill("input[type='number']", "100")
        
        # Click "Save & Add Receipts" (which was Save as Draft, but we need to submit)
        # Actually in the UI it says "Save & Add Receipts" for the main submit if isDraft=false.
        # Wait, the button text for isDraft=false is "Save & Add Receipts".
        await page.click("button:has-text('Save & Add Receipts')")
        
        # We also need to click the Review & Submit button that we just enabled!
        # The expense is created, wait for "Review & Submit"
        await page.wait_for_selector("button:has-text('Review & Submit')", timeout=15000)
        await page.click("button:has-text('Review & Submit')")
        
        # Click the declaration checkbox (it's required!)
        await page.wait_for_selector("input[type='checkbox']", timeout=10000)
        await page.check("input[type='checkbox']")
        
        # Click Confirm & Submit
        await page.click("button:has-text('Confirm & Submit')")
        
        # Wait for submit confirmation
        await page.wait_for_selector("text=Report submitted for approval", timeout=15000)
        
        # 2c. Manager Login
        await page.click("button:has-text('Log out')")
        await page.wait_for_timeout(1000)
        await page.goto(BASE_URL)
        await page.click("text=David Kim") # Manager
        await page.wait_for_url("**/", timeout=15000)
        
        # 2d. Approve
        await page.goto(f"{BASE_URL}/#/approvals")
        try:
            await page.wait_for_selector("button:has-text('Approve')", timeout=10000)
            await page.click("button:has-text('Approve')")
            await page.wait_for_selector("button:has-text('Confirm')", timeout=10000)
            await page.click("button:has-text('Confirm')")
            print("✅ Expense Approved successfully!")
        except Exception as e:
            print("❌ Expense Approval failed or button not found.")
            print(e)

        await context.close()
        await browser.close()
        print("Done.")

if __name__ == "__main__":
    asyncio.run(test_full_workflows())
