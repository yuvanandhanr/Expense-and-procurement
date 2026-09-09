import urllib.request
import json
import time

url = "https://api.render.com/v1/services/srv-dad9uaqfngtc738f6ki0/deploys"
headers = {
    "Authorization": "Bearer rnd_VnCvXPBjPxHvrjUYPmOJWAYskAQt",
    "Accept": "application/json"
}

req = urllib.request.Request(url, headers=headers)
print("Polling deploy status...")
while True:
    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            status = data[0]["deploy"]["status"]
            print(f"Current status: {status}")
            if status in ["live", "deactivated", "build_failed", "update_failed", "canceled"]:
                break
    except Exception as e:
        print(f"Error: {e}")
    time.sleep(10)
