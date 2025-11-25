from __future__ import annotations

import os
from typing import List

from googleapiclient.errors import HttpError
from output.get_gmail_service import get_gmail_service

def get_last_3_subjects() -> List[str]:
    """Return the Subject header of the three most recent Gmail messages.

    The function relies on an already‑authenticated Gmail service obtained via
    ``get_gmail_service()``. It fetches up to three messages, extracts the
    ``Subject`` header from each, and returns a list of three strings (empty
    strings are used when a subject cannot be retrieved).

    Raises:
        RuntimeError: If the Gmail API call fails or the response format is
            unexpected.
    """
    try:
        service = get_gmail_service()
        # Retrieve up to three message IDs (most recent first).
        list_response = service.users().messages().list(userId="me", maxResults=3).execute()
        messages = list_response.get("messages", [])
        subjects: List[str] = []
        for msg_meta in messages:
            msg_id = msg_meta.get("id")
            if not msg_id:
                subjects.append("")
                continue
            msg = (
                service.users()
                .messages()
                .get(userId="me", id=msg_id, format="metadata", metadataHeaders=["Subject"])
                .execute()
            )
            # The metadata payload contains a list of headers.
            headers = msg.get("payload", {}).get("headers", [])
            subject = ""
            for header in headers:
                if header.get("name", "").lower() == "subject":
                    subject = header.get("value", "")
                    break
            subjects.append(subject)
        # Ensure exactly three entries.
        while len(subjects) < 3:
            subjects.append("")
        return subjects[:3]
    except HttpError as e:
        raise RuntimeError(f"Gmail API error: {e}") from e
    except Exception as e:
        raise RuntimeError(f"Unexpected error while retrieving subjects: {e}") from e
