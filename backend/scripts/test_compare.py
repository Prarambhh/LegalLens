import requests
import json

url = "http://localhost:8000/api/compare/analyze"
data = {"query": "IPC 378"}

try:
    print(f"Sending request to {url} with query '{data['query']}'...")
    response = requests.post(url, json=data)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        res = response.json()
        print("\n--- OLD LAW ---")
        print(f"{res['old']['act']} {res['old']['section']}")
        print(f"Content: {res['old']['content'][:100]}...")
        
        print("\n--- NEW LAW ---")
        print(f"{res['new']['act']} {res['new']['section']}")
        print(f"Content: {res['new']['content'][:100]}...")
        
        print("\n--- MAPPING ---")
        print(f"Change: {res['mapping']['changeType']}")
        print(f"Summary: {res['mapping']['summary']}")
    else:
        print(f"Error: {response.text}")
except Exception as e:
    print(f"Exception: {e}")
