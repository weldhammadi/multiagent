from agents.validator import validate_tool_response

def test_validate_tool_response_valid():
    tool_data = {
        "source_code": "def foo(): return 42",
        "metadata": {
            "nom": "foo",
            "description": "Fonction de test",
            "inputs": {},
            "output": "int",
            "dependencies": [],
            "env_vars": []
        }
    }
    errors = validate_tool_response(tool_data)
    assert errors == []

def test_validate_tool_response_missing_fields():
    tool_data = {
        "source_code": "def foo(): return 42",
        "metadata": {
            "inputs": {},
            "output": "int"
        }
    }
    errors = validate_tool_response(tool_data)
    assert any("nom" in e for e in errors)
    assert any("description" in e for e in errors)
