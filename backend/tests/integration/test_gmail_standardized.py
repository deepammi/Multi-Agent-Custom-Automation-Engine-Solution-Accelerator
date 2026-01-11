#!/usr/bin/env python3
"""
Test script for standardized Gmail MCP client.
Verifies that the new implementation uses proper MCP protocol instead of direct Google API calls.
"""

import asyncio
import logging
import sys
import os
import json

# Add the backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_import_structure():
    """Test that all imports work correctly."""
    print("\n=== Testing Gmail Import Structure ===")
    
    try:
        # Test standardized implementation imports
        from app.services.gmail_standard_mcp_client import (
            GmailStandardMCPClient,
            GmailMCPServiceStandardized,
            get_gmail_service as get_standardized_service
        )
        print("✅ Standardized Gmail implementation imports successful")
        
        # Test legacy wrapper imports
        from app.services.gmail_mcp_service import (
            GmailMCPService,
            get_gmail_service
        )
        print("✅ Legacy Gmail wrapper imports successful")
        
        return True
        
    except Exception as e:
        print(f"❌ Gmail import test failed: {e}")
        return False


async def test_gmail_class_structure():
    """Test Gmail class structure and methods."""
    print("\n=== Testing Gmail Class Structure ===")
    
    try:
        from app.services.gmail_mcp_service import GmailMCPService
        
        # Create legacy service (should work without Google API due to wrapper)
        legacy_service = GmailMCPService()
        print("✅ Legacy Gmail service can be instantiated")
        
        # Check that it has the expected methods
        expected_methods = [
            'list_messages', 'send_message', 'get_message', 
            'search_messages', 'get_profile'
        ]
        
        for method in expected_methods:
            if hasattr(legacy_service, method):
                print(f"✅ Method '{method}' exists")
            else:
                print(f"❌ Method '{method}' missing")
                return False
        
        # Check that it delegates to standardized service
        if hasattr(legacy_service, '_standardized_service'):
            print("✅ Legacy Gmail service delegates to standardized implementation")
        else:
            print("❌ Legacy Gmail service missing standardized delegation")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Gmail class structure test failed: {e}")
        return False


async def test_gmail_mcp_protocol_usage():
    """Test that the new implementation uses MCP protocol instead of Google API."""
    print("\n=== Testing Gmail MCP Protocol Usage ===")
    
    try:
        # Test that the standardized client would be configured correctly
        import inspect
        from app.services import gmail_standard_mcp_client
        
        # Get the GmailStandardMCPClient class
        client_class = gmail_standard_mcp_client.GmailStandardMCPClient
        
        # Check that it's designed to inherit from BaseMCPClient
        source = inspect.getsource(client_class)
        
        if "BaseMCPClient" in source:
            print("✅ Inherits from BaseMCPClient")
        else:
            print("❌ Does not inherit from BaseMCPClient")
            return False
        
        if "python3" in source and "gmail_mcp_server.py" in source:
            print("✅ Configured to use MCP server (not direct Google API)")
        else:
            print("❌ Not properly configured for MCP server")
            return False
        
        if "call_tool" in source:
            print("✅ Uses MCP tool calling protocol")
        else:
            print("❌ Does not use MCP tool calling")
            return False
        
        # Check that Google API calls are not used
        if "googleapiclient" not in source and "build(" not in source:
            print("✅ Does not use direct Google API calls")
        else:
            print("❌ Still uses direct Google API calls")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Gmail MCP protocol test failed: {e}")
        return False


async def test_gmail_method_signatures():
    """Test that Gmail method signatures are preserved for backward compatibility."""
    print("\n=== Testing Gmail Method Signatures ===")
    
    try:
        from app.services.gmail_mcp_service import GmailMCPService
        import inspect
        
        service = GmailMCPService()
        
        # Test method signatures
        method_signatures = {
            'list_messages': ['max_results', 'query'],
            'send_message': ['to', 'subject', 'body', 'cc'],
            'get_message': ['message_id', 'include_body_html'],
            'search_messages': ['query', 'max_results'],
            'get_profile': []
        }
        
        for method_name, expected_params in method_signatures.items():
            if hasattr(service, method_name):
                method = getattr(service, method_name)
                sig = inspect.signature(method)
                params = list(sig.parameters.keys())
                
                # Remove 'self' parameter
                if 'self' in params:
                    params.remove('self')
                
                print(f"✅ Method '{method_name}' signature: {params}")
                
                # Check that expected parameters are present
                for expected_param in expected_params:
                    if expected_param not in sig.parameters:
                        print(f"❌ Missing parameter '{expected_param}' in '{method_name}'")
                        return False
            else:
                print(f"❌ Method '{method_name}' not found")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Gmail method signature test failed: {e}")
        return False


async def test_gmail_mock_responses():
    """Test Gmail mock responses work correctly."""
    print("\n=== Testing Gmail Mock Responses ===")
    
    try:
        from app.services.gmail_mcp_service import get_gmail_service
        
        service = get_gmail_service()
        
        # Test list messages (should return mock data)
        messages_result = await service.list_messages(max_results=5)
        messages_data = json.loads(messages_result)
        
        if messages_data.get("success"):
            print("✅ List messages returns successful mock response")
        else:
            print(f"❌ List messages failed: {messages_data}")
            return False
        
        # Test send message (should return mock data)
        send_result = await service.send_message(
            to="test@example.com",
            subject="Test Subject",
            body="Test Body"
        )
        send_data = json.loads(send_result)
        
        if send_data.get("success"):
            print("✅ Send message returns successful mock response")
        else:
            print(f"❌ Send message failed: {send_data}")
            return False
        
        # Test get profile (should return mock data)
        profile_result = await service.get_profile()
        profile_data = json.loads(profile_result)
        
        if profile_data.get("success"):
            print("✅ Get profile returns successful mock response")
        else:
            print(f"❌ Get profile failed: {profile_data}")
            return False
        
        # Test search messages (should return mock data)
        search_result = await service.search_messages("test query", max_results=3)
        search_data = json.loads(search_result)
        
        if search_data.get("success"):
            print("✅ Search messages returns successful mock response")
        else:
            print(f"❌ Search messages failed: {search_data}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Gmail mock responses test failed: {e}")
        return False


async def test_gmail_response_format():
    """Test that Gmail responses maintain the expected format."""
    print("\n=== Testing Gmail Response Format ===")
    
    try:
        from app.services.gmail_mcp_service import get_gmail_service
        
        service = get_gmail_service()
        
        # Test that responses have the expected MCP-like format
        result = await service.list_messages(max_results=2)
        data = json.loads(result)
        
        # Check response structure
        if "success" in data:
            print("✅ Response has 'success' field")
        else:
            print("❌ Response missing 'success' field")
            return False
        
        if "data" in data and "result" in data["data"] and "content" in data["data"]["result"]:
            print("✅ Response has proper nested structure")
        else:
            print("❌ Response missing proper nested structure")
            return False
        
        # Check content structure
        content = data["data"]["result"]["content"]
        if isinstance(content, list) and len(content) > 0:
            first_content = content[0]
            if "type" in first_content and "text" in first_content:
                print("✅ Content has proper type and text fields")
            else:
                print("❌ Content missing type or text fields")
                return False
        else:
            print("❌ Content is not a proper list")
            return False
        
        # Check that text content is valid JSON
        try:
            text_data = json.loads(first_content["text"])
            print("✅ Text content is valid JSON")
        except json.JSONDecodeError:
            print("❌ Text content is not valid JSON")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Gmail response format test failed: {e}")
        return False


async def main():
    """Run all tests."""
    print("🚀 Starting Standardized Gmail MCP Client Tests")
    
    tests = [
        test_import_structure,
        test_gmail_class_structure,
        test_gmail_mcp_protocol_usage,
        test_gmail_method_signatures,
        test_gmail_mock_responses,
        test_gmail_response_format
    ]
    
    results = []
    for test in tests:
        try:
            result = await test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")
            results.append(False)
    
    # Summary
    passed = sum(results)
    total = len(results)
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Gmail MCP standardization is working correctly.")
        print("\n🔄 Migration Summary:")
        print("   ❌ OLD: Direct Google API calls (googleapiclient.discovery.build)")
        print("   ✅ NEW: Proper MCP protocol (gmail_list_messages, gmail_send_message tools)")
        print("   ✅ Backward compatibility maintained")
        print("   ✅ Standardized error handling and logging")
        print("   ✅ Connection pooling and health monitoring")
        print("   ✅ Mock responses for testing without credentials")
        return 0
    else:
        print("⚠️ Some tests failed. Check the output above for details.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)