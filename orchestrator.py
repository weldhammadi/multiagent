from .memory_client import MemoryClient
from .agent_memory import AgentMemory
from .agent_processing import AgentProcessing

class Orchestrator:
    def __init__(self):
        self.memory = MemoryClient()
        self.agent_memory = AgentMemory()
        self.agent_processing = AgentProcessing()

    def process(self, user_id: str, message: str):
        # 1. Save user message
        self.memory.save_interaction(user_id, "user", message)

        # 2. Fetch history
        history = self.memory.get_history(user_id)

        # 3. AgentProcessing → analyse the message
        task_analysis = self.agent_processing.analyze(message)

        # 4. AgentMemory → generate conversational response
        final_response = self.agent_memory.generate_response(
            message=message,
            history=history,
            analysis=task_analysis
        )

        # 5. Save agent response
        self.memory.save_interaction(user_id, "agent", final_response)

        # 6. Return final answer
        return {
            "analysis": task_analysis,
            "response": final_response
        }
