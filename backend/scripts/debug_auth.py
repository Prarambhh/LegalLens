
import requests

url = "http://localhost:8000/api/auth/login/access-token"
# FULL Swagger UI payload
data = {
    "grant_type": "password",
    "username": "admin@legallens.com",
    "password": "password123",
    "scope": "",
    "client_id": "",
    "client_secret": ""
}

try:
    print(f"Sending FULL OAuth2 POST to {url}...")
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'accept': 'application/json'
    }
    r = requests.post(url, data=data, headers=headers) 
    print(f"Status: {r.status_code}")
    print(f"Response: {r.text}")
except Exception as e:
    print(f"Request failed: {e}")
