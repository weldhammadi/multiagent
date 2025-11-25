import json
from typing import Optional
import redis

from chat_service.domain.models import ChatSession, ChatMessage


class RedisChatMemory:
    """
    Redis-based storage for chat sessions.
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        prefix: str = "chat_session:",
    ) -> None:
        self.client = redis.Redis(host=host, port=port, db=db, decode_responses=True)
        self.prefix = prefix

    def _key(self, session_id: str) -> str:
        return f"{self.prefix}{session_id}"

    def save_session(self, session: ChatSession) -> None:
        """Save chat session to Redis"""
        self.client.set(
            self._key(session.session_id),
            session.model_dump_json()
        )

    def get_session(self, session_id: str) -> Optional[ChatSession]:
        """Retrieve chat session from Redis"""
        data = self.client.get(self._key(session_id))
        if data:
            return ChatSession.model_validate_json(data)
        return None

    def delete_session(self, session_id: str) -> None:
        """Delete chat session from Redis"""
        self.client.delete(self._key(session_id))
