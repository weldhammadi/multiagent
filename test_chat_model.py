import requests
import json

def test_chat():
    url = "http://localhost:8000/api/chat"
    payload = {
        "user_id": "test_user_model",
        "message": "Hello, are you running on llama-3.1-8b-instant?"
    }
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_chat()
