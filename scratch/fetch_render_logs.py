import urllib.request
import urllib.parse
import json
import os

url = "https://api.render.com/v1/services/srv-dad9uaqfngtc738f6ki0/deploys?limit=1"
headers = {
    "Authorization": "Bearer rnd_VnCvXPBjPxHvrjUYPmOJWAYskAQt",
    "Accept": "application/json"
}

req = urllib.request.Request(url, headers=headers)
try:
    with urllib.request.urlopen(req) as response:
        deploys = json.loads(response.read().decode())
        if deploys:
            deploy_id = deploys[0]['deploy']['id']
            print("Latest deploy:", deploy_id)
            
            # Fetch logs? Wait, Render API for logs is not available or requires a websocket.
            # But maybe I can hit my backend's actual URL to see what returns 500?
except Exception as e:
    print(e)
