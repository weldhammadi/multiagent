import logging
import uuid
import httpx
from datetime import datetime
from typing import Optional

from chat_service.domain.models import (
    ChatSession,
    ChatMessage,
    NeedStatus,
    ChatRequest,
    ChatResponse,
)
from chat_service.infrastructure.llm.groq_chat_llm import GroqChatLLM
# from chat_service.infrastructure.memory.redis_chat_memory import RedisChatMemory
from typing import Any

logger = logging.getLogger(__name__)


class ChatAgentService:
    """
    Main service for Agent 1 (Chat UX).
    Handles conversation, need clarification, and calls Agent 2 when ready.
    """

    def __init__(
        self,
        llm: GroqChatLLM,
        memory: Any, # RedisChatMemory or InMemoryChatMemory
        interpreter_api_url: str = "http://localhost:8000/api/interpret",
    ) -> None:
        self.llm = llm
        self.memory = memory
        self.interpreter_api_url = interpreter_api_url

    async def process_message(self, request: ChatRequest) -> ChatResponse:
        """
        Process a user message and return assistant response.
        
        Args:
            request: ChatRequest with user message
            
        Returns:
            ChatResponse with assistant message and status
        """
        # Get or create session
        if request.session_id:
            session = self.memory.get_session(request.session_id)
            if not session:
                logger.warning(f"Session {request.session_id} not found, creating new one")
                session = self._create_session(request.user_id, request.session_id)
        else:
            session = self._create_session(request.user_id)

        # Add user message to session
        user_message = ChatMessage(role="user", content=request.message)
        session.messages.append(user_message)
        session.updated_at = datetime.now()

        # Get LLM response
        assistant_content = await self.llm.chat(session.messages)
        
        # Add assistant message to session
        assistant_message = ChatMessage(role="assistant", content=assistant_content)
        session.messages.append(assistant_message)

        # Check if need is ready
        agent_spec = None
        if "NEED_READY:" in assistant_content:
            logger.info(f"Need is ready for session {session.session_id}")
            session.need_status = NeedStatus.READY
            
            # Extract structured need description
            need_description = assistant_content.split("NEED_READY:")[1].strip()
            session.structured_need = need_description
            
            # Call Agent 2 (Interpretation Service)
            try:
                agent_spec = await self._call_interpreter(
                    user_id=session.user_id,
                    text=need_description,
                    conversation_id=session.session_id,
                )
                logger.info(f"AgentSpec generated for session {session.session_id}")
            except Exception as e:
                logger.error(f"Failed to call interpreter: {e}")
        elif session.need_status == NeedStatus.UNCLEAR:
            session.need_status = NeedStatus.CLARIFYING

        # Save session
        self.memory.save_session(session)

        return ChatResponse(
            session_id=session.session_id,
            message=assistant_content,
            need_status=session.need_status,
            agent_spec=agent_spec,
        )

    def _create_session(self, user_id: str, session_id: Optional[str] = None) -> ChatSession:
        """Create a new chat session"""
        if not session_id:
            session_id = str(uuid.uuid4())
        
        session = ChatSession(
            session_id=session_id,
            user_id=user_id,
        )
        self.memory.save_session(session)
        return session

    async def _call_interpreter(
        self,
        user_id: str,
        text: str,
        conversation_id: str,
    ) -> dict:
        """
        Call Agent 2 (Interpretation Service) to generate AgentSpec.
        
        Args:
            user_id: User ID
            text: Structured need description
            conversation_id: Conversation ID
            
        Returns:
            AgentRequest dict from Agent 2
        """
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                self.interpreter_api_url,
                data={
                    "user_id": user_id,
                    "text": text,
                    "conversation_id": conversation_id,
                    "turn_index": 1,
                }
            )
            response.raise_for_status()
            return response.json()
