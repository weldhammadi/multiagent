import json
from typing import List, Dict, Any

import redis


class RedisMemory:
    """
    Mémoire conversationnelle simple basée sur Redis.
    Stocke les tours sous forme de liste JSON par conversation_id.
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        prefix: str = "conv:",
    ) -> None:
        self.client = redis.Redis(host=host, port=port, db=db, decode_responses=True)
        self.prefix = prefix

    def _key(self, conversation_id: str) -> str:
        return f"{self.prefix}{conversation_id}"

    def append_message(self, conversation_id: str, message: Dict[str, Any]) -> None:
        self.client.rpush(self._key(conversation_id), json.dumps(message))

    def get_history(self, conversation_id: str) -> List[Dict[str, Any]]:
        raw_items = self.client.lrange(self._key(conversation_id), 0, -1)
        return [json.loads(item) for item in raw_items]

    def clear(self, conversation_id: str) -> None:
        self.client.delete(self._key(conversation_id))
