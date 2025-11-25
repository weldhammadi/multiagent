from datetime import datetime
from typing import List, Optional, Literal
from enum import Enum

from pydantic import BaseModel, Field


class NeedStatus(str, Enum):
    """Status of need clarification"""
    UNCLEAR = "unclear"          # Need more information
    CLARIFYING = "clarifying"    # In process of clarification
    READY = "ready"              # Ready to generate AgentSpec


class ChatMessage(BaseModel):
    """Single message in a chat conversation"""
    role: Literal["user", "assistant", "system"]
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)


class ChatSession(BaseModel):
    """Chat session with conversation history"""
    session_id: str
    user_id: str
    messages: List[ChatMessage] = Field(default_factory=list)
    need_status: NeedStatus = NeedStatus.UNCLEAR
    structured_need: Optional[str] = None  # Structured description when ready
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class ChatRequest(BaseModel):
    """Request to chat endpoint"""
    session_id: Optional[str] = None
    user_id: str
    message: str


class ChatResponse(BaseModel):
    """Response from chat endpoint"""
    session_id: str
    message: str
    need_status: NeedStatus
    agent_spec: Optional[dict] = None  # Populated when need_status == READY
