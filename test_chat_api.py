import requests
import json
import time

url = "http://127.0.0.1:8008/chat"
session_id = f"test_session_{int(time.time())}"
user_id = "test_user_chat"

def send_message(message):
    payload = {
        "session_id": session_id,
        "user_id": user_id,
        "message": message,
        "metadata": {}
    }
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error: {e}")
        return None

print(f"--- Starting Chat Session: {session_id} ---")

# 1. Premier message
msg1 = "Bonjour, je veux créer un agent."
print(f"\nUser: {msg1}")
resp1 = send_message(msg1)
print(f"Assistant: {resp1['reply']}")
print(f"Done: {resp1['done']}")

# 2. Deuxième message (précision)
msg2 = "Il doit surveiller mes emails et m'envoyer un résumé chaque matin."
print(f"\nUser: {msg2}")
resp2 = send_message(msg2)
print(f"Assistant: {resp2['reply']}")
print(f"Done: {resp2['done']}")

# 3. Troisième message (forcing completion if not ready)
# Note: Le prompt système demande de taguer [READY], on espère que le LLM le fera vite.
# Si ce n'est pas fini, ce n'est pas grave, c'est le comportement attendu du chat.
if resp2 and not resp2['done']:
    msg3 = "C'est tout ce que je veux. [READY]" # Hack pour forcer le test si le LLM est bavard
    print(f"\nUser: {msg3}")
    resp3 = send_message(msg3)
    print(f"Assistant: {resp3['reply']}")
    print(f"Done: {resp3['done']}")
    if resp3['done']:
        print("\n--- Agent Spec Generated ---")
        print(json.dumps(resp3['agent_spec'], indent=2, ensure_ascii=False))
