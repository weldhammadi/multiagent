"""Auto-generated agent by Orchestrator."""

import os
import json
import requests
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv
import imaplib
import email
from email.header import decode_header
from groq import Groq

# Load environment variables
load_dotenv()


def fetch_emails(max_emails: int) -> List[Dict[str, str]]:
    """Récupère les *max_emails* derniers e‑mails de la boîte de réception.

    La fonction se connecte à un serveur IMAP en utilisant les variables
    d'environnement suivantes :

    - ``EMAIL_HOST`` : adresse du serveur IMAP (ex. ``imap.gmail.com``)
    - ``EMAIL_PORT`` : port du serveur IMAP (généralement ``993``)
    - ``EMAIL_USER`` : adresse e‑mail de l'utilisateur
    - ``EMAIL_PASSWORD`` : mot de passe ou token d'application

    Chaque e‑mail retourné est représenté par un dictionnaire contenant les
    clés ``subject``, ``sender`` et ``body``.

    Args:
        max_emails: Nombre maximal d'e‑mails à récupérer.

    Returns:
        Une liste de dictionnaires, chaque dictionnaire décrivant un e‑mail.

    Raises:
        RuntimeError: Si une variable d'environnement requise est absente ou si
            la connexion/connexion IMAP échoue.
    """
    # Vérification des variables d'environnement
    host: str | None = os.getenv("EMAIL_HOST")
    port_str: str | None = os.getenv("EMAIL_PORT")
    user: str | None = os.getenv("EMAIL_USER")
    password: str | None = os.getenv("EMAIL_PASSWORD")

    if host is None:
        raise RuntimeError("La variable d'environnement EMAIL_HOST est manquante.")
    if port_str is None:
        raise RuntimeError("La variable d'environnement EMAIL_PORT est manquante.")
    if user is None:
        raise RuntimeError("La variable d'environnement EMAIL_USER est manquante.")
    if password is None:
        raise RuntimeError("La variable d'environnement EMAIL_PASSWORD est manquante.")

    try:
        port: int = int(port_str)
    except ValueError as exc:
        raise RuntimeError("EMAIL_PORT doit être un entier.") from exc

    # Connexion au serveur IMAP
    try:
        mail = imaplib.IMAP4_SSL(host, port)
        mail.login(user, password)
    except imaplib.IMAP4.error as exc:
        raise RuntimeError("Échec de la connexion ou de l'authentification IMAP.") from exc

    # Sélection de la boîte de réception
    status, _ = mail.select("INBOX")
    if status != "OK":
        mail.logout()
        raise RuntimeError("Impossible de sélectionner la boîte de réception.")

    # Recherche de tous les messages
    status, data = mail.search(None, "ALL")
    if status != "OK":
        mail.logout()
        raise RuntimeError("Échec de la recherche des e‑mails.")

    # Liste des identifiants d'e‑mail, du plus ancien au plus récent
    mail_ids = data[0].split()
    # On veut les plus récents, on inverse la liste
    mail_ids = mail_ids[::-1][:max_emails]

    emails: List[Dict[str, str]] = []

    for mail_id in mail_ids:
        status, msg_data = mail.fetch(mail_id, "(RFC822)")
        if status != "OK":
            continue  # on ignore les messages qui ne peuvent pas être récupérés
        raw_email = msg_data[0][1]
        msg = email.message_from_bytes(raw_email)

        # Décodage du sujet
        subject, encoding = decode_header(msg.get("Subject", ""))[0]
        if isinstance(subject, bytes):
            try:
                subject = subject.decode(encoding or "utf-8", errors="replace")
            except Exception:
                subject = subject.decode("utf-8", errors="replace")
        else:
            subject = str(subject)

        # Expéditeur
        sender = msg.get("From", "")

        # Extraction du corps (texte brut préféré)
        body = ""
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                disposition = str(part.get("Content-Disposition"))
                if content_type == "text/plain" and "attachment" not in disposition:
                    try:
                        body_bytes = part.get_payload(decode=True)
                        charset = part.get_content_charset() or "utf-8"
                        body = body_bytes.decode(charset, errors="replace")
                    except Exception:
                        body = ""
                    break
        else:
            try:
                body_bytes = msg.get_payload(decode=True)
                charset = msg.get_content_charset() or "utf-8"
                body = body_bytes.decode(charset, errors="replace")
            except Exception:
                body = ""

        emails.append({"subject": subject, "sender": sender, "body": body})

    mail.logout()
    return emails


def classify_email_category(email_text: str) -> Dict[str, Any]:
    """
    Analyse le contenu d'un email et le classe dans l'une des catégories
    prédéfinies : ``work``, ``personal``, ``spam`` ou ``important`` en utilisant
    le modèle LLM ``openai/gpt-oss-120b`` via l'API Groq.

    Args:
        email_text: Le texte complet de l'email à analyser. Doit être une chaîne
            non vide.

    Returns:
        dict: Un dictionnaire contenant la clé ``category`` dont la valeur est
        la catégorie attribuée (``work``, ``personal``, ``spam`` ou ``important``).

    Raises:
        ValueError: Si ``email_text`` n'est pas une chaîne non vide ou si la
            variable d'environnement ``GROQ_API_KEY`` est absente.
        RuntimeError: En cas d'échec de l'appel à l'API Groq ou de réponse
            inattendue du modèle.
    """
    # Step 1: Validate input
    if not isinstance(email_text, str) or not email_text.strip():
        raise ValueError("email_text must be a non‑empty string")

    # Step 2: Get API key from environment
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY not set in environment variables")

    # Step 3: Create Groq client - PASS ONLY api_key
    groq_client = Groq(api_key=api_key)

    # Step 4: Build the prompt for the LLM
    system_message = (
        "You are an expert email classifier. Classify the given email text "
        "into exactly one of the following categories: work, personal, spam, "
        "important. Return only the category name as a plain word."
    )
    user_message = f"Email content:\n\"\"\"\n{email_text}\n\"\"\""

    # Step 5: Call LLM - use model openai/gpt-oss-120b
    try:
        llm_response = groq_client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message},
            ],
            temperature=0.3,
            max_tokens=64,
        )
    except Exception as exc:
        raise RuntimeError(f"Failed to call Groq API: {exc}") from exc

    # Step 6: Extract result from response
    try:
        raw_category = llm_response.choices[0].message.content.strip()
    except (AttributeError, IndexError) as exc:
        raise RuntimeError("Unexpected response format from Groq API") from exc

    # Normalise and validate the category
    category = raw_category.lower()
    allowed_categories = {"work", "personal", "spam", "important"}
    if category not in allowed_categories:
        raise RuntimeError(
            f"Model returned invalid category '{raw_category}'. "
            f"Expected one of {sorted(allowed_categories)}."
        )

    # Step 7: Return dictionary with EXACT output key specified
    return {"category": category}


# =============================================================================
# MAIN
# =============================================================================

if __name__ == '__main__':
    print("Running maria 6798...")
    # TODO: Implement main workflow here
    # Available functions:
    # - fetch_emails()
    # - classify_email_category()
    pass