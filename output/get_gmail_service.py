import os
import os
from dotenv import load_dotenv 
from typing import Any
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request

SCOPES = [
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/spreadsheets'
]


def get_gmail_service() -> Any:
    """Initialise et retourne un client Gmail authentifié."""
        # 👇 CHARGE LES VARIABLES DU .env
    load_dotenv()
    client_secret_path = os.getenv('GMAIL_CLIENT_SECRET')
    if not client_secret_path:
        raise RuntimeError('Environment variable GMAIL_CLIENT_SECRET is not set')
    if not os.path.isfile(client_secret_path):
        raise RuntimeError(f'Client secret file not found: {client_secret_path}')
    token_path = 'token.json'
    creds = None
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e:
                raise RuntimeError(f'Failed to refresh credentials: {e}')
        else:
            flow = InstalledAppFlow.from_client_secrets_file(client_secret_path, SCOPES)
            try:
                creds = flow.run_local_server(port=0)
            except Exception as e:
                raise RuntimeError(f'Failed to complete OAuth flow: {e}')
        try:
            with open(token_path, 'w') as token_file:
                token_file.write(creds.to_json())
        except Exception as e:
            raise RuntimeError(f'Failed to write token file: {e}')
    try:
        service = build('gmail', 'v1', credentials=creds)
    except Exception as e:
        raise RuntimeError(f'Failed to build Gmail service: {e}')
    return service