import asyncio
import logging
from interpretation_service.infrastructure.llm.langchain_groq_llm import LangChainGroqLLMProvider
from interpretation_service.infrastructure.stt.mock_stt import MockSTTProvider
from interpretation_service.infrastructure.bus.mock_bus import MockMessageBus
from interpretation_service.application.services.request_interpreter import RequestInterpreterService
from interpretation_service.infrastructure.logging_config import configure_logging
from interpretation_service.domain.models import RawInput

async def main():
    configure_logging()
    
    # Setup dependencies
    stt = MockSTTProvider()
    llm = LangChainGroqLLMProvider()
    bus = MockMessageBus()
    
    service = RequestInterpreterService(
        stt_provider=stt,
        llm_provider=llm,
        bus_publisher=bus,
    )

    # Test request
    raw = RawInput(
        user_id="test_user_groq_langchain",
        raw_text="Crée-moi un agent qui surveille mes emails et envoie un résumé chaque matin.",
        metadata={"source": "cli"},
    )

    print(f"Sending request: {raw.raw_text}")
    try:
        result = await service.process_request(raw)
        print("\n--- Result ---")
        print(result.model_dump_json(indent=2))
    except Exception as e:
        print(f"\nError: {e}")

if __name__ == "__main__":
    asyncio.run(main())
