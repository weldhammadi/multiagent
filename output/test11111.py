"""Auto-generated agent by Orchestrator."""

import os
import json
import imaplib
import email
from email.header import decode_header
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv
from groq import Groq

# Load environment variables
load_dotenv()

# --------------------------------------------------------------------------- #
# CONSTANTS (no magic numbers)
# --------------------------------------------------------------------------- #
MODEL_NAME: str = "openai/gpt-oss-120b"
TEMPERATURE: float = 0.2          # deterministic enough for classification
MAX_TOKENS: int = 50
VALID_CATEGORIES = {"work", "personal", "spam", "important"}
SYSTEM_PROMPT: str = (
    "You are an expert email classification assistant. "
    "Given the full content of an email, return **only** one of the following "
    "lower‑case categories without any additional text: work, personal, spam, or important."
)


def fetch_emails(max_emails: int) -> List[Dict[str, str]]:
    """Fetch recent unread emails via IMAP.

    Args:
        max_emails (int): Maximum number of unread emails to retrieve.

    Returns:
        List[Dict[str, str]]: List of dictionaries each containing ``id``, ``subject`` and ``body``.

    Raises:
        RuntimeError: If required environment variables are missing or any IMAP error occurs.
    """
    # Retrieve environment variables
    email_address: str | None = os.getenv("EMAIL_ADDRESS")
    email_password: str | None = os.getenv("EMAIL_PASSWORD")
    imap_server: str | None = os.getenv("IMAP_SERVER")
    imap_port: str | None = os.getenv("IMAP_PORT")

    if email_address is None:
        raise RuntimeError("La variable d'environnement EMAIL_ADDRESS est manquante.")
    if email_password is None:
        raise RuntimeError("La variable d'environnement EMAIL_PASSWORD est manquante.")
    if imap_server is None:
        raise RuntimeError("La variable d'environnement IMAP_SERVER est manquante.")
    if imap_port is None:
        raise RuntimeError("La variable d'environnement IMAP_PORT est manquante.")

    try:
        imap = imaplib.IMAP4_SSL(imap_server, int(imap_port))
        imap.login(email_address, email_password)
        imap.select("INBOX")
        status, messages = imap.search(None, "UNSEEN")
        if status != "OK":
            raise RuntimeError("Échec de la recherche des e‑mails non lus.")
        email_ids = messages[0].split()
        email_ids = email_ids[:max_emails]

        result: List[Dict[str, str]] = []
        for eid in email_ids:
            status, msg_data = imap.fetch(eid, "(RFC822)")
            if status != "OK":
                continue
            raw_email = msg_data[0][1]
            msg = email.message_from_bytes(raw_email)

            # Decode subject
            subject_header = msg.get("Subject", "")
            decoded_subject = decode_header(subject_header)
            subject, encoding = decoded_subject[0] if decoded_subject else ("", None)
            if isinstance(subject, bytes):
                subject = subject.decode(encoding or "utf-8", errors="ignore")
            else:
                subject = str(subject)

            # Extract plain‑text body
            body = ""
            if msg.is_multipart():
                for part in msg.walk():
                    content_type = part.get_content_type()
                    disposition = str(part.get("Content-Disposition"))
                    if content_type == "text/plain" and "attachment" not in disposition:
                        charset = part.get_content_charset() or "utf-8"
                        body = part.get_payload(decode=True).decode(charset, errors="ignore")
                        break
            else:
                charset = msg.get_content_charset() or "utf-8"
                body = msg.get_payload(decode=True).decode(charset, errors="ignore")

            result.append({"id": eid.decode(), "subject": subject, "body": body})

        imap.logout()
        return result
    except imaplib.IMAP4.error as e:
        raise RuntimeError(f"Erreur IMAP : {e}") from e


def classify_email_category(email_text: str) -> Dict[str, Any]:
    """
    Classify the content of an e‑mail into one of four predefined categories using
    the Groq LLM ``openai/gpt-oss-120b``.

    Args:
        email_text: The raw e‑mail body to be classified. Must be a non‑empty string.

    Returns:
        Dict[str, Any]: A dictionary containing a single key:
            - ``category`` (str): One of ``"work"``, ``"personal"``, ``"spam"``, or ``"important"``.

    Raises:
        ValueError: If ``email_text`` is not a non‑empty string or the environment
            variable ``GROQ_API_KEY`` is missing.
        RuntimeError: If the Groq API call fails or the LLM returns an unexpected
            category.
    """
    if not isinstance(email_text, str) or not email_text.strip():
        raise ValueError("email_text must be a non‑empty string")

    api_key: str | None = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY not set in environment variables")

    try:
        groq_client = Groq(api_key=api_key)
    except Exception as exc:
        raise RuntimeError(f"Failed to initialise Groq client: {exc}") from exc

    user_prompt: str = f"Classify this email:\n\n{email_text.strip()}"

    try:
        response = groq_client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS,
        )
    except Exception as exc:
        raise RuntimeError(f"Groq API request failed: {exc}") from exc

    try:
        raw_category: str = response.choices[0].message.content.strip().lower()
    except Exception as exc:
        raise RuntimeError(f"Failed to extract category from LLM response: {exc}") from exc

    if raw_category not in VALID_CATEGORIES:
        raise RuntimeError(
            f"LLM returned an invalid category '{raw_category}'. "
            f"Expected one of {sorted(VALID_CATEGORIES)}."
        )

    return {"category": raw_category}


# =============================================================================
# MAIN
# =============================================================================

if __name__ == '__main__':
    print("Running test11111...")
    # TODO: Implement main workflow here
    # Available functions:
    # - fetch_emails()
    # - classify_email_category()
    pass