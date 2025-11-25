import logging

from interpretation_service.ports.bus_port import IMessageBus
from interpretation_service.domain.models import AgentRequest

logger = logging.getLogger(__name__)


class MockMessageBus(IMessageBus):
    """
    Bus factice qui se contente de logger le message.
    Aucun envoi réel à un orchestrateur en V1.
    """

    async def publish(self, topic: str, message: AgentRequest) -> None:
        logger.info("Mock BUS publish to topic '%s'", topic)
        logger.debug(
            "Message payload: %s",
            message.model_dump_json(indent=2, ensure_ascii=False),
        )

