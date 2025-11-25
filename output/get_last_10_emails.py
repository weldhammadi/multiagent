from typing import List, Dict
from output.get_gmail_service import get_gmail_service

def get_last_10_emails() -> List[Dict]:
    """Retrieve the 10 most recent Gmail messages with id, sender, and subject.

    Returns:
        List[Dict]: A list of dictionaries each containing "id", "from", and "subject" keys.
    """
    service = get_gmail_service()
    try:
        response = service.users().messages().list(userId="me", maxResults=10).execute()
    except Exception as exc:
        raise RuntimeError(f"Failed to list messages: {exc}") from exc

    messages = response.get("messages")
    if not messages:
        return []

    result: List[Dict] = []
    for msg in messages:
        msg_id = msg.get("id")
        if not msg_id:
            raise RuntimeError("Message without ID encountered.")
        try:
            msg_detail = (
                service.users()
                .messages()
                .get(
                    userId="me",
                    id=msg_id,
                    format="metadata",
                    metadataHeaders=["Subject", "From"],
                )
                .execute()
            )
        except Exception as exc:
            raise RuntimeError(f"Failed to get message {msg_id}: {exc}") from exc

        headers = msg_detail.get("payload", {}).get("headers", [])
        header_dict = {h["name"]: h["value"] for h in headers if "name" in h and "value" in h}
        result.append(
            {
                "id": msg_id,
                "from": header_dict.get("From", ""),
                "subject": header_dict.get("Subject", ""),
            }
        )
    return result