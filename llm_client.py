"""
Client LLM pour Groq API.
Utilise le modèle openai/gpt-oss-120b.
"""

import os
from typing import Optional

from groq import Groq, APIError, APIConnectionError, RateLimitError


class GroqClient:
    """
    Client pour interagir avec l'API Groq.
    
    Attributes:
        model: Nom du modèle LLM à utiliser
        max_tokens: Nombre maximum de tokens en sortie
        temperature: Température de génération (0.0-2.0)
    """
    
    def __init__(
        self,
        model: str = "openai/gpt-oss-120b",
        max_tokens: int = 8000,
        temperature: float = 0.1
    ) -> None:
        """
        Initialise le client Groq.
        
        Args:
            model: Modèle LLM à utiliser (défaut: openai/gpt-oss-120b)
            max_tokens: Limite de tokens en sortie
            temperature: Température de génération (plus bas = plus déterministe)
            
        Raises:
            RuntimeError: Si GROQ_API_KEY n'est pas définie
        """
        api_key = os.getenv("GROQ_API_KEY")
        
        if not api_key:
            raise RuntimeError(
                "Variable d'environnement GROQ_API_KEY manquante. "
                "Configurez votre clé API dans .env"
            )
        
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        
        try:
            self.client = Groq(api_key=api_key)
        except Exception as exc:
            raise RuntimeError(
                f"Impossible d'initialiser le client Groq: {exc}"
            ) from exc
    
    def generate_tool(
        self,
        context: str,
        user_request: str,
        timeout: int = 60
    ) -> str:
        """
        Génère un outil Python via le LLM.
        
        Args:
            context: Contexte permanent avec règles strictes
            user_request: Demande spécifique de l'utilisateur
            timeout: Timeout en secondes pour la requête
            
        Returns:
            Réponse JSON brute du LLM
            
        Raises:
            RuntimeError: Si erreur API, timeout ou rate limit
        """
        messages = [
            {
                "role": "system",
                "content": context
            },
            {
                "role": "user",
                "content": user_request
            }
        ]
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                timeout=timeout
            )
            
            if not response.choices:
                raise RuntimeError("Réponse LLM vide - aucun choix retourné")
            
            content = response.choices[0].message.content
            
            if not content:
                raise RuntimeError("Contenu de réponse LLM vide")
            
            return content
            
        except RateLimitError as exc:
            raise RuntimeError(
                f"Limite de débit Groq atteinte. Réessayez dans quelques secondes. "
                f"Détails: {exc}"
            ) from exc
        
        except APIConnectionError as exc:
            raise RuntimeError(
                f"Erreur de connexion à l'API Groq. Vérifiez votre réseau. "
                f"Détails: {exc}"
            ) from exc
        
        except APIError as exc:
            raise RuntimeError(
                f"Erreur API Groq: {exc}"
            ) from exc
        
        except Exception as exc:
            raise RuntimeError(
                f"Erreur inattendue lors de l'appel Groq: {type(exc).__name__}: {exc}"
            ) from exc