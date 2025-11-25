from fastapi import FastAPI

from interpretation_service.api.http_api import router as interpret_http_router
from interpretation_service.api.ws_api import router as interpret_ws_router
from chat_service.api.chat_api import router as chat_router
from interpretation_service.infrastructure.logging_config import configure_logging


def create_app() -> FastAPI:
    configure_logging()
    app = FastAPI(title="Multi-Agent Service", version="0.1.0")

    # Agent 2 (Interpretation Service)
    app.include_router(interpret_http_router, prefix="/api", tags=["Agent 2 - Interpretation"])
    app.include_router(interpret_ws_router, prefix="/api", tags=["Agent 2 - Interpretation"])
    
    # Agent 1 (Chat Service)
    app.include_router(chat_router, prefix="/api", tags=["Agent 1 - Chat"])

    return app


app = create_app()
