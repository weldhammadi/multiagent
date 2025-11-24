from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any
import logging

from interpretation_service.domain.models import RawInput, AgentRequest
from interpretation_service.application.services.request_interpreter import RequestInterpreterService
from interpretation_service.infrastructure.stt.mock_stt import MockSTTProvider
from interpretation_service.infrastructure.llm.langchain_groq_llm import LangChainGroqLLMProvider
from interpretation_service.infrastructure.bus.mock_bus import MockMessageBus
from interpretation_service.infrastructure.logging_config import configure_logging

# Configuration du logging
configure_logging()
logger = logging.getLogger(__name__)

app = FastAPI(title="Interpretation Service API")

# Configuration CORS pour permettre l'accès depuis le front
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Pour le dev, on autorise tout
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import os

static_dir = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/chat-ui", response_class=HTMLResponse)
async def chat_ui():
    file_path = os.path.join(static_dir, "chat.html")
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()

from interpretation_service.interfaces.api.chat_api import router as chat_router
app.include_router(chat_router)

# Modèles Pydantic pour l'API
class InterpretRequest(BaseModel):
    user_id: str
    text: str
    metadata: Optional[Dict[str, Any]] = {}

class InterpretResponse(BaseModel):
    request_id: str
    agent_spec: Dict[str, Any]
    needs_clarification: bool
    clarification_question: Optional[str] = None

# Instanciation du service (Singleton pour l'instant)
# Dans un vrai contexte, on utiliserait l'injection de dépendances
service = RequestInterpreterService(
    stt_provider=MockSTTProvider(),
    llm_provider=LangChainGroqLLMProvider(),
    bus_publisher=MockMessageBus(),
)

@app.post("/interpret", response_model=InterpretResponse)
async def interpret(request: InterpretRequest):
    logger.info(f"Received interpretation request from user {request.user_id}")
    
    raw_input = RawInput(
        user_id=request.user_id,
        raw_text=request.text,
        metadata=request.metadata
    )
    
    try:
        result: AgentRequest = await service.process_request(raw_input)
        
        return InterpretResponse(
            request_id=result.request_id,
            agent_spec=result.spec.model_dump(),
            needs_clarification=result.spec.needs_clarification,
            clarification_question=result.spec.clarification_question
        )
    except Exception as e:
        logger.error(f"Error processing request: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health():
    return {"status": "ok"}
