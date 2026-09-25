from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)
response = client.post("/api/v1/auth/google", json={"credential": "mock_google_y.raja@dataeko.ai"})
if response.status_code != 200:
    print("Auth failed", response.status_code, response.text)
else:
    token = response.json().get("access_token")
    response = client.get("/api/v1/approvals/pending", headers={"Authorization": f"Bearer {token}"})
    print(response.status_code)
    if response.status_code != 200:
        print(response.text)

