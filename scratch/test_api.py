import requests
import time

# 1. Login to get token
# Wait for server to start
time.sleep(2)
login_url = "http://127.0.0.1:8000/api/v1/auth/google"
resp = requests.post(login_url, json={"credential": "mock_google_y.raja@dataeko.ai"})
if resp.status_code != 200:
    print("Login failed:", resp.status_code, resp.text)
    exit(1)

token = resp.json()["access_token"]
print("Got token")

# 2. Fetch expenses
exp_url = "http://127.0.0.1:8000/api/v1/expenses"
resp = requests.get(exp_url, headers={"Authorization": f"Bearer {token}"})
print("Expenses status:", resp.status_code)
if resp.status_code != 200:
    print("Response:", resp.text)
else:
    print("Success")
