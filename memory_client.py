# agents/memory_client.py
import os
import uuid
from typing import Any, Dict, List, Optional
import requests

DEFAULT_URL = os.getenv("AGENT_MEMORY_URL", "http://127.0.0.1:8003")

class MemoryClient:
    def __init__(self, base_url: Optional[str] = None):
        self.base_url = base_url or DEFAULT_URL

    def _post_mcp(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        message = {
            "message_id": str(uuid.uuid4()),
            "from_agent": "orchestrator",
            "to_agent": "agent_memory",
            "type": "request",
            "payload": payload,
            "context": {},
        }
        url = f"{self.base_url}/mcp"
        resp = requests.post(url, json=message, timeout=5)
        resp.raise_for_status()
        return resp.json()

    def save_interaction(self, user_id: str, role: str, text: str, metadata: Optional[Dict[str, Any]] = None) -> Optional[int]:
        payload = {
            "task": "save_interaction",
            "user_id": user_id,
            "role": role,
            "text": text,
            "metadata": metadata or {},
        }
        data = self._post_mcp(payload)
        return data.get("payload", {}).get("interaction_id")

    def get_history(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        payload = {"task": "get_history", "user_id": user_id, "limit": limit}
        data = self._post_mcp(payload)
        return data.get("payload", {}).get("history", [])
