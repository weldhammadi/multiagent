import os
import requests
from typing import List, Dict


def get_last_50_gmail_emails() -> List[Dict[str, str]]:
    """Retrieve the 50 most recent Gmail messages for the authenticated user.

    Args:
        None

    Returns:
        List[Dict[str, str]]: A list where each element is a dictionary containing
        the keys ``id``, ``from``, ``subject`` and ``snippet`` of an email.

    Raises:
        RuntimeError: If environment variables are missing, the HTTP request fails,
        or the response cannot be parsed.
    """
    api_key: str | None = os.getenv("GMAIL_API_KEY")
    oauth_token: str | None = os.getenv("GMAIL_OAUTH_TOKEN")
    if not api_key or not oauth_token:
        raise RuntimeError("Missing GMAIL_API_KEY or GMAIL_OAUTH_TOKEN environment variables.")

    base_url: str = "https://gmail.googleapis.com/gmail/v1/users/me/messages"
    headers: Dict[str, str] = {"Authorization": f"Bearer {oauth_token}"}
    params: Dict[str, str] = {"maxResults": "50", "key": api_key}

    try:
        response = requests.get(base_url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
    except Exception as exc:
        raise RuntimeError(f"Failed to fetch message list: {exc}") from exc

    try:
        messages = response.json().get("messages", [])
    except Exception as exc:
        raise RuntimeError(f"Invalid JSON response when fetching messages: {exc}") from exc

    emails: List[Dict[str, str]] = []
    for msg in messages:
        msg_id: str = msg.get("id")
        if not msg_id:
            continue
        detail_url: str = f"{base_url}/{msg_id}"
        detail_params: Dict[str, str] = {"format": "metadata", "metadataHeaders": "From", "metadataHeaders": "Subject", "key": api_key}
        try:
            detail_resp = requests.get(detail_url, headers=headers, params=detail_params, timeout=10)
            detail_resp.raise_for_status()
        except Exception as exc:
            raise RuntimeError(f"Failed to fetch details for message {msg_id}: {exc}") from exc
        try:
            detail_json = detail_resp.json()
            headers_list = detail_json.get("payload", {}).get("headers", [])
            header_dict = {h["name"].lower(): h["value"] for h in headers_list if "name" in h and "value" in h}
            email_dict: Dict[str, str] = {
                "id": msg_id,
                "from": header_dict.get("from", ""),
                "subject": header_dict.get("subject", ""),
                "snippet": detail_json.get("snippet", ""),
            }
            emails.append(email_dict)
        except Exception as exc:
            raise RuntimeError(f"Failed to parse details for message {msg_id}: {exc}") from exc

    return emails
