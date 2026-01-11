# gmail_auth.py

import json
import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
TOKEN_FILE = 'token.json'
CREDENTIALS_FILE = 'credentials.json'

def get_valid_credentials():
    """Get valid credentials, refreshing if necessary."""
    
    creds = None
    
    # Load existing token
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    
    # Check if token is expired and refresh if possible
    if creds and creds.expired and creds.refresh_token:
        print("🔄 Access token expired, refreshing...")
        try:
            creds.refresh(Request())
            print("✅ Token refreshed successfully")
            
            # Save the refreshed token
            with open(TOKEN_FILE, 'w') as token:
                token.write(creds.to_json())
            
            return creds
            
        except Exception as e:
            print(f"❌ Token refresh failed: {e}")
            print("   You need to re-authenticate")
            creds = None
    
    # If no valid credentials, need to authenticate
    if not creds or not creds.valid:
        if not os.path.exists(CREDENTIALS_FILE):
            raise FileNotFoundError(
                f"❌ {CREDENTIALS_FILE} not found. "
                f"Download from Google Cloud Console"
            )
        
        print("🔐 Starting OAuth flow...")
        flow = InstalledAppFlow.from_client_secrets_file(
            CREDENTIALS_FILE, SCOPES
        )
        creds = flow.run_local_server(port=0)
        
        # Save the credentials
        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())
        
        print("✅ Authentication successful")
    
    return creds