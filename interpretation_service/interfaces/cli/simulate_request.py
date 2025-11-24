import asyncio
import logging

from interpretation_service.domain.models import RawInput
from interpretation_service.application.services.request_interpreter import (
    RequestInterpreterService,
)
from interpretation_service.infrastructure.stt.mock_stt import MockSTTProvider
from interpretation_service.infrastructure.llm.mock_llm import MockLLMProvider
from interpretation_service.infrastructure.llm.langchain_groq_llm import LangChainGroqLLMProvider
from interpretation_service.infrastructure.bus.mock_bus import MockMessageBus
from interpretation_service.infrastructure.config.settings import settings

from interpretation_service.domain.exceptions import InvalidInputError
from interpretation_service.infrastructure.logging_config import configure_logging


def _select_llm_provider():
    # Avec la v2, settings valide la présence de la clé.
    # On peut donc instancier directement le provider LangChain.
    # Si on voulait garder le mock, on pourrait utiliser une variable ENV=mock
    if settings.environment == "local_mock":
        return MockLLMProvider()
    
    logging.getLogger(__name__).info("Using LangChainGroqLLMProvider.")
    return LangChainGroqLLMProvider()


async def run_simulation() -> None:
    """
    Simule une requête utilisateur en ligne de commande.
    """
    configure_logging()
    logger = logging.getLogger(__name__)

    service = RequestInterpreterService(
        stt_provider=MockSTTProvider(),
        llm_provider=_select_llm_provider(),
        bus_publisher=MockMessageBus(),
    )

    try:
        user_text = input("Tape ta demande d'agent (FR): ").strip()
    except EOFError:
        user_text = ""

    raw = RawInput(
        user_id="cli_user",
        raw_text=user_text or None,
        metadata={"source": "cli"},
    )

    try:
        result = await service.process_request(raw)
    except InvalidInputError as e:
        print(f"\n⚠️ Demande vide ou invalide : {e}")
        return

    print("\n=== Résultat AgentRequest ===")
    print(result.model_dump_json(indent=2, ensure_ascii=False))


if __name__ == "__main__":
    asyncio.run(run_simulation())

