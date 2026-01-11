#!/usr/bin/env python3
"""
Manual Gmail Credentials Update Script

Use this if you want to manually update your Gmail OAuth credentials
without going through the full OAuth flow again.
"""

import json
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def update_gmail_credentials():
    """Manually update Gmail OAuth credentials."""
    
    config_dir = Path.home() / ".gmail-mcp"
    config_dir.mkdir(exist_ok=True)
    
    credentials_path = config_dir / "credentials.json"
    oauth_keys_path = config_dir / "gcp-oauth.keys.json"
    
    logger.info("🔧 Manual Gmail Credentials Update")
    logger.info(f"📁 Config directory: {config_dir}")
    
    print("\n" + "="*60)
    print("MANUAL CREDENTIALS UPDATE")
    print("="*60)
    print("Enter your new OAuth credentials from Google Cloud Console:")
    print()
    
    # Get OAuth client info
    client_id = input("OAuth Client ID: ").strip()
    client_secret = input("OAuth Client Secret: ").strip()
    
    if not client_id or not client_secret:
        logger.error("❌ Client ID and Client Secret are required!")
        return False
    
    print("\nIf you have existing access/refresh tokens, enter them:")
    print("(Leave blank if you don't have them - you'll need to run the full OAuth flow)")
    print()
    
    access_token = input("Access Token (optional): ").strip()
    refresh_token = input("Refresh Token (optional): ").strip()
    
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
    
    logger.info(f"✅ Updated OAuth keys: {oauth_keys_path}")
    
    # Create/update credentials file
    if access_token and refresh_token:
        creds_data = {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'token_type': 'Bearer',
            'client_id': client_id,
            'client_secret': client_secret,
            'scope': 'https://www.googleapis.com/auth/gmail.settings.basic https://www.googleapis.com/auth/gmail.modify https://www.googleapis.com/auth/gmail.settings.sharing https://www.googleapis.com/auth/gmail.compose https://www.googleapis.com/auth/gmail.send',
            'expiry_date': None  # Will be set when token is used
        }
        
        with open(credentials_path, 'w') as f:
            json.dump(creds_data, f, indent=2)
        
        logger.info(f"✅ Updated credentials: {credentials_path}")
        
        print("\n✅ Credentials updated successfully!")
        print("🧪 Run the test script to verify: python3 test_gmail_token_refresh.py")
        
    else:
        logger.info("⚠️  No access/refresh tokens provided.")
        print("\n⚠️  OAuth client updated, but no access tokens provided.")
        print("🔄 Run the full OAuth setup: python3 setup_gmail_oauth.py")
    
    return True

if __name__ == "__main__":
    print("🔧 Manual Gmail Credentials Update")
    print("="*40)
    
    try:
        update_gmail_credentials()
    except KeyboardInterrupt:
        print("\n❌ Update cancelled by user.")
    except Exception as e:
        logger.error(f"❌ Update failed: {e}")