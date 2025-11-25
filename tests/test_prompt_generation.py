from pathlib import Path
from llm_server_core import AgentAssembler, ExecutionPlan, AgentRequirements, AgentType


def test_execution_prompt_generation_simple():
    """Teste la génération de prompts pour un agent simple"""
    assembler = AgentAssembler(Path('.'))

    req = AgentRequirements(
        role="CSV Cleaner",
        description="Nettoie des fichiers CSV",
        agent_type=AgentType.DATA_PROCESSOR,
        objectives=["Supprimer les doublons", "Gérer les valeurs manquantes"],
        tools_needed=[
            {"name": "read_csv", "description": "Lit un CSV", "params": ["file_path: str"], "returns": "DataFrame"},
            {"name": "clean_data", "description": "Nettoie les données", "params": ["df: DataFrame"], "returns": "DataFrame"},
        ],
        models_needed=[],
        constraints=[],
        input_format="dict",
        output_format="json",
    )

    plan = ExecutionPlan(agent_requirements=req, tools_to_generate=req.tools_needed, models_to_configure=req.models_needed, dependencies=["pandas"], architecture_type="tool_based_agent", estimated_complexity="simple")

    prompt = assembler._generate_execution_prompt(plan)

    assert "Tu es" in prompt
    assert len(prompt) > 100
    assert "OBJECTIFS" in prompt


def test_execution_prompt_generation_ai_models():
    """Teste la génération de prompts pour un agent nécessitant des modèles IA"""
    assembler = AgentAssembler(Path('.'))

    req = AgentRequirements(
        role="Sentiment Analyzer",
        description="Analyse le sentiment de textes",
        agent_type=AgentType.AI_ASSISTANT,
        objectives=["Détecter le sentiment", "Extraire entités", "Générer rapport"],
        tools_needed=[],
        models_needed=[{"purpose": "sentiment_detection", "provider": "groq", "model_type": "llm"}],
        constraints=[],
        input_format="str",
        output_format="json",
    )

    plan = ExecutionPlan(agent_requirements=req, tools_to_generate=req.tools_needed, models_to_configure=req.models_needed, dependencies=["groq"], architecture_type="ai_only_agent", estimated_complexity="medium")

    prompt = assembler._generate_execution_prompt(plan)

    assert "Tu es" in prompt
    assert len(prompt) > 100
    assert ("modèle" in prompt.lower()) or ("model" in prompt.lower())