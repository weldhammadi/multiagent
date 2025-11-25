import asyncio

from interpretation_service.domain.models import RawInput
from interpretation_service.application.services.request_interpreter import RequestInterpreterService
from interpretation_service.infrastructure.stt.mock_stt import MockSTTProvider
from interpretation_service.infrastructure.llm.mock_llm import MockLLMProvider
from interpretation_service.infrastructure.bus.mock_bus import MockMessageBus
from interpretation_service.infrastructure.logging_config import configure_logging


async def main():
    configure_logging()

    service = RequestInterpreterService(
        stt_provider=MockSTTProvider(),
        llm_provider=MockLLMProvider(),
        bus_publisher=MockMessageBus(),
    )

    # Ici on ne met PAS de texte, uniquement de l'audio
    raw = RawInput(
        user_id="voice_user_1",
        raw_text=None,
        raw_audio_url="mock://audio/commande1",  # juste un identifiant fictif
        conversation_id="conv_123",
        turn_index=1,
        metadata={"source": "voice_test"},
    )

    result = await service.process_request(raw)

    print("\n=== AgentRequest (pipeline VOIX mock) ===")
    print(result.model_dump_json(indent=2))


if __name__ == "__main__":
    asyncio.run(main())
