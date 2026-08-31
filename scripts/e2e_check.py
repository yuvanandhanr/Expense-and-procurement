import requests
import json
import uuid

API_BASE = "http://localhost:8080/api/v1"

def run_tests():
    print("Running E2E automated API loop tests...")

    # 1. Auth Login (Using mock payload)
    print("\n--- Testing Authentication ---")
    resp = requests.post(f"{API_BASE}/auth/google", json={"credential": "mock_google_test@dataeko.ai"})
    
    if resp.status_code != 200:
        print(f"Auth failed: {resp.status_code} {resp.text}")
        return
        
    token = resp.json().get("access_token")
    headers = {"Authorization": f"Bearer {token}"}
    print("Auth Login: SUCCESS")
    
    # 2. Get User Profile
    resp = requests.get(f"{API_BASE}/users/me", headers=headers)
    print(f"Get Profile: {resp.status_code}")
    
    # 3. Test Dashboard APIs
    print("\n--- Testing Dashboards ---")
    dashboards = ["executive", "procurement", "contracts", "finance", "vendor", "sustainability"]
    for db in dashboards:
        resp = requests.get(f"{API_BASE}/dashboard/{db}", headers=headers)
        if resp.status_code == 200:
            print(f"Dashboard '{db}': SUCCESS")
        else:
            print(f"Dashboard '{db}': FAILED {resp.status_code} - {resp.text}")

    # 4. Create a PR
    print("\n--- Testing Procurement Lifecycle ---")
    pr_payload = {
        "title": "Test PR " + str(uuid.uuid4())[:8],
        "justification": "E2E testing",
        "department_id": 1,
        "cost_center_id": 1,
        "priority": "Low",
        "purchase_type": "IT",
        "items": [
            {
                "category": "Software",
                "item_name": "API Testing Tool",
                "quantity": 1,
                "unit_price": 50.00
            }
        ]
    }
    
    resp = requests.post(f"{API_BASE}/pr/", json=pr_payload, headers=headers)
    if resp.status_code == 201:
        pr_id = resp.json()["pr_id"]
        print(f"Create PR: SUCCESS (ID: {pr_id})")
        
        # Submit PR
        resp = requests.post(f"{API_BASE}/pr/{pr_id}/submit", headers=headers)
        print(f"Submit PR: {resp.status_code} - {resp.text}")
    else:
        print(f"Create PR FAILED: {resp.status_code} - {resp.text}")

    print("\nE2E check completed.")

if __name__ == "__main__":
    run_tests()
