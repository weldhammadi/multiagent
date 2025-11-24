from abc import ABC, abstractmethod
from typing import List
from interpretation_service.domain.conversation_models import ChatMessage


class IChatLLMProvider(ABC):
    """
    LLM orienté conversation (différent de ton ILLMProvider pour AgentSpec).
    """

    @abstractmethod
    async def generate_reply(
        self,
        messages: List[ChatMessage],
    ) -> str:
        """
        Prend l'historique des messages et renvoie la prochaine réponse de l'assistant.
        """
        raise NotImplementedError
