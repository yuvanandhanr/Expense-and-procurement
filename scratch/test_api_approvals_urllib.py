import urllib.request
import urllib.parse
import json
import time
import subprocess
import os

proc = subprocess.Popen(["python3", "-m", "uvicorn", "src.main:app", "--port", "8003"])
time.sleep(3)

try:
    req = urllib.request.Request("http://127.0.0.1:8003/api/v1/auth/google", data=json.dumps({"credential": "mock_google_y.raja@dataeko.ai"}).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as response:
        token = json.loads(response.read())["access_token"]
    
    req2 = urllib.request.Request("http://127.0.0.1:8003/api/v1/approvals/pending", headers={"Authorization": f"Bearer {token}"})
    try:
        with urllib.request.urlopen(req2) as response:
            print("Status:", response.status)
    except urllib.error.HTTPError as e:
        print("Error Status:", e.code)
        print("Response:", e.read().decode())
finally:
    proc.terminate()
