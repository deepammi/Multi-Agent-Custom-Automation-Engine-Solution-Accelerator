#!/usr/bin/env python3
"""
Test MCP HTTP Server Connectivity

This script tests direct HTTP connectivity to the running MCP servers
to verify they are working correctly before testing the full integration.
"""

import asyncio
import logging
import sys
import os
import json

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Set up logging
logging.basicConfig(level=logging.INFO)

async def test_fastmcp_client_connectivity():
    """Test direct FastMCP client connectivity to HTTP servers."""
    
    print("🔧 Testing FastMCP HTTP Client Connectivity")
    print("=" * 60)
    
    try:
        from fastmcp import Client
        print("✅ FastMCP client library available")
    except ImportError:
        print("❌ FastMCP client library not available. Install with: pip install fastmcp")
        return False
    
    # Test servers
    servers = [
        {"name": "bill_com", "url": "http://localhost:9000/mcp", "test_tool": "get_bill_com_invoices"},
        {"name": "salesforce", "url": "http://localhost:9001/mcp", "test_tool": "salesforce_get_accounts"},
        {"name": "gmail", "url": "http://localhost:9002/mcp", "test_tool": "gmail_search_messages"}
    ]
    
    results = {}
    
    for server in servers:
        print(f"\n🔍 Testing {server['name']} server at {server['url']}")
        
        try:
            # Create FastMCP client
            client = Client(server['url'])
            
            async with client:
                print(f"   ✅ Connected to {server['name']} MCP server")
                
                # List available tools
                try:
                    tools = await client.list_tools()
                    tool_names = [tool.name for tool in tools.tools] if hasattr(tools, 'tools') else []
                    print(f"   📋 Available tools ({len(tool_names)}): {tool_names[:3]}{'...' if len(tool_names) > 3 else ''}")
                    
                    # Test a simple tool call
                    if server['test_tool'] in tool_names:
                        print(f"   🔧 Testing tool: {server['test_tool']}")
                        
                        # Use minimal arguments for testing
                        test_args = {}
                        if server['name'] == 'bill_com':
                            test_args = {"limit": 1}
                        elif server['name'] == 'salesforce':
                            test_args = {"limit": 1}
                        elif server['name'] == 'gmail':
                            test_args = {"query": "test", "max_results": 1}
                        
                        result = await client.call_tool(server['test_tool'], test_args)
                        print(f"   ✅ Tool call successful: {type(result).__name__}")
                        
                        # Show result summary
                        if hasattr(result, 'content') and result.content:
                            content = result.content[0].text if result.content else "No content"
                            try:
                                parsed = json.loads(content)
                                print(f"   📊 Result: {len(str(parsed))} chars, type: {type(parsed).__name__}")
                            except:
                                print(f"   📊 Result: {len(content)} chars (text)")
                        else:
                            print(f"   📊 Result: {str(result)[:100]}...")
                        
                        results[server['name']] = {
                            "status": "success",
                            "tools_count": len(tool_names),
                            "test_tool_works": True
                        }
                    else:
                        print(f"   ⚠️ Test tool '{server['test_tool']}' not found in available tools")
                        results[server['name']] = {
                            "status": "partial",
                            "tools_count": len(tool_names),
                            "test_tool_works": False,
                            "error": f"Test tool '{server['test_tool']}' not available"
                        }
                        
                except Exception as tool_error:
                    print(f"   ❌ Tool operation failed: {tool_error}")
                    results[server['name']] = {
                        "status": "connection_ok_tools_failed",
                        "tools_count": 0,
                        "test_tool_works": False,
                        "error": str(tool_error)
                    }
                    
        except Exception as e:
            print(f"   ❌ Connection failed: {e}")
            results[server['name']] = {
                "status": "connection_failed",
                "tools_count": 0,
                "test_tool_works": False,
                "error": str(e)
            }
    
    # Summary
    print(f"\n📊 MCP HTTP Connectivity Test Results:")
    print("=" * 60)
    
    success_count = 0
    for server_name, result in results.items():
        status_icon = "✅" if result["status"] == "success" else "⚠️" if result["status"] == "partial" else "❌"
        print(f"   {status_icon} {server_name}: {result['status']}")
        if result.get("error"):
            print(f"      Error: {result['error']}")
        if result["tools_count"] > 0:
            print(f"      Tools: {result['tools_count']} available")
        if result["status"] == "success":
            success_count += 1
    
    print(f"\n🎯 Overall Result: {success_count}/{len(servers)} servers working correctly")
    
    return success_count == len(servers)


async def main():
    """Main function to test MCP HTTP connectivity."""
    
    print("🚀 MCP HTTP Server Connectivity Test")
    print("=" * 60)
    print("Testing direct HTTP connectivity to running MCP servers")
    print("=" * 60)
    
    # Test FastMCP client connectivity
    success = await test_fastmcp_client_connectivity()
    
    if success:
        print(f"\n🎉 ALL MCP HTTP SERVERS ARE WORKING CORRECTLY!")
        print(f"   FastMCP client can connect and call tools successfully")
        print(f"   Ready for full integration testing")
        sys.exit(0)
    else:
        print(f"\n❌ SOME MCP HTTP SERVERS HAVE ISSUES")
        print(f"   Check server logs and configuration")
        print(f"   Ensure servers are running on correct ports")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())