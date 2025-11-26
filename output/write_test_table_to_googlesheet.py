import os
from typing import Any, Dict, List

from googleapiclient.discovery import build
from output.get_gmail_service import get_gmail_service

def write_test_table_to_googlesheet() -> bool:
    """Write a predefined test table to a Google Sheet.

    The function reads the spreadsheet ID from the ``GOOGLE_SHEET_ID`` environment
    variable, obtains the already‑authenticated Gmail service, extracts its
    credentials, builds a Sheets service and writes the table to the range
    ``A1:B3`` using ``valueInputOption="RAW"``. It overwrites any existing data
    in that range.

    Returns:
        bool: ``True`` if the update succeeded.

    Raises:
        RuntimeError: If the environment variable is missing, the update fails,
            or an unexpected response is received.
    """
    sheet_id: str | None = os.getenv("GOOGLE_SHEET_ID")
    if sheet_id is None:
        raise RuntimeError("La variable d'environnement GOOGLE_SHEET_ID est manquante.")

    gmail_service = get_gmail_service()
    creds = gmail_service._http.credentials  # type: ignore[attr-defined]

    sheets_service = build("sheets", "v4", credentials=creds)

    values: List[List[Any]] = [
        ["Nom", "Age"],
        ["Alice", 22],
        ["Bob", 31],
    ]

    body: Dict[str, Any] = {"values": values}

    try:
        result = (
            sheets_service.spreadsheets()
            .values()
            .update(
                spreadsheetId=sheet_id,
                range="A1:B3",
                valueInputOption="RAW",
                body=body,
            )
            .execute()
        )
    except Exception as exc:
        raise RuntimeError(f"Erreur lors de l'écriture dans Google Sheet: {exc}") from exc

    if not isinstance(result, dict) or result.get("updatedCells", 0) == 0:
        raise RuntimeError("L'écriture dans Google Sheet a échoué ou n'a mis à jour aucune cellule.")

    return True