import os
import json
import re
from typing import Optional, Dict, Any, Literal
from pathlib import Path
from groq import Groq


class AgentModeles:
    """
    Agent spécialisé dans la génération automatique de fonctions Python
    basées sur des modèles IA via l'API Groq.
    
    Supporte plusieurs types de modèles:
    - LLM (text generation)
    - Speech-to-Text (transcription)
    - Text-to-Speech (synthesis)
    - Text-to-Video (generation)
    - Image generation
    """
    
    # Configuration des modèles par type
    MODEL_CONFIG = {
        "llm": {
            "model": "openai/gpt-oss-120b",
            "description": "Large Language Model pour génération de texte"
        },
        "speech_to_text": {
            "model": "whisper-large-v3",
            "description": "Modèle de transcription audio vers texte"
        },
        "text_to_speech": {
            "model": "playai-tts",
            "description": "Modèle de synthèse vocale texte vers audio"
        },
        "text_to_video": {
            "model": "stable-video-diffusion",
            "description": "Modèle de génération de vidéo depuis texte"
        },
        "image_generation": {
            "model": "dall-e-3",
            "description": "Modèle de génération d'images depuis texte"
        }
    }
    
    PROMPTS_DIR = "prompts"
    
    def __init__(self):
        """
        Initialise l'agent avec le client Groq.
        Récupère la clé API depuis les variables d'environnement.
        """
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError(
                "GROQ_API_KEY non trouvée. "
                "Veuillez définir la variable d'environnement GROQ_API_KEY."
            )
        self.client = Groq(api_key=api_key)
        self._ensure_prompts_dir()
    
    def _ensure_prompts_dir(self) -> None:
        """Crée le répertoire des prompts s'il n'existe pas."""
        Path(self.PROMPTS_DIR).mkdir(exist_ok=True)
    
    def _load_prompt_template(self, filename: str) -> str:
        """
        Charge un template de prompt depuis un fichier txt.
        
        Args:
            filename: Nom du fichier dans le répertoire prompts/
        
        Returns:
            Contenu du fichier
        """
        script_dir = Path(__file__).parent
        prompts_path = script_dir / self.PROMPTS_DIR
        filepath = prompts_path / filename
        
        try:
            return filepath.read_text(encoding='utf-8')
        except FileNotFoundError:
            raise FileNotFoundError(
                f"Fichier prompt non trouvé: {filepath}"
            )
    
    def generate_model_function(
        self,
        description: str,
        inputs: Dict[str, str],
        outputs: Dict[str, str],
        model_type: Literal["llm", "speech_to_text", "text_to_speech", 
                           "text_to_video", "image_generation"] = "llm",
        constraints: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 2048
    ) -> Dict[str, Any]:
        """
        Génère une fonction Python IA basée sur une description.
        
        Args:
            description: Description textuelle de la fonction à générer
            inputs: Dictionnaire {nom_param: type_param}
            outputs: Dictionnaire {nom_return: type_return}
            model_type: Type de modèle à utiliser
            constraints: Contraintes additionnelles (optionnel)
            temperature: Température pour la génération (0.0-1.0)
            max_tokens: Nombre maximum de tokens à générer
        
        Returns:
            Dict structuré contenant le code généré et métadonnées détaillées
        """
        # Validation du type de modèle
        if model_type not in self.MODEL_CONFIG:
            raise ValueError(
                f"Type de modèle invalide: {model_type}. "
                f"Types disponibles: {list(self.MODEL_CONFIG.keys())}"
            )
        
        # Récupération de la configuration du modèle
        model_info = self.MODEL_CONFIG[model_type]
        
        # Construction du prompt
        prompt = self.build_prompt(
            description=description,
            inputs=inputs,
            outputs=outputs,
            model_type=model_type,
            model_name=model_info["model"],
            constraints=constraints
        )
        
        # Appel au LLM
        llm_output = self.call_llm(
            prompt=prompt,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        # Parsing de la sortie
        parsed = self.parse_llm_output(llm_output)
        
        # Construction du contexte professionnel détaillé
        context = self._build_detailed_context(
            description=description,
            inputs=inputs,
            outputs=outputs,
            model_type=model_type,
            model_info=model_info,
            constraints=constraints,
            parsed=parsed
        )
        
        return {
            "source_code": parsed["code"],
            "context": context,
            "prompt": prompt,
            "metadata": {
                "fonction": {
                    "nom": parsed["function_name"],
                    "input": inputs,
                    "output": outputs,
                    "descriptif": description
                },
                "modele": {
                    "type": model_type,
                    "nom": model_info["model"],
                    "description": model_info["description"]
                },
                "generation": {
                    "temperature": temperature,
                    "max_tokens": max_tokens
                }
            }
        }
    
    def _build_detailed_context(
        self,
        description: str,
        inputs: Dict[str, str],
        outputs: Dict[str, str],
        model_type: str,
        model_info: Dict[str, str],
        constraints: Optional[str],
        parsed: Dict[str, Any]
    ) -> str:
        """
        Construit un contexte détaillé et professionnel pour la fonction générée.
        
        Args:
            description: Description de la fonction
            inputs: Paramètres d'entrée
            outputs: Paramètres de sortie
            model_type: Type de modèle utilisé
            model_info: Informations sur le modèle
            constraints: Contraintes appliquées
            parsed: Résultat du parsing
        
        Returns:
            Contexte formaté en markdown professionnel
        """
        context_parts = [
            "# Fonction Générée par AgentModeles",
            "",
            "## 📋 Informations Générales",
            "",
            f"**Nom de la fonction:** `{parsed['function_name']}`",
            f"**Description:** {description}",
            f"**Type de modèle:** {model_type}",
            f"**Modèle IA utilisé:** {model_info['model']}",
            f"**Description du modèle:** {model_info['description']}",
            "",
            "## 📥 Paramètres d'Entrée",
            ""
        ]
        
        for param_name, param_type in inputs.items():
            context_parts.append(f"- **{param_name}** (`{param_type}`)")
        
        context_parts.extend([
            "",
            "## 📤 Paramètres de Sortie",
            ""
        ])
        
        for output_name, output_type in outputs.items():
            context_parts.append(f"- **{output_name}** (`{output_type}`)")
        
        if constraints:
            context_parts.extend([
                "",
                "## ⚠️ Contraintes Appliquées",
                "",
                constraints
            ])
        
        context_parts.extend([
            "",
            "## 🔧 Détails Techniques",
            "",
            "### Configuration API",
            "- **Provider:** Groq API",
            "- **Authentification:** Variable d'environnement `GROQ_API_KEY`",
            f"- **Endpoint du modèle:** `{model_info['model']}`",
            "",
            "### Spécificités du Type de Modèle",
            ""
        ])
        
        # Ajout de détails spécifiques selon le type de modèle
        if model_type == "speech_to_text":
            context_parts.extend([
                "- **Type:** Transcription audio vers texte",
                "- **Formats supportés:** MP3, WAV, M4A, FLAC",
                "- **Langues:** Multi-langues avec détection automatique",
                "- **Qualité:** Haute précision avec timestamps disponibles"
            ])
        elif model_type == "text_to_speech":
            context_parts.extend([
                "- **Type:** Synthèse vocale",
                "- **Format de sortie:** Audio encodé (MP3/WAV)",
                "- **Voix:** Configurable selon disponibilité",
                "- **Qualité:** Haute fidélité naturelle"
            ])
        elif model_type == "text_to_video":
            context_parts.extend([
                "- **Type:** Génération vidéo depuis description",
                "- **Format de sortie:** Vidéo MP4",
                "- **Résolution:** Configurable",
                "- **Durée:** Variable selon configuration"
            ])
        elif model_type == "image_generation":
            context_parts.extend([
                "- **Type:** Génération d'images depuis texte",
                "- **Format de sortie:** PNG/JPEG",
                "- **Résolution:** Haute qualité configurable",
                "- **Style:** Personnalisable via prompt"
            ])
        else:  # llm
            context_parts.extend([
                "- **Type:** Large Language Model",
                "- **Capacités:** Génération de texte, analyse, raisonnement",
                "- **Contexte:** Jusqu'à 8K tokens",
                "- **Temperature:** Ajustable pour contrôler la créativité"
            ])
        
        context_parts.extend([
            "",
            "## 📝 Utilisation",
            "",
            "```python",
            f"# Exemple d'utilisation de {parsed['function_name']}",
            "from groq import Groq",
            "import os",
            "",
            "# La fonction utilise automatiquement GROQ_API_KEY",
            f"result = {parsed['function_name']}(",
        ])
        
        # Ajouter les paramètres d'exemple
        for i, param_name in enumerate(inputs.keys()):
            comma = "," if i < len(inputs) - 1 else ""
            context_parts.append(f"    {param_name}=<valeur>{comma}")
        
        context_parts.extend([
            ")",
            "",
            "# Accéder aux résultats",
        ])
        
        for output_name in outputs.keys():
            context_parts.append(f"print(result['{output_name}'])")
        
        context_parts.extend([
            "```",
            "",
            "## 🛡️ Gestion des Erreurs",
            "",
            "La fonction gère automatiquement:",
            "- Validation des paramètres d'entrée",
            "- Vérification de la présence de `GROQ_API_KEY`",
            "- Gestion des erreurs API Groq",
            "- Retour structuré avec toutes les clés requises",
            "",
            "## 📚 Dépendances",
            "",
            "```bash",
            "pip install groq",
            "```",
            "",
            "## 🔐 Configuration Requise",
            "",
            "```bash",
            "export GROQ_API_KEY='votre-clé-api'",
            "# ou dans .env",
            "GROQ_API_KEY=votre-clé-api",
            "```",
            "",
            "---",
            "",
            f"*Généré automatiquement par AgentModeles v2.0 - {model_type.replace('_', ' ').title()}*"
        ])
        
        return "\n".join(context_parts)
    
    def build_prompt(
        self,
        description: str,
        inputs: Dict[str, str],
        outputs: Dict[str, str],
        model_type: str,
        model_name: str,
        constraints: Optional[str] = None
    ) -> str:
        """
        Construit le prompt à envoyer au modèle LLM.
        Charge les templates depuis des fichiers txt.
        
        Args:
            description: Description de la fonction
            inputs: Dictionnaire des paramètres d'entrée
            outputs: Dictionnaire des paramètres de sortie
            model_type: Type de modèle (llm, speech_to_text, etc.)
            model_name: Nom exact du modèle Groq
            constraints: Contraintes additionnelles
        
        Returns:
            Prompt formaté pour le LLM
        """
        # Charger le template approprié selon le type de modèle
        template_file = f"prompt_{model_type}.txt"
        
        try:
            template = self._load_prompt_template(template_file)
        except FileNotFoundError:
            # Fallback sur le template par défaut
            template = self._load_prompt_template("prompt_main.txt")
        
        # Charger les sections communes
        inputs_section = self._load_prompt_template("inputs_section.txt")
        outputs_section = self._load_prompt_template("outputs_section.txt")
        instructions_section = self._load_prompt_template("instructions_section.txt")
        format_section = self._load_prompt_template(f"format_{model_type}.txt")
        
        # Formater les inputs
        inputs_str = "\n".join(
            [f"  - {name}: {type_}" for name, type_ in inputs.items()]
        )
        inputs_formatted = inputs_section.format(inputs=inputs_str)
        
        # Formater les outputs
        outputs_str = "\n".join(
            [f"  - {name}: {type_}" for name, type_ in outputs.items()]
        )
        outputs_formatted = outputs_section.format(outputs=outputs_str)
        
        # Formater les contraintes
        constraints_formatted = ""
        if constraints:
            constraints_section_template = self._load_prompt_template(
                "constraints_section.txt"
            )
            constraints_formatted = constraints_section_template.format(
                constraints=constraints
            )
        
        # Assembler le prompt complet
        prompt = template.format(
            description=description,
            model_name=model_name,
            inputs_section=inputs_formatted,
            outputs_section=outputs_formatted,
            constraints_section=constraints_formatted,
            instructions_section=instructions_section,
            format_section=format_section
        )
        
        return prompt
    
    def _build_system_context(self, model_type: str) -> str:
        """
        Construit un contexte système détaillé pour le LLM selon le type de modèle.
        
        Args:
            model_type: Type de modèle cible
        
        Returns:
            Contexte système riche et professionnel
        """
        base_context = """Tu es un Architecte Logiciel Senior spécialisé dans l'ingénierie IA et l'intégration d'APIs de modèles génératifs. 

Tu possèdes une expertise approfondie dans:

🎯 COMPÉTENCES PRINCIPALES:
- Architecture de systèmes d'IA en production avec plus de 10 ans d'expérience
- Développement Python avancé (PEP 8, type hints, design patterns)
- Intégration d'APIs Groq et modèles de Machine Learning
- Conception de fonctions robustes, testables et maintenables
- Gestion d'erreurs exhaustive et validation de données stricte
- Documentation technique de niveau entreprise
- Sécurité applicative et bonnes pratiques DevSecOps
- Optimisation de performance et gestion de ressources

💼 TON RÔLE:
Générer du code Python de qualité PRODUCTION (pas de prototype!) qui:
1. Fonctionne immédiatement sans modification
2. Gère tous les cas limites et erreurs possibles
3. Suit les standards industriels (Clean Code, SOLID)
4. Inclut une documentation complète et professionnelle
5. Est sécurisé contre les vulnérabilités courantes
6. Peut être déployé en environnement critique

⚡ PHILOSOPHIE DE CODE:
- "Fail fast, fail explicitly" - détection rapide des erreurs
- "No surprises" - comportement prévisible et documenté
- "Production-first" - code prêt pour la production dès la génération
- "Type-safe" - utilisation maximale des type hints Python
- "Self-documenting" - code lisible qui s'explique lui-même

🔒 EXIGENCES DE SÉCURITÉ:
- Validation stricte de TOUTES les entrées utilisateur
- Pas d'injection de code (eval, exec, subprocess)
- Gestion sécurisée des secrets (variables d'environnement uniquement)
- Traitement approprié des données sensibles
- Logging des erreurs sans exposer d'informations sensibles

"""
        
        # Contexte spécifique selon le type de modèle
        specific_contexts = {
            "llm": """
📚 SPÉCIALISATION LLM:
Tu es expert en:
- Prompt engineering et optimisation de prompts
- Gestion de contexte et fenêtres de tokens
- Streaming de réponses pour UX améliorée
- Chaînage de prompts et workflows complexes
- Extraction structurée depuis texte non-structuré
- Gestion de la température et sampling pour qualité optimale

Tu génères des fonctions qui utilisent les LLMs pour:
- Analyse de texte et extraction d'informations
- Génération de contenu créatif et professionnel
- Traduction et reformulation intelligente
- Résumé et synthèse de documents
- Classification et catégorisation
- Dialogue conversationnel contextuel
""",
            "speech_to_text": """
🎤 SPÉCIALISATION SPEECH-TO-TEXT:
Tu es expert en:
- Traitement audio et formats multimedia (MP3, WAV, FLAC, M4A)
- Modèles Whisper et leurs capacités multilingues
- Gestion de fichiers volumineux et chunking audio
- Extraction de métadonnées (timestamps, speakers, langue)
- Optimisation de la qualité de transcription
- Gestion de contexte audio (bruit, accents, domaines techniques)

Tu génères des fonctions qui:
- Transcrivent avec précision dans 99+ langues
- Détectent automatiquement la langue source
- Fournissent timestamps au niveau mot/phrase/paragraphe
- Gèrent l'identification de locuteurs (diarization)
- Supportent les fichiers audio jusqu'à 25MB
- Retournent des métadonnées riches (durée, confiance, langue)
""",
            "text_to_speech": """
🔊 SPÉCIALISATION TEXT-TO-SPEECH:
Tu es expert en:
- Synthèse vocale naturelle et expressive
- Modèles TTS avancés (PlayAI, ElevenLabs patterns)
- Contrôle prosodique (vitesse, ton, émotion)
- Gestion de voix multilingues et multi-speakers
- Encodage audio optimal (MP3, Opus, AAC)
- Streaming audio pour latence minimale

Tu génères des fonctions qui:
- Produisent une voix naturelle et engageante
- Supportent plusieurs voix et styles (casual/professional/narrative)
- Contrôlent vitesse (0.25x-4.0x) et expressivité
- Gèrent les longues transcriptions avec chunking intelligent
- Retournent audio en base64 ou fichier direct
- Optimisent la qualité audio (bitrate, sample rate)
""",
            "text_to_video": """
🎬 SPÉCIALISATION TEXT-TO-VIDEO:
Tu es expert en:
- Génération vidéo depuis descriptions textuelles
- Modèles de diffusion vidéo (Stable Video, Runway patterns)
- Contrôle de style, résolution et durée
- Gestion de prompts visuels complexes
- Optimisation de rendu et qualité d'image
- Formats vidéo et encodage (MP4, WebM)

Tu génères des fonctions qui:
- Créent des vidéos HD/4K depuis descriptions détaillées
- Contrôlent durée (3-30s), FPS et résolution
- Supportent différents styles (réaliste, artistique, cinématique)
- Gèrent les prompts négatifs pour éviter contenu indésirable
- Retournent URL ou fichier vidéo avec thumbnail
- Incluent métadonnées complètes (codec, bitrate, dimensions)
""",
            "image_generation": """
🎨 SPÉCIALISATION IMAGE GENERATION:
Tu es expert en:
- Génération d'images par IA (DALL-E, Stable Diffusion patterns)
- Prompt engineering visuel avancé
- Contrôle de style, composition et qualité
- Résolutions multiples et ratios d'aspect
- Post-processing et amélioration d'images
- Formats optimaux (PNG, JPEG, WebP)

Tu génères des fonctions qui:
- Créent des images haute qualité depuis descriptions
- Supportent multiples tailles (256px à 1792px)
- Contrôlent style (vivid/natural/artistic)
- Optimisent les prompts automatiquement (revised prompt)
- Retournent images en base64 ou URL
- Gèrent qualité standard/HD selon besoin
- Incluent métadonnées (dimensions, format, prompt optimisé)
"""
        }
        
        specific = specific_contexts.get(model_type, specific_contexts["llm"])
        
        final_context = base_context + specific + """

🎓 STANDARDS DE CODE À RESPECTER:
1. Type hints sur TOUTES les fonctions et paramètres
2. Docstrings Google-style avec Args, Returns, Raises
3. Validation d'entrée exhaustive avec messages d'erreur explicites
4. Try-except ciblés avec gestion d'erreur appropriée
5. Nommage descriptif (variables, fonctions explicites)
6. Retour structuré en dictionnaire avec clés documentées
7. Constantes en MAJUSCULES, pas de magic numbers
8. Logging approprié sans exposer de secrets
9. Code DRY (Don't Repeat Yourself)
10. Complexité cyclomatique < 10 par fonction

✅ CHECKLIST AVANT GÉNÉRATION:
- [ ] Imports minimaux et nécessaires uniquement
- [ ] Validation de tous les paramètres d'entrée
- [ ] Gestion GROQ_API_KEY via os.getenv()
- [ ] Client Groq initialisé proprement
- [ ] Appel API avec paramètres appropriés
- [ ] Extraction et transformation des résultats
- [ ] Dictionnaire de retour avec TOUTES les clés requises
- [ ] Gestion d'erreurs complète (ValueError, FileNotFoundError, APIError, etc.)
- [ ] Docstring complète et exemples d'utilisation
- [ ] Code prêt pour tests unitaires

🚀 GÉNÈRE MAINTENANT DU CODE DE NIVEAU SENIOR ENGINEER!
"""
        
        return final_context.strip()
    
    def call_llm(
        self,
        prompt: str,
        temperature: float = 0.3,
        max_tokens: int = 2048
    ) -> str:
        """
        Appelle le modèle Groq pour génération de code.
        
        Args:
            prompt: Prompt à envoyer au modèle
            temperature: Contrôle la créativité (0.0-1.0)
            max_tokens: Nombre maximum de tokens à générer
        
        Returns:
            Réponse brute du modèle
        """
        # Extraire le type de modèle du prompt si possible
        model_type = "llm"  # default
        for mtype in self.MODEL_CONFIG.keys():
            if mtype in prompt.lower():
                model_type = mtype
                break
        
        try:
            # Construire un contexte système détaillé et professionnel
            system_context = self._build_system_context(model_type)
            
            message = self.client.chat.completions.create(
                model=self.MODEL_CONFIG["llm"]["model"],
                messages=[
                    {
                        "role": "system",
                        "content": system_context
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=0.9
            )
            return message.choices[0].message.content
        except Exception as e:
            raise RuntimeError(
                f"Erreur lors de l'appel à l'API Groq: {str(e)}"
            ) from e
    
    def parse_llm_output(self, llm_raw_output: str) -> Dict[str, Any]:
        """
        Parse la réponse brute du LLM pour extraire le code.
        
        Args:
            llm_raw_output: Réponse brute du modèle
        
        Returns:
            Dict avec 'code', 'function_name' et 'context'
        """
        code = ""
        function_name = "generated_function"
        context = ""
        
        # Extraction du code Python entre ```python et ```
        python_match = re.search(
            r"```python\s*(.*?)\s*```",
            llm_raw_output,
            re.DOTALL
        )
        
        if python_match:
            code = python_match.group(1).strip()
        else:
            # Fallback: chercher juste entre ``` et ```
            code_match = re.search(
                r"```\s*(.*?)\s*```",
                llm_raw_output,
                re.DOTALL
            )
            if code_match:
                code = code_match.group(1).strip()
            else:
                # Si pas de markdown, prendre la sortie entière
                code = llm_raw_output.strip()
        
        # Extraction du nom de fonction
        def_match = re.search(r"def\s+(\w+)\s*\(", code)
        if def_match:
            function_name = def_match.group(1)
        
        # Contexte = ce qui n'est pas du code
        context = llm_raw_output.replace(f"```python\n{code}\n```", "").strip()
        if not context:
            context = "Fonction générée par AgentModeles via Groq"
        
        return {
            "code": code,
            "function_name": function_name,
            "context": context
        }
    
    def get_available_models(self) -> Dict[str, Dict[str, str]]:
        """
        Retourne la liste des modèles disponibles et leurs descriptions.
        
        Returns:
            Dictionnaire des modèles disponibles
        """
        return self.MODEL_CONFIG.copy()