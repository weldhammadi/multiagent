from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from typing import Dict, Optional

from interpretation_service.application.conversation.conversation_agent_service import ConversationAgentService
from interpretation_service.infrastructure.llm.chat_langchain_groq_llm import ChatLangChainGroqLLMProvider
from interpretation_service.infrastructure.conversation_memory.in_memory_repo import InMemoryConversationMemoryRepository
from interpretation_service.infrastructure.interpreter_client.local_interpreter_client import LocalInterpreterClient
from interpretation_service.application.services.request_interpreter import RequestInterpreterService
from interpretation_service.infrastructure.stt.mock_stt import MockSTTProvider
from interpretation_service.infrastructure.llm.langchain_groq_llm import LangChainGroqLLMProvider
from interpretation_service.infrastructure.bus.mock_bus import MockMessageBus
from interpretation_service.domain.conversation_models import ChatTurnResult


router = APIRouter()


class ChatRequest(BaseModel):
    session_id: str = Field(..., description="Identifiant de session de chat.")
    user_id: str
    message: str
    metadata: Dict = {}


class ChatResponse(BaseModel):
    session_id: str
    reply: str
    done: bool
    agent_spec: Optional[dict] = None


def get_conversation_service() -> ConversationAgentService:
    """
    Wiring simple pour l'instant (sans container DI).
    """
    # On reconstruit les dépendances nécessaires :
    interpreter_service = RequestInterpreterService(
        stt_provider=MockSTTProvider(),
        llm_provider=LangChainGroqLLMProvider(),
        bus_publisher=MockMessageBus(),
    )
    interpreter_client = LocalInterpreterClient(interpreter_service)
    chat_llm = ChatLangChainGroqLLMProvider()
    memory_repo = InMemoryConversationMemoryRepository()

    return ConversationAgentService(
        chat_llm=chat_llm,
        memory_repo=memory_repo,
        interpreter_client=interpreter_client,
    )


@router.post("/chat", response_model=ChatResponse)
async def chat(
    payload: ChatRequest,
    service: ConversationAgentService = Depends(get_conversation_service),
):
    """
    Endpoint de chat utilisateur.
    """
    result: ChatTurnResult = await service.handle_user_message(
        session_id=payload.session_id,
        user_id=payload.user_id,
        message=payload.message,
        metadata=payload.metadata,
    )

    return ChatResponse(
        session_id=result.session_id,
        reply=result.reply,
        done=result.done,
        agent_spec=result.agent_spec.model_dump() if result.agent_spec else None,
    )
