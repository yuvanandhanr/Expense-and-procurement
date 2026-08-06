import requests

url = "http://localhost:8000/api/v1/invoices/upload"
files = {'file': open('/app/test_invoice.png', 'rb')}
# Fake the auth token if needed, or check if it's 401
try:
    response = requests.post(url, files=files)
    print("Status:", response.status_code)
    print("Body:", response.text)
except Exception as e:
    print("Exception:", str(e))
