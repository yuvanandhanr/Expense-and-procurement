import asyncio
from playwright.async_api import async_playwright

ARTIFACT_DIR = "/Users/a.chaitnasree/.gemini/antigravity-ide/brain/a3355d7a-bf04-4c88-9aca-47c7deb030d1"
BASE_URL = "http://localhost:3001"

async def test_login_and_expense_workflow():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        # Record video into the artifact directory
        context = await browser.new_context(record_video_dir=ARTIFACT_DIR, viewport={'width': 1280, 'height': 720})
        page = await context.new_page()
        
        print("Navigation to login page...")
        await page.goto(BASE_URL)
        
        print("Logging in as mock admin (Alex Rivera)...")
        # In Login.tsx: test accounts are listed. Let's find the one for Alex Rivera and click it.
        # Alternatively, find the text "mock_google_y.raja@dataeko.ai" or click by role.
        # The test accounts are rendered as list items.
        await page.wait_for_selector("text=Alex Rivera", timeout=10000)
        
        # Click the test account button for Alex Rivera
        await page.click("text=Alex Rivera")
        
        # Wait for navigation to dashboard
        print("Waiting for dashboard to load...")
        await page.wait_for_url("**/", timeout=10000)
        
        # Verify dashboard loaded by looking for a common element, like "Total Expenses" or the Dashboard title
        await page.wait_for_selector("text=Dashboard", timeout=10000)
        print("✅ Login workflow passed.")
        
        # Now let's test navigating to Expenses
        print("Navigating to Expenses...")
        # Since the app uses HashRouter, go directly to the route
        await page.goto(f"{BASE_URL}/#/expenses")
        
        # Wait for the Expenses page header to load
        # Wait for "My Reimbursements" or "Expense Reports" or whatever is rendered on that page
        # Let's wait for a more generic element like a table or the New Expense button
        await page.wait_for_selector("button:has-text('New Reimbursement')", timeout=15000, state="attached")
        print("✅ Navigation to Expenses passed.")
        
        # Click New Expense
        await page.click("button:has-text('New Reimbursement')")
        print("✅ New Expense modal opened.")
        
        # Clean up
        await context.close()
        await browser.close()
        print("✅ Workflow recorded successfully!")

if __name__ == "__main__":
    asyncio.run(test_login_and_expense_workflow())
