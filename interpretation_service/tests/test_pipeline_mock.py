import asyncio

from interpretation_service.domain.models import RawInput
from interpretation_service.application.services.request_interpreter import (
    RequestInterpreterService,
)
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

    raw = RawInput(
        user_id="test_user",
        raw_text="Crée-moi un agent qui surveille mes emails et m'envoie un résumé.",
        metadata={"source": "test_pipeline_mock"},
    )

    result = await service.process_request(raw)

    print("\n=== AgentRequest (pipeline mock) ===")
    print(result.model_dump_json(indent=2, ensure_ascii=False))


if __name__ == "__main__":
    asyncio.run(main())

