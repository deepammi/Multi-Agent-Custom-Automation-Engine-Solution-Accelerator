#!/usr/bin/env python3
"""
Gmail OAuth Setup Script

This script helps you set up new Gmail OAuth credentials for the MCP server.
Run this after creating a new OAuth client in Google Cloud Console.
"""

import json
import os
import logging
from pathlib import Path
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Gmail API scopes
SCOPES = [
    'https://www.googleapis.com/auth/gmail.settings.basic',
    'https://www.googleapis.com/auth/gmail.modify', 
    'https://www.googleapis.com/auth/gmail.settings.sharing',
    'https://www.googleapis.com/auth/gmail.compose',
    'https://www.googleapis.com/auth/gmail.send'
]

def setup_gmail_oauth():
    """Set up Gmail OAuth credentials."""
    
    # Create config directory
    config_dir = Path.home() / ".gmail-mcp"
    config_dir.mkdir(exist_ok=True)
    
    credentials_path = config_dir / "credentials.json"
    oauth_keys_path = config_dir / "gcp-oauth.keys.json"
    
    logger.info("🔧 Gmail OAuth Setup")
    logger.info(f"📁 Config directory: {config_dir}")
    
    # Step 1: Get OAuth client credentials
    print("\n" + "="*60)
    print("STEP 1: OAuth Client Credentials")
    print("="*60)
    print("You need to provide your new OAuth client credentials from Google Cloud Console.")
    print("These should be from the 'credentials.json' file you downloaded.")
    print()
    
    client_id = input("Enter your OAuth Client ID: ").strip()
    client_secret = input("Enter your OAuth Client Secret: ").strip()
    
    if not client_id or not client_secret:
        logger.error("❌ Client ID and Client Secret are required!")
        return False
    
    # Create OAuth keys file
    oauth_keys = {
        "installed": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "redirect_uris": ["http://localhost"]
        }
    }
    
    with open(oauth_keys_path, 'w') as f:
        json.dump(oauth_keys, f, indent=2)
    
    logger.info(f"✅ Saved OAuth keys to: {oauth_keys_path}")
    
    # Step 2: Perform OAuth flow
    print("\n" + "="*60)
    print("STEP 2: OAuth Authorization Flow")
    print("="*60)
    print("This will open your browser for Gmail authorization...")
    print()
    
    try:
        # Create OAuth flow
        flow = InstalledAppFlow.from_client_secrets_file(
            str(oauth_keys_path), 
            SCOPES
        )
        
        # Run local server flow
        creds = flow.run_local_server(port=0)
        
        # Save credentials
        creds_data = {
            'access_token': creds.token,
            'refresh_token': creds.refresh_token,
            'token_type': 'Bearer',
            'client_id': client_id,
            'client_secret': client_secret,
            'scope': ' '.join(SCOPES),
            'expiry_date': int(creds.expiry.timestamp() * 1000) if creds.expiry else None
        }
        
        with open(credentials_path, 'w') as f:
            json.dump(creds_data, f, indent=2)
        
        logger.info(f"✅ Saved credentials to: {credentials_path}")
        
        # Step 3: Test the credentials
        print("\n" + "="*60)
        print("STEP 3: Testing Credentials")
        print("="*60)
        
        from googleapiclient.discovery import build
        
        service = build('gmail', 'v1', credentials=creds)
        profile = service.users().getProfile(userId='me').execute()
        
        logger.info(f"✅ Gmail API test successful!")
        logger.info(f"📧 Email: {profile.get('emailAddress')}")
        logger.info(f"📬 Total messages: {profile.get('messagesTotal')}")
        
        print("\n" + "="*60)
        print("🎉 SETUP COMPLETE!")
        print("="*60)
        print(f"✅ OAuth keys saved to: {oauth_keys_path}")
        print(f"✅ Credentials saved to: {credentials_path}")
        print(f"✅ Gmail API access verified")
        print(f"📧 Authorized email: {profile.get('emailAddress')}")
        print()
        print("You can now run Gmail MCP server and agents!")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ OAuth setup failed: {e}")
        logger.error(f"Error type: {type(e).__name__}")
        
        # Clean up partial files
        if oauth_keys_path.exists():
            oauth_keys_path.unlink()
        if credentials_path.exists():
            credentials_path.unlink()
            
        return False

def check_existing_credentials():
    """Check if credentials already exist."""
    config_dir = Path.home() / ".gmail-mcp"
    credentials_path = config_dir / "credentials.json"
    oauth_keys_path = config_dir / "gcp-oauth.keys.json"
    
    if credentials_path.exists() and oauth_keys_path.exists():
        print("\n⚠️  Existing Gmail credentials found!")
        print(f"📁 Location: {config_dir}")
        
        overwrite = input("Do you want to overwrite them? (y/N): ").strip().lower()
        return overwrite in ['y', 'yes']
    
    return True

if __name__ == "__main__":
    print("🚀 Gmail OAuth Setup for MCP Server")
    print("="*50)
    
    if not check_existing_credentials():
        print("❌ Setup cancelled.")
        exit(0)
    
    try:
        success = setup_gmail_oauth()
        if success:
            print("\n🎉 Setup completed successfully!")
            exit(0)
        else:
            print("\n💥 Setup failed!")
            exit(1)
            
    except KeyboardInterrupt:
        print("\n❌ Setup cancelled by user.")
        exit(1)
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        exit(1)