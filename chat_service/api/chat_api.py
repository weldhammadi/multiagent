from fastapi import APIRouter, HTTPException
import logging

from chat_service.domain.models import ChatRequest, ChatResponse
from chat_service.application.chat_agent_service import ChatAgentService
from chat_service.infrastructure.llm.groq_chat_llm import GroqChatLLM
from chat_service.infrastructure.memory.in_memory_chat_memory import InMemoryChatMemory
from interpretation_service.infrastructure.config.settings import settings

logger = logging.getLogger(__name__)

# >>> IL MANQUAIT ÇA (selon l'utilisateur, même si c'était là, on le remet proprement) <<<
router = APIRouter(tags=["Agent 1 - Chat"])

# Initialize service
# Note: In production, use dependency injection
try:
    llm = GroqChatLLM(api_key=settings.groq_api_key)
    memory = InMemoryChatMemory()
    chat_service = ChatAgentService(llm=llm, memory=memory)
except Exception as e:
    logger.exception("Failed to initialize ChatService")
    raise

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(req: ChatRequest) -> ChatResponse:
    """Chat endpoint for Agent 1"""
    try:
        return await chat_service.process_message(req)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Erreur dans /api/chat")
        raise HTTPException(status_code=500, detail=str(e))
