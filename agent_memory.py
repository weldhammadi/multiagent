# agents/agent_memory.py
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Dict, Any, List, Optional

app = FastAPI(title="agent_memory")

# stockage simple en mémoire
DB: List[Dict[str, Any]] = []

class MCPMessage(BaseModel):
    message_id: Optional[str]
    from_agent: Optional[str]
    to_agent: Optional[str]
    type: Optional[str]
    payload: Dict[str, Any]
    context: Optional[Dict[str, Any]] = {}

@app.post("/mcp")
def mcp_endpoint(msg: MCPMessage):
    payload = msg.payload or {}
    task = payload.get("task")

    if task == "save_interaction":
        interaction = {
            "id": len(DB) + 1,
            "user_id": payload.get("user_id"),
            "role": payload.get("role"),
            "text": payload.get("text"),
            "metadata": payload.get("metadata", {}),
        }
        DB.append(interaction)
        return {"payload": {"status": "ok", "interaction_id": interaction["id"]}}

    if task == "get_history":
        user_id = payload.get("user_id")
        limit = int(payload.get("limit", 10))
        history = [x for x in DB if x["user_id"] == user_id]
        return {"payload": {"status": "ok", "history": history[-limit:]}}

    return {"payload": {"status": "error", "message": "unknown task"}}
