import urllib.request
import json

url = "https://api.render.com/v1/services/srv-dadfvc6q1p3s73dh42o0/env-vars"
headers = {
    "Authorization": "Bearer rnd_VnCvXPBjPxHvrjUYPmOJWAYskAQt",
    "Accept": "application/json"
}

req = urllib.request.Request(url, headers=headers)
try:
    with urllib.request.urlopen(req) as response:
        logs = json.loads(response.read().decode())
        print(logs)
except Exception as e:
    print(e)
    if hasattr(e, 'read'):
        print(e.read().decode())
