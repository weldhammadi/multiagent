import requests

# Test the API endpoint
url = "http://localhost:8000/api/interpret"

data = {
    "user_id": "test_user",
    "text": "Crée-moi un agent qui surveille mes emails.",
    "conversation_id": "test_conv_1",
    "turn_index": 1
}

print("Testing API endpoint...")
print(f"URL: {url}")
print(f"Data: {data}\n")

try:
    response = requests.post(url, data=data)
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        print("\n✅ API is working!")
        print("\nResponse:")
        import json
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    else:
        print(f"\n❌ Error: {response.text}")
except Exception as e:
    print(f"\n❌ Connection error: {e}")
    print("\nMake sure the API server is running:")
    print("  python run_api.py")
