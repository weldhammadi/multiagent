class DomainError(Exception):
    """Erreur générique de la couche domaine."""


class InvalidInputError(DomainError):
    """Aucun texte / audio exploitable."""


class ClarificationNeededError(DomainError):
    """Le LLM indique qu'il lui faut une clarification utilisateur."""

