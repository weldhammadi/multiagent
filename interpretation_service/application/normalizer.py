import re


class InputNormalizer:
    """
    Service de normalisation simple du texte.
    V1 : nettoyage léger, facilement extensible.
    """

    def normalize(self, text: str) -> str:
        if not text:
            return ""
        text = re.sub(r"\s+", " ", text).strip()
        return text

