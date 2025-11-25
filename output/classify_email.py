from __future__ import annotations

import re
from typing import List

def classify_email(email_text: str) -> str:
    """Classify an email as SPAM, IMPORTANT, or NORMAL.

    Args:
        email_text: The full raw text of the email to analyse.

    Returns:
        A string: "IMPORTANT" if the email contains any important keyword,
        "SPAM" if it contains any spam keyword, otherwise "NORMAL".

    Raises:
        ValueError: If ``email_text`` is not a string or is empty.
    """
    if not isinstance(email_text, str):
        raise ValueError("email_text must be a string")
    if not email_text.strip():
        raise ValueError("email_text cannot be empty")

    lowered = email_text.lower()

    important_keywords: List[str] = [
        "urgent",
        "facture",
        "paiement",
        "problème",
        "client",
    ]
    spam_keywords: List[str] = [
        "promo",
        "promotion",
        "réduction",
        "gagner",
        "cadeau",
    ]

    for kw in important_keywords:
        if re.search(rf"\b{re.escape(kw)}\b", lowered):
            return "IMPORTANT"

    for kw in spam_keywords:
        if re.search(rf"\b{re.escape(kw)}\b", lowered):
            return "SPAM"

    return "NORMAL"
