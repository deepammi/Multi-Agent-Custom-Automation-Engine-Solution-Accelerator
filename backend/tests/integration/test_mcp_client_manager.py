#!/usr/bin/env python3
"""
Test script for unified MCP client manager and tool registry.
Tests centralized connection management, tool discovery, and routing.
"""

import asyncio
import logging
import sys
import os
from datetime import datetime
from typing import List

# Add the backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.services.mcp_client_service import (
    MCPClientManager,
    ToolRegistry,
    ConnectionPool,
    BaseMCPClient,
    ToolInfo,
    HealthStatus,
    get_mcp_manager,
    initialize_mcp_services
)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MockMCPClient(BaseMCPClient):
    """Mock MCP client for testing without actual MCP servers."""
    
    def __init__(self, service_name: str, tools: List[str] = None):
        # Initialize without calling parent __init__ to avoid MCP SDK requirement
        self.service_name = service_name
        self.server_command = "mock"
        self.server_args = ["mock"]
        self.timeout = 30
        self.retry_attempts = 3
        self.health_check_interval = 60
        
        # Mock connection state
        self._session = "mock_session"
        self._connection_status = None
        self._last_health_check = None
        self._health_status = None
        
        # Mock tool registry
        self._available_tools = tools or [f"{service_name}_tool_1", f"{service_name}_tool_2"]
        self._tool_metadata = {}
        
        # Create mock tool metadata
        for tool_name in self._available_tools:
            self._tool_metadata[tool_name] = ToolInfo(
                name=tool_name,
                service=service_name,
                description=f"Mock tool: {tool_name}",
                parameters={"param1": {"type": "string"}},
                return_type="dict",
                category="mock",
                requires_auth=False
            )
        
        # Performance metrics
        self._connection_time = 0.1
        self._last_tool_call_time = None
        self._tool_call_count = 0
        self._error_count = 0
    
    async def connect(self):
        """Mock connect method."""
        logger.info(f"Mock connecting to {self.service_name}")
        await asyncio.sleep(0.01)  # Simulate connection time
    
    async def disconnect(self):
        """Mock disconnect method."""
        logger.info(f"Mock disconnecting from {self.service_name}")
    
    async def call_tool(self, tool_name: str, arguments: dict) -> dict:
        """Mock tool call."""
        self._tool_call_count += 1
        return {
            "success": True,
            "service": self.service_name,
            "tool": tool_name,
            "arguments": arguments,
            "result": f"Mock result from {tool_name}"
        }
    
    async def check_health(self) -> HealthStatus:
        """Mock health check."""
        return HealthStatus(
            is_healthy=True,
            last_check=datetime.now(),
            response_time_ms=50,
            available_tools=len(self._available_tools),
            connection_status="connected"
        )


async def test_tool_registry():
    """Test tool registry functionality."""
    print("\n=== Testing Tool Registry ===")
    
    try:
        registry = ToolRegistry()
        
        # Create mock clients
        client1 = MockMCPClient("service1", ["tool_a", "tool_b"])
        client2 = MockMCPClient("service2", ["tool_c", "tool_a"])  # tool_a conflict
        
        # Register services
        await registry.register_service("service1", client1)
        await registry.register_service("service2", client2)
        
        # Test tool discovery
        all_tools = registry.get_all_tools()
        print(f"✅ Total tools registered: {len(all_tools)}")
        
        # Test conflict resolution
        if "service2_tool_a" in all_tools:
            print("✅ Tool name conflict resolved correctly")
        else:
            print("❌ Tool name conflict not resolved")
            return False
        
        # Test service-specific tools
        service1_tools = registry.get_tools_by_service("service1")
        service2_tools = registry.get_tools_by_service("service2")
        
        print(f"✅ Service1 tools: {len(service1_tools)}")
        print(f"✅ Service2 tools: {len(service2_tools)}")
        
        # Test tool lookup
        tool_info = registry.find_tool("tool_b")
        if tool_info and tool_info.service == "service1":
            print("✅ Tool lookup working correctly")
        else:
            print("❌ Tool lookup failed")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Tool registry test failed: {e}")
        return False


async def test_connection_pool():
    """Test connection pool functionality."""
    print("\n=== Testing Connection Pool ===")
    
    try:
        pool = ConnectionPool(max_connections=2)
        
        # Create client factories
        async def create_client1():
            return MockMCPClient("service1")
        
        async def create_client2():
            return MockMCPClient("service2")
        
        # Get connections
        client1 = await pool.get_connection("service1", create_client1)
        client2 = await pool.get_connection("service2", create_client2)
        
        print(f"✅ Created 2 connections")
        
        # Test connection reuse
        client1_reused = await pool.get_connection("service1", create_client1)
        if client1 is client1_reused:
            print("✅ Connection reuse working")
        else:
            print("❌ Connection reuse failed")
            return False
        
        # Test pool stats
        stats = pool.get_pool_stats()
        print(f"✅ Pool stats: {stats}")
        
        # Test pool cleanup
        await pool.close_all()
        stats_after = pool.get_pool_stats()
        if stats_after["active_connections"] == 0:
            print("✅ Pool cleanup working")
        else:
            print("❌ Pool cleanup failed")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Connection pool test failed: {e}")
        return False


async def test_mcp_client_manager():
    """Test unified MCP client manager."""
    print("\n=== Testing MCP Client Manager ===")
    
    try:
        manager = MCPClientManager(max_connections=3)
        
        # Register services
        async def create_service1():
            client = MockMCPClient("service1", ["get_data", "process_data"])
            await client.connect()
            return client
        
        async def create_service2():
            client = MockMCPClient("service2", ["send_email", "get_contacts"])
            await client.connect()
            return client
        
        manager.register_service("service1", create_service1)
        manager.register_service("service2", create_service2)
        
        print("✅ Services registered")
        
        # Test tool discovery
        tools_by_service = await manager.discover_tools()
        print(f"✅ Discovered tools: {len(tools_by_service)} services")
        
        for service, tools in tools_by_service.items():
            print(f"   {service}: {len(tools)} tools")
        
        # Test tool calling
        result1 = await manager.call_tool("service1", "get_data", {"param": "test"})
        if result1.get("success"):
            print("✅ Tool call to service1 successful")
        else:
            print("❌ Tool call to service1 failed")
            return False
        
        result2 = await manager.call_tool("service2", "send_email", {"to": "test@example.com"})
        if result2.get("success"):
            print("✅ Tool call to service2 successful")
        else:
            print("❌ Tool call to service2 failed")
            return False
        
        # Test health monitoring
        health_status = await manager.get_all_service_health()
        print(f"✅ Health status for {len(health_status)} services")
        
        for service, health in health_status.items():
            print(f"   {service}: {'healthy' if health.is_healthy else 'unhealthy'}")
        
        # Test manager stats
        stats = manager.get_manager_stats()
        print(f"✅ Manager stats: {stats}")
        
        # Test shutdown
        await manager.shutdown()
        print("✅ Manager shutdown successful")
        
        return True
        
    except Exception as e:
        print(f"❌ MCP client manager test failed: {e}")
        return False


async def test_global_manager():
    """Test global manager instance."""
    print("\n=== Testing Global Manager ===")
    
    try:
        # Get global manager
        manager1 = get_mcp_manager()
        manager2 = get_mcp_manager()
        
        if manager1 is manager2:
            print("✅ Global manager singleton working")
        else:
            print("❌ Global manager singleton failed")
            return False
        
        # Test initialization
        await initialize_mcp_services()
        print("✅ MCP services initialization completed")
        
        return True
        
    except Exception as e:
        print(f"❌ Global manager test failed: {e}")
        return False


async def main():
    """Run all tests."""
    print("🚀 Starting MCP Client Manager Tests")
    
    tests = [
        test_tool_registry,
        test_connection_pool,
        test_mcp_client_manager,
        test_global_manager
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
        print("🎉 All tests passed! MCP Client Manager is working correctly.")
        return 0
    else:
        print("⚠️ Some tests failed. Check the output above for details.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)