import base64
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build


def send_html_email(subject: str, html_content: str):
    # Authenticate using environment secrets
    creds = Credentials(
        token=None,
        refresh_token=os.environ["GMAIL_REFRESH_TOKEN"],
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.environ["GMAIL_CLIENT_ID"],
        client_secret=os.environ["GMAIL_CLIENT_SECRET"],
        scopes=["https://www.googleapis.com/auth/gmail.send"]
    )

    service = build("gmail", "v1", credentials=creds)

    # Extract recipients
    sender = os.environ["GMAIL_SENDER"]
    recipients = os.environ["GMAIL_RECIPIENTS"].split(",")
    bcc_list = os.environ.get("GMAIL_BCC_RECIPIENTS", "").split(",") if "GMAIL_BCC_RECIPIENTS" in os.environ else []

    # Build email message
    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = sender
    message["To"] = ", ".join(recipients)
    if bcc_list:
        message["Bcc"] = ", ".join(bcc_list)

    message.attach(MIMEText(html_content, "html"))

    # Encode and send
    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
    body = {"raw": raw_message}
    result = service.users().messages().send(userId="me", body=body).execute()
    print("📧 Gmail response:", result["id"])
