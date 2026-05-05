import os
import requests
from dotenv import load_dotenv

load_dotenv(".env")
api_key = os.getenv("GROQ_API_KEY")

def list_models():
    url = "https://api.groq.com/openai/v1/models"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            models = response.json()
            print("Available Groq Models:")
            for m in models['data']:
                print(f"- {m['id']}")
        else:
            print(f"Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    list_models()
