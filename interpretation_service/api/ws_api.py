from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Optional

from interpretation_service.domain.models import RawInput
from interpretation_service.application.services.request_interpreter import RequestInterpreterService

from interpretation_service.infrastructure.stt.mock_stt import MockSTTProvider
from interpretation_service.infrastructure.llm.langchain_groq_llm import LangChainGroqLLMProvider
from interpretation_service.infrastructure.bus.mock_bus import MockMessageBus

router = APIRouter()

# Note: In a real app, use dependency injection
service = RequestInterpreterService(
    stt_provider=MockSTTProvider(),
    llm_provider=LangChainGroqLLMProvider(),
    bus_publisher=MockMessageBus(),
)


@router.websocket("/ws/interpret")
async def ws_interpret(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_json()

            raw = RawInput(
                user_id=data["user_id"],
                raw_text=data.get("text"),
                raw_audio_url=None,  # vocal plus tard
                conversation_id=data.get("conversation_id"),
                turn_index=data.get("turn_index"),
            )

            result = await service.process_request(raw)

            await websocket.send_json(result.model_dump())
    except WebSocketDisconnect:
        # tu peux loguer la fin de session ici
        pass
