class AgentProcessing:
    def analyze(self, message: str):
        message = message.lower()

        if "projet" in message:
            return "Demande d'aide sur un projet."
        if "data" in message:
            return "Demande liée à la data."
        if "ia" in message or "intelligence" in message:
            return "Demande liée à l'intelligence artificielle."
        if "bonjour" in message or "salam" in message:
            return "Salutation."

        return "Demande générale."
