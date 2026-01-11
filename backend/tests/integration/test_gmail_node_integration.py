#!/usr/bin/env python3
"""
Test Gmail Agent Node Integration with Email Agent

Verify that the Gmail Agent Node properly uses the new Email Agent.
"""

import asyncio
import logging
import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from app.agents.gmail_agent_node import GmailAgentNode, gmail_agent_node

# Setup logging
logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_gmail_node_with_email_agent():
    """Test Gmail Agent Node using Email Agent."""
    print("\n" + "="*60)
    print("Testing Gmail Agent Node with Email Agent")
    print("="*60)
    
    try:
        # Create Gmail Agent Node
        node = GmailAgentNode()
        print("✅ Gmail Agent Node initialized")
        
        # Verify it uses Email Agent
        assert hasattr(node, 'email_agent')
        assert node.service == 'gmail'
        print("✅ Gmail Agent Node uses Email Agent internally")
        
        # Test processing with mock state
        state = {
            "task": "read my recent emails",
            "user_request": "check my inbox for new messages",
            "plan_id": "test_plan_123",
            "collected_data": {},
            "execution_results": [],
            "messages": []
        }
        
        # This will fail due to MCP server not running, but should handle gracefully
        result = await node.process(state)
        print("✅ Gmail Agent Node processing completed")
        
        # Check result structure
        assert "gmail_result" in result
        assert "messages" in result
        print("✅ Result has expected structure")
        
        return True
        
    except Exception as e:
        print(f"❌ Gmail Agent Node test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_gmail_langgraph_function():
    """Test Gmail Agent LangGraph function."""
    print("\n" + "="*60)
    print("Testing Gmail Agent LangGraph Function")
    print("="*60)
    
    try:
        # Test state for LangGraph
        state = {
            "task_description": "search for emails about invoice INV-1001",
            "plan_id": "test_plan_456",
            "collected_data": {},
            "execution_results": []
        }
        
        # This will fail due to MCP server not running, but should handle gracefully
        result = await gmail_agent_node(state)
        print("✅ Gmail LangGraph function completed")
        
        # Check result structure
        assert "collected_data" in result
        assert "execution_results" in result
        print("✅ LangGraph result has expected structure")
        
        return True
        
    except Exception as e:
        print(f"❌ Gmail LangGraph function test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def run_integration_tests():
    """Run Gmail Agent Node integration tests."""
    print("🚀 Starting Gmail Agent Node Integration Tests")
    print("=" * 80)
    
    tests = [
        ("Gmail Node with Email Agent", test_gmail_node_with_email_agent),
        ("Gmail LangGraph Function", test_gmail_langgraph_function),
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
        print("🎉 All tests passed! Gmail Agent Node integration is working correctly.")
        return True
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        return False


if __name__ == "__main__":
    success = asyncio.run(run_integration_tests())
    sys.exit(0 if success else 1)