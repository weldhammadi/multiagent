import base64
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any, Dict

from output.get_gmail_service import get_gmail_service

def _encode_message(message: MIMEMultipart) -> str:
    """Encode a MIME message to a URL‑safe base64 string.

    Args:
        message: The MIME message to encode.

    Returns:
        A base64 URL‑safe encoded string ready for the Gmail API.
    """
    raw_bytes: bytes = message.as_bytes()
    return base64.urlsafe_b64encode(raw_bytes).decode()

def send_reminder_email() -> bool:
    """Send a reminder email via Gmail API.

    Returns:
        True if the email was sent successfully.

    Raises:
        RuntimeError: If the Gmail API call fails or no message ID is returned.
    """
    service = get_gmail_service()

    mime_msg = MIMEMultipart()
    mime_msg["From"] = "me"
    mime_msg["To"] = "hendellynamaria@gmail.com"
    mime_msg["Subject"] = "Rappel automatique"
    body_text = "Ceci est un rappel automatique envoyé par un agent autonome."
    mime_msg.attach(MIMEText(body_text, "plain"))

    raw_message: str = _encode_message(mime_msg)

    try:
        result: Dict[str, Any] = (
            service.users()
            .messages()
            .send(userId="me", body={"raw": raw_message})
            .execute()
        )
    except Exception as exc:
        raise RuntimeError("Failed to send reminder email via Gmail API") from exc

    if not result or "id" not in result:
        raise RuntimeError("Email sent but no message ID was returned")

    return True