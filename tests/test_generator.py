import pytest
from pathlib import Path
from agents.generator import ToolGenerator
import shutil
import os

TEST_DIR = Path("./output/test_toolgen")

def setup_module(module):
    # Nettoyage avant tests
    if TEST_DIR.exists():
        shutil.rmtree(TEST_DIR)
    TEST_DIR.mkdir(parents=True, exist_ok=True)

def teardown_module(module):
    # Nettoyage après tests
    if TEST_DIR.exists():
        shutil.rmtree(TEST_DIR)

def test_init_and_save_tool():
    gen = ToolGenerator(TEST_DIR)
    source_code = "def foo():\n    return 42"
    metadata = {
        "nom": "foo",
        "description": "Fonction de test",
        "inputs": {},
        "output": "int",
        "env_vars": ["API_KEY"],
        "config_files": ["config"]
    }
    result = gen.save_tool("foo", source_code, metadata)
    # Vérifie fichiers créés
    assert result["python"].exists()
    assert result["metadata"].exists()
    assert result["env"].exists()
    assert "config_files" in result
    assert "config" in result["config_files"]
    assert result["config_files"]["config"].exists()
    # Vérifie contenu .env
    env_content = result["env"].read_text()
    assert "API_KEY=" in env_content
    # Vérifie contenu Python
    py_content = result["python"].read_text()
    assert "def foo" in py_content
    # Vérifie contenu metadata
    meta = result["metadata"].read_text()
    assert "description" in meta
