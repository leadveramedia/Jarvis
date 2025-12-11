#!/usr/bin/env python3
"""
One-time OAuth setup script for Gmail API.

Run this locally to generate token.json:
    python setup_oauth.py

After running, copy the contents of token.json to your GitHub secret GMAIL_TOKEN_JSON
"""

import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

# Gmail API scope - allows reading and modifying emails (marking as read)
SCOPES = ['https://www.googleapis.com/auth/gmail.modify']

def main():
    creds = None

    # Check if token.json already exists
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        print("Found existing token.json")

    # If no valid credentials, run the OAuth flow
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("Refreshing expired token...")
            creds.refresh(Request())
        else:
            if not os.path.exists('credentials.json'):
                print("ERROR: credentials.json not found!")
                print("Download it from Google Cloud Console:")
                print("  1. Go to https://console.cloud.google.com")
                print("  2. APIs & Services -> Credentials")
                print("  3. Download your OAuth 2.0 Client ID")
                return

            print("Starting OAuth flow...")
            print("A browser window will open for you to log in to Google.")

            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)

        # Save the credentials for future use
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
        print("Token saved to token.json")

    print("\n" + "="*50)
    print("SUCCESS! OAuth setup complete.")
    print("="*50)
    print("\nNext steps:")
    print("1. Copy the contents of 'credentials.json' to GitHub secret: GMAIL_CREDENTIALS_JSON")
    print("2. Copy the contents of 'token.json' to GitHub secret: GMAIL_TOKEN_JSON")
    print("\nYou can now run 'python src/main.py' to test locally.")

if __name__ == '__main__':
    main()
