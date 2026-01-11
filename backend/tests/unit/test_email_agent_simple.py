#!/usr/bin/env python3
"""
Simple Email Agent Test

Test the new category-based Email Agent without MCP server connections.
"""

import asyncio
import logging
import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from app.agents.email_agent import EmailAgent, get_email_agent, GmailAgentLegacy, get_gmail_agent

# Setup logging
logging.basicConfig(
    level=logging.WARNING,  # Reduce noise
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_email_agent_basic():
    """Test basic Email Agent functionality without MCP connections."""
    print("\n" + "="*60)
    print("Testing Email Agent Basic Functionality")
    print("="*60)
    
    try:
        # Test initialization
        email_agent = EmailAgent()
        print("✅ Email Agent initialized successfully")
        
        # Test supported services
        services = email_agent.get_supported_services()
        print(f"✅ Supported services: {services}")
        assert 'gmail' in services
        assert 'outlook' in services
        
        # Test service info
        gmail_info = email_agent.get_service_info('gmail')
        print(f"✅ Gmail info: {gmail_info}")
        assert gmail_info['name'] == 'Gmail'
        assert 'list_messages' in gmail_info['operations']
        assert 'send_message' in gmail_info['operations']
        
        # Test service validation
        email_agent._validate_service('gmail')  # Should not raise
        print("✅ Service validation works")
        
        try:
            email_agent._validate_service('invalid')
            assert False, "Should have raised ValueError"
        except ValueError:
            print("✅ Invalid service properly rejected")
        
        # Test tool name resolution
        tool_name = email_agent._get_tool_name('gmail', 'list_messages')
        assert tool_name == 'gmail_list_messages'
        print(f"✅ Tool name resolution: {tool_name}")
        
        return True
        
    except Exception as e:
        print(f"❌ Email Agent basic test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_gmail_legacy_wrapper():
    """Test Gmail legacy wrapper."""
    print("\n" + "="*60)
    print("Testing Gmail Legacy Wrapper")
    print("="*60)
    
    try:
        # Test legacy wrapper
        legacy_agent = GmailAgentLegacy()
        print("✅ Legacy Gmail Agent initialized")
        
        assert legacy_agent.service == 'gmail'
        print("✅ Legacy agent correctly uses Gmail service")
        
        # Test global instance
        global_legacy = get_gmail_agent()
        print("✅ Global legacy Gmail Agent created")
        
        return True
        
    except Exception as e:
        print(f"❌ Gmail legacy wrapper test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_gmail_agent_node():
    """Test Gmail Agent Node compatibility."""
    print("\n" + "="*60)
    print("Testing Gmail Agent Node")
    print("="*60)
    
    try:
        from app.agents.gmail_agent_node import GmailAgentNode
        
        # Test node initialization
        node = GmailAgentNode()
        print("✅ Gmail Agent Node initialized")
        
        # Verify it uses Email Agent
        assert hasattr(node, 'email_agent')
        assert node.service == 'gmail'
        print("✅ Gmail Agent Node uses Email Agent internally")
        
        return True
        
    except Exception as e:
        print(f"❌ Gmail Agent Node test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_parameter_validation():
    """Test parameter validation in Email Agent methods."""
    print("\n" + "="*60)
    print("Testing Parameter Validation")
    print("="*60)
    
    try:
        email_agent = EmailAgent()
        
        # Test send_message validation
        try:
            await email_agent.send_message("", "subject", "body")
            assert False, "Should have raised ValueError for empty 'to'"
        except ValueError as e:
            print(f"✅ Empty 'to' parameter properly rejected: {e}")
        
        try:
            await email_agent.send_message("test@example.com", "", "body")
            assert False, "Should have raised ValueError for empty subject"
        except ValueError as e:
            print(f"✅ Empty subject parameter properly rejected: {e}")
        
        # Test get_message validation
        try:
            await email_agent.get_message("")
            assert False, "Should have raised ValueError for empty message_id"
        except ValueError as e:
            print(f"✅ Empty message_id parameter properly rejected: {e}")
        
        # Test search_messages validation
        try:
            await email_agent.search_messages("")
            assert False, "Should have raised ValueError for empty query"
        except ValueError as e:
            print(f"✅ Empty query parameter properly rejected: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Parameter validation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def run_simple_tests():
    """Run simple Email Agent tests without MCP connections."""
    print("🚀 Starting Simple Email Agent Tests")
    print("=" * 80)
    
    tests = [
        ("Email Agent Basic", test_email_agent_basic),
        ("Gmail Legacy Wrapper", test_gmail_legacy_wrapper),
        ("Gmail Agent Node", test_gmail_agent_node),
        ("Parameter Validation", test_parameter_validation),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            success = await test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ {test_name} crashed: {e}")
            results.append((test_name, False))
    
    # Print summary
    print("\n" + "="*80)
    print("📊 TEST SUMMARY")
    print("="*80)
    
    passed = 0
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {test_name}")
        if success:
            passed += 1
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Email Agent is working correctly.")
        return True
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        return False


if __name__ == "__main__":
    success = asyncio.run(run_simple_tests())
    sys.exit(0 if success else 1)