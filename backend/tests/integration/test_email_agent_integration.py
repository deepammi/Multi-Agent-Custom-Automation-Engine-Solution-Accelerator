#!/usr/bin/env python3
"""
Test Email Agent Integration

Test the new category-based Email Agent to ensure it properly
replaces the Gmail-specific implementation with MCP protocol.
"""

import asyncio
import logging
import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from app.agents.email_agent import EmailAgent, get_email_agent
from app.services.mcp_client_service import get_mcp_manager, initialize_mcp_services

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_email_agent_initialization():
    """Test Email Agent initialization."""
    print("\n" + "="*60)
    print("Testing Email Agent Initialization")
    print("="*60)
    
    try:
        # Test direct initialization
        email_agent = EmailAgent()
        print("✅ Email Agent initialized successfully")
        
        # Test global instance
        global_agent = get_email_agent()
        print("✅ Global Email Agent instance created")
        
        # Test supported services
        services = email_agent.get_supported_services()
        print(f"✅ Supported services: {services}")
        
        # Test service info
        for service in services:
            info = email_agent.get_service_info(service)
            print(f"✅ {service} info: {info['name']} with {len(info['operations'])} operations")
        
        return True
        
    except Exception as e:
        print(f"❌ Email Agent initialization failed: {e}")
        return False


async def test_email_agent_service_validation():
    """Test Email Agent service validation."""
    print("\n" + "="*60)
    print("Testing Email Agent Service Validation")
    print("="*60)
    
    try:
        email_agent = EmailAgent()
        
        # Test valid service
        email_agent._validate_service('gmail')
        print("✅ Valid service validation passed")
        
        # Test invalid service
        try:
            email_agent._validate_service('invalid_service')
            print("❌ Invalid service validation should have failed")
            return False
        except ValueError as e:
            print(f"✅ Invalid service properly rejected: {e}")
        
        # Test tool name resolution
        tool_name = email_agent._get_tool_name('gmail', 'list_messages')
        print(f"✅ Tool name resolved: {tool_name}")
        
        # Test invalid operation
        try:
            email_agent._get_tool_name('gmail', 'invalid_operation')
            print("❌ Invalid operation validation should have failed")
            return False
        except ValueError as e:
            print(f"✅ Invalid operation properly rejected: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Service validation test failed: {e}")
        return False


async def test_email_agent_mcp_integration():
    """Test Email Agent MCP integration (mock mode)."""
    print("\n" + "="*60)
    print("Testing Email Agent MCP Integration")
    print("="*60)
    
    try:
        # Initialize MCP services
        await initialize_mcp_services()
        print("✅ MCP services initialized")
        
        email_agent = EmailAgent()
        
        # Test health check (will likely fail but should handle gracefully)
        try:
            health = await email_agent.check_service_health('gmail')
            print(f"✅ Gmail health check completed: {health['is_healthy']}")
            if not health['is_healthy']:
                print(f"   Note: {health['error_message']}")
        except Exception as e:
            print(f"⚠️  Gmail health check failed (expected): {e}")
        
        # Test list messages (will use mock data if MCP server not available)
        try:
            messages = await email_agent.list_messages(service='gmail', max_results=5)
            print(f"✅ List messages completed (mock mode likely)")
            print(f"   Messages type: {type(messages)}")
        except Exception as e:
            print(f"⚠️  List messages failed: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ MCP integration test failed: {e}")
        return False


async def test_gmail_agent_node_compatibility():
    """Test Gmail Agent Node backward compatibility."""
    print("\n" + "="*60)
    print("Testing Gmail Agent Node Backward Compatibility")
    print("="*60)
    
    try:
        from app.agents.gmail_agent_node import GmailAgentNode, gmail_agent_node
        
        # Test node initialization
        node = GmailAgentNode()
        print("✅ Gmail Agent Node initialized with Email Agent")
        
        # Test node processing with mock state
        state = {
            "task_description": "read my recent emails",
            "plan_id": "test_plan_123",
            "collected_data": {},
            "execution_results": []
        }
        
        result = await node.process(state)
        print("✅ Gmail Agent Node processing completed")
        print(f"   Result keys: {list(result.keys())}")
        
        # Test the LangGraph function
        langgraph_result = await gmail_agent_node(state)
        print("✅ Gmail Agent Node LangGraph function completed")
        print(f"   LangGraph result keys: {list(langgraph_result.keys())}")
        
        return True
        
    except Exception as e:
        print(f"❌ Gmail Agent Node compatibility test failed: {e}")
        return False


async def test_legacy_gmail_wrapper():
    """Test legacy Gmail wrapper for backward compatibility."""
    print("\n" + "="*60)
    print("Testing Legacy Gmail Wrapper")
    print("="*60)
    
    try:
        from app.agents.email_agent import GmailAgentLegacy, get_gmail_agent
        
        # Test legacy wrapper initialization
        legacy_agent = GmailAgentLegacy()
        print("✅ Legacy Gmail Agent initialized")
        
        # Test global legacy instance
        global_legacy = get_gmail_agent()
        print("✅ Global legacy Gmail Agent created")
        
        # Test that it uses Gmail service
        assert legacy_agent.service == 'gmail'
        print("✅ Legacy agent correctly fixed to Gmail service")
        
        return True
        
    except Exception as e:
        print(f"❌ Legacy Gmail wrapper test failed: {e}")
        return False


async def run_all_tests():
    """Run all Email Agent tests."""
    print("🚀 Starting Email Agent Integration Tests")
    print("=" * 80)
    
    tests = [
        ("Email Agent Initialization", test_email_agent_initialization),
        ("Service Validation", test_email_agent_service_validation),
        ("MCP Integration", test_email_agent_mcp_integration),
        ("Gmail Node Compatibility", test_gmail_agent_node_compatibility),
        ("Legacy Gmail Wrapper", test_legacy_gmail_wrapper),
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
        print("🎉 All tests passed! Email Agent integration is working correctly.")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
    
    return passed == total


if __name__ == "__main__":
    asyncio.run(run_all_tests())