#!/usr/bin/env python3
"""
Direct Gmail MCP Server Test
Test Gmail connectivity and see what emails are actually available.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.mcp_http_client import get_mcp_http_manager

async def test_gmail_direct():
    """Test Gmail MCP server directly."""
    print("🔍 Direct Gmail MCP Server Test")
    print("=" * 50)
    
    try:
        # Get MCP manager
        mcp_manager = get_mcp_http_manager()
        
        # Test 1: Get Gmail profile
        print("\n📋 Test 1: Get Gmail Profile")
        try:
            profile_result = await mcp_manager.call_tool("gmail", "gmail_get_profile", {})
            print(f"Profile Result: {profile_result}")
        except Exception as e:
            print(f"Profile Error: {e}")
        
        # Test 2: List recent messages (no search query)
        print("\n📋 Test 2: List Recent Messages (No Query)")
        try:
            list_result = await mcp_manager.call_tool("gmail", "gmail_list_messages", {
                "max_results": 5,
                "query": ""
            })
            print(f"List Result Type: {type(list_result)}")
            print(f"List Result: {list_result}")
            
            # Extract actual data if wrapped
            if isinstance(list_result, dict) and 'result' in list_result:
                actual_data = list_result['result'].data if hasattr(list_result['result'], 'data') else list_result['result']
                print(f"Actual Data: {actual_data}")
                
                if isinstance(actual_data, dict):
                    messages = actual_data.get('messages', [])
                    print(f"Messages Count: {len(messages)}")
                    
                    for i, msg in enumerate(messages[:3], 1):
                        print(f"\nMessage {i}:")
                        if isinstance(msg, dict):
                            print(f"  ID: {msg.get('id', 'N/A')}")
                            print(f"  Snippet: {msg.get('snippet', 'N/A')[:100]}...")
                            
                            # Check headers
                            payload = msg.get('payload', {})
                            headers = payload.get('headers', [])
                            for header in headers:
                                if header.get('name') in ['From', 'Subject', 'Date']:
                                    print(f"  {header.get('name')}: {header.get('value', 'N/A')}")
        except Exception as e:
            print(f"List Error: {e}")
        
        # Test 3: Search with simple query
        print("\n📋 Test 3: Search with Simple Query")
        try:
            search_result = await mcp_manager.call_tool("gmail", "gmail_search_messages", {
                "query": "invoice",
                "max_results": 5
            })
            print(f"Search Result: {search_result}")
        except Exception as e:
            print(f"Search Error: {e}")
        
        # Test 4: Search with time constraint
        print("\n📋 Test 4: Search with Time Constraint")
        try:
            search_result = await mcp_manager.call_tool("gmail", "gmail_search_messages", {
                "query": "newer_than:1m",
                "max_results": 10
            })
            print(f"Time Search Result: {search_result}")
        except Exception as e:
            print(f"Time Search Error: {e}")
        
        # Test 5: Search with subject constraint
        print("\n📋 Test 5: Search with Subject Constraint")
        try:
            search_result = await mcp_manager.call_tool("gmail", "gmail_search_messages", {
                "query": "subject:invoice",
                "max_results": 10
            })
            print(f"Subject Search Result: {search_result}")
        except Exception as e:
            print(f"Subject Search Error: {e}")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_gmail_direct())