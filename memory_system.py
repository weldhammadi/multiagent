"""
Système de gestion de la mémoire persistante
Stocke l'historique des agents, fonctions, prompts et configurations
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass, asdict


@dataclass
class ToolRecord:
    """Enregistrement d'un outil généré"""
    name: str
    description: str
    code: str
    parameters: List[str]
    return_type: str
    external_api: Optional[str]
    created_at: str
    used_in_agents: List[str]


@dataclass
class ModelRecord:
    """Enregistrement d'une configuration de modèle"""
    purpose: str
    provider: str
    model_name: str
    temperature: float
    max_tokens: int
    system_prompt: str
    created_at: str
    used_in_agents: List[str]


@dataclass
class AgentRecord:
    """Enregistrement d'un agent généré"""
    name: str
    description: str
    agent_type: str
    tools_used: List[str]
    models_used: List[str]
    created_at: str
    github_url: Optional[str]
    render_url: Optional[str]
    status: str


class MemoryManager:
    """Gère la persistance de la mémoire du système"""
    
    def __init__(self, memory_file: Path = Path("memory/memory.json")):
        self.memory_file = memory_file
        self.memory_file.parent.mkdir(parents=True, exist_ok=True)
        self.memory = self._load_memory()
    
    def _load_memory(self) -> Dict[str, Any]:
        """Charge la mémoire depuis le fichier"""
        if self.memory_file.exists():
            try:
                with open(self.memory_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # S'assurer que la structure contient les clés attendues
                    fixed = self._ensure_defaults(data)
                    if fixed is not data:
                        # Si on a ajouté des valeurs par défaut, sauvegarder
                        self.memory = fixed
                        self.save()
                        return fixed
                    return data
            except json.JSONDecodeError:
                print("⚠️  Fichier mémoire corrompu, création d'une nouvelle mémoire")
                return self._create_empty_memory()
        else:
            return self._create_empty_memory()

    def _ensure_defaults(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Vérifie et complète la structure de mémoire avec des valeurs par défaut.

        Retourne l'objet (modifié ou non). Si `data` est None ou non dictionnaire,
        retourne une nouvelle structure vide.
        """
        if not isinstance(data, dict):
            return self._create_empty_memory()

        modified = False

        # Champs top-level attendus
        defaults = {
            'version': '1.0',
            'created_at': datetime.now().isoformat(),
            'last_updated': datetime.now().isoformat(),
            'tools': {},
            'models': {},
            'agents': {},
            'statistics': {
                'total_tools': 0,
                'total_models': 0,
                'total_agents': 0,
                'successful_deployments': 0,
                'failed_deployments': 0
            }
        }

        for key, val in defaults.items():
            if key not in data:
                data[key] = val
                modified = True

        # Ensure statistics subkeys
        stats = data.get('statistics', {})
        for k, v in defaults['statistics'].items():
            if k not in stats:
                data['statistics'][k] = v
                modified = True

        return data if modified else data
    
    def _create_empty_memory(self) -> Dict[str, Any]:
        """Crée une structure de mémoire vide"""
        return {
            "version": "1.0",
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            "tools": {},
            "models": {},
            "agents": {},
            "statistics": {
                "total_tools": 0,
                "total_models": 0,
                "total_agents": 0,
                "successful_deployments": 0,
                "failed_deployments": 0
            }
        }
    
    def save(self):
        """Sauvegarde la mémoire dans le fichier"""
        self.memory["last_updated"] = datetime.now().isoformat()
        
        with open(self.memory_file, 'w', encoding='utf-8') as f:
            json.dump(self.memory, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Mémoire sauvegardée: {self.memory_file}")
    
    def add_tool(self, tool: ToolRecord):
        """Ajoute un outil à la mémoire"""
        self.memory["tools"][tool.name] = asdict(tool)
        self.memory["statistics"]["total_tools"] = len(self.memory["tools"])
        self.save()
    
    def add_model(self, model: ModelRecord):
        """Ajoute une configuration de modèle à la mémoire"""
        key = f"{model.provider}_{model.model_name}_{model.purpose}"
        self.memory["models"][key] = asdict(model)
        self.memory["statistics"]["total_models"] = len(self.memory["models"])
        self.save()
    
    def add_agent(self, agent: AgentRecord):
        """Ajoute un agent à la mémoire"""
        self.memory["agents"][agent.name] = asdict(agent)
        self.memory["statistics"]["total_agents"] = len(self.memory["agents"])
        
        if agent.status == "deployed":
            self.memory["statistics"]["successful_deployments"] += 1
        elif agent.status == "failed":
            self.memory["statistics"]["failed_deployments"] += 1
        
        self.save()
    
    def get_tool(self, name: str) -> Optional[ToolRecord]:
        """Récupère un outil de la mémoire"""
        data = self.memory["tools"].get(name)
        if data:
            return ToolRecord(**data)
        return None
    
    def get_model(self, key: str) -> Optional[ModelRecord]:
        """Récupère une configuration de modèle"""
        data = self.memory["models"].get(key)
        if data:
            return ModelRecord(**data)
        return None
    
    def get_agent(self, name: str) -> Optional[AgentRecord]:
        """Récupère un agent de la mémoire"""
        data = self.memory["agents"].get(name)
        if data:
            return AgentRecord(**data)
        return None
    
    def search_tools(self, keyword: str) -> List[ToolRecord]:
        """Recherche des outils par mot-clé"""
        results = []
        keyword_lower = keyword.lower()
        
        for tool_data in self.memory["tools"].values():
            if (keyword_lower in tool_data["name"].lower() or
                keyword_lower in tool_data["description"].lower()):
                results.append(ToolRecord(**tool_data))
        
        return results
    
    def search_agents(self, keyword: str) -> List[AgentRecord]:
        """Recherche des agents par mot-clé"""
        results = []
        keyword_lower = keyword.lower()
        
        for agent_data in self.memory["agents"].values():
            if (keyword_lower in agent_data["name"].lower() or
                keyword_lower in agent_data["description"].lower()):
                results.append(AgentRecord(**agent_data))
        
        return results
    
    def get_reusable_tools(self, description: str) -> List[ToolRecord]:
        """
        Trouve des outils réutilisables basés sur une description.
        Utile pour éviter de régénérer des outils identiques.
        """
        # Simple recherche par mots-clés
        keywords = description.lower().split()
        matches = []
        
        for tool_data in self.memory["tools"].values():
            tool_desc = tool_data["description"].lower()
            score = sum(1 for kw in keywords if kw in tool_desc)
            
            if score >= 2:  # Au moins 2 mots-clés correspondent
                matches.append((score, ToolRecord(**tool_data)))
        
        # Trier par pertinence
        matches.sort(reverse=True, key=lambda x: x[0])
        
        return [tool for _, tool in matches[:5]]  # Top 5
    
    def get_statistics(self) -> Dict[str, Any]:
        """Retourne les statistiques du système"""
        return self.memory["statistics"].copy()
    
    def export_to_json(self, output_file: Path):
        """Exporte toute la mémoire vers un fichier JSON"""
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.memory, f, indent=2, ensure_ascii=False)
        
        print(f"📤 Mémoire exportée: {output_file}")
    
    def generate_report(self) -> str:
        """Génère un rapport lisible de la mémoire"""
        stats = self.memory["statistics"]
        report = (
            "╔═════════════════════════════════════════════╗\n"
            "║   RAPPORT MÉMOIRE DU SYSTÈME MULTI-AGENTS   ║\n"
            "╚═════════════════════════════════════════════╝\n"
            f"📊 STATISTIQUES\n{'─'*40}\n"
            f"Outils: {stats['total_tools']} | Modèles: {stats['total_models']} | Agents: {stats['total_agents']} | OK: {stats['successful_deployments']} | Échecs: {stats['failed_deployments']}\n"
            f"🔧 OUTILS\n{'─'*40}\n"
        )
        for name, tool in self.memory["tools"].items():
            report += f"• {name}: {tool['description'][:40]}... | {len(tool['used_in_agents'])} agent(s)\n"

        # MODÈLES
        report += f"🧠 MODÈLES\n{'─'*40}\n"
        if self.memory["models"]:
            for key, model in self.memory["models"].items():
                used_in = model.get('used_in_agents', [])
                used_str = ', '.join(used_in) if used_in else 'aucun agent'
                report += f"• {model['model_name']} ({model['provider']}, {model['purpose']}) | {used_str}\n"
        else:
            report += "(Aucun modèle)\n"

        report += f"🤖 AGENTS\n{'─'*40}\n"
        for name, agent in self.memory["agents"].items():
            status_emoji = "✅" if agent['status'] == 'deployed' else "❌"
            report += f"{status_emoji} {name} | Type: {agent['agent_type']} | Outils: {len(agent['tools_used'])} | Modèles: {len(agent['models_used'])}\n"
            if agent.get('render_url'):
                report += f"  URL: {agent['render_url']}\n"

        report += f"{'═'*40}\n"
        report += f"Maj: {self.memory['last_updated']}\n"
        report += f"{'═'*40}\n"
        return report
    
    def identify_patterns(self) -> Dict[str, Any]:
        """Identifie les patterns dans les agents créés"""
        patterns = {
            'most_used_tools': {},
            'most_used_models': {},
            'common_agent_types': {},
            'popular_apis': {}
        }
        
        # Analyser les outils les plus utilisés
        for tool_name, tool_data in self.memory.memory["tools"].items():
            usage_count = len(tool_data['used_in_agents'])
            if usage_count > 0:
                patterns['most_used_tools'][tool_name] = usage_count
        
        # Analyser les types d'agents
        for agent_data in self.memory.memory["agents"].values():
            agent_type = agent_data['agent_type']
            patterns['common_agent_types'][agent_type] = \
                patterns['common_agent_types'].get(agent_type, 0) + 1
        
        return patterns
    
    def optimize_memory(self) -> Dict[str, int]:
        """Nettoie la mémoire (supprime les entrées inutilisées)"""
        removed = {
            'tools': 0,
            'models': 0,
            'agents': 0
        }
        
        # Supprimer les outils jamais utilisés après 30 jours
        # Supprimer les agents en échec après 60 jours
        # etc.
        
        # TODO: Implémenter la logique de nettoyage
        
        return removed


def test_memory_system():
    """Test du système de mémoire"""
    print("🧪 Test du système de mémoire...\n")
    
    # Créer un gestionnaire de mémoire
    memory = MemoryManager(Path("memory/test_memory.json"))
    
    # Ajouter un outil de test
    tool = ToolRecord(
        name="csv_cleaner",
        description="Nettoie les fichiers CSV en supprimant les doublons",
        code="def csv_cleaner(file_path): ...",
        parameters=["file_path: str"],
        return_type="pd.DataFrame",
        external_api=None,
        created_at=datetime.now().isoformat(),
        used_in_agents=["data_processor_agent"]
    )
    memory.add_tool(tool)
    
    # Ajouter un modèle de test
    model = ModelRecord(
        purpose="text_analysis",
        provider="groq",
        model_name="llama-3.3-70b-versatile",
        temperature=0.1,
        max_tokens=1000,
        system_prompt="Tu es un analyseur de texte.",
        created_at=datetime.now().isoformat(),
        used_in_agents=["text_analyzer_agent"]
    )
    memory.add_model(model)
    
    # Ajouter un agent de test
    agent = AgentRecord(
        name="data_processor_agent",
        description="Agent qui traite des données CSV",
        agent_type="data_processor",
        tools_used=["csv_cleaner"],
        models_used=["groq_llama-3.3-70b-versatile_text_analysis"],
        created_at=datetime.now().isoformat(),
        github_url="https://github.com/user/repo",
        render_url="https://app.render.com/service",
        status="deployed"
    )
    memory.add_agent(agent)
    
    # Générer un rapport
    print(memory.generate_report())
    
    # Exporter
    memory.export_to_json(Path("memory/export_test.json"))
    
    print("\n✅ Test terminé avec succès!")


if __name__ == "__main__":
    test_memory_system()