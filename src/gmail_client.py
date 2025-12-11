"""
Gmail API client for fetching and managing emails.
"""

import base64
import os
from email.mime.text import MIMEText
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/gmail.modify']


class GmailClient:
    def __init__(self, credentials_path='credentials.json', token_path='token.json'):
        """Initialize Gmail client with OAuth credentials."""
        self.service = self._authenticate(credentials_path, token_path)

    def _authenticate(self, credentials_path, token_path):
        """Authenticate with Gmail API using stored credentials."""
        creds = None

        if os.path.exists(token_path):
            creds = Credentials.from_authorized_user_file(token_path, SCOPES)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
                # Save refreshed token
                with open(token_path, 'w') as token:
                    token.write(creds.to_json())
            else:
                raise Exception(
                    "No valid credentials found. Run setup_oauth.py first."
                )

        return build('gmail', 'v1', credentials=creds)

    def get_unread_emails(self, max_results=10):
        """
        Fetch unread emails from inbox.

        Returns:
            List of email dictionaries with 'id', 'subject', 'sender', 'body'
        """
        emails = []

        # Search for unread messages
        results = self.service.users().messages().list(
            userId='me',
            q='is:unread',
            maxResults=max_results
        ).execute()

        messages = results.get('messages', [])

        for msg in messages:
            email_data = self._get_email_details(msg['id'])
            if email_data:
                emails.append(email_data)

        return emails

    def _get_email_details(self, msg_id):
        """Extract details from a single email message."""
        try:
            msg = self.service.users().messages().get(
                userId='me',
                id=msg_id,
                format='full'
            ).execute()

            headers = msg['payload']['headers']

            # Extract headers
            subject = ''
            sender = ''
            for header in headers:
                if header['name'].lower() == 'subject':
                    subject = header['value']
                elif header['name'].lower() == 'from':
                    sender = header['value']

            # Extract body
            body = self._extract_body(msg['payload'])

            return {
                'id': msg_id,
                'subject': subject,
                'sender': sender,
                'body': body,
                'snippet': msg.get('snippet', '')
            }
        except Exception as e:
            print(f"Error fetching email {msg_id}: {e}")
            return None

    def _extract_body(self, payload):
        """Extract plain text body from email payload."""
        body = ''

        if 'body' in payload and payload['body'].get('data'):
            body = base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8')
        elif 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    if 'data' in part['body']:
                        body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                        break
                elif part['mimeType'] == 'multipart/alternative':
                    # Recursively check nested parts
                    body = self._extract_body(part)
                    if body:
                        break

        # Truncate very long bodies to avoid token limits
        max_length = 3000
        if len(body) > max_length:
            body = body[:max_length] + "...[truncated]"

        return body

    def mark_as_read(self, msg_id):
        """Mark an email as read by removing UNREAD label."""
        try:
            self.service.users().messages().modify(
                userId='me',
                id=msg_id,
                body={'removeLabelIds': ['UNREAD']}
            ).execute()
            return True
        except Exception as e:
            print(f"Error marking email {msg_id} as read: {e}")
            return False
