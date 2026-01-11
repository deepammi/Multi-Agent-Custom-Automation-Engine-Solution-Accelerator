#!/usr/bin/env python3
"""
Test Bill.com MCP tools to verify they are available and working.
"""

import asyncio
import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_bill_com_tools():
    """Test Bill.com MCP tools."""
    try:
        from fastmcp import Client
        
        print("🔍 Testing Bill.com MCP tools...")
        
        # Connect to Bill.com MCP server
        client = Client("http://localhost:9000/mcp")
        
        async with client:
            print("✅ Connected to Bill.com MCP server")
            
            # List available tools
            tools = await client.list_tools()
            print(f"📋 Available tools ({len(tools)}):")
            
            bill_com_tools = []
            for tool in tools:
                print(f"   - {tool.name}: {tool.description}")
                if "bill_com" in tool.name.lower():
                    bill_com_tools.append(tool.name)
            
            print(f"\n🔧 Bill.com specific tools ({len(bill_com_tools)}):")
            for tool_name in bill_com_tools:
                print(f"   - {tool_name}")
            
            # Test the search tool specifically
            if "search_bill_com_invoices" in bill_com_tools:
                print(f"\n🔍 Testing search_bill_com_invoices tool...")
                try:
                    result = await client.call_tool("search_bill_com_invoices", {
                        "query": "INV-1001",
                        "search_type": "invoice_number"
                    })
                    print(f"✅ Tool call successful: {type(result)}")
                    print(f"   Result: {str(result)[:200]}...")
                except Exception as e:
                    print(f"❌ Tool call failed: {e}")
            else:
                print(f"❌ search_bill_com_invoices tool not found")
                
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_bill_com_tools())