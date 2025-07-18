import base64
from email.mime.text import MIMEText
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import os

def send_html_email(subject: str, html_content: str):
    creds = Credentials(
        token=None,
        refresh_token=os.environ["GMAIL_REFRESH_TOKEN"],
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.environ["GMAIL_CLIENT_ID"],
        client_secret=os.environ["GMAIL_CLIENT_SECRET"],
        scopes=["https://www.googleapis.com/auth/gmail.send"]
    )

    service = build("gmail", "v1", credentials=creds)
    message = MIMEText(html_content, "html")
    message["to"] = os.environ["GMAIL_TO"]
    message["from"] = os.environ["GMAIL_FROM"]
    message["subject"] = subject

    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    body = {"raw": raw}
    result = service.users().messages().send(userId="me", body=body).execute()
    print("📧 Gmail response:", result["id"])
