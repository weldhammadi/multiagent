import os
from typing import List
from googleapiclient.discovery import build
from output.get_gmail_service import get_gmail_service


def write_last_30_gmail_subjects_to_sheet() -> bool:
    """Récupère les 30 derniers objets Gmail et les écrit dans Google Sheets.

    La fonction utilise le service Gmail déjà authentifié fourni par
    ``get_gmail_service`` et écrit les sujets dans la colonne A du tableau
    identifié par la variable d'environnement ``GOOGLE_SHEET_ID``.

    Returns:
        bool: ``True`` si l'opération s'est déroulée sans erreur.
    """
    # Vérification de la variable d'environnement
    sheet_id: str | None = os.getenv("GOOGLE_SHEET_ID")
    if sheet_id is None:
        raise RuntimeError("La variable d'environnement GOOGLE_SHEET_ID est manquante.")

    # Récupération du service Gmail déjà authentifié
    gmail_service = get_gmail_service()
    # Extraction des credentials du service Gmail
    creds = getattr(gmail_service._http, "credentials", None)
    if creds is None:
        raise RuntimeError("Impossible de récupérer les credentials du service Gmail.")

    # Construction du service Sheets avec les mêmes credentials
    sheets_service = build("sheets", "v4", credentials=creds)

    # Récupération des 30 derniers messages de la boîte de réception
    try:
        messages_response = gmail_service.users().messages().list(
            userId="me",
            maxResults=30,
            labelIds=["INBOX"],
            q=None
        ).execute()
    except Exception as e:
        raise RuntimeError(f"Erreur lors de la récupération des messages Gmail: {e}")

    messages = messages_response.get("messages", [])
    subjects: List[str] = []

    for msg in messages:
        msg_id = msg.get("id")
        if not msg_id:
            continue
        try:
            msg_detail = gmail_service.users().messages().get(
                userId="me",
                id=msg_id,
                format="metadata",
                metadataHeaders=["Subject"]
            ).execute()
        except Exception as e:
            raise RuntimeError(f"Erreur lors de la lecture du message {msg_id}: {e}")

        headers = msg_detail.get("payload", {}).get("headers", [])
        subject = "Sans objet"
        for header in headers:
            if header.get("name", "").lower() == "subject":
                subject = header.get("value", "Sans objet") or "Sans objet"
                break
        subjects.append(subject)

    # Compléter la liste jusqu'à 30 éléments avec des chaînes vides
    while len(subjects) < 30:
        subjects.append("")

    # Préparer les valeurs au format attendu par l'API Sheets
    values = [[s] for s in subjects]

    # Mise à jour de la plage A1:A30
    try:
        sheets_service.spreadsheets().values().update(
            spreadsheetId=sheet_id,
            range="A1:A30",
            valueInputOption="RAW",
            body={"values": values}
        ).execute()
    except Exception as e:
        raise RuntimeError(f"Erreur lors de l'écriture dans Google Sheets: {e}")

    return True
