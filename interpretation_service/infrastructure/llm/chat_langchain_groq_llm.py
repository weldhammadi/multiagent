from typing import List
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from interpretation_service.ports.chat_llm_port import IChatLLMProvider
from interpretation_service.domain.conversation_models import ChatMessage
from interpretation_service.infrastructure.config.settings import settings


class ChatLangChainGroqLLMProvider(IChatLLMProvider):
    def __init__(self) -> None:
        self._llm = ChatGroq(
            model=settings.groq_model,   # ou un modèle différent pour le chat
            temperature=0.2,
            api_key=settings.groq_api_key,
        )
        # Prompt système pour le mode "assistant de discussion"
        self._prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    (
                        "Tu es un assistant qui aide l'utilisateur à préciser le besoin "
                        "pour créer un agent logiciel. Tu poses des questions de clarification "
                        "courtes, tu reformules, puis tu t'arrêtes quand le besoin est clair."
                        "Si tu penses avoir assez d'informations, termine ta réponse par le tag [READY]."
                    ),
                ),
                # Le reste (historique) sera injecté dynamiquement
            ]
        )

    async def generate_reply(self, messages: List[ChatMessage]) -> str:
        """
        Implémentation : mapper ChatMessage -> format LangChain,
        appeler self._llm, renvoyer le contenu texte.
        """
        # 1. Convertir les messages
        lc_messages = []
        
        # Ajouter le system prompt manuellement ou via invoke
        # Ici on va construire la liste complète pour l'envoyer au LLM
        # Note: ChatPromptTemplate est utile si on veut templater, mais ici on a déjà la liste
        # On va utiliser le system message défini dans _prompt manuellement pour simplifier
        
        # Récupérer le contenu du system prompt
        system_content = self._prompt.messages[0].prompt.template
        lc_messages.append(SystemMessage(content=system_content))
        
        for msg in messages:
            if msg.role == "user":
                lc_messages.append(HumanMessage(content=msg.content))
            elif msg.role == "assistant":
                lc_messages.append(AIMessage(content=msg.content))
        
        # 2. Appeler le LLM
        response = await self._llm.ainvoke(lc_messages)
        
        return response.content
