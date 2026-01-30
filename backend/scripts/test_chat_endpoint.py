
import requests
import json

url = "http://localhost:8000/api/chat/"
payload = {
    "message": "what is the punishment for murder",
    "top_k": 5
}
try:
    print(f"Sending request to {url}...")
    r = requests.post(url, json=payload)
    print(f"Status: {r.status_code}")
    print(f"Response: {r.text}")
except Exception as e:
    print(f"Request failed: {e}")
