#!/usr/bin/env python3
"""
Test script for enhanced AccountsPayable agent improvements.

This script tests the enhancements implemented in Task 4.2:
- Improved Bill.com MCP server connection handling
- Better error parsing for Bill.com API responses
- Connection pooling for HTTP MCP client
- Enhanced retry logic and timeout handling
"""

import asyncio
import logging
import os
import sys
from unittest.mock import AsyncMock, patch, MagicMock

# Add the backend directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from app.agents.accounts_payable_agent_http import AccountsPayableAgentHTTP, BillComAPIError
from app.services.mcp_http_client import MCPHTTPError, MCPHTTPConnectionError, MCPHTTPTimeoutError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_bill_com_error_parsing():
    """Test enhanced Bill.com API error parsing."""
    logger.info("🧪 Testing Bill.com API error parsing")
    
    agent = AccountsPayableAgentHTTP()
    
    # Test various Bill.com error response formats
    test_cases = [
        # Standard Bill.com API error format
        {
            "response": {"error_code": "AUTH_FAILED", "error_message": "Invalid credentials"},
            "expected_error": "AUTH_FAILED",
            "expected_message": "Invalid credentials"
        },
        # Alternative error format
        {
            "response": {"error": "TIMEOUT", "message": "Request timed out"},
            "expected_error": "TIMEOUT",
            "expected_message": "Request timed out"
        },
        # Nested error format
        {
            "response": {"result": {"error_code": "PERMISSION_DENIED", "error_message": "Access denied"}},
            "expected_error": "PERMISSION_DENIED",
            "expected_message": "Access denied"
        }
    ]
    
    for i, test_case in enumerate(test_cases):
        try:
            agent._validate_bill_com_response(test_case["response"])
            logger.error(f"❌ Test case {i+1} should have raised BillComAPIError")
            return False
        except BillComAPIError as e:
            if e.error_code == test_case["expected_error"] and e.error_message == test_case["expected_message"]:
                logger.info(f"✅ Test case {i+1} passed: {e.error_code} - {e.error_message}")
            else:
                logger.error(f"❌ Test case {i+1} failed: Expected {test_case['expected_error']}, got {e.error_code}")
                return False
        except Exception as e:
            logger.error(f"❌ Test case {i+1} failed with unexpected error: {e}")
            return False
    
    # Test valid response (should not raise error)
    try:
        agent._validate_bill_com_response({"response_data": [{"id": "123", "amount": 100}]})
        logger.info("✅ Valid response test passed")
    except Exception as e:
        logger.error(f"❌ Valid response test failed: {e}")
        return False
    
    logger.info("✅ Bill.com API error parsing test passed")
    return True


async def test_enhanced_retry_logic():
    """Test enhanced retry logic with exponential backoff."""
    logger.info("🧪 Testing enhanced retry logic")
    
    # Mock the MCP manager to simulate failures
    mock_manager = AsyncMock()
    
    # First 2 calls fail, 3rd succeeds
    mock_manager.call_tool.side_effect = [
        MCPHTTPConnectionError("Connection failed", "bill_com", "CONNECTION_FAILED"),
        MCPHTTPTimeoutError("Timeout", "bill_com", "TIMEOUT"),
        {"response_data": [{"id": "123", "vendor": "Test Vendor"}]}  # Success
    ]
    
    agent = AccountsPayableAgentHTTP(mcp_manager=mock_manager)
    
    try:
        # This should succeed after 3 attempts
        result = await agent.get_bills(service='bill_com')
        
        logger.info("✅ Enhanced retry logic test passed")
        assert "response_data" in result
        assert mock_manager.call_tool.call_count == 3  # Should have retried twice
        return True
        
    except Exception as e:
        logger.error(f"❌ Enhanced retry logic test failed: {e}")
        return False


async def test_performance_metrics():
    """Test performance metrics tracking."""
    logger.info("🧪 Testing performance metrics tracking")
    
    mock_manager = AsyncMock()
    mock_manager.call_tool.return_value = {"response_data": []}
    
    agent = AccountsPayableAgentHTTP(mcp_manager=mock_manager)
    
    # Make some calls to generate metrics
    await agent.get_bills(service='bill_com')
    await agent.get_vendors(service='bill_com')
    
    metrics = agent.get_performance_metrics()
    
    expected_fields = ['total_calls', 'error_count', 'success_rate', 'last_successful_call', 'supported_services', 'bill_com_settings']
    
    for field in expected_fields:
        if field not in metrics:
            logger.error(f"❌ Missing field in metrics: {field}")
            return False
    
    if metrics['total_calls'] != 2:
        logger.error(f"❌ Expected 2 total calls, got {metrics['total_calls']}")
        return False
    
    if metrics['success_rate'] != 1.0:
        logger.error(f"❌ Expected success rate 1.0, got {metrics['success_rate']}")
        return False
    
    logger.info("✅ Performance metrics test passed")
    return True


async def test_enhanced_health_check():
    """Test enhanced health check with Bill.com diagnostics."""
    logger.info("🧪 Testing enhanced health check")
    
    # Mock the MCP manager health status
    mock_manager = AsyncMock()
    
    # Mock health status object
    mock_health = MagicMock()
    mock_health.is_healthy = True
    mock_health.last_check = asyncio.get_event_loop().time()
    mock_health.response_time_ms = 150
    mock_health.available_tools = 5
    mock_health.error_message = None
    mock_health.connection_status = "connected"
    
    # Convert to datetime for isoformat
    from datetime import datetime
    mock_health.last_check = datetime.now()
    
    mock_manager.get_service_health.return_value = mock_health
    
    # Mock successful vendor call for API test
    mock_manager.call_tool.return_value = {"response_data": []}
    
    agent = AccountsPayableAgentHTTP(mcp_manager=mock_manager)
    
    try:
        health_status = await agent.check_service_health('bill_com')
        
        # Check for enhanced fields
        expected_fields = ['service', 'is_healthy', 'bill_com_specific', 'api_test']
        
        for field in expected_fields:
            if field not in health_status:
                logger.error(f"❌ Missing field in health status: {field}")
                return False
        
        # Check Bill.com specific settings
        bill_com_specific = health_status['bill_com_specific']
        if 'max_retries' not in bill_com_specific or 'timeout' not in bill_com_specific:
            logger.error("❌ Missing Bill.com specific settings")
            return False
        
        # Check API test results
        api_test = health_status['api_test']
        if not api_test.get('success'):
            logger.error(f"❌ API test failed: {api_test}")
            return False
        
        logger.info("✅ Enhanced health check test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Enhanced health check test failed: {e}")
        return False


async def test_bill_com_api_error_handling():
    """Test that Bill.com API errors are not retried."""
    logger.info("🧪 Testing Bill.com API error handling (no retry)")
    
    mock_manager = AsyncMock()
    
    # Simulate Bill.com API error response
    mock_manager.call_tool.return_value = {
        "error_code": "INVALID_SESSION",
        "error_message": "Session expired"
    }
    
    agent = AccountsPayableAgentHTTP(mcp_manager=mock_manager)
    
    try:
        await agent.get_bills(service='bill_com')
        logger.error("❌ Should have raised BillComAPIError")
        return False
        
    except BillComAPIError as e:
        # Should only call once (no retries for API errors)
        if mock_manager.call_tool.call_count == 1:
            logger.info(f"✅ Bill.com API error correctly not retried: {e.error_code}")
            return True
        else:
            logger.error(f"❌ Expected 1 call, got {mock_manager.call_tool.call_count}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Unexpected error type: {e}")
        return False


async def test_mock_mode_compatibility():
    """Test that enhanced agent works with mock mode."""
    logger.info("🧪 Testing mock mode compatibility")
    
    # Enable mock mode
    os.environ['USE_MOCK_MODE'] = 'true'
    
    # Force reload of environment config
    from app.config.environment import _env_config
    import app.config.environment
    app.config.environment._env_config = None
    
    try:
        agent = AccountsPayableAgentHTTP()
        
        # This should return mock data
        result = await agent.get_bills(service='bill_com')
        
        # Check for mock data indicators
        if 'mock_mode' in result or 'result' in result:
            logger.info("✅ Mock mode compatibility test passed")
            return True
        else:
            logger.error(f"❌ Expected mock data, got: {result}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Mock mode compatibility test failed: {e}")
        return False
    finally:
        # Reset mock mode
        os.environ['USE_MOCK_MODE'] = 'false'
        app.config.environment._env_config = None


async def main():
    """Run all enhanced AccountsPayable agent tests."""
    logger.info("🚀 Starting enhanced AccountsPayable agent tests")
    
    tests = [
        test_bill_com_error_parsing,
        test_enhanced_retry_logic,
        test_performance_metrics,
        test_enhanced_health_check,
        test_bill_com_api_error_handling,
        test_mock_mode_compatibility
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if await test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            logger.error(f"💥 Test {test.__name__} crashed: {e}")
            failed += 1
    
    logger.info(f"🎯 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        logger.info("🎉 All enhanced AccountsPayable agent tests passed!")
        return 0
    else:
        logger.error(f"💥 {failed} tests failed")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)