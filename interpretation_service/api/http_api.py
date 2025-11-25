from fastapi import APIRouter, UploadFile, File, Form
from typing import Optional
import uuid
import aiofiles

from interpretation_service.domain.models import RawInput
from interpretation_service.application.services.request_interpreter import RequestInterpreterService

# Adapters (à ajuster selon ce que tu utilises)
from interpretation_service.infrastructure.stt.mock_stt import MockSTTProvider
from interpretation_service.infrastructure.llm.langchain_groq_llm import LangChainGroqLLMProvider
from interpretation_service.infrastructure.bus.mock_bus import MockMessageBus

router = APIRouter()

# Service global (tu peux gérer l’injection plus proprement plus tard)
service = RequestInterpreterService(
    stt_provider=MockSTTProvider(),
    llm_provider=LangChainGroqLLMProvider(),
    bus_publisher=MockMessageBus(),
)


@router.post("/interpret")
async def interpret(
    user_id: str = Form(...),
    text: Optional[str] = Form(None),
    conversation_id: Optional[str] = Form(None),
    turn_index: Optional[int] = Form(None),
    audio_file: Optional[UploadFile] = File(None),
):
    audio_url: Optional[str] = None

    # Si un fichier audio est envoyé, on le sauvegarde temporairement
    if audio_file is not None:
        temp_name = f"/tmp/{uuid.uuid4()}_{audio_file.filename}"
        async with aiofiles.open(temp_name, "wb") as f:
            content = await audio_file.read()
            await f.write(content)
        audio_url = temp_name

    raw = RawInput(
        user_id=user_id,
        raw_text=text,
        raw_audio_url=audio_url,
        conversation_id=conversation_id,
        turn_index=turn_index,
    )

    result = await service.process_request(raw)
    return result
