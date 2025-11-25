import os
from typing import Any
from googleapiclient.discovery import build
from output.get_gmail_service import get_gmail_service

def write_test_table_to_sheet() -> bool:
    """Write a predefined 2‑column table to range A1:B3 of a Google Sheet.

    Returns:
        bool: True if the update succeeded.

    Raises:
        RuntimeError: If the sheet ID is missing or the API call fails.
    """
    sheet_id = os.getenv("GOOGLE_SHEET_ID")
    if not sheet_id:
        raise RuntimeError("Environment variable GOOGLE_SHEET_ID is not set")

    try:
        gmail_service = get_gmail_service()
        creds = gmail_service._http.credentials  # type: ignore[attr-defined]

        sheets_service = build("sheets", "v4", credentials=creds)

        values = [
            ["Nom", "Age"],
            ["Alice", 22],
            ["Bob", 31],
        ]
        body = {"values": values}

        request = sheets_service.spreadsheets().values().update(
            spreadsheetId=sheet_id,
            range="A1:B3",
            valueInputOption="RAW",
            body=body,
        )
        response = request.execute()
        if not response or response.get("updatedCells", 0) == 0:
            raise RuntimeError("No cells were updated")
        return True
    except Exception as exc:
        raise RuntimeError(str(exc)) from exc
