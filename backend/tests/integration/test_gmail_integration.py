#!/usr/bin/env python3
"""
Test Gmail MCP Integration
Simple test to verify Gmail MCP service and agent integration
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

async def test_gmail_service():
    """Test Gmail MCP service wrapper."""
    print("\\n" + "="*50)
    print("Testing Gmail MCP Service")
    print("="*50)
    
    try:
        gmail_service = get_gmail_service()
        print("✅ Gmail service initialized")
        
        # Test getting profile (basic connectivity test)
        print("\\n📋 Testing Gmail profile access...")
        profile_result = await gmail_service.get_profile()
        print(f"Profile result: {profile_result[:200]}...")
        
        # Test listing messages
        print("\\n📧 Testing message listing...")
        messages_result = await gmail_service.list_messages(max_results=5)
        print(f"Messages result: {messages_result[:200]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Gmail service test failed: {e}")
        return False

async def test_gmail_agent():
    """Test Gmail agent node."""
    print("\\n" + "="*50)
    print("Testing Gmail Agent Node")
    print("="*50)
    
    try:
        gmail_agent = GmailAgentNode()
        print("✅ Gmail agent initialized")
        
        # Test different task types
        test_cases = [
            {
                "task": "read my recent emails",
                "user_request": "check my inbox",
                "description": "Email reading test"
            },
            {
                "task": "help with gmail",
                "user_request": "what can you do with emails",
                "description": "Help message test"
            }
        ]
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\\n📝 Test {i}: {test_case['description']}")
            
            state = {
                "task": test_case["task"],
                "user_request": test_case["user_request"],
                "messages": []
            }
            
            result = await gmail_agent.process(state)
            
            print(f"✅ Agent result: {result.get('gmail_result', 'No result')[:100]}...")
            print(f"✅ Last agent: {result.get('last_agent')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Gmail agent test failed: {e}")
        return False

async def test_oauth_setup():
    """Test OAuth setup and configuration."""
    print("\\n" + "="*50)
    print("Testing OAuth Configuration")
    print("="*50)
    
    try:
        # Check if OAuth files exist
        config_dir = Path.home() / ".gmail-mcp"
        oauth_keys_path = config_dir / "gcp-oauth.keys.json"
        credentials_path = config_dir / "credentials.json"
        
        print(f"📁 Config directory: {config_dir}")
        print(f"🔑 OAuth keys exist: {oauth_keys_path.exists()}")
        print(f"🎫 Credentials exist: {credentials_path.exists()}")
        
        if oauth_keys_path.exists():
            print("✅ OAuth keys file found")
        else:
            print("⚠️  OAuth keys file not found - run setup_gmail_oauth.py")
        
        if credentials_path.exists():
            print("✅ Credentials file found")
            return True
        else:
            print("⚠️  Credentials file not found - OAuth authentication needed")
            return False
            
    except Exception as e:
        print(f"❌ OAuth setup test failed: {e}")
        return False

async def main():
    """Run all tests."""
    print("Gmail MCP Integration Test Suite")
    print("="*60)
    
    results = []
    
    # Test OAuth setup
    oauth_ok = await test_oauth_setup()
    results.append(("OAuth Setup", oauth_ok))
    
    if oauth_ok:
        # Test Gmail service
        service_ok = await test_gmail_service()
        results.append(("Gmail Service", service_ok))
        
        # Test Gmail agent
        agent_ok = await test_gmail_agent()
        results.append(("Gmail Agent", agent_ok))
    else:
        print("\\n⚠️  Skipping service and agent tests - OAuth not configured")
        print("   Run: python3 backend/setup_gmail_oauth.py")
        results.append(("Gmail Service", False))
        results.append(("Gmail Agent", False))
    
    # Print summary
    print("\\n" + "="*60)
    print("Test Results Summary")
    print("="*60)
    
    all_passed = True
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name:20} {status}")
        if not passed:
            all_passed = False
    
    print("="*60)
    if all_passed:
        print("🎉 All tests passed! Gmail MCP integration is working.")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        if not oauth_ok:
            print("\\n💡 Next steps:")
            print("   1. Run: python3 backend/setup_gmail_oauth.py")
            print("   2. Complete the OAuth authentication flow")
            print("   3. Run this test again")
    
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