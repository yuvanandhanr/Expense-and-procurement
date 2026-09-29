import urllib.request
import urllib.error
import json

BASE_URL = "http://127.0.0.1:8081"

def print_result(method, url, status_code, ok):
    icon = "✅" if ok else "❌"
    print(f"{icon} {method.upper()} {url} - Status: {status_code}")

def make_request(method, path, headers=None, data=None):
    url = f"{BASE_URL}{path}"
    req = urllib.request.Request(url, method=method)
    if headers:
        for k, v in headers.items():
            req.add_header(k, v)
    
    body = None
    if data:
        body = json.dumps(data).encode('utf-8')
        req.add_header('Content-Type', 'application/json')
    
    try:
        with urllib.request.urlopen(req, data=body, timeout=5) as response:
            return response.status, response.read().decode('utf-8')
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8')
    except Exception as e:
        raise e

def main():
    print("Starting API health check...")
    
    endpoints_no_auth = [
        ("GET", "/health"),
        ("GET", "/ready"),
        ("GET", "/openapi.json")
    ]
    
    for method, path in endpoints_no_auth:
        try:
            status, text = make_request(method, path)
            print_result(method, path, status, status == 200)
        except Exception as e:
            print(f"❌ {method.upper()} {path} - Error: {e}")

    print("\nAuthenticating...")
    auth_payload = {"credential": "mock_google_y.raja@dataeko.ai"}
    try:
        status, text = make_request("POST", "/api/v1/auth/google", data=auth_payload)
        if status != 200:
            print(f"❌ Authentication failed: {status} - {text}")
            return
        
        token = json.loads(text).get("access_token")
        if not token:
            print("❌ No access token found in response.")
            return
        print("✅ Authentication successful.")
    except Exception as e:
        print(f"❌ Authentication error: {e}")
        return

    headers = {"Authorization": f"Bearer {token}"}
    
    endpoints_auth = [
        "/api/v1/users/me",
        "/api/v1/departments",
        "/api/v1/users",
        "/api/v1/roles",
        "/api/v1/expenses",
        "/api/v1/approvals/inbox",
        "/api/v1/purchase-requisitions",
        "/api/v1/vendors",
        "/api/v1/rfq",
        "/api/v1/purchase-orders",
        "/api/v1/assets",
        "/api/v1/asset-incidents",
        "/api/v1/deliveries",
        "/api/v1/grn",
        "/api/v1/invoices",
        "/api/v1/reports",
        "/api/v1/dashboard/overview",
        "/api/v1/audit",
        "/api/v1/settings"
    ]
    
    print("\nTesting Authenticated GET endpoints...")
    all_passed = True
    for path in endpoints_auth:
        try:
            status, text = make_request("GET", path, headers=headers)
            ok = status in [200, 403, 404] 
            print_result("GET", path, status, ok)
            if not ok:
                all_passed = False
                print(f"   Response: {text[:200]}")
        except Exception as e:
            print(f"❌ GET {path} - Error: {e}")
            all_passed = False
            
    print("\nAPI Check Complete.")
    if all_passed:
        print("🎉 All tested APIs responded gracefully (no 500 server errors).")
    else:
        print("⚠️ Some APIs returned unexpected errors (e.g. 500 Internal Server Error).")

if __name__ == "__main__":
    main()
