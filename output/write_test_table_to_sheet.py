import os
from typing import Any, Dict, List

from googleapiclient.discovery import build
from output.get_gmail_service import get_gmail_service


def write_test_table_to_sheet() -> bool:
    """Write a static 3×2 table to a Google Sheet.

    The function reads the sheet identifier from the ``GOOGLE_SHEET_ID``
    environment variable, re‑uses the credentials embedded in the Gmail
    service returned by ``get_gmail_service`` and updates the range ``A1:B3``
    with a hard‑coded table.  It returns ``True`` on success or raises a
    ``RuntimeError`` on any failure.
    """
    sheet_id: str | None = os.getenv("GOOGLE_SHEET_ID")
    if not sheet_id:
        raise RuntimeError("Environment variable GOOGLE_SHEET_ID is missing")

    gmail_service = get_gmail_service()
    # The credentials are stored on the underlying HTTP object.
    try:
        creds = gmail_service._http.credentials  # type: ignore[attr-defined]
    except Exception as exc:
        raise RuntimeError("Unable to extract credentials from Gmail service") from exc
    if creds is None:
        raise RuntimeError("Credentials extracted from Gmail service are None")

    sheets_service = build("sheets", "v4", credentials=creds)

    values: List[List[Any]] = [
        ["Nom", "Age"],
        ["Alice", 22],
        ["Bob", 31],
    ]
    body: Dict[str, Any] = {"values": values}

    try:
        request = sheets_service.spreadsheets().values().update(
            spreadsheetId=sheet_id,
            range="A1:B3",
            valueInputOption="RAW",
            body=body,
        )
        response = request.execute()
    except Exception as exc:
        raise RuntimeError("Failed to write data to Google Sheet") from exc

    # The API returns a dict; a successful update contains 'updatedCells'.
    if not isinstance(response, dict) or response.get("updatedCells") is None:
        raise RuntimeError("Google Sheets API did not confirm the update")

    return True
