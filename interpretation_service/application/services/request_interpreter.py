import logging
from typing import Optional

from interpretation_service.infrastructure.memory.redis_memory import RedisMemory

from interpretation_service.domain.models import RawInput, NormalizedInput, AgentRequest
from interpretation_service.domain.exceptions import InvalidInputError
from interpretation_service.application.normalizer import InputNormalizer
from interpretation_service.ports.stt_port import ISTTProvider
from interpretation_service.ports.llm_port import ILLMProvider
from interpretation_service.ports.bus_port import IMessageBus

logger = logging.getLogger(__name__)


class RequestInterpreterService:
    """
    Cas d’usage principal :
    - reçoit RawInput (texte + éventuel audio)
    - applique STT si besoin
    - normalise
    - appelle le LLM pour obtenir un AgentSpec
    - construit un AgentRequest
    - en V1 : publie sur un bus mock (log) et renvoie l'objet
    """

    def __init__(
        self,
        stt_provider: ISTTProvider,
        llm_provider: ILLMProvider,
        bus_publisher: IMessageBus,
        memory: Optional[RedisMemory] = None,
    ) -> None:
        self.stt = stt_provider
        self.llm = llm_provider
        self.bus = bus_publisher
        self.normalizer = InputNormalizer()
        self.memory = memory

    async def process_request(self, raw_input: RawInput) -> AgentRequest:
        logger.info(
            "Processing request %s for user %s", raw_input.request_id, raw_input.user_id
        )

        # 0. Si on a une mémoire et une conversation_id, on log le tour brut
        if self.memory and raw_input.conversation_id:
            self.memory.append_message(
                raw_input.conversation_id,
                {
                    "role": "user",
                    "text": raw_input.raw_text,
                    "audio": bool(raw_input.raw_audio_url),
                },
            )

        text_content = raw_input.raw_text

        if raw_input.raw_audio_url:
            logger.info("Audio detected, starting transcription...")
            transcription = await self.stt.transcribe(raw_input.raw_audio_url)
            logger.debug("Transcription result: %s", transcription)
            text_content = f"{text_content or ''} {transcription}".strip()

        if not text_content:
            logger.error("No input text after STT fusion.")
            raise InvalidInputError(
                "No input provided (neither text nor audio produced text)."
            )

        clean_text = self.normalizer.normalize(text_content)
        logger.debug("Normalized text: %s", clean_text)

        # 2bis. Historique de conversation (optionnel)
        history = []
        if self.memory and raw_input.conversation_id:
            history = self.memory.get_history(raw_input.conversation_id)

        normalized_input = NormalizedInput(
            text=clean_text,
            user_context={
                "user_id": raw_input.user_id,
                "conversation_id": raw_input.conversation_id,
                "turn_index": raw_input.turn_index,
                "history": history,
                **raw_input.metadata,
            },
        )

        agent_spec = await self.llm.analyze_and_structure(normalized_input)
        logger.info("AgentSpec generated for request %s", raw_input.request_id)

        final_request = AgentRequest(
            request_id=raw_input.request_id,
            user_id=raw_input.user_id,
            spec=agent_spec,
        )

        await self.bus.publish("agent_factory.requests.local", final_request)
        logger.info("Request %s processed and 'published' locally.", raw_input.request_id)

        # 4. Si mémoire, loguer la réponse aussi
        if self.memory and raw_input.conversation_id:
            self.memory.append_message(
                raw_input.conversation_id,
                {
                    "role": "system",
                    "agent_spec": final_request.spec.model_dump(),
                },
            )

        return final_request

