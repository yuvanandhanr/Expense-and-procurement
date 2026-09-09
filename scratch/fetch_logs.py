import urllib.request
import json

url = "https://api.render.com/v1/services/srv-dad9uaqfngtc738f6ki0/logs?limit=50"
headers = {
    "Authorization": "Bearer rnd_VnCvXPBjPxHvrjUYPmOJWAYskAQt",
    "Accept": "application/json"
}

req = urllib.request.Request(url, headers=headers)
try:
    with urllib.request.urlopen(req) as response:
        logs = json.loads(response.read().decode())
        for log in reversed(logs):
            print(log['message'])
except Exception as e:
    print(e)
    if hasattr(e, 'read'):
        print(e.read().decode())
