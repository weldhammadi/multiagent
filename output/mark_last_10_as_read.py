from __future__ import annotations

import os
from typing import List

from googleapiclient.errors import HttpError
from output.get_gmail_service import get_gmail_service

def mark_last_10_as_read() -> bool:
    """Mark the last 10 unread Gmail messages as read.

    Returns:
        bool: ``True`` if the operation succeeds.

    Raises:
        RuntimeError: If the Gmail API call fails or a message ID is missing.
    """
    service = get_gmail_service()
    try:
        # Retrieve up to 10 unread messages.
        result = service.users().messages().list(userId="me", maxResults=10, q="is:unread").execute()
        messages = result.get("messages", [])
        if not messages:
            return True
        # Ensure every message has an ID.
        message_ids: List[str] = []
        for msg in messages:
            msg_id = msg.get("id")
            if not msg_id:
                raise RuntimeError("Missing message ID in Gmail response.")
            message_ids.append(msg_id)
        # Batch modify to remove the UNREAD label.
        batch = service.new_batch_http_request()
        for msg_id in message_ids:
            batch.add(
                service.users()
                .messages()
                .modify(
                    userId="me",
                    id=msg_id,
                    body={"removeLabelIds": ["UNREAD"], "addLabelIds": []},
                )
            )
        batch.execute()
        return True
    except HttpError as err:
        raise RuntimeError(f"Gmail API error: {err}")
    except Exception as exc:
        raise RuntimeError(f"Unexpected error: {exc}")
