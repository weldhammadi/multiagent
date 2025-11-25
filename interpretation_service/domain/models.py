from datetime import datetime
from typing import List, Optional, Literal, Dict, Any
import uuid

from pydantic import BaseModel, Field


class RawInput(BaseModel):
    """Requête brute en entrée du service (texte et/ou audio)."""

    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    raw_text: Optional[str] = None
    raw_audio_url: Optional[str] = None
    conversation_id: Optional[str] = None
    turn_index: Optional[int] = None
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class NormalizedInput(BaseModel):
    """Texte normalisé + contexte utilisateur transmis au LLM."""

    text: str
    user_context: Dict[str, Any] = Field(default_factory=dict)
    language: str = "fr"


class IOField(BaseModel):
    name: str
    type: str
    description: str


class AgentSpec(BaseModel):
    """
    Spécification d'agent à créer.
    C'est le JSON contractuel échangé avec la 'factory' d'agents.
    """

    agent_purpose: str
    high_level_goal: str
    inputs: List[IOField]
    outputs: List[IOField]
    constraints: List[str] = Field(default_factory=list)
    success_criteria: List[str] = Field(default_factory=list)
    needs_clarification: bool = False
    clarification_question: Optional[str] = None


class AgentRequest(BaseModel):
    """
    Payload complet correspondant à une demande d'agent.
    En V1 locale, c'est simplement ce que le service retourne.
    """

    request_id: str
    user_id: str
    spec: AgentSpec
    status: Literal["created", "pending", "failed"] = "created"
    created_at: datetime = Field(default_factory=datetime.now)

