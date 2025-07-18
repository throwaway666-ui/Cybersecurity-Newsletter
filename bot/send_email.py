import base64
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build


def send_html_email(subject: str, html_content: str):
    # Load credentials from env vars
    creds = Credentials(
        token=None,
        refresh_token=os.environ["GMAIL_REFRESH_TOKEN"],
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.environ["GMAIL_CLIENT_ID"],
        client_secret=os.environ["GMAIL_CLIENT_SECRET"],
        scopes=["https://www.googleapis.com/auth/gmail.send"]
    )

    # Setup Gmail service
    service = build("gmail", "v1", credentials=creds)

    # Email parameters
    sender = os.environ["GMAIL_SENDER"]
    recipient = os.environ["GMAIL_RECIPIENT"]

    # Construct HTML email
    message = MIMEMultipart("alternative")
    message["To"] = recipient
    message["From"] = sender
    message["Subject"] = subject

    mime_text = MIMEText(html_content, "html")
    message.attach(mime_text)

    # Encode message
    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
    body = {"raw": raw_message}

    # Send email
    response = service.users().messages().send(userId="me", body=body).execute()
    print(f"📧 Gmail sent to {recipient} — Message ID: {response['id']}")
