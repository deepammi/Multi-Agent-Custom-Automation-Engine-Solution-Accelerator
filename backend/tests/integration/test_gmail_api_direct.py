#!/usr/bin/env python3
"""
Direct Gmail API Test
Test Gmail API directly using Google's Python client library
"""

import asyncio
import json
import sys
import os
from pathlib import Path

async def test_gmail_api_direct():
    """Test Gmail API directly."""
    print("Direct Gmail API Test")
    print("=" * 25)
    
    try:
        # Import Google API libraries
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build
        
        print("✅ Google API libraries imported")
        
        # Check for credentials
        config_dir = Path.home() / ".gmail-mcp"
        credentials_path = config_dir / "credentials.json"
        
        if not credentials_path.exists():
            print("❌ No credentials file found")
            return False
        
        print("✅ Credentials file found")
        
        # Load OAuth keys for client info
        oauth_keys_path = config_dir / "gcp-oauth.keys.json"
        if not oauth_keys_path.exists():
            print("❌ No OAuth keys file found")
            return False
        
        with open(oauth_keys_path, 'r') as f:
            oauth_keys = json.load(f)
        
        client_id = oauth_keys['installed']['client_id']
        client_secret = oauth_keys['installed']['client_secret']
        
        # Load and fix credentials
        with open(credentials_path, 'r') as f:
            creds_data = json.load(f)
        
        # Add missing client info
        creds_data['client_id'] = client_id
        creds_data['client_secret'] = client_secret
        
        # Create credentials object
        creds = Credentials.from_authorized_user_info(creds_data)
        
        # Refresh if needed
        if creds.expired and creds.refresh_token:
            print("🔄 Refreshing credentials...")
            creds.refresh(Request())
        
        if not creds.valid:
            print("❌ Invalid credentials")
            return False
        
        print("✅ Credentials are valid")
        
        # Build Gmail service
        service = build('gmail', 'v1', credentials=creds)
        print("✅ Gmail service built")
        
        # Test 1: Get profile
        print("\\n👤 Testing profile access...")
        profile = service.users().getProfile(userId='me').execute()
        print(f"✅ Profile: {profile.get('emailAddress', 'N/A')}")
        
        # Test 2: List recent messages
        print("\\n📧 Testing message listing...")
        results = service.users().messages().list(userId='me', maxResults=5).execute()
        messages = results.get('messages', [])
        print(f"✅ Found {len(messages)} recent messages")
        
        # Test 3: Search for invoice emails
        print("\\n🔍 Searching for invoice emails...")
        search_results = service.users().messages().list(
            userId='me', 
            q='subject:Invoice',
            maxResults=5
        ).execute()
        
        invoice_messages = search_results.get('messages', [])
        print(f"✅ Found {len(invoice_messages)} invoice messages")
        
        # Test 4: Search for specific invoice
        print("\\n🎯 Searching for 'Invoice INV-1001'...")
        specific_search = service.users().messages().list(
            userId='me',
            q='subject:"Invoice INV-1001"',
            maxResults=3
        ).execute()
        
        specific_messages = specific_search.get('messages', [])
        print(f"✅ Found {len(specific_messages)} messages with 'Invoice INV-1001'")
        
        # Get details of first message if found
        if specific_messages:
            msg_id = specific_messages[0]['id']
            print(f"\\n📄 Getting details for message {msg_id}...")
            
            message = service.users().messages().get(
                userId='me',
                id=msg_id,
                format='full'
            ).execute()
            
            # Extract subject and sender
            headers = message['payload'].get('headers', [])
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No subject')
            sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown sender')
            
            print(f"✅ Subject: {subject}")
            print(f"✅ From: {sender}")
            print(f"✅ Snippet: {message.get('snippet', 'No snippet')[:100]}...")
        
        return True
        
    except ImportError as e:
        print(f"❌ Missing Google API libraries: {e}")
        print("💡 Install with: pip install google-auth google-auth-oauthlib google-api-python-client")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

async def main():
    """Run the direct Gmail API test."""
    success = await test_gmail_api_direct()
    
    print("\\n" + "=" * 25)
    if success:
        print("🎉 Direct Gmail API access is working!")
        print("📧 You can search for real Gmail data")
    else:
        print("⚠️  Direct Gmail API test failed")
    
    return success

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\\n⚠️  Test interrupted")
        sys.exit(1)