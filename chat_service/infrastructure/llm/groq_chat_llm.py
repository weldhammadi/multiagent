from pathlib import Path
from typing import List
from groq import AsyncGroq

from chat_service.domain.models import ChatMessage


class GroqChatLLM:
    """
    LLM provider for chat using Groq.
    Uses a chat-optimized model for natural conversation.
    """

    def __init__(self, api_key: str, model: str = "llama-3.1-8b-instant") -> None:
        self.client = AsyncGroq(api_key=api_key)
        self.model = model
        
        # Load system prompt
        prompt_path = (
            Path(__file__)
            .parent.parent.parent
            .joinpath("prompts")
            .joinpath("chat_agent_prompt.txt")
        )
        
        with open(prompt_path, "r", encoding="utf-8") as f:
            self.system_prompt = f.read()

    async def chat(self, messages: List[ChatMessage]) -> str:
        """
        Send messages to LLM and get response.
        
        Args:
            messages: List of ChatMessage objects
            
        Returns:
            Assistant's response text
        """
        # Convert to Groq format
        groq_messages = [
            {"role": "system", "content": self.system_prompt}
        ]
        
        for msg in messages:
            groq_messages.append({
                "role": msg.role,
                "content": msg.content
            })
        
        # Call Groq API
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=groq_messages,
            temperature=0.7,  # Higher for more natural conversation
            max_tokens=1000,
        )
        
        return response.choices[0].message.content
