import os
import base64
from typing import Dict, List, Optional

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from httplib2 import Http


def gmail_fetch_last_email(token_path: str, credentials_path: str) -> Dict[str, str]:
    """Récupère le dernier email reçu dans la boîte Gmail.

    Cette fonction utilise un token OAuth déjà obtenu (fichier ``token.json``) et
    les informations d'application (``client_secret.json``) pour appeler l'API
    Gmail en lecture seule. Elle renvoie le sujet et le corps texte du message le
    plus récent présent dans la boîte de réception.

    Args:
        token_path: Chemin absolu ou relatif vers le fichier ``token.json``
            contenant les informations d'authentification OAuth.
        credentials_path: Chemin vers le fichier ``client_secret.json`` fourni
            par Google Cloud Console. Le fichier n'est pas lu directement par
            cette fonction mais il doit être présent pour que le token soit
            valide.

    Returns:
        Dict[str, str]: Un dictionnaire avec les clés ``"subject"`` et ``"body"``.
            ``subject`` contient l'objet du mail (ou chaîne vide si absent) et
            ``body`` le texte brut du corps du mail (ou chaîne vide si non trouvé).

    Raises:
        RuntimeError: Si le token est manquant, si l'API renvoie une erreur ou si
            aucun message n'est trouvé dans la boîte de réception.
    """
    # Vérification de la présence du token
    if not os.path.isfile(token_path):
        raise RuntimeError(f"Fichier token introuvable : {token_path}")

    # Chargement des credentials OAuth (lecture seule Gmail)
    try:
        creds = Credentials.from_authorized_user_file(
            token_path,
            scopes=["https://www.googleapis.com/auth/gmail.readonly"],
        )
    except Exception as exc:
        raise RuntimeError("Impossible de charger les credentials depuis le token.") from exc

    # Construction du client Gmail avec timeout réseau de 10 s
    try:
        http = Http(timeout=10)
        service = build(
            "gmail",
            "v1",
            credentials=creds,
            http=http,
            cache_discovery=False,
        )
    except Exception as exc:
        raise RuntimeError("Échec de la création du service Gmail.") from exc

    # Récupération du dernier message de la boîte de réception
    try:
        response = (
            service.users()
            .messages()
            .list(userId="me", maxResults=1, labelIds=["INBOX"])
            .execute()
        )
    except HttpError as exc:
        raise RuntimeError(f"Erreur HTTP lors de la liste des messages : {exc.resp.status}") from exc
    except Exception as exc:
        raise RuntimeError("Erreur inattendue lors de la récupération de la liste des messages.") from exc

    messages: List[Dict[str, str]] = response.get("messages", [])
    if not messages:
        raise RuntimeError("Aucun email trouvé dans la boîte de réception.")

    message_id = messages[0]["id"]

    # Récupération du contenu complet du message
    try:
        msg = (
            service.users()
            .messages()
            .get(userId="me", id=message_id, format="full")
            .execute()
        )
    except HttpError as exc:
        raise RuntimeError(f"Erreur HTTP lors de la récupération du message {message_id}: {exc.resp.status}") from exc
    except Exception as exc:
        raise RuntimeError("Erreur inattendue lors de la récupération du message.") from exc

    # Extraction du sujet depuis les en‑têtes
    subject: str = ""
    headers: List[Dict[str, str]] = msg.get("payload", {}).get("headers", [])
    for header in headers:
        if header.get("name", "").lower() == "subject":
            subject = header.get("value", "")
            break

    # Extraction du corps texte (plain) – recherche récursive dans les parties
    def _extract_plain_text(payload: Dict) -> str:
        """Retourne le texte brut du payload ou d'une de ses sous‑parties.

        Args:
            payload: Le dictionnaire ``payload`` d'un message Gmail.

        Returns:
            Le texte décodé en UTF‑8 ou une chaîne vide si aucune partie texte
            n'est trouvée.
        """
        mime_type = payload.get("mimeType", "")
        if mime_type == "text/plain" and "data" in payload.get("body", {}):
            data = payload["body"]["data"]
            try:
                decoded_bytes = base64.urlsafe_b64decode(data.encode("ASCII"))
                return decoded_bytes.decode("utf-8", errors="replace")
            except Exception:
                return ""
        # Si le message est multipart, parcourir les sous‑parties
        for part in payload.get("parts", []):
            text = _extract_plain_text(part)
            if text:
                return text
        return ""

    body: str = _extract_plain_text(msg.get("payload", {}))

    return {"subject": subject, "body": body}
