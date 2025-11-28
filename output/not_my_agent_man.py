"""Auto-generated agent by Orchestrator."""

import os
import json
import base64
import imaplib
import requests
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv
from groq import Groq

# Load environment variables
load_dotenv()


def connect_to_email(credentials: Dict[str, Any]) -> imaplib.IMAP4_SSL:
    """Connect to an IMAP email server.

    Args:
        credentials (dict): Dictionary containing connection parameters:
            - host (str): IMAP server hostname.
            - port (int, optional): Port number, defaults to 993.
            - username (str): Email account username.
            - password (str): Email account password.
            - use_ssl (bool, optional): Whether to use SSL, defaults to True.

    Returns:
        imaplib.IMAP4_SSL: Authenticated IMAP client object.

    Raises:
        RuntimeError: If required credential fields are missing or connection fails.
    """
    host = credentials.get("host")
    username = credentials.get("username")
    password = credentials.get("password")
    port = credentials.get("port", 993)
    use_ssl = credentials.get("use_ssl", True)

    if not host or not username or not password:
        raise RuntimeError("Missing required email credentials: host, username, or password.")

    try:
        if use_ssl:
            client = imaplib.IMAP4_SSL(host, port)
        else:
            client = imaplib.IMAP4(host, port)  # type: ignore
        client.login(username, password)
        return client
    except Exception as e:
        raise RuntimeError(f"Failed to connect to email server: {e}") from e


def _get_plain_text(part: Dict[str, Any]) -> str:
    """Recursively extract plain‑text content from a Gmail API payload part."""
    mime_type = part.get("mimeType", "")
    if mime_type == "text/plain" and "data" in part.get("body", {}):
        data = part["body"]["data"]
        try:
            return base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")
        except Exception:
            return ""
    for sub_part in part.get("parts", []):
        text = _get_plain_text(sub_part)
        if text:
            return text
    return ""


def fetch_emails(client: Any, max_results: int) -> List[Dict[str, str]]:
    """Retrieve unread emails from the connected account.

    Args:
        client: Authenticated email client providing ``users().messages()`` methods.
        max_results: Maximum number of unread messages to retrieve.

    Returns:
        List of dictionaries each containing ``id``, ``subject`` and ``body`` keys.

    Raises:
        RuntimeError: If the client call fails or required fields are missing.
    """
    try:
        response = (
            client.users()
            .messages()
            .list(userId="me", q="is:unread", maxResults=max_results)
            .execute()
        )
    except Exception as exc:
        raise RuntimeError(f"Erreur lors de la récupération de la liste des e‑mails : {exc}")

    messages = response.get("messages", [])
    emails: List[Dict[str, str]] = []

    for msg in messages:
        msg_id = msg.get("id")
        if not msg_id:
            continue
        try:
            msg_detail = (
                client.users()
                .messages()
                .get(userId="me", id=msg_id, format="full")
                .execute()
            )
        except Exception as exc:
            raise RuntimeError(f"Erreur lors de la récupération du message {msg_id} : {exc}")

        headers = msg_detail.get("payload", {}).get("headers", [])
        subject = ""
        for header in headers:
            if header.get("name", "").lower() == "subject":
                subject = header.get("value", "")
                break

        body = _get_plain_text(msg_detail.get("payload", {}))
        emails.append({"id": msg_id, "subject": subject, "body": body})

    return emails


def classify_email_category(email_text: str) -> Dict[str, Any]:
    """
    Analyse le corps d'un e‑mail (et éventuellement son sujet) à l'aide du modèle
    LLM ``openai/gpt-oss-120b`` via l'API Groq et le classe dans l'une des
    catégories suivantes : ``work``, ``personal``, ``spam`` ou ``important``.
    Le modèle est invité à ne retourner **que** le nom de la catégorie afin de
    garantir un format de sortie stable.

    Args:
        email_text: Texte complet de l'e‑mail à analyser. Doit être une chaîne
            non vide.

    Returns:
        Dict contenant la clé ``category`` dont la valeur est l'une des chaînes
        suivantes : ``"work"``, ``"personal"``, ``"spam"``, ``"important"``.

    Raises:
        ValueError: Si ``email_text`` n'est pas une chaîne non vide ou si la clé
            d'API Groq n'est pas définie dans les variables d'environnement.
        RuntimeError: En cas d'échec de l'appel à l'API Groq ou de réponse
            inattendue du modèle.
    """
    if not isinstance(email_text, str) or not email_text.strip():
        raise ValueError("email_text must be a non‑empty string")

    api_key: Optional[str] = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY not set in environment variables")

    try:
        groq_client = Groq(api_key=api_key)
    except Exception as exc:
        raise RuntimeError(f"Failed to initialise Groq client: {exc}") from exc

    system_message = (
        "You are an AI assistant that classifies an email into one of the "
        "following categories: work, personal, spam, important. Return ONLY the "
        "category name in lowercase without any additional text."
    )
    user_message = f"Email content:\n\"\"\"\n{email_text.strip()}\n\"\"\""

    try:
        llm_response = groq_client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message},
            ],
            temperature=0.3,
            max_tokens=10,
        )
    except Exception as exc:
        raise RuntimeError(f"Groq API request failed: {exc}") from exc

    try:
        raw_category: str = llm_response.choices[0].message.content.strip().lower()
    except (AttributeError, IndexError) as exc:
        raise RuntimeError("Malformed response from Groq LLM") from exc

    allowed_categories = {"work", "personal", "spam", "important"}
    if raw_category not in allowed_categories:
        raise RuntimeError(
            f"Unexpected category returned by LLM: '{raw_category}'. "
            f"Expected one of {sorted(allowed_categories)}."
        )

    return {"category": raw_category}


if __name__ == "__main__":
    print("Running not_my_agent_man...")
    # TODO: Implement main workflow here
    # Available functions:
    # - connect_to_email()
    # - fetch_emails()
    # - classify_email_category()
    pass