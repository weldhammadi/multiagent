from abc import ABC, abstractmethod

from interpretation_service.domain.models import AgentRequest


class IMessageBus(ABC):
    """
    Interface pour un bus de messages.
    En V1 locale, l'implémentation est un simple logger.
    """

    @abstractmethod
    async def publish(self, topic: str, message: AgentRequest) -> None:
        raise NotImplementedError

