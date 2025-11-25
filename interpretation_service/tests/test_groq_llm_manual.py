# interpretation_service/tests/test_groq_llm_manual.py

import asyncio
from json import dumps

from interpretation_service.domain.models import NormalizedInput
from interpretation_service.infrastructure.logging_config import configure_logging
from interpretation_service.infrastructure.llm.langchain_groq_llm import LangChainGroqLLMProvider


async def main():
    configure_logging()

    llm = LangChainGroqLLMProvider()

    ni = NormalizedInput(
        text="Crée-moi un agent qui surveille mes emails et m'envoie un résumé chaque matin.",
        user_context={"user_id": "test_user_groq_manual"},
    )

    spec = await llm.analyze_and_structure(ni)

    print("\n=== AgentSpec (Groq via LangChain) ===")
    print(spec.model_dump_json(indent=2, ensure_ascii=False))


if __name__ == "__main__":
    asyncio.run(main())
