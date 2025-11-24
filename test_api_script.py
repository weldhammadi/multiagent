import requests
import json

url = "http://127.0.0.1:8005/interpret"
payload = {
    "user_id": "test_user_script",
    "text": "Crée un agent qui résume mes emails",
    "metadata": {"source": "test_script"}
}
headers = {"Content-Type": "application/json"}

try:
    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()
    print("Status Code:", response.status_code)
    print("Response JSON:")
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))
except Exception as e:
    print(f"Error: {e}")
