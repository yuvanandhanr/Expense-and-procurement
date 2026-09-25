import urllib.request
import json

# Add SPA rewrite rule via Render API
# Render static sites need a "Rewrite and Redirect" rule to serve index.html for all routes
url = "https://api.render.com/v1/services/srv-dadaefgn74is73dvio8g/routes"
headers = {
    "Authorization": "Bearer rnd_VnCvXPBjPxHvrjUYPmOJWAYskAQt",
    "Content-Type": "application/json",
    "Accept": "application/json"
}

# First list existing routes
req = urllib.request.Request(url, headers=headers)
try:
    with urllib.request.urlopen(req) as response:
        routes = json.loads(response.read().decode())
        print("Existing routes:", json.dumps(routes, indent=2))
except Exception as e:
    print(f"List routes error: {e}")
    if hasattr(e, 'read'):
        print(e.read().decode())

# Add catch-all rewrite rule for SPA
data = {
    "type": "rewrite",
    "source": "/*",
    "destination": "/index.html"
}
req = urllib.request.Request(url, data=json.dumps(data).encode("utf-8"), headers=headers, method="POST")
try:
    with urllib.request.urlopen(req) as response:
        result = json.loads(response.read().decode())
        print("Route added:", json.dumps(result, indent=2))
except Exception as e:
    print(f"Add route error: {e}")
    if hasattr(e, 'read'):
        print(e.read().decode())
