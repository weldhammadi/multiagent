from pathlib import Path
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
import json

from interpretation_service.ports.llm_port import ILLMProvider
from interpretation_service.domain.models import NormalizedInput, AgentSpec
from interpretation_service.infrastructure.config.settings import settings


class LangChainGroqLLMProvider(ILLMProvider):
    """
    Implémentation de ILLMProvider basée sur LangChain + Groq.
    Utilise PydanticOutputParser pour une compatibilité maximale.
    Charge le prompt depuis un fichier externe.
    """

    def __init__(self) -> None:
        # Load prompt file
        prompt_path = (
            Path(__file__)
            .parent
            .joinpath("prompts")
            .joinpath("agent_interpreter_prompt.txt")
        )

        with open(prompt_path, "r", encoding="utf-8") as f:
            self.system_prompt = f.read()

        self._llm = ChatGroq(
            model=settings.groq_model,
            temperature=0.1, # Temperature basse pour plus de déterminisme
            api_key=settings.groq_api_key,
        )

        self._parser = PydanticOutputParser(pydantic_object=AgentSpec)

        self._prompt = ChatPromptTemplate.from_messages(
            [
                ("system", self.system_prompt),
                (
                    "user",
                    (
                        "Texte utilisateur:\n{user_text}\n\n"
                        "Contexte utilisateur:\n{user_context_json}"
                    ),
                ),
            ]
        )

    async def analyze_and_structure(self, input_data: NormalizedInput) -> AgentSpec:
        chain = self._prompt | self._llm | self._parser

        result: AgentSpec = await chain.ainvoke(
            {
                "user_text": input_data.text,
                "user_context_json": json.dumps(input_data.user_context, ensure_ascii=False, indent=2),
                "format_instructions": self._parser.get_format_instructions(),
            }
        )

        return result
