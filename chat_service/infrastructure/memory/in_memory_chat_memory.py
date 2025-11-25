from typing import Dict, Optional
from chat_service.domain.models import ChatSession

class InMemoryChatMemory:
    """
    In-memory storage for chat sessions.
    Replaces RedisChatMemory for local development without Redis.
    """

    def __init__(self):
        self.storage: Dict[str, ChatSession] = {}

    def save_session(self, session: ChatSession) -> None:
        """Save chat session to memory"""
        self.storage[session.session_id] = session

    def get_session(self, session_id: str) -> Optional[ChatSession]:
        """Retrieve chat session from memory"""
        return self.storage.get(session_id)

    def delete_session(self, session_id: str) -> None:
        """Delete chat session from memory"""
        if session_id in self.storage:
            del self.storage[session_id]
