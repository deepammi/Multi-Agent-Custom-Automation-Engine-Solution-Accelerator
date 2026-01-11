#!/usr/bin/env python3
"""
Test script for enhanced MCP client infrastructure.
Tests the new standardization features without requiring actual MCP servers.
"""

import asyncio
import logging
import sys
import os

# Add the backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.services.mcp_client_service import (
    BaseMCPClient, 
    MCPError, 
    MCPConnectionError,
    ToolInfo,
    HealthStatus,
    ConnectionStatus
)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_mcp_client_initialization():
    """Test MCP client initialization and configuration."""
    print("\n=== Testing MCP Client Initialization ===")
    
    try:
        # Test basic initialization
        client = BaseMCPClient(
            service_name="test_service",
            server_command="echo",  # Use echo command for testing
            server_args=["test"],
            timeout=5,
            retry_attempts=2
        )
        
        print(f"✅ Client initialized successfully")
        print(f"   Service: {client.service_name}")
        print(f"   Command: {client.server_command}")
        print(f"   Args: {client.server_args}")
        print(f"   Timeout: {client.timeout}s")
        print(f"   Retry attempts: {client.retry_attempts}")
        
        # Test performance metrics
        metrics = client.get_performance_metrics()
        print(f"   Initial metrics: {metrics}")
        
        return True
        
    except Exception as e:
        print(f"❌ Initialization failed: {e}")
        return False


async def test_error_handling():
    """Test standardized error handling."""
    print("\n=== Testing Error Handling ===")
    
    try:
        # Test different error types
        errors = [
            MCPError("Test error", "test_service", "TEST_ERROR"),
            MCPConnectionError("Connection failed", "test_service", "CONN_ERROR"),
        ]
        
        for error in errors:
            print(f"✅ {type(error).__name__}: {error}")
            print(f"   Service: {error.service}")
            print(f"   Error code: {error.error_code}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error handling test failed: {e}")
        return False


async def test_tool_metadata():
    """Test tool metadata handling."""
    print("\n=== Testing Tool Metadata ===")
    
    try:
        # Create sample tool metadata
        tool_info = ToolInfo(
            name="test_tool",
            service="test_service",
            description="A test tool",
            parameters={"param1": {"type": "string"}},
            return_type="dict",
            category="test",
            requires_auth=False
        )
        
        print(f"✅ Tool metadata created:")
        print(f"   Name: {tool_info.name}")
        print(f"   Service: {tool_info.service}")
        print(f"   Description: {tool_info.description}")
        print(f"   Parameters: {tool_info.parameters}")
        print(f"   Requires auth: {tool_info.requires_auth}")
        
        return True
        
    except Exception as e:
        print(f"❌ Tool metadata test failed: {e}")
        return False


async def test_health_status():
    """Test health status monitoring."""
    print("\n=== Testing Health Status ===")
    
    try:
        from datetime import datetime
        
        # Create sample health status
        health = HealthStatus(
            is_healthy=True,
            last_check=datetime.now(),
            response_time_ms=150,
            available_tools=5,
            connection_status="connected"
        )
        
        print(f"✅ Health status created:")
        print(f"   Healthy: {health.is_healthy}")
        print(f"   Response time: {health.response_time_ms}ms")
        print(f"   Available tools: {health.available_tools}")
        print(f"   Connection status: {health.connection_status}")
        
        return True
        
    except Exception as e:
        print(f"❌ Health status test failed: {e}")
        return False


async def test_connection_status():
    """Test connection status enumeration."""
    print("\n=== Testing Connection Status ===")
    
    try:
        statuses = [
            ConnectionStatus.DISCONNECTED,
            ConnectionStatus.CONNECTING,
            ConnectionStatus.CONNECTED,
            ConnectionStatus.RECONNECTING,
            ConnectionStatus.FAILED
        ]
        
        for status in statuses:
            print(f"✅ Status: {status.value}")
        
        return True
        
    except Exception as e:
        print(f"❌ Connection status test failed: {e}")
        return False


async def main():
    """Run all tests."""
    print("🚀 Starting Enhanced MCP Client Tests")
    
    tests = [
        test_mcp_client_initialization,
        test_error_handling,
        test_tool_metadata,
        test_health_status,
        test_connection_status
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
        print("🎉 All tests passed! Enhanced MCP client infrastructure is working.")
        return 0
    else:
        print("⚠️ Some tests failed. Check the output above for details.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)