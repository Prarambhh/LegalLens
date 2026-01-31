import requests
import json

url = "http://localhost:8000/api/chat/"
headers = {"Content-Type": "application/json"}
data = {
    "message": "Draft a professional Vakalatnama (Authorization for legal representation) for use in Indian Courts.",
    "top_k": 3
}

try:
    print(f"Sending request to {url}...")
    response = requests.post(url, headers=headers, json=data)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        res = response.json()
        print("\n--- ANSWER START ---")
        print(res["answer"][:500] + "...")
        print("--- ANSWER END ---\n")
    else:
        print(f"Error: {response.text}")
except Exception as e:
    print(f"Error: {e}")
