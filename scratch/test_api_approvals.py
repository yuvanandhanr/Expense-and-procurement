import requests
import time
import subprocess
import os

# Start server
proc = subprocess.Popen(["python3", "-m", "uvicorn", "src.main:app", "--port", "8002"])
time.sleep(3)

try:
    login_url = "http://127.0.0.1:8002/api/v1/auth/google"
    resp = requests.post(login_url, json={"credential": "mock_google_y.raja@dataeko.ai"})
    if resp.status_code != 200:
        print("Login failed:", resp.status_code, resp.text)
        exit(1)

    token = resp.json()["access_token"]
    print("Got token")

    app_url = "http://127.0.0.1:8002/api/v1/approvals/pending"
    resp = requests.get(app_url, headers={"Authorization": f"Bearer {token}"})
    print("Approvals status:", resp.status_code)
    if resp.status_code != 200:
        print("Response:", resp.text)
    else:
        print("Success")
finally:
    proc.terminate()
