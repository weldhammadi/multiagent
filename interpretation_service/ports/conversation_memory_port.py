from abc import ABC, abstractmethod
from typing import Optional
from interpretation_service.domain.conversation_models import ConversationState


class IConversationMemoryRepository(ABC):
    """
    Abstraction pour stocker/charger l'état d'une conversation.
    V1: in-memory ; V2: Redis, DB, etc.
    """

    @abstractmethod
    async def load(self, session_id: str) -> Optional[ConversationState]:
        ...

    @abstractmethod
    async def save(self, state: ConversationState) -> None:
        ...
