from interpretation_service.application.services.request_interpreter import RequestInterpreterService
from interpretation_service.infrastructure.stt.mock_stt import MockSTTProvider
from interpretation_service.infrastructure.bus.mock_bus import MockMessageBus
from interpretation_service.infrastructure.llm.langchain_groq_llm import LangChainGroqLLMProvider
from interpretation_service.domain.models import RawInput
import asyncio

async def main():
    print("Instantiating service...")
    try:
        service = RequestInterpreterService(
            stt_provider=MockSTTProvider(),
            llm_provider=LangChainGroqLLMProvider(),
            bus_publisher=MockMessageBus(),
        )
        print("Service instantiated.")
        
        raw = RawInput(user_id="test", raw_text="test", metadata={})
        print("Processing request...")
        result = await service.process_request(raw)
        print("Request processed successfully.")
        print(result)
    except Exception as e:
        print(f"Error in service: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
