from typing import Dict, Optional
from interpretation_service.domain.conversation_models import ConversationState, ChatTurnResult, ChatMessage
from interpretation_service.ports.chat_llm_port import IChatLLMProvider
from interpretation_service.ports.conversation_memory_port import IConversationMemoryRepository
from interpretation_service.ports.interpreter_client_port import IInterpreterClient


class ConversationAgentService:
    """
    Gère la discussion multi-tours avec l'utilisateur pour affiner le besoin.
    Quand le besoin est prêt, appelle l'interpréteur pour produire un AgentSpec.
    """

    def __init__(
        self,
        chat_llm: IChatLLMProvider,
        memory_repo: IConversationMemoryRepository,
        interpreter_client: IInterpreterClient,
    ) -> None:
        self._chat_llm = chat_llm
        self._memory_repo = memory_repo
        self._interpreter_client = interpreter_client

    async def handle_user_message(
        self,
        session_id: str,
        user_id: str,
        message: str,
        metadata: Dict,
    ) -> ChatTurnResult:
        """
        Méthode principale appelée par l'API /chat.
        1. Charge l'état de conversation.
        2. Ajoute le message utilisateur.
        3. Demande une réponse au LLM de chat.
        4. Décide si on est prêt pour l'interprétation.
        5. Si oui, appelle l'interpréteur et retourne l'AgentSpec.
        """
        # 1. Charge ou crée l'état
        state = await self._load_or_create_state(session_id, user_id)
        
        # 2. Ajoute le message utilisateur
        await self._append_user_message(state, message)
        
        # 3. Génère la réponse de l'assistant
        reply_text = await self._generate_reply(state)
        
        # 4. Vérifie si prêt
        is_ready = self._is_ready_for_interpretation(state, reply_text)
        
        # Nettoyer le tag [READY] de la réponse visible
        clean_reply = reply_text.replace("[READY]", "").strip()
        
        # Ajouter la réponse de l'assistant à l'historique
        await self._append_assistant_message(state, clean_reply)
        
        result = ChatTurnResult(
            session_id=session_id,
            reply=clean_reply,
            done=False
        )

        if is_ready:
            # 5. Si prêt, appeler l'interpréteur
            state.status = "ready_for_interpretation"
            await self._memory_repo.save(state) # Sauvegarder l'état avant l'appel
            
            agent_request = await self._call_interpreter(state, metadata)
            
            state.status = "completed"
            state.agent_request_id = agent_request.request_id
            
            result.done = True
            result.agent_spec = agent_request.spec

        # Sauvegarder l'état final
        await self._memory_repo.save(state)
        
        return result

    async def _load_or_create_state(
        self,
        session_id: str,
        user_id: str,
    ) -> ConversationState:
        """
        Charge l'état existant ou en crée un nouveau.
        """
        state = await self._memory_repo.load(session_id)
        if not state:
            state = ConversationState(session_id=session_id, user_id=user_id)
        return state

    async def _append_user_message(
        self,
        state: ConversationState,
        content: str,
    ) -> None:
        """
        Ajoute un ChatMessage(role='user') à l'état.
        """
        state.messages.append(ChatMessage(role="user", content=content))

    async def _append_assistant_message(
        self,
        state: ConversationState,
        content: str,
    ) -> None:
        """
        Ajoute un ChatMessage(role='assistant') à l'état.
        """
        state.messages.append(ChatMessage(role="assistant", content=content))

    async def _generate_reply(
        self,
        state: ConversationState,
    ) -> str:
        """
        Appelle le LLM de chat avec l'historique de messages
        pour obtenir la prochaine réponse.
        """
        return await self._chat_llm.generate_reply(state.messages)

    def _is_ready_for_interpretation(
        self,
        state: ConversationState,
        reply_text: str
    ) -> bool:
        """
        Logique métier : décider si on a assez d'info pour appeler l'interpréteur.
        V1 simple : on se base sur un flag dans metadata ou une commande de l'utilisateur.
        Ici on utilise le tag [READY] généré par le LLM.
        """
        return "[READY]" in reply_text

    def _build_summary_text(
        self,
        state: ConversationState,
    ) -> str:
        """
        Construit un résumé du besoin à partir de l'historique.
        C'est ce texte qui sera envoyé à l'interpréteur.
        """
        full_text = "Voici une conversation entre un utilisateur et un assistant pour définir un agent IA.\n\n"
        for msg in state.messages:
            role = "Utilisateur" if msg.role == "user" else "Assistant"
            full_text += f"{role}: {msg.content}\n"
        
        full_text += "\n\nExtrais la spécification de l'agent demandé par l'utilisateur."
        return full_text

    async def _call_interpreter(
        self,
        state: ConversationState,
        metadata: Dict,
    ):
        """
        Appelle l'interpréteur via IInterpreterClient et met à jour le state.
        """
        summary_text = self._build_summary_text(state)
        return await self._interpreter_client.interpret_from_summary(
            user_id=state.user_id,
            summary_text=summary_text,
            metadata=metadata
        )
