#!/usr/bin/env python3
"""
Test MCP servers directly without the backend API
"""
import asyncio
import aiohttp
import json

async def test_mcp_server(port, name):
    """Test if an MCP server is responding"""
    try:
        async with aiohttp.ClientSession() as session:
            # Test basic connectivity
            async with session.get(f"http://localhost:{port}/") as response:
                print(f"✅ {name} (port {port}): Status {response.status}")
                return True
    except Exception as e:
        print(f"❌ {name} (port {port}): {e}")
        return False

async def test_bill_com_tools():
    """Test Bill.com tools in the main MCP server"""
    try:
        async with aiohttp.ClientSession() as session:
            # Test MCP endpoint
            mcp_url = "http://localhost:9002/mcp/"
            
            # Try to get server info
            async with session.post(mcp_url, json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "test-client", "version": "1.0.0"}
                }
            }) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Main MCP Server initialized successfully")
                    print(f"   Server: {data.get('result', {}).get('serverInfo', {}).get('name', 'Unknown')}")
                    return True
                else:
                    print(f"❌ Main MCP Server initialization failed: {response.status}")
                    return False
                    
    except Exception as e:
        print(f"❌ Bill.com MCP test failed: {e}")
        return False

async def main():
    """Test all MCP servers"""
    print("🧪 Testing MCP Servers Directly")
    print("================================")
    
    # Test basic connectivity
    servers = [
        (9000, "Gmail MCP Server"),
        (9001, "Salesforce MCP Server"), 
        (9002, "Main MCP Server (Bill.com)")
    ]
    
    results = []
    for port, name in servers:
        result = await test_mcp_server(port, name)
        results.append(result)
    
    print("\n🔧 Testing Bill.com Tools...")
    bill_com_result = await test_bill_com_tools()
    
    print(f"\n📊 Results:")
    print(f"   MCP Servers: {sum(results)}/{len(results)} online")
    print(f"   Bill.com Tools: {'✅' if bill_com_result else '❌'}")
    
    if all(results) and bill_com_result:
        print("🎉 All MCP servers are working correctly!")
        return True
    else:
        print("❌ Some MCP servers have issues")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)