#!/usr/bin/env python3
"""
Test Gmail Real Data Search
Test searching for real Gmail data with subject containing "Invoice INV-1001"
"""

import asyncio
import logging
import sys
import os
from pathlib import Path

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.gmail_mcp_service import get_gmail_service
from app.agents.gmail_agent_node import GmailAgentNode

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_gmail_search_real():
    """Test searching for real Gmail data."""
    print("\\n" + "="*60)
    print("Testing Gmail Real Data Search")
    print("="*60)
    
    try:
        gmail_service = get_gmail_service()
        print("✅ Gmail service initialized")
        
        # Test search for specific invoice
        search_query = "subject:Invoice INV-1001"
        print(f"\\n🔍 Searching for: {search_query}")
        
        result = await gmail_service.search_messages(search_query, max_results=5)
        print(f"\\n📧 Search result:")
        print(result)
        
        # Also test with a broader search
        broad_search = "subject:Invoice"
        print(f"\\n🔍 Broader search for: {broad_search}")
        
        broad_result = await gmail_service.search_messages(broad_search, max_results=3)
        print(f"\\n📧 Broad search result:")
        print(broad_result)
        
        return True
        
    except Exception as e:
        print(f"❌ Gmail search test failed: {e}")
        return False

async def test_gmail_agent_search():
    """Test Gmail agent search functionality."""
    print("\\n" + "="*60)
    print("Testing Gmail Agent Search")
    print("="*60)
    
    try:
        gmail_agent = GmailAgentNode()
        print("✅ Gmail agent initialized")
        
        # Test agent search
        state = {
            "task": "search for emails containing Invoice INV-1001",
            "user_request": "find emails with subject Invoice INV-1001",
            "messages": []
        }
        
        result = await gmail_agent.process(state)
        
        print(f"\\n📧 Agent search result:")
        print(f"Gmail result: {result.get('gmail_result', 'No result')}")
        print(f"Last agent: {result.get('last_agent')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Gmail agent search test failed: {e}")
        return False

async def test_oauth_status():
    """Check OAuth authentication status."""
    print("\\n" + "="*60)
    print("Checking OAuth Authentication Status")
    print("="*60)
    
    try:
        # Check OAuth files
        config_dir = Path.home() / ".gmail-mcp"
        oauth_keys_path = config_dir / "gcp-oauth.keys.json"
        credentials_path = config_dir / "credentials.json"
        
        print(f"📁 Config directory: {config_dir}")
        print(f"🔑 OAuth keys exist: {oauth_keys_path.exists()}")
        print(f"🎫 Credentials exist: {credentials_path.exists()}")
        
        if credentials_path.exists():
            import json
            with open(credentials_path, 'r') as f:
                creds = json.load(f)
            
            has_refresh_token = "refresh_token" in creds
            has_access_token = "access_token" in creds
            
            print(f"🔄 Has refresh token: {has_refresh_token}")
            print(f"🎟️  Has access token: {has_access_token}")
            
            if has_refresh_token:
                print("✅ OAuth authentication appears to be configured")
                return True
            else:
                print("⚠️  OAuth authentication may need to be completed")
                return False
        else:
            print("❌ No credentials file found - OAuth authentication needed")
            return False
            
    except Exception as e:
        print(f"❌ OAuth status check failed: {e}")
        return False

async def test_direct_mcp_call():
    """Test direct MCP server call to bypass port issues."""
    print("\\n" + "="*60)
    print("Testing Direct MCP Server Call")
    print("="*60)
    
    try:
        gmail_service = get_gmail_service()
        
        # Try a simple profile call first
        print("\\n👤 Testing profile access...")
        profile_result = await gmail_service.get_profile()
        print(f"Profile result: {profile_result[:300]}...")
        
        # Try list messages
        print("\\n📧 Testing message listing...")
        messages_result = await gmail_service.list_messages(max_results=3)
        print(f"Messages result: {messages_result[:300]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Direct MCP call test failed: {e}")
        return False

async def main():
    """Run all Gmail real data tests."""
    print("Gmail Real Data Search Test Suite")
    print("="*70)
    
    results = []
    
    # Check OAuth status first
    oauth_ok = await test_oauth_status()
    results.append(("OAuth Status", oauth_ok))
    
    # Test direct MCP calls
    mcp_ok = await test_direct_mcp_call()
    results.append(("Direct MCP Call", mcp_ok))
    
    # Test Gmail search
    search_ok = await test_gmail_search_real()
    results.append(("Gmail Search", search_ok))
    
    # Test Gmail agent search
    agent_ok = await test_gmail_agent_search()
    results.append(("Gmail Agent Search", agent_ok))
    
    # Print summary
    print("\\n" + "="*70)
    print("Real Data Test Results Summary")
    print("="*70)
    
    all_passed = True
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name:20} {status}")
        if not passed:
            all_passed = False
    
    print("="*70)
    if all_passed:
        print("🎉 All real data tests passed!")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        
        if not oauth_ok:
            print("\\n💡 OAuth authentication may need to be completed:")
            print("   Run: python3 backend/setup_gmail_oauth.py")
            print("   Complete the browser authentication flow")
    
    return all_passed

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\\n⚠️  Test interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)