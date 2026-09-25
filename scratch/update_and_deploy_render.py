import urllib.request
import json

url = "https://api.render.com/v1/services/srv-dad9uaqfngtc738f6ki0/env-vars"
headers = {
    "Authorization": "Bearer rnd_VnCvXPBjPxHvrjUYPmOJWAYskAQt",
    "Content-Type": "application/json",
    "Accept": "application/json"
}
data = [
    {"key": "SUPABASE_URL", "value": "https://qagextokkrxrrmowyser.supabase.co"},
    {"key": "SUPABASE_KEY", "value": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFhZ2V4dG9ra3J4cnJtb3d5c2VyIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODUzMDc4MTksImV4cCI6MjEwMDg4MzgxOX0.6cxTtCld8P09nIbqjtigx4BIxJvQu0FZQNlWso4ZuvI"},
    {"key": "ENVIRONMENT", "value": "production"},
    {"key": "JWT_SECRET", "value": "placeholder-jwt-secret"},
    {"key": "DATABASE_URL", "value": "postgresql+asyncpg://postgres.qagextokkrxrrmowyser:postgres%25123@aws-1-ap-south-1.pooler.supabase.com:5432/postgres"}
]

req = urllib.request.Request(url, data=json.dumps(data).encode("utf-8"), headers=headers, method="PUT")
try:
    with urllib.request.urlopen(req) as response:
        print("Updated Env Vars Successfully!")
except Exception as e:
    print(e)
    if hasattr(e, 'read'):
        print(e.read().decode())

# After updating, trigger a deploy to make sure it runs with the new DB
deploy_url = "https://api.render.com/v1/services/srv-dad9uaqfngtc738f6ki0/deploys"
deploy_req = urllib.request.Request(deploy_url, data=b"{}", headers=headers, method="POST")
try:
    with urllib.request.urlopen(deploy_req) as response:
        print("Triggered deploy successfully!")
except Exception as e:
    print("Deploy trigger error:", e)
    if hasattr(e, 'read'):
        print(e.read().decode())
