import requests
import json

# Test Agent 1 (Chat) endpoint
CHAT_URL = "http://localhost:8000/api/chat"

print("=" * 60)
print("Testing Agent 1 (Chat Service) → Agent 2 (Interpretation)")
print("=" * 60)

# Conversation flow
messages = [
    "Je veux un agent pour mes emails",
    "Gmail",
    "Envoyer un résumé sur Slack toutes les 30 minutes"
]

session_id = None

for i, user_message in enumerate(messages, 1):
    print(f"\n[Tour {i}] User: {user_message}")
    
    payload = {
        "user_id": "test_user",
        "message": user_message
    }
    
    if session_id:
        payload["session_id"] = session_id
    
    try:
        response = requests.post(CHAT_URL, json=payload)
        
        if response.status_code == 200:
            data = response.json()
            
            # Store session_id for next turn
            if not session_id:
                session_id = data["session_id"]
                print(f"Session ID: {session_id}")
            
            print(f"[Tour {i}] Assistant: {data['message']}")
            print(f"Need Status: {data['need_status']}")
            
            # If AgentSpec was generated
            if data.get("agent_spec"):
                print("\n" + "=" * 60)
                print("✅ AGENTSPEC GÉNÉRÉ!")
                print("=" * 60)
                print(json.dumps(data["agent_spec"], indent=2, ensure_ascii=False))
                break
        else:
            print(f"❌ Error: {response.status_code} - {response.text}")
            break
    except Exception as e:
        print(f"❌ Connection error: {e}")
        print("\nMake sure the API is running: python run_api.py")
        break

print("\n" + "=" * 60)
print("Test completed!")
print("=" * 60)
