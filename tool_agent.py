# agents/tool_agent.py
from typing import Dict, Any

class ToolAgent:
    def __init__(self):
        pass

    def run(self, command: str) -> Dict[str, Any]:
        # Très simple router : si command commence par "calc:" -> calcule l'expression
        if command.startswith("calc:"):
            expr = command[len("calc:"):].strip()
            try:
                # sécurité: eval limité — ici pour démo seulement
                result = eval(expr, {"__builtins__": {}}, {})
                return {"ok": True, "result": result}
            except Exception as e:
                return {"ok": False, "error": str(e)}
        # autre commande -> echo
        return {"ok": True, "result": f"tool echo: {command}"}
