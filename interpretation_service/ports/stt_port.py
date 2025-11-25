from abc import ABC, abstractmethod


class ISTTProvider(ABC):
    """Interface pour un provider Speech-to-Text."""

    @abstractmethod
    async def transcribe(self, audio_url: str) -> str:
        """Transcrit un fichier audio identifié par son URL en texte brut."""
        raise NotImplementedError

