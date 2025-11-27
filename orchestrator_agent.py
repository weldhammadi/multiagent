"""
orchestrator.py

This module implements the Orchestrator class, which receives a user request to create
an agent, delegates planning to Groq OSS 120B, generates tool and LLM functions via 
ToolAgent and LLMAgent, and assembles everything into a single Python file.
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable

from dotenv import load_dotenv

# Import your existing agents
from tool_generator_agent import ToolAgent
from model_generator_agent import AgentModeles as LLMAgent
from execute_test_agent import AgentTestExecuteur


class Orchestrator:
    """
    Orchestrateur principal qui coordonne ToolAgent et LLMAgent pour créer
    des agents complets à partir de descriptions utilisateur.
    
    Workflow:
    1. Planification via LLM (découpe en tools + llm_functions)
    2. Génération des tools via ToolAgent
    3. Génération des fonctions LLM via LLMAgent
    4. Assemblage du code final
    """
    
    # Chemins des fichiers de prompts
    PROMPTS_DIR = Path(__file__).parent / "prompts"
    PLANNER_CONTEXT_FILE = "orchestrator_planner_context.txt"
    PLANNER_PROMPT_FILE = "orchestrator_planner_prompt.txt"
    TOOL_PROMPT_FILE = "orchestrator_tool_prompt.txt"
    
    def __init__(
        self,
        output_dir: str = "./output",
        enable_github_search: bool = False,
        model: str = "openai/gpt-oss-120b",
        temperature: float = 0.1,
        max_tokens: int = 2048
    ):
        """
        Initialize orchestrator.
        
        Args:
            output_dir: Directory to save final agent file
            enable_github_search: Enable GitHub search in ToolAgent
            model: LLM model to use for planning
            temperature: Temperature for LLM generation
            max_tokens: Max tokens for LLM generation
        """
        load_dotenv()
        
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Configuration LLM
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        
        # Initialisation des agents
        self.tool_agent = ToolAgent(
            output_dir=output_dir,
            enable_github_search=enable_github_search,
            model=model,
            temperature=temperature
        )
        self.llm_agent = LLMAgent()
        
        # Code parts pour l'assemblage final
        self.final_code_parts: List[str] = []
        self.generated_tools: List[Dict[str, Any]] = []
        self.generated_llm_functions: List[Dict[str, Any]] = []
        
        # Progress callback for UI updates
        self._progress_callback: Optional[Callable[[str, str], None]] = None
    
    def set_progress_callback(self, callback: Callable[[str, str], None]) -> None:
        """
        Set a callback function to receive progress updates.
        
        Args:
            callback: Function that takes (message, level) as arguments.
                     Level can be: 'info', 'success', 'error', 'warning', 
                     'progress', 'tool', 'llm', 'plan', 'code', 'file', 'test'
        """
        self._progress_callback = callback
    
    def _emit_progress(self, message: str, level: str = "info") -> None:
        """Emit a progress update to the callback if set."""
        print(message)  # Always print to console
        if self._progress_callback:
            self._progress_callback(message, level)
    
    def _load_prompt(self, filename: str) -> str:
        """
        Charge un fichier de prompt depuis le dossier prompts.
        
        Args:
            filename: Nom du fichier de prompt
            
        Returns:
            Contenu du fichier
            
        Raises:
            FileNotFoundError: Si le fichier n'existe pas
        """
        filepath = self.PROMPTS_DIR / filename
        try:
            return filepath.read_text(encoding="utf-8")
        except FileNotFoundError:
            raise FileNotFoundError(f"Fichier prompt introuvable: {filepath}")

    def plan_agent(self, user_request: str) -> Dict[str, Any]:
        """
        Sends user request to LLM to generate structured plan.
        
        Args:
            user_request: Textual description of the desired agent
            
        Returns:
            JSON dict with keys "tools" and "llm_functions"
            
        Raises:
            ValueError: If LLM returns invalid JSON
        """
        # Charger les prompts depuis les fichiers
        context = self._load_prompt(self.PLANNER_CONTEXT_FILE)
        prompt_template = self._load_prompt(self.PLANNER_PROMPT_FILE)
        
        # Formater le prompt avec la requête utilisateur
        prompt = prompt_template.format(user_request=user_request)
        
        response = self.tool_agent.call_llm(
            context=context,
            user_request=prompt
        )
        
        # Parse JSON response
        cleaned = response.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        if cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()
        
        try:
            plan = json.loads(cleaned)
        except json.JSONDecodeError as exc:
            raise ValueError(f"LLM returned invalid JSON plan: {exc}\nResponse: {cleaned[:500]}")
        
        return plan

    def generate_tools(self, tools_plan: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Calls ToolAgent to generate code for each tool.
        
        Args:
            tools_plan: List of tool descriptions from LLM plan
            
        Returns:
            List of dicts containing code and metadata
        """
        generated_tools = []
        
        # Charger le template de prompt pour les tools
        prompt_template = self._load_prompt(self.TOOL_PROMPT_FILE)
        total_tools = len(tools_plan)
        
        for idx, tool in enumerate(tools_plan, 1):
            tool_name = tool.get('name', 'unknown')
            self._emit_progress(f"🔧 [{idx}/{total_tools}] Generating tool: {tool_name}", "tool")
            
            # Construire le prompt pour ToolAgent
            inputs_str = json.dumps(tool.get('inputs', {}), indent=2)
            outputs_str = json.dumps(tool.get('outputs', {}), indent=2)
            prompt = prompt_template.format(
                tool_name=tool.get('name', 'tool'),
                tool_description=tool.get('description', 'No description provided'),
                inputs=inputs_str,
                outputs=outputs_str
            )
            
            try:
                self._emit_progress(f"   ⏳ Calling LLM for {tool_name}...", "info")
                # save_files=False pour ne pas créer de fichiers individuels
                result = self.tool_agent.generate_tool(user_prompt=prompt, save_files=False)
                generated_tools.append(result)
                self.final_code_parts.append(result["source_code"])
                self._emit_progress(f"   ✅ Tool generated: {result['metadata'].get('nom', tool_name)}", "success")
            except Exception as exc:
                self._emit_progress(f"   ❌ Error generating tool {tool_name}: {exc}", "error")
                continue
        
        self.generated_tools = generated_tools
        return generated_tools

    def generate_llm_functions(self, llm_plan: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Calls LLMAgent to generate LLM-based functions.
        
        Args:
            llm_plan: List of LLM function descriptions from plan
            
        Returns:
            List of dicts containing code and metadata
        """
        generated_llm = []
        total_funcs = len(llm_plan)
        
        for idx, func in enumerate(llm_plan, 1):
            func_name = func.get('name', 'unknown')
            model_type = func.get('model_type', 'llm')
            self._emit_progress(f"🤖 [{idx}/{total_funcs}] Generating LLM function: {func_name} (type: {model_type})", "llm")
            
            try:
                self._emit_progress(f"   ⏳ Calling LLM for {func_name}...", "info")
                result = self.llm_agent.generate_model_function(
                    description=func.get("description", ""),
                    inputs=func.get("inputs", {}),
                    outputs=func.get("outputs", {}),
                    model_type=model_type,
                    constraints=func.get("constraints"),
                    temperature=func.get("temperature", 0.3),
                    max_tokens=func.get("max_tokens", 2048)
                )
                generated_llm.append(result)
                self.final_code_parts.append(result["source_code"])
                self._emit_progress(f"   ✅ LLM function generated: {result['metadata']['fonction']['nom']}", "success")
            except Exception as exc:
                self._emit_progress(f"   ❌ Error generating LLM function {func_name}: {exc}", "error")
                continue
        
        self.generated_llm_functions = generated_llm
        return generated_llm

    def correct_agent(self, code: str, errors: List[str]) -> str:
        """
        Sends code and errors to Groq LLM to get corrected code.
        
        Args:
            code: The code with errors
            errors: List of error messages
            
        Returns:
            Corrected code string
        """
        errors_str = "\n".join(errors)
        
        context = """Tu es un expert Python. Tu reçois du code Python et une liste d'erreurs.
                    Tu dois corriger le code pour éliminer toutes les erreurs.
                    Renvoie UNIQUEMENT le code corrigé, sans explication, sans markdown, sans ```python.
                    Le code doit être complet et fonctionnel.
                    ne oublie pas de mettre tous les imports en haut du fichier pas d'inport entre les fonctions.
                    organise bien la structure du code sans modifier la logique initiale."""
        
        prompt = f"""Voici le code Python avec des erreurs:

{code}

Erreurs détectées:
{errors_str}

Corrige le code pour éliminer ces erreurs. Renvoie UNIQUEMENT le code corrigé."""
        
        response = self.tool_agent.call_llm(
            context=context,
            user_request=prompt
        )
        
        # Nettoyer la réponse
        corrected = response.strip()
        if corrected.startswith("```python"):
            corrected = corrected[9:]
        if corrected.startswith("```"):
            corrected = corrected[3:]
        if corrected.endswith("```"):
            corrected = corrected[:-3]
        
        return corrected.strip()

    def assemble_final_agent(self, agent_name: str = "final_agent", max_retries: int = 5) -> Path:
        """
        Combines all generated code into a single Python file.
        Tests the code and retries correction up to max_retries times.
        
        Args:
            agent_name: Filename for the final agent
            max_retries: Max correction attempts (default 5)
            
        Returns:
            Path to the generated Python file
        """
        final_path = self.output_dir / f"{agent_name}.py"

        # Header avec imports communs
        imports = '''"""'
Auto-generated agent by Orchestrator.
"""

import os
import json
import requests
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

'''
        
        # Assembler le code
        code = imports + "\n\n".join(self.final_code_parts)

        # Add a main wrapper
        main_wrapper = f'''

# =============================================================================
# MAIN
# =============================================================================

if __name__ == '__main__':
    print("🚀 Running {agent_name}...")
    # TODO: Implement main workflow here
    # Available functions:
'''
        
        # Lister les fonctions disponibles
        for tool in self.generated_tools:
            func_name = tool.get("metadata", {}).get("nom", "unknown")
            main_wrapper += f"    # - {func_name}()\n"
        
        for llm_func in self.generated_llm_functions:
            func_name = llm_func.get("metadata", {}).get("fonction", {}).get("nom", "unknown")
            main_wrapper += f"    # - {func_name}()\n"
        
        main_wrapper += "    pass\n"
        
        code += main_wrapper

        # Test and correct loop
        tester = AgentTestExecuteur(timeout=60)
        
        for attempt in range(1, max_retries + 1):
            self._emit_progress(f"🧪 Testing code (attempt {attempt}/{max_retries})...", "test")
            
            resultat = tester.tester_code(code, description=f"Agent {agent_name}")
            
            if resultat["statut"] == "OK":
                self._emit_progress(f"✅ Code valid! No errors detected.", "success")
                break
            else:
                self._emit_progress(f"❌ {len(resultat['erreurs'])} error(s) detected", "error")
                for err in resultat["erreurs"]:
                    self._emit_progress(f"   • {err[:100]}...", "warning")
                
                if attempt < max_retries:
                    self._emit_progress(f"🔄 Correcting code with LLM...", "progress")
                    code = self.correct_agent(code, resultat["erreurs"])
                    self._emit_progress(f"   Code corrected, retesting...", "info")
                else:
                    self._emit_progress(f"⚠️ Max attempts reached ({max_retries}). Saving final code despite errors.", "warning")
        
        final_path.write_text(code, encoding="utf-8")
        self._emit_progress(f"📄 Final agent saved: {final_path.name}", "file")
        return final_path
    
    def _collect_env_vars_and_configs(self) -> Dict[str, Any]:
        """
        Collecte toutes les variables d'environnement et fichiers de config
        requis par les tools et fonctions LLM générés.
        
        Returns:
            Dict avec 'env_vars' (list) et 'config_files' (list)
        """
        env_vars = set()
        config_files = set()
        
        # Collecter depuis les tools générés
        for tool in self.generated_tools:
            metadata = tool.get("metadata", {})
            
            # Variables d'environnement
            tool_env_vars = metadata.get("env_vars", [])
            if isinstance(tool_env_vars, list):
                env_vars.update(tool_env_vars)
            
            # Fichiers de configuration
            tool_configs = metadata.get("config_files", [])
            if isinstance(tool_configs, list):
                config_files.update(tool_configs)
        
        # Collecter depuis les fonctions LLM générées
        for llm_func in self.generated_llm_functions:
            metadata = llm_func.get("metadata", {})
            
            # Chercher dans la structure imbriquée
            func_meta = metadata.get("fonction", {})
            
            llm_env_vars = func_meta.get("env_vars", [])
            if isinstance(llm_env_vars, list):
                env_vars.update(llm_env_vars)
            
            llm_configs = func_meta.get("config_files", [])
            if isinstance(llm_configs, list):
                config_files.update(llm_configs)
        
        # Ajouter les variables communes toujours nécessaires
        env_vars.add("GROQ_API_KEY")
        
        return {
            "env_vars": sorted(list(env_vars)),
            "config_files": sorted(list(config_files))
        }
    
    def _generate_env_file(self, agent_name: str, env_vars: List[str]) -> Path:
        """
        Génère un fichier .env avec les variables requises (valeurs vides).
        
        Args:
            agent_name: Nom de l'agent
            env_vars: Liste des variables d'environnement
            
        Returns:
            Chemin du fichier .env créé
        """
        env_file = self.output_dir / f"{agent_name}.env"
        
        if env_file.exists():
            self._emit_progress(f"   ⚠️ {env_file.name} already exists, not overwritten", "warning")
            return env_file
        
        # Générer le contenu avec commentaires
        lines = [
            f"# Configuration pour {agent_name}",
            "# Remplissez les valeurs ci-dessous avant d'exécuter l'agent",
            "",
        ]
        
        for var in env_vars:
            lines.append(f"{var}=")
        
        lines.append("")  # Ligne vide finale
        
        env_file.write_text("\n".join(lines), encoding="utf-8")
        self._emit_progress(f"   🔐 {env_file.name} created (needs manual configuration)", "file")
        return env_file
    
    def _generate_config_files(self, agent_name: str, config_files: List[str]) -> Dict[str, Path]:
        """
        Génère des fichiers JSON de configuration vides.
        
        Args:
            agent_name: Nom de l'agent
            config_files: Liste des noms de fichiers de config
            
        Returns:
            Dict {nom: Path} des fichiers créés
        """
        created = {}
        
        for config_name in config_files:
            # Nettoyer le nom
            clean_name = config_name.replace(".json", "")
            config_file = self.output_dir / f"{agent_name}_{clean_name}.json"
            
            if config_file.exists():
                self._emit_progress(f"   ⚠️ {config_file.name} already exists, not overwritten", "warning")
                created[clean_name] = config_file
                continue
            
            # Créer un JSON vide avec structure de base selon le type
            if "credentials" in clean_name.lower() or "oauth" in clean_name.lower():
                content = {
                    "_comment": f"Configuration {clean_name} pour {agent_name}",
                    "_instructions": "Remplissez ce fichier avec vos credentials",
                    "client_id": "",
                    "client_secret": "",
                    "redirect_uri": ""
                }
            elif "config" in clean_name.lower() or "settings" in clean_name.lower():
                content = {
                    "_comment": f"Configuration {clean_name} pour {agent_name}",
                    "_instructions": "Ajoutez vos paramètres de configuration ici"
                }
            else:
                content = {
                    "_comment": f"Fichier {clean_name} pour {agent_name}",
                    "_instructions": "Remplissez ce fichier selon vos besoins"
                }
            
            config_file.write_text(
                json.dumps(content, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8"
            )
            self._emit_progress(f"   ⚙️ {config_file.name} created (needs manual configuration)", "file")
            created[clean_name] = config_file
        
        return created
    
    def _generate_credentials_template(self, agent_name: str) -> Path:
        """
        Génère un fichier template pour les credentials OAuth2 (Gmail, etc.).
        
        Args:
            agent_name: Nom de l'agent
            
        Returns:
            Chemin du fichier créé
        """
        creds_file = self.output_dir / f"{agent_name}_credentials.json"
        
        if creds_file.exists():
            self._emit_progress(f"   ⚠️ {creds_file.name} already exists, not overwritten", "warning")
            return creds_file
        
        template = {
            "_comment": "Template OAuth2 credentials - Remplacez par vos vraies credentials",
            "_instructions": [
                "1. Allez sur https://console.cloud.google.com/",
                "2. Créez un projet ou sélectionnez-en un existant",
                "3. Activez l'API Gmail (ou autre API nécessaire)",
                "4. Créez des identifiants OAuth 2.0",
                "5. Téléchargez le fichier JSON et remplacez ce contenu"
            ],
            "installed": {
                "client_id": "VOTRE_CLIENT_ID.apps.googleusercontent.com",
                "project_id": "votre-project-id",
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                "client_secret": "VOTRE_CLIENT_SECRET",
                "redirect_uris": ["http://localhost"]
            }
        }
        
        creds_file.write_text(
            json.dumps(template, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8"
        )
        self._emit_progress(f"   🔑 {creds_file.name} created (OAuth2 template needs configuration)", "file")
        return creds_file
    
    def generate_config_files_for_agent(self, agent_name: str) -> Dict[str, Any]:
        """
        Génère tous les fichiers de configuration nécessaires pour l'agent.
        
        Args:
            agent_name: Nom de l'agent
            
        Returns:
            Dict avec les chemins des fichiers créés
        """
        self._emit_progress("   Generating configuration files...", "info")
        
        # Collecter les requirements
        requirements = self._collect_env_vars_and_configs()
        
        result = {
            "env_file": None,
            "config_files": {},
            "credentials_file": None
        }
        
        # Générer le fichier .env
        if requirements["env_vars"]:
            result["env_file"] = self._generate_env_file(agent_name, requirements["env_vars"])
        
        # Générer les fichiers de config JSON
        if requirements["config_files"]:
            result["config_files"] = self._generate_config_files(agent_name, requirements["config_files"])
        
        # Analyser le code pour détecter si on a besoin de credentials OAuth
        full_code = "\n".join(self.final_code_parts)
        needs_oauth = any(keyword in full_code.lower() for keyword in [
            "oauth", "credentials", "gmail", "google", "client_secrets",
            "installedappflow", "credentials_path"
        ])
        
        if needs_oauth:
            result["credentials_file"] = self._generate_credentials_template(agent_name)
        
        return result

    def run(self, user_request: str, agent_name: str = "final_agent") -> Dict[str, Any]:
        """
        Full orchestrator pipeline: plan, generate functions, assemble final agent.
        
        Args:
            user_request: User description of the agent
            agent_name: Output filename
        Returns:
            Dict with plan, generated tools, llm functions, and final path
        """
        self._emit_progress("=" * 50, "info")
        self._emit_progress("🎯 Orchestrator - Complete Agent Generation", "info")
        self._emit_progress("=" * 50, "info")

        # Phase 1: Planning
        self._emit_progress("📋 PHASE 1: Planning agent structure...", "plan")
        self._emit_progress(f"   Analyzing request: {user_request[:80]}...", "info")
        plan = self.plan_agent(user_request)

        # --- Centralize and automate model_type assignment for LLM functions ---
        def infer_model_type(func: dict) -> str:
            name = func.get("name", "").lower()
            desc = func.get("description", "").lower()
            # Heuristics for model_type
            if "speech" in name or "speech" in desc or "tts" in name or "tts" in desc:
                return "text_to_speech"
            if "audio" in name or "audio" in desc:
                # If it's about converting text to audio, prefer text_to_speech
                if "text" in desc or "story" in desc:
                    return "text_to_speech"
            if "stt" in name or "stt" in desc or "transcribe" in name or "transcribe" in desc:
                return "speech_to_text"
            if "image" in name or "image" in desc or "vision" in name or "vision" in desc:
                return "image_generation"
            if "video" in name or "video" in desc:
                return "text_to_video"
            # Default
            return "llm"

        # Set or correct model_type for each LLM function
        for func in plan.get("llm_functions", []):
            func["model_type"] = infer_model_type(func)

        tools_count = len(plan.get("tools", []))
        llm_count = len(plan.get("llm_functions", []))
        self._emit_progress(f"   ✅ Plan created: {tools_count} tools, {llm_count} LLM functions", "success")
        
        # Log planned items
        for tool in plan.get("tools", []):
            self._emit_progress(f"   📌 Tool planned: {tool.get('name', 'unknown')}", "info")
        for func in plan.get("llm_functions", []):
            self._emit_progress(f"   📌 LLM function planned: {func.get('name', 'unknown')}", "info")

        # Phase 2: Generate tools
        self._emit_progress("\n🔧 PHASE 2: Generating Tools...", "progress")
        self.generate_tools(plan.get("tools", []))
        self._emit_progress(f"   ✅ Generated {len(self.generated_tools)} tools", "success")

        # Phase 3: Generate LLM functions
        self._emit_progress("\n🤖 PHASE 3: Generating LLM Functions...", "progress")
        self.generate_llm_functions(plan.get("llm_functions", []))
        self._emit_progress(f"   ✅ Generated {len(self.generated_llm_functions)} LLM functions", "success")

        # Phase 4: Assemble
        self._emit_progress("\n📦 PHASE 4: Assembling final agent...", "progress")
        final_path = self.assemble_final_agent(agent_name)

        # Phase 5: Generate config files (.env, JSON configs, credentials)
        self._emit_progress("\n📁 PHASE 5: Generating configuration files...", "progress")
        config_result = self.generate_config_files_for_agent(agent_name)

        self._emit_progress("\n" + "=" * 50, "info")
        self._emit_progress("🎉 Agent generated successfully!", "success")
        self._emit_progress("=" * 50, "info")

        # Afficher un résumé des fichiers créés
        self._emit_progress("\n📁 Files created:", "file")
        self._emit_progress(f"   📄 {final_path.name}", "file")
        if config_result.get("env_file"):
            self._emit_progress(f"   🔐 {config_result['env_file'].name} (⚠️ needs configuration)", "file")
        if config_result.get("credentials_file"):
            self._emit_progress(f"   🔑 {config_result['credentials_file'].name} (⚠️ needs configuration)", "file")
        for name, path in config_result.get("config_files", {}).items():
            self._emit_progress(f"   ⚙️ {path.name} (⚠️ needs configuration)", "file")

        return {
            "plan": plan,
            "tools": self.generated_tools,
            "llm_functions": self.generated_llm_functions,
            "final_path": final_path,
            "config_files": config_result,
            "code_parts_count": len(self.final_code_parts)
        }
    
    def reset(self) -> None:
        """Reset the orchestrator state for a new generation."""
        self.final_code_parts = []
        self.generated_tools = []
        self.generated_llm_functions = []


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    # Exemple d'utilisation
    orchestrator = Orchestrator(
        output_dir="./output",
        enable_github_search=False
    )
    
    #user_request = """i want an agent that creates kids stories and saves them as mp4 audio files using text to speech synthesis in French. The agent should create story theme , then generate a creative story accordingly. Finally, it should convert the text story into an engaging audio format suitable for children."""
    user_request = """i want an agent that reads my mails and classify them into categories such as work, personal, spam, and important. The agent should connect to my Gmail account using OAuth2 authentication, fetch unread emails, analyze their content, and categorize them accordingly. Finally, it should generate a summary report of the categorized emails."""
    
    result = orchestrator.run(user_request, agent_name="kids_story_agent")
    
    print(f"\n📊 Résumé:")
    print(f"   - Tools générés: {len(result['tools'])}")
    print(f"   - Fonctions LLM: {len(result['llm_functions'])}")
    print(f"   - Fichier final: {result['final_path']}")
