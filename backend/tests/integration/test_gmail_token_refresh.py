#!/usr/bin/env python3
"""
Test Gmail token refresh to diagnose OAuth issues.
"""

import json
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_gmail_token_refresh():
    """Test Gmail OAuth token refresh."""
    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        
        # Load credentials
        config_dir = Path.home() / ".gmail-mcp"
        credentials_path = config_dir / "credentials.json"
        oauth_keys_path = config_dir / "gcp-oauth.keys.json"
        
        logger.info(f"Loading credentials from: {credentials_path}")
        
        # Load OAuth keys for client info
        with open(oauth_keys_path, 'r') as f:
            oauth_keys = json.load(f)
        
        client_id = oauth_keys['installed']['client_id']
        client_secret = oauth_keys['installed']['client_secret']
        
        logger.info(f"Credentials Before:{oauth_keys}")
        logger.info(f"Client ID:{client_id}")
        logger.info(f"Client Secret:{client_secret}")
        
        # Load and fix credentials
        with open(credentials_path, 'r') as f:
            creds_data = json.load(f)
        
        logger.info(f"Token expiry: {creds_data.get('expiry_date')}")
        logger.info(f"Has refresh token: {bool(creds_data.get('refresh_token'))}")
        
        # Add missing client info
        creds_data['client_id'] = client_id
        creds_data['client_secret'] = client_secret
        
        logger.info(f"Creds_Data After Adding{creds_data}:")
        logger.info(f"Client ID:{creds_data['client_id']}")
        logger.info(f"Client Secret:{creds_data['client_secret']}")
        
        # Create credentials object
        creds = Credentials.from_authorized_user_info(creds_data)
        
        logger.info(f"Credentials expired: {creds.expired}")
        logger.info(f"Has refresh token: {bool(creds.refresh_token)}")
        
        # Try to refresh if needed
        if creds.expired and creds.refresh_token:
            logger.info("🔄 Attempting to refresh expired token...")
            try:
                creds.refresh(Request())
                logger.info("✅ Token refresh successful!")
                
                # Save refreshed credentials
                refreshed_data = {
                    'access_token': creds.token,
                    'refresh_token': creds.refresh_token,
                    'token_type': 'Bearer',
                    'client_id': client_id,
                    'client_secret': client_secret,
                    'scope': ' '.join(creds.scopes) if creds.scopes else creds_data.get('scope', ''),
                    'expiry_date': int(creds.expiry.timestamp() * 1000) if creds.expiry else None
                }
                
                logger.info(f"After Refresh: {refreshed_data}:")
                

                with open(credentials_path, 'w') as f:
                    json.dump(refreshed_data, f, indent=2)
                
                logger.info(f"💾 Saved refreshed token with new expiry: {refreshed_data['expiry_date']}")
                
            except Exception as refresh_error:
                logger.error(f"❌ Token refresh failed: {refresh_error}")
                logger.error(f"Error type: {type(refresh_error).__name__}")
                return False
        
        logger.info(f"Final token valid: {creds.valid}")
        return creds.valid
        
    except ImportError as e:
        logger.error(f"❌ Missing Google API libraries: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Token refresh test failed: {e}")
        logger.error(f"Error type: {type(e).__name__}")
        return False

if __name__ == "__main__":
    success = test_gmail_token_refresh()
    if success:
        logger.info("🎉 Gmail token is now valid!")
    else:
        logger.error("💥 Gmail token refresh failed!")