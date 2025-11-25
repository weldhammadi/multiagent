import logging
import os
from groq import AsyncGroq
from interpretation_service.ports.stt_port import ISTTProvider
from interpretation_service.infrastructure.config.settings import settings

logger = logging.getLogger(__name__)

class GroqSTTProvider(ISTTProvider):
    """
    Implémentation de ISTTProvider utilisant l'API Groq (Whisper).
    """

    def __init__(self) -> None:
        self.client = AsyncGroq(api_key=settings.groq_api_key)
        self.model = settings.groq_stt_model

    async def transcribe(self, audio_url: str) -> str:
        """
        Transcrit un fichier audio via Groq.
        audio_url peut être un chemin de fichier local ou une URL (ici on gère le local).
        """
        # Pour l'instant, on suppose que audio_url est un chemin de fichier local
        if not os.path.exists(audio_url):
            logger.error(f"Audio file not found: {audio_url}")
            return ""

        try:
            with open(audio_url, "rb") as file:
                transcription = await self.client.audio.transcriptions.create(
                    file=(os.path.basename(audio_url), file.read()),
                    model=self.model,
                    response_format="text"
                )
            return str(transcription)
        except Exception as e:
            logger.error(f"Groq STT error: {e}")
            return ""
