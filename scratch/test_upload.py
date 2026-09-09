import httpx
import asyncio

async def run():
    async with httpx.AsyncClient() as client:
        # Use json=
        login_data = {
            "email": "chaitna@company.com",
            "password": "Password123!"
        }
        res = await client.post("http://127.0.0.1:8001/api/v1/auth/login", json=login_data)
        if res.status_code != 200:
            print("Login failed:", res.text)
            return

        token = res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Create an expense report first
        report_data = {
            "title": "Test Report",
            "cost_center_id": None,
            "project_code": "PRJ-123",
            "justification": "Test justification"
        }
        res = await client.post("http://127.0.0.1:8001/api/v1/expenses", json=report_data, headers=headers)
        if res.status_code not in [200, 201]:
            print("Create report failed:", res.text)
            return

        report_id = res.json()["expense_report_id"]
        print(f"Created report {report_id}")

        # Create a dummy image
        with open("test_image.png", "wb") as f:
            f.write(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82")

        # Upload the image
        with open("test_image.png", "rb") as f:
            files = {"files": ("test_image.png", f, "image/png")}
            print("Uploading...")
            try:
                res = await client.post(f"http://127.0.0.1:8001/api/v1/expenses/{report_id}/receipts", headers=headers, files=files)
                print("Upload status:", res.status_code)
                print("Upload response:", res.text)
            except Exception as e:
                print("CONNECTION ERROR! The server crashed!", e)

asyncio.run(run())
