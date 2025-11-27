"""Auto-generated agent by Orchestrator."""

import os
import json
import requests
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

import imaplib
from email import message_from_bytes
from email.header import decode_header
from email.policy import default

from groq import Groq

# Load environment variables
load_dotenv()

# --------------------------------------------------------------------------- #
# Constants (immutable configuration)
# --------------------------------------------------------------------------- #
_MODEL_NAME: str = "openai/gpt-oss-120b"
_TEMPERATURE: float = 0.3
_MAX_TOKENS: int = 512
_ALLOWED_CATEGORIES = {"work", "personal", "spam", "important"}


def fetch_emails(max_emails: int) -> List[Dict[str, str]]:
    """Récupère les *max_emails* derniers courriels de la boîte de réception.

    La fonction se connecte à un serveur IMAP en utilisant les variables
    d'environnement ``EMAIL_HOST``, ``EMAIL_USER`` et ``EMAIL_PASSWORD``.
    Elle renvoie une liste de dictionnaires contenant le sujet et le corps
    en texte‑plain de chaque message.

    Args:
        max_emails: Nombre maximum d'e‑mails à récupérer. Si la boîte contient
            moins de messages, tous seront retournés.

    Returns:
        Une liste de dictionnaires avec les clés ``subject`` et ``body``.

    Raises:
        RuntimeError: Si une variable d'environnement requise est absente ou si
            la connexion/lecture IMAP échoue.
    """
    host: str | None = os.getenv("EMAIL_HOST")
    user: str | None = os.getenv("EMAIL_USER")
    password: str | None = os.getenv("EMAIL_PASSWORD")
    if host is None:
        raise RuntimeError("La variable d'environnement EMAIL_HOST est manquante.")
    if user is None:
        raise RuntimeError("La variable d'environnement EMAIL_USER est manquante.")
    if password is None:
        raise RuntimeError("La variable d'environnement EMAIL_PASSWORD est manquante.")

    try:
        imap = imaplib.IMAP4_SSL(host)
        imap.login(user, password)
    except imaplib.IMAP4.error as exc:
        raise RuntimeError(f"Échec de la connexion IMAP : {exc}")

    try:
        imap.select("INBOX")
        typ, data = imap.search(None, "ALL")
        if typ != "OK":
            raise RuntimeError("Impossible de rechercher les e‑mails dans la boîte de réception.")
        all_ids = data[0].split()
        recent_ids = all_ids[-max_emails:] if max_emails > 0 else []
        emails: List[Dict[str, str]] = []
        for mail_id in reversed(recent_ids):
            typ, msg_data = imap.fetch(mail_id, "(RFC822)")
            if typ != "OK":
                raise RuntimeError(f"Échec du fetch du mail ID {mail_id.decode()}.")
            raw_email = msg_data[0][1]
            msg = message_from_bytes(raw_email, policy=default)

            raw_subject = msg["Subject"] or ""
            decoded_parts = decode_header(raw_subject)
            subject_parts = []
            for part, enc in decoded_parts:
                if isinstance(part, bytes):
                    subject_parts.append(part.decode(enc or "utf-8", errors="replace"))
                else:
                    subject_parts.append(part)
            subject = "".join(subject_parts)

            body = ""
            if msg.is_multipart():
                for part in msg.walk():
                    content_type = part.get_content_type()
                    disposition = part.get_content_disposition()
                    if content_type == "text/plain" and disposition != "attachment":
                        body = part.get_content()
                        break
            else:
                if msg.get_content_type() == "text/plain":
                    body = msg.get_content()
            emails.append({"subject": subject, "body": body})
        return emails
    finally:
        imap.logout()


def classify_email(subject: str, body: str) -> Dict[str, Any]:
    """
    Classifies an email into one of the predefined categories using the Groq LLM.

    Args:
        subject: The email subject line. Must be a non‑empty string.
        body: The full email body. Must be a non‑empty string.

    Returns:
        Dict[str, Any]: {"category": "<category>"}
    """
    if not isinstance(subject, str) or not subject.strip():
        raise ValueError("subject must be a non‑empty string")
    if not isinstance(body, str) or not body.strip():
        raise ValueError("body must be a non‑empty string")

    api_key: str | None = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY not set in environment variables")

    groq_client = Groq(api_key=api_key)

    system_message = (
        "You are an assistant that classifies emails into one of the following "
        "categories: work, personal, spam, important. Respond with only the "
        "category name in lowercase."
    )
    user_message = (
        f"Subject: {subject.strip()}\n"
        f"Body: {body.strip()}\n"
        "Classify the above email."
    )

    try:
        llm_response = groq_client.chat.completions.create(
            model=_MODEL_NAME,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message},
            ],
            temperature=_TEMPERATURE,
            max_tokens=_MAX_TOKENS,
        )
    except Exception as exc:
        raise RuntimeError(f"Failed to obtain classification from Groq API: {exc}") from exc

    try:
        raw_category: str = llm_response.choices[0].message.content.strip().lower()
    except (AttributeError, IndexError) as exc:
        raise RuntimeError("Malformed response received from Groq API") from exc

    if raw_category not in _ALLOWED_CATEGORIES:
        raise ValueError(
            f"Unexpected category '{raw_category}'. Expected one of: {', '.join(sorted(_ALLOWED_CATEGORIES))}"
        )

    return {"category": raw_category}


if __name__ == "__main__":
    print("Running my_agenttedt2...")
    # TODO: Implement main workflow here
    # Available functions:
    # - fetch_emails()
    # - classify_email()
    pass