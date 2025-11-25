from __future__ import annotations
from typing import Literal, List, Optional, TYPE_CHECKING
from datetime import datetime
from pydantic import BaseModel, Field
import uuid

if TYPE_CHECKING:
    from interpretation_service.domain.models import AgentSpec

class ChatMessage(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    role: Literal["user", "assistant"]
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ConversationState(BaseModel):
    session_id: str
    user_id: str
    messages: List[ChatMessage] = []
    status: Literal["in_progress", "ready_for_interpretation", "completed"] = "in_progress"
    # Optionnel : lien vers un AgentRequest déjà créé
    agent_request_id: Optional[str] = None


class ChatTurnResult(BaseModel):
    session_id: str
    reply: str                      # Ce que l'assistant répond à l'utilisateur
    done: bool                      # True si on a fini la phase de clarification
    agent_spec: Optional[AgentSpec] = None  # rempli seulement si done=True

# Avoid circular imports at runtime if needed, but here we use TYPE_CHECKING
# The user's snippet had:
# from domain.models import AgentSpec  # type: ignore
# ChatTurnResult.model_rebuild()
# We'll do it properly with imports:
from interpretation_service.domain.models import AgentSpec
ChatTurnResult.model_rebuild()
