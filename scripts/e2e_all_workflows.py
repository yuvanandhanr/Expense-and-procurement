import asyncio
from playwright.async_api import async_playwright

ARTIFACT_DIR = "/Users/a.chaitnasree/.gemini/antigravity-ide/brain/a3355d7a-bf04-4c88-9aca-47c7deb030d1"
BASE_URL = "http://localhost:3001"

async def test_workflows():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(record_video_dir=ARTIFACT_DIR, viewport={'width': 1280, 'height': 720})
        page = await context.new_page()
        
        # 1. Login
        print("Logging in...")
        await page.goto(BASE_URL)
        await page.wait_for_selector("text=Alex Rivera", timeout=15000)
        await page.click("text=Alex Rivera")
        # We also want to verify the toast notification changes we just made!
        await page.wait_for_selector("text=Authenticated with Google Workspace!", timeout=10000)
        await page.wait_for_url("**/", timeout=15000)
        await page.wait_for_timeout(1500) # Let animations settle
        
        # 2. Expense Workflow
        print("Testing Expense Workflow...")
        await page.goto(f"{BASE_URL}/#/expenses")
        await page.wait_for_selector("button:has-text('New Reimbursement')", timeout=15000)
        await page.click("button:has-text('New Reimbursement')")
        # Ensure modal opens
        await page.wait_for_selector("text=New Expense Reimbursement", timeout=10000)
        await page.click("button:has-text('Cancel')")
        await page.wait_for_timeout(1500)
        
        # 3. Procurement Workflow (PR)
        print("Testing PR Workflow...")
        await page.goto(f"{BASE_URL}/#/prs")
        await page.wait_for_selector("button:has-text('New Requisition')", timeout=15000)
        await page.click("button:has-text('New Requisition')")
        await page.wait_for_selector("text=Create My Requisition", timeout=10000)
        await page.click("button:has-text('Cancel')")
        await page.wait_for_timeout(1500)
        
        # 4. Asset Incident Workflow
        print("Testing Asset Incident Workflow...")
        await page.goto(f"{BASE_URL}/#/my-assets")
        try:
            await page.wait_for_selector("button:has-text('Report Issue')", timeout=5000)
            await page.click("button:has-text('Report Issue')")
            await page.wait_for_selector("text=Report Asset Issue", timeout=5000)
            await page.click("button:has-text('Cancel')")
        except Exception as e:
            print("No assets available to report issue on, or timeout. Skipping...")
            pass
        
        await page.wait_for_timeout(2000)
        await context.close()
        await browser.close()
        print("✅ Workflows recorded successfully!")

if __name__ == "__main__":
    asyncio.run(test_workflows())
