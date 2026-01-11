#!/usr/bin/env python3
"""
Example usage of the unified MCP client manager.
Shows how agents and services would use the centralized MCP management.
"""

import asyncio
import logging
import sys
import os

# Add the backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.services.mcp_client_service import (
    get_mcp_manager,
    BaseMCPClient,
    MCPClientManager
)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def setup_services():
    """Setup example MCP services."""
    manager = get_mcp_manager()
    
    # Register Salesforce service
    async def create_salesforce_client():
        client = BaseMCPClient(
            service_name="salesforce",
            server_command="python3",
            server_args=["src/mcp_server/salesforce_mcp_server.py"],
            timeout=30
        )
        # In real usage, this would connect to actual MCP server
        # await client.connect()
        logger.info("Salesforce MCP client created (mock)")
        return client
    
    # Register Gmail service
    async def create_gmail_client():
        client = BaseMCPClient(
            service_name="gmail",
            server_command="python3",
            server_args=["src/mcp_server/gmail_mcp_server.py"],
            timeout=20
        )
        # In real usage, this would connect to actual MCP server
        # await client.connect()
        logger.info("Gmail MCP client created (mock)")
        return client
    
    # Register Zoho service
    async def create_zoho_client():
        client = BaseMCPClient(
            service_name="zoho",
            server_command="python3",
            server_args=["src/mcp_server/zoho_mcp_server.py"],
            timeout=25
        )
        # In real usage, this would connect to actual MCP server
        # await client.connect()
        logger.info("Zoho MCP client created (mock)")
        return client
    
    # Register all services
    manager.register_service("salesforce", create_salesforce_client)
    manager.register_service("gmail", create_gmail_client)
    manager.register_service("zoho", create_zoho_client)
    
    logger.info("All MCP services registered with manager")


async def agent_workflow_example():
    """Example of how an agent would use the unified MCP manager."""
    manager = get_mcp_manager()
    
    print("\n=== Agent Workflow Example ===")
    
    try:
        # Agent needs to get Salesforce account data
        print("🤖 Agent: Getting Salesforce account data...")
        # In real usage:
        # salesforce_result = await manager.call_tool(
        #     "salesforce", 
        #     "get_accounts", 
        #     {"limit": 10}
        # )
        print("✅ Salesforce data retrieved (mock)")
        
        # Agent needs to send email via Gmail
        print("🤖 Agent: Sending email via Gmail...")
        # In real usage:
        # gmail_result = await manager.call_tool(
        #     "gmail",
        #     "send_email",
        #     {
        #         "to": "customer@example.com",
        #         "subject": "Account Update",
        #         "body": "Your account has been updated."
        #     }
        # )
        print("✅ Email sent via Gmail (mock)")
        
        # Agent needs to create invoice in Zoho
        print("🤖 Agent: Creating invoice in Zoho...")
        # In real usage:
        # zoho_result = await manager.call_tool(
        #     "zoho",
        #     "create_invoice",
        #     {
        #         "customer_id": "12345",
        #         "amount": 1500.00,
        #         "description": "Consulting services"
        #     }
        # )
        print("✅ Invoice created in Zoho (mock)")
        
        print("🎉 Agent workflow completed successfully!")
        
    except Exception as e:
        print(f"❌ Agent workflow failed: {e}")


async def service_discovery_example():
    """Example of service and tool discovery."""
    manager = get_mcp_manager()
    
    print("\n=== Service Discovery Example ===")
    
    try:
        # Discover all available tools
        print("🔍 Discovering available tools...")
        # In real usage:
        # tools_by_service = await manager.discover_tools()
        # 
        # print(f"📋 Available services: {len(tools_by_service)}")
        # for service, tools in tools_by_service.items():
        #     print(f"   {service}: {len(tools)} tools")
        #     for tool in tools:
        #         print(f"     - {tool.name}: {tool.description}")
        
        print("✅ Tool discovery completed (mock)")
        
        # Check service health
        print("🏥 Checking service health...")
        # In real usage:
        # health_status = await manager.get_all_service_health()
        # 
        # for service, health in health_status.items():
        #     status = "🟢 Healthy" if health.is_healthy else "🔴 Unhealthy"
        #     print(f"   {service}: {status} ({health.response_time_ms}ms)")
        
        print("✅ Health check completed (mock)")
        
        # Get manager statistics
        stats = manager.get_manager_stats()
        print(f"📊 Manager stats: {stats}")
        
    except Exception as e:
        print(f"❌ Service discovery failed: {e}")


async def error_handling_example():
    """Example of error handling with the unified manager."""
    manager = get_mcp_manager()
    
    print("\n=== Error Handling Example ===")
    
    try:
        # Try to call a non-existent service
        print("🚫 Attempting to call non-existent service...")
        try:
            # This would fail in real usage:
            # await manager.call_tool("nonexistent", "some_tool", {})
            print("❌ Service not found (expected)")
        except Exception as e:
            print(f"✅ Error handled correctly: {type(e).__name__}")
        
        # Try to call a non-existent tool
        print("🚫 Attempting to call non-existent tool...")
        try:
            # This would fail in real usage:
            # await manager.call_tool("salesforce", "nonexistent_tool", {})
            print("❌ Tool not found (expected)")
        except Exception as e:
            print(f"✅ Error handled correctly: {type(e).__name__}")
        
        print("✅ Error handling working correctly")
        
    except Exception as e:
        print(f"❌ Error handling test failed: {e}")


async def main():
    """Main example function."""
    print("🚀 MCP Client Manager Usage Examples")
    
    # Setup services
    await setup_services()
    
    # Run examples
    await agent_workflow_example()
    await service_discovery_example()
    await error_handling_example()
    
    print("\n🎯 Key Benefits of Unified MCP Manager:")
    print("   ✅ Centralized connection management")
    print("   ✅ Automatic tool discovery and registration")
    print("   ✅ Connection pooling and reuse")
    print("   ✅ Standardized error handling")
    print("   ✅ Health monitoring and metrics")
    print("   ✅ Tool name conflict resolution")
    print("   ✅ Unified interface for all services")
    
    print("\n📝 Usage in Agent Code:")
    print("   # Get manager instance")
    print("   manager = get_mcp_manager()")
    print("   ")
    print("   # Call any tool from any service")
    print("   result = await manager.call_tool('salesforce', 'get_accounts', {'limit': 10})")
    print("   result = await manager.call_tool('gmail', 'send_email', {...})")
    print("   result = await manager.call_tool('zoho', 'create_invoice', {...})")


if __name__ == "__main__":
    asyncio.run(main())