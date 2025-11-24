from abc import ABC, abstractmethod
from typing import Dict
from interpretation_service.domain.models import AgentRequest


class IInterpreterClient(ABC):
    """
    Abstraction pour appeler ton service d'interprétation.
    V1: appel direct au RequestInterpreterService
    V2: appel HTTP à /interpret
    """

    @abstractmethod
    async def interpret_from_summary(
        self,
        user_id: str,
        summary_text: str,
        metadata: Dict,
    ) -> AgentRequest:
        ...
