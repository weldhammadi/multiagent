import os
import json
import requests
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv
import imaplib
import email
from email.policy import default
from groq import Groq

# Load environment variables
load_dotenv()


def fetch_emails(max_emails: int) -> List[Dict[str, str]]:
    """Récupère les e‑mails non lus les plus récents.

    Cette fonction se connecte à un serveur IMAP via SSL en utilisant les
    variables d’environnement suivantes :

    - ``EMAIL_HOST`` : adresse du serveur IMAP (ex. ``imap.gmail.com``)
    - ``EMAIL_PORT`` : port du serveur IMAP (généralement ``993``)
    - ``EMAIL_USER`` : adresse e‑mail de l’utilisateur
    - ``EMAIL_PASSWORD`` : mot de passe ou token d’application

    Elle recherche les messages marqués comme *UNSEEN*, en récupère jusqu’à
    ``max_emails`` et renvoie une liste de dictionnaires contenant le sujet et le
    corps texte du message.

    Args:
        max_emails: Nombre maximum d’e‑mails à récupérer.

    Returns:
        Une liste de dictionnaires avec les clés ``subject`` et ``body``.

    Raises:
        RuntimeError: Si une variable d’environnement requise est absente, si la
            connexion au serveur IMAP échoue ou si la récupération des messages
            rencontre une erreur.
    """
    # Vérification des variables d’environnement
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
        raise RuntimeError("Échec de l'authentification ou de la connexion IMAP.") from exc

    # Sélection de la boîte de réception
    status, _ = mail.select("INBOX")
    if status != "OK":
        mail.logout()
        raise RuntimeError("Impossible de sélectionner la boîte de réception.")

    # Recherche des e‑mails non lus
    status, data = mail.search(None, "UNSEEN")
    if status != "OK":
        mail.logout()
        raise RuntimeError("La recherche des e‑mails non lus a échoué.")

    email_ids = data[0].split()
    # On garde les plus récents en inversant l’ordre
    email_ids = email_ids[::-1][:max_emails]

    results: List[Dict[str, str]] = []
    for eid in email_ids:
        status, msg_data = mail.fetch(eid, "RFC822")
        if status != "OK":
            continue  # on ignore les messages qui posent problème
        raw_email = msg_data[0][1]
        msg = email.message_from_bytes(raw_email, policy=default)
        subject = msg.get("subject", "")
        # Extraction du corps texte (plain)
        body = ""
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain" and not part.get_filename():
                    body = part.get_content()
                    break
        else:
            if msg.get_content_type() == "text/plain":
                body = msg.get_content()
        results.append({"subject": subject, "body": body})

    mail.logout()
    return results


def classify_email_category(email_text: str) -> Dict[str, Any]:
    """
    Analyse le contenu d'un e‑mail à l'aide du modèle LLM « openai/gpt-oss-120b » via l'API Groq
    et attribue l'e‑mail à l'une des catégories suivantes : **work**, **personal**, **spam** ou **important**.

    Args:
        email_text (str): Texte complet de l'e‑mail à analyser. Doit être une chaîne non vide.

    Returns:
        Dict[str, Any]: Dictionnaire contenant la clé ``category`` dont la valeur est l'une des
        catégories autorisées (``"work"``, ``"personal"``, ``"spam"``, ``"important"``).

    Raises:
        ValueError: Si ``email_text`` n'est pas une chaîne non vide ou si la variable d'environnement
        ``GROQ_API_KEY`` est absente.
        RuntimeError: En cas d'échec de l'appel à l'API Groq ou si la réponse du modèle ne correspond
        pas aux catégories attendues.
    """
    # Step 1 – Validation de l'entrée
    if not isinstance(email_text, str) or not email_text.strip():
        raise ValueError("email_text must be a non‑empty string")

    # Step 2 – Récupération de la clé API
    api_key: str | None = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY not set in environment variables")

    # Step 3 – Instanciation du client Groq
    groq_client = Groq(api_key=api_key)

    # Step 4 – Construction du prompt
    system_message = (
        "You are an assistant that classifies e‑mail content into one of the following "
        "categories: work, personal, spam, important. Return only the category name."
    )
    user_message = f"Classify the following e‑mail:\n\n{email_text.strip()}"

    # Step 5 – Appel du modèle LLM
    try:
        llm_response = groq_client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message},
            ],
            temperature=0.3,
            max_tokens=50,
        )
    except Exception as exc:
        raise RuntimeError(f"Failed to call Groq API: {exc}") from exc

    # Step 6 – Extraction et validation du résultat
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

    # Step 7 – Retour du dictionnaire conforme à la spécification
    return {"category": raw_category}


if __name__ == '__main__':
    print("Running test_agent...")
    # TODO: Implement main workflow here
    # Available functions:
    # - fetch_emails()
    # - classify_email_category()
    pass