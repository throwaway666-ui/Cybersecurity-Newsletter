import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import os

def send_html_email(subject: str, html_content: str):
    # Setup credentials from environment variables
    creds = Credentials(
        token=None,
        refresh_token=os.environ["GMAIL_REFRESH_TOKEN"],
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.environ["GMAIL_CLIENT_ID"],
        client_secret=os.environ["GMAIL_CLIENT_SECRET"],
        scopes=["https://www.googleapis.com/auth/gmail.send"]
    )

    # Initialize Gmail API
    service = build("gmail", "v1", credentials=creds)

    sender = os.environ["GMAIL_SENDER"]
    bcc_recipients = [
        email.strip()
        for email in os.environ["GMAIL_RECIPIENTS"].split(",")
        if email.strip()
    ]

    # Create a MIME email message
    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = sender
    message["To"] = sender  # visible 'To:' line
    message["Bcc"] = ", ".join(bcc_recipients)  # actual recipients hidden

    # Attach the HTML content
    part_html = MIMEText(html_content, "html")
    message.attach(part_html)

    # Encode and send
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    body = {"raw": raw}
    result = service.users().messages().send(userId="me", body=body).execute()
    print("📧 Gmail response:", result["id"])
