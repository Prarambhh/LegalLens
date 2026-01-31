import requests
import json

url = "http://localhost:8000/api/documents/chat"
headers = {"Content-Type": "application/json"}
data = {
    "query": "what is this document about?",
    "document_text": "This is a Service Agreement entered into by and between The Company and The Customer. 1. TERMINATION. The Provider reserves the right to terminate at any time."
}

try:
    print(f"Sending request to {url}...")
    response = requests.post(url, headers=headers, json=data)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        res_json = response.json()
        print("\n--- ANSWER ---")
        print(res_json.get("answer"))
        print("\n--- CITATIONS ---")
        print(len(res_json.get("citations", [])))
    else:
        print(f"Error: {response.text}")
except Exception as e:
    print(f"Error: {e}")
