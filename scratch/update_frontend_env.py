import urllib.request
import json

url = "https://api.render.com/v1/services/srv-dadaefgn74is73dvio8g/env-vars"
headers = {
    "Authorization": "Bearer rnd_VnCvXPBjPxHvrjUYPmOJWAYskAQt",
    "Content-Type": "application/json",
    "Accept": "application/json"
}
data = [
    {"key": "VITE_API_URL", "value": "https://expense-backend-1mpl.onrender.com/api/v1"},
    {"key": "VITE_GOOGLE_CLIENT_ID", "value": "1015460714060-8emtp3j6gksbh5ficfrm4tl3f5ovq4a5.apps.googleusercontent.com"},
    {"key": "NODE_ENV", "value": "production"}
]

req = urllib.request.Request(url, data=json.dumps(data).encode("utf-8"), headers=headers, method="PUT")
try:
    with urllib.request.urlopen(req) as response:
        print("Updated Frontend Env Vars Successfully!")
except Exception as e:
    print(e)
    if hasattr(e, 'read'):
        print(e.read().decode())
