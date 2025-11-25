from typing import Optional, Dict
from interpretation_service.domain.conversation_models import ConversationState
from interpretation_service.ports.conversation_memory_port import IConversationMemoryRepository


class InMemoryConversationMemoryRepository(IConversationMemoryRepository):
    """
    Simple dict en mémoire pour commencer.
    À remplacer plus tard par Redis/DB sans toucher au core.
    """

    def __init__(self) -> None:
        self._store: Dict[str, ConversationState] = {}

    async def load(self, session_id: str) -> Optional[ConversationState]:
        return self._store.get(session_id)

    async def save(self, state: ConversationState) -> None:
        self._store[state.session_id] = state
