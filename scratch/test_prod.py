import urllib.request
import json

base_url = "https://expense-backend-1mpl.onrender.com"

# Try getting token
login_url = f"{base_url}/api/v1/auth/google"
req = urllib.request.Request(login_url, json.dumps({"credential": "mock_google_y.raja@dataeko.ai"}).encode(), headers={"Content-Type": "application/json"})
try:
    with urllib.request.urlopen(req) as resp:
        token = json.loads(resp.read().decode())["access_token"]
        print("Got token")
except Exception as e:
    print("Login failed:", e)
    if hasattr(e, 'read'):
        print(e.read().decode())
    exit(1)

headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
endpoints = [
    "/api/v1/approvals",
    "/api/v1/expenses",
    "/api/v1/dashboard",
    "/api/v1/purchase-requisitions",
    "/api/v1/asset-incidents"
]

for ep in endpoints:
    url = f"{base_url}{ep}"
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req) as resp:
            print(f"{ep}: {resp.status}")
    except urllib.error.HTTPError as e:
        print(f"{ep}: {e.code}")
        print(e.read().decode())
    except Exception as e:
        print(f"{ep}:", e)
