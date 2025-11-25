from abc import ABC, abstractmethod

from interpretation_service.domain.models import NormalizedInput, AgentSpec


class ILLMProvider(ABC):
    """Interface pour le LLM 'cerveau'."""

    @abstractmethod
    async def analyze_and_structure(self, input_data: NormalizedInput) -> AgentSpec:
        """
        Transforme un NormalizedInput en AgentSpec structuré.
        """
        raise NotImplementedError

