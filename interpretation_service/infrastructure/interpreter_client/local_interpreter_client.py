from typing import Dict
from interpretation_service.domain.models import RawInput, AgentRequest
from interpretation_service.application.services.request_interpreter import RequestInterpreterService
from interpretation_service.ports.interpreter_client_port import IInterpreterClient


class LocalInterpreterClient(IInterpreterClient):
    """
    Version locale : au lieu d'appeler /interpret en HTTP,
    on appelle directement RequestInterpreterService.
    """

    def __init__(self, interpreter_service: RequestInterpreterService) -> None:
        self._service = interpreter_service

    async def interpret_from_summary(
        self,
        user_id: str,
        summary_text: str,
        metadata: Dict,
    ) -> AgentRequest:
        raw = RawInput(
            user_id=user_id,
            raw_text=summary_text,
            metadata=metadata,
        )
        return await self._service.process_request(raw)
