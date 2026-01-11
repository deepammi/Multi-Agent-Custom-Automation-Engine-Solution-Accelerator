#!/usr/bin/env python3
"""
Test script for enhanced MCP HTTP client retry logic.

This script tests the retry logic improvements implemented in Task 4.1:
- Exponential backoff with jitter
- Enhanced timeout handling
- Improved logging for debugging
- Maximum retry attempts and timeout values
"""

import asyncio
import logging
import os
import sys
from unittest.mock import AsyncMock, patch, MagicMock

# Add the backend directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from app.services.mcp_http_client import FastMCPHTTPClient, MCPHTTPConnectionError, MCPHTTPTimeoutError
from app.config.environment import get_environment_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_connection_retry_logic():
    """Test connection retry logic with exponential backoff."""
    logger.info("🧪 Testing connection retry logic with exponential backoff")
    
    # Mock the FastMCP Client to simulate connection failures
    with patch('app.services.mcp_http_client.Client') as mock_client_class:
        # Configure mock to fail first 2 attempts, succeed on 3rd
        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client
        
        # First two attempts fail, third succeeds
        mock_client.__aenter__.side_effect = [
            ConnectionError("Connection refused"),
            asyncio.TimeoutError("Connection timeout"),
            None  # Success on third attempt
        ]
        
        # Create client with enhanced retry settings
        client = FastMCPHTTPClient(
            service_name="test_service",
            server_url="http://localhost:9999/mcp",
            retry_attempts=5,
            max_backoff_time=10,
            base_backoff_time=0.1  # Fast for testing
        )
        
        try:
            # This should succeed after 3 attempts
            await client.connect()
            logger.info("✅ Connection retry logic test passed - connected after retries")
            
            # Verify the client is marked as connected
            assert client._connected == True
            assert client._retry_count == 2  # Two retries before success
            
            await client.disconnect()
            
        except Exception as e:
            logger.error(f"❌ Connection retry test failed: {e}")
            raise


async def test_tool_call_retry_logic():
    """Test tool call retry logic with mock mode disabled."""
    logger.info("🧪 Testing tool call retry logic")
    
    # Ensure mock mode is disabled for this test
    os.environ['USE_MOCK_MODE'] = 'false'
    
    with patch('app.services.mcp_http_client.Client') as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client
        
        # Connection succeeds
        mock_client.__aenter__.return_value = None
        
        # Tool calls fail first 2 times, succeed on 3rd
        mock_client.call_tool.side_effect = [
            ConnectionError("Service unavailable"),
            asyncio.TimeoutError("Request timeout"),
            {"result": "success", "data": "test_data"}  # Success on third attempt
        ]
        
        client = FastMCPHTTPClient(
            service_name="test_service",
            server_url="http://localhost:9999/mcp",
            retry_attempts=3,
            base_backoff_time=0.1  # Fast for testing
        )
        
        try:
            await client.connect()
            
            # This should succeed after 3 attempts
            result = await client.call_tool("test_tool", {"param": "value"})
            
            logger.info("✅ Tool call retry logic test passed")
            assert result["result"] == "success"
            assert client._tool_call_count == 1  # Only successful calls are counted
            
            await client.disconnect()
            
        except Exception as e:
            logger.error(f"❌ Tool call retry test failed: {e}")
            raise


async def test_mock_mode_bypass():
    """Test that mock mode bypasses retry logic entirely."""
    logger.info("🧪 Testing mock mode bypass of retry logic")
    
    # Enable mock mode
    os.environ['USE_MOCK_MODE'] = 'true'
    
    # Force reload of environment config to pick up the change
    from app.config.environment import _env_config
    import app.config.environment
    app.config.environment._env_config = None  # Reset singleton
    
    # Create client - no need to mock FastMCP since mock mode should bypass it
    client = FastMCPHTTPClient(
        service_name="gmail",
        server_url="http://localhost:9999/mcp",  # Non-existent server
        retry_attempts=3
    )
    
    try:
        # This should return mock data immediately without attempting connection
        result = await client.call_tool("search_messages", {"query": "test"})
        
        logger.info("✅ Mock mode bypass test passed")
        assert result["mock_mode"] == True
        assert "messages" in result
        assert client._tool_call_count == 0  # No real tool calls made
        
    except Exception as e:
        logger.error(f"❌ Mock mode bypass test failed: {e}")
        raise
    finally:
        # Reset mock mode
        os.environ['USE_MOCK_MODE'] = 'false'
        # Reset singleton again
        app.config.environment._env_config = None


async def test_exponential_backoff_timing():
    """Test that exponential backoff timing works correctly."""
    logger.info("🧪 Testing exponential backoff timing")
    
    import time
    
    with patch('app.services.mcp_http_client.Client') as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client
        
        # All connection attempts fail
        mock_client.__aenter__.side_effect = ConnectionError("Always fails")
        
        client = FastMCPHTTPClient(
            service_name="test_service",
            server_url="http://localhost:9999/mcp",
            retry_attempts=3,
            max_backoff_time=5,
            base_backoff_time=0.5
        )
        
        start_time = time.time()
        
        try:
            await client.connect()
        except MCPHTTPConnectionError:
            # Expected to fail after all retries
            pass
        
        elapsed_time = time.time() - start_time
        
        # Should have taken at least the backoff times:
        # Attempt 1: immediate
        # Attempt 2: ~0.5s backoff (with jitter 0.4-0.6s)
        # Attempt 3: ~1.0s backoff (with jitter 0.8-1.2s)
        # Total: at least ~1.2s (conservative estimate with jitter)
        
        logger.info(f"Total retry time: {elapsed_time:.2f}s")
        assert elapsed_time >= 1.0, f"Backoff timing too fast: {elapsed_time}s"
        assert elapsed_time <= 10.0, f"Backoff timing too slow: {elapsed_time}s"
        
        logger.info("✅ Exponential backoff timing test passed")


async def test_performance_metrics():
    """Test that performance metrics include retry information."""
    logger.info("🧪 Testing performance metrics with retry information")
    
    with patch('app.services.mcp_http_client.Client') as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client
        
        # First attempt fails, second succeeds
        mock_client.__aenter__.side_effect = [
            ConnectionError("First attempt fails"),
            None  # Success on second attempt
        ]
        
        client = FastMCPHTTPClient(
            service_name="test_service",
            server_url="http://localhost:9999/mcp",
            retry_attempts=3
        )
        
        try:
            await client.connect()
            
            # Get performance metrics
            metrics = client.get_performance_metrics()
            
            logger.info("✅ Performance metrics test passed")
            assert "retry_count" in metrics
            assert "retry_rate" in metrics
            assert "retry_configuration" in metrics
            assert metrics["retry_count"] == 1  # One retry before success
            assert metrics["retry_configuration"]["max_retry_attempts"] == 3
            
            await client.disconnect()
            
        except Exception as e:
            logger.error(f"❌ Performance metrics test failed: {e}")
            raise


async def main():
    """Run all retry logic tests."""
    logger.info("🚀 Starting MCP HTTP client retry logic tests")
    
    try:
        await test_connection_retry_logic()
        await test_tool_call_retry_logic()
        await test_mock_mode_bypass()
        await test_exponential_backoff_timing()
        await test_performance_metrics()
        
        logger.info("🎉 All retry logic tests passed successfully!")
        
    except Exception as e:
        logger.error(f"💥 Test suite failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())