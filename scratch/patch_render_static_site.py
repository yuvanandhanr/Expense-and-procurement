import urllib.request
import json

url = "https://api.render.com/v1/services/srv-dadfvc6q1p3s73dh42o0"
headers = {
    "Authorization": "Bearer rnd_VnCvXPBjPxHvrjUYPmOJWAYskAQt",
    "Content-Type": "application/json",
    "Accept": "application/json"
}

data = {
    "serviceDetails": {
        "routes": [
            {
                "type": "rewrite",
                "source": "/*",
                "destination": "/index.html"
            }
        ]
    }
}

req = urllib.request.Request(url, data=json.dumps(data).encode("utf-8"), headers=headers, method="PATCH")
try:
    with urllib.request.urlopen(req) as response:
        print("Updated Routes Successfully!")
        print(response.read().decode())
except Exception as e:
    print(e)
    if hasattr(e, 'read'):
        print(e.read().decode())
