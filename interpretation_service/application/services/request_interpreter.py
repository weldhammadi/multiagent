import logging

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
    ) -> None:
        self.stt = stt_provider
        self.llm = llm_provider
        self.bus = bus_publisher
        self.normalizer = InputNormalizer()

    async def process_request(self, raw_input: RawInput) -> AgentRequest:
        logger.info(
            "Processing request %s for user %s", raw_input.request_id, raw_input.user_id
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

        normalized_input = NormalizedInput(
            text=clean_text,
            user_context={"user_id": raw_input.user_id, **raw_input.metadata},
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

        return final_request

