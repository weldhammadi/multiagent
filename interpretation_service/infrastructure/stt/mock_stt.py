from interpretation_service.ports.stt_port import ISTTProvider


class MockSTTProvider(ISTTProvider):
    """
    Implémentation mock de STT.
    Pour la V1 locale, on renvoie un texte fixe ou simple.
    """

    async def transcribe(self, audio_url: str) -> str:
        return (
            "Je voudrais un agent qui surveille mes emails et m'envoie un résumé."
        )

