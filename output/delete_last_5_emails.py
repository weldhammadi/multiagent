from output.get_gmail_service import get_gmail_service


def delete_last_5_emails() -> bool:
    """Supprime les 5 derniers emails Gmail.

    La fonction utilise le service Gmail déjà authentifié fourni par
    ``get_gmail_service``. Elle récupère les 5 derniers messages et les
    supprime un par un. En cas d'échec, une ``RuntimeError`` est levée.

    Returns:
        bool: ``True`` si les 5 suppressions ont réussi.
    """
    service = get_gmail_service()
    try:
        response = (
            service.users()
            .messages()
            .list(userId="me", maxResults=5)
            .execute()
        )
    except Exception as exc:
        raise RuntimeError(f"Erreur lors de la récupération des messages : {exc}") from exc

    messages = response.get("messages", [])
    if len(messages) < 5:
        raise RuntimeError("Moins de 5 messages trouvés dans la boîte de réception.")

    for message in messages:
        msg_id = message.get("id")
        if not msg_id:
            raise RuntimeError("Message sans identifiant récupéré.")
        try:
            (
                service.users()
                .messages()
                .delete(userId="me", id=msg_id)
                .execute()
            )
        except Exception as exc:
            raise RuntimeError(f"Erreur lors de la suppression du message {msg_id} : {exc}") from exc

    return True