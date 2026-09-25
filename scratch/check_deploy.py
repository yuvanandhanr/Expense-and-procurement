import urllib.request
import json

url = "https://api.render.com/v1/services/srv-dad9uaqfngtc738f6ki0/deploys/dep-daocd5jtqb8s73b7tcqg"
headers = {
    "Authorization": "Bearer rnd_VnCvXPBjPxHvrjUYPmOJWAYskAQt",
    "Accept": "application/json"
}

req = urllib.request.Request(url, headers=headers)
try:
    with urllib.request.urlopen(req) as response:
        deploy = json.loads(response.read().decode())
        print(deploy['status'])
except Exception as e:
    print(e)
