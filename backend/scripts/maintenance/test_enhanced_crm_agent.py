#!/usr/bin/env python3
"""
Test script for enhanced CRM agent improvements.

This script tests the enhancements implemented in Task 4.3:
- Improved Salesforce MCP server connection handling
- Better error parsing for Salesforce API responses
- Optimized query patterns for better data retrieval
- Enhanced retry logic and timeout handling
"""

import asyncio
import logging
import os
import sys
from unittest.mock import AsyncMock, patch, MagicMock

# Add the backend directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from app.agents.crm_agent_http import CRMAgentHTTP, SalesforceAPIError
from app.services.mcp_http_client import MCPHTTPError, MCPHTTPConnectionError, MCPHTTPTimeoutError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_salesforce_error_parsing():
    """Test enhanced Salesforce API error parsing."""
    logger.info("🧪 Testing Salesforce API error parsing")
    
    agent = CRMAgentHTTP()
    
    # Test various Salesforce error response formats
    test_cases = [
        # Standard Salesforce API error format
        {
            "response": {"errorCode": "INVALID_LOGIN", "message": "Invalid username, password, security token; or user locked out"},
            "expected_error": "INVALID_LOGIN",
            "expected_message": "Invalid username, password, security token; or user locked out"
        },
        # SOQL error format (array of errors)
        {
            "response": {"errors": [{"errorCode": "MALFORMED_QUERY", "message": "Unexpected token 'FROM'"}]},
            "expected_error": "MALFORMED_QUERY",
            "expected_message": "Unexpected token 'FROM'"
        },
        # Success=false format
        {
            "response": {"success": False, "message": "Operation failed"},
            "expected_error": "OPERATION_FAILED",
            "expected_message": "Operation failed"
        }
    ]
    
    for i, test_case in enumerate(test_cases):
        try:
            agent._validate_salesforce_response(test_case["response"])
            logger.error(f"❌ Test case {i+1} should have raised SalesforceAPIError")
            return False
        except SalesforceAPIError as e:
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
        agent._validate_salesforce_response({"success": True, "records": [{"Id": "123", "Name": "Test"}]})
        logger.info("✅ Valid response test passed")
    except Exception as e:
        logger.error(f"❌ Valid response test failed: {e}")
        return False
    
    logger.info("✅ Salesforce API error parsing test passed")
    return True


async def test_query_optimization():
    """Test SOQL query optimization for better data retrieval."""
    logger.info("🧪 Testing SOQL query optimization")
    
    agent = CRMAgentHTTP()
    
    # Test optimized query generation
    test_cases = [
        {
            "operation": "get_accounts",
            "params": {"account_name": "Acme Corp", "limit": 10},
            "should_optimize": True
        },
        {
            "operation": "get_opportunities", 
            "params": {"limit": 5},
            "should_optimize": True
        },
        {
            "operation": "get_contacts",
            "params": {"account_name": "Test Company", "limit": 3},
            "should_optimize": True
        }
    ]
    
    for test_case in test_cases:
        optimized_query = agent._optimize_query_for_salesforce(
            test_case["operation"],
            **test_case["params"]
        )
        
        if test_case["should_optimize"]:
            if optimized_query:
                logger.info(f"✅ {test_case['operation']} optimization generated query: {len(optimized_query)} chars")
                # Verify query contains expected elements
                if "SELECT" in optimized_query and "FROM" in optimized_query:
                    logger.info(f"✅ Query structure valid for {test_case['operation']}")
                else:
                    logger.error(f"❌ Invalid query structure for {test_case['operation']}")
                    return False
            else:
                logger.error(f"❌ Expected optimization for {test_case['operation']} but got None")
                return False
        else:
            if optimized_query is None:
                logger.info(f"✅ No optimization for {test_case['operation']} as expected")
            else:
                logger.error(f"❌ Unexpected optimization for {test_case['operation']}")
                return False
    
    logger.info("✅ SOQL query optimization test passed")
    return True


async def test_enhanced_retry_logic():
    """Test enhanced retry logic with exponential backoff."""
    logger.info("🧪 Testing enhanced retry logic")
    
    # Mock the MCP manager to simulate failures
    mock_manager = AsyncMock()
    
    # First 2 calls fail, 3rd succeeds
    mock_manager.call_tool.side_effect = [
        MCPHTTPConnectionError("Connection failed", "salesforce", "CONNECTION_FAILED"),
        MCPHTTPTimeoutError("Timeout", "salesforce", "TIMEOUT"),
        {"result": "text='{'success': True, 'records': [{'Id': '123', 'Name': 'Test Account'}]}'"}  # Success
    ]
    
    agent = CRMAgentHTTP(mcp_manager=mock_manager)
    
    try:
        # This should succeed after 3 attempts
        result = await agent.get_accounts(service='salesforce')
        
        logger.info("✅ Enhanced retry logic test passed")
        assert "success" in result or "records" in result
        assert mock_manager.call_tool.call_count == 3  # Should have retried twice
        return True
        
    except Exception as e:
        logger.error(f"❌ Enhanced retry logic test failed: {e}")
        return False


async def test_performance_metrics():
    """Test performance metrics tracking including query optimization."""
    logger.info("🧪 Testing performance metrics tracking")
    
    mock_manager = AsyncMock()
    mock_manager.call_tool.return_value = {"result": "text='{'success': True, 'records': []}'"}
    
    agent = CRMAgentHTTP(mcp_manager=mock_manager)
    
    # Make some calls to generate metrics
    await agent.get_accounts(service='salesforce')
    await agent.get_opportunities(service='salesforce')
    
    metrics = agent.get_performance_metrics()
    
    expected_fields = ['total_calls', 'error_count', 'success_rate', 'last_successful_call', 
                      'query_optimization_count', 'supported_services', 'salesforce_settings']
    
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
    
    # Check that query optimization was used
    if metrics['query_optimization_count'] < 1:
        logger.error(f"❌ Expected query optimization to be used, got count: {metrics['query_optimization_count']}")
        return False
    
    logger.info("✅ Performance metrics test passed")
    return True


async def test_enhanced_health_check():
    """Test enhanced health check with Salesforce diagnostics."""
    logger.info("🧪 Testing enhanced health check")
    
    # Mock the MCP manager health status
    mock_manager = AsyncMock()
    
    # Mock health status object
    mock_health = MagicMock()
    mock_health.is_healthy = True
    mock_health.last_check = asyncio.get_event_loop().time()
    mock_health.response_time_ms = 200
    mock_health.available_tools = 6
    mock_health.error_message = None
    mock_health.connection_status = "connected"
    
    # Convert to datetime for isoformat
    from datetime import datetime
    mock_health.last_check = datetime.now()
    
    mock_manager.get_service_health.return_value = mock_health
    
    # Mock successful SOQL query for API test
    mock_manager.call_tool.return_value = {"result": "text='{'success': True, 'records': [{'Id': '123'}]}'"}
    
    agent = CRMAgentHTTP(mcp_manager=mock_manager)
    
    try:
        health_status = await agent.check_service_health('salesforce')
        
        # Check for enhanced fields
        expected_fields = ['service', 'is_healthy', 'salesforce_specific', 'api_test']
        
        for field in expected_fields:
            if field not in health_status:
                logger.error(f"❌ Missing field in health status: {field}")
                return False
        
        # Check Salesforce specific settings
        salesforce_specific = health_status['salesforce_specific']
        if 'max_retries' not in salesforce_specific or 'timeout' not in salesforce_specific:
            logger.error("❌ Missing Salesforce specific settings")
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


async def test_salesforce_api_error_handling():
    """Test that Salesforce API errors are not retried."""
    logger.info("🧪 Testing Salesforce API error handling (no retry)")
    
    mock_manager = AsyncMock()
    
    # Simulate Salesforce API error response
    mock_manager.call_tool.return_value = {
        "result": "text='{'errorCode': 'INVALID_SESSION_ID', 'message': 'Session expired or invalid'}'"
    }
    
    agent = CRMAgentHTTP(mcp_manager=mock_manager)
    
    try:
        await agent.get_accounts(service='salesforce')
        logger.error("❌ Should have raised SalesforceAPIError")
        return False
        
    except SalesforceAPIError as e:
        # Should only call once (no retries for API errors)
        if mock_manager.call_tool.call_count == 1:
            logger.info(f"✅ Salesforce API error correctly not retried: {e.error_code}")
            return True
        else:
            logger.error(f"❌ Expected 1 call, got {mock_manager.call_tool.call_count}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Unexpected error type: {e}")
        return False


async def test_optimized_query_integration():
    """Test that optimized queries are used in real method calls."""
    logger.info("🧪 Testing optimized query integration")
    
    mock_manager = AsyncMock()
    
    # Mock successful SOQL query response
    mock_manager.call_tool.return_value = {
        "result": "text='{'success': True, 'records': [{'Id': '123', 'Name': 'Acme Corp'}]}'"
    }
    
    agent = CRMAgentHTTP(mcp_manager=mock_manager)
    
    try:
        # This should trigger query optimization for account search
        result = await agent.get_accounts(service='salesforce', account_name='Acme Corp', limit=5)
        
        # Verify the call was made to SOQL query tool (optimization path)
        call_args = mock_manager.call_tool.call_args
        if call_args:
            service, tool_name, arguments = call_args[0]
            if tool_name == 'salesforce_soql_query' and 'query' in arguments:
                logger.info("✅ Optimized query integration test passed - used SOQL query")
                return True
            else:
                logger.error(f"❌ Expected SOQL query tool, got: {tool_name}")
                return False
        else:
            logger.error("❌ No MCP tool call made")
            return False
            
    except Exception as e:
        logger.error(f"❌ Optimized query integration test failed: {e}")
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
        agent = CRMAgentHTTP()
        
        # This should return mock data
        result = await agent.get_accounts(service='salesforce')
        
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
    """Run all enhanced CRM agent tests."""
    logger.info("🚀 Starting enhanced CRM agent tests")
    
    tests = [
        test_salesforce_error_parsing,
        test_query_optimization,
        test_enhanced_retry_logic,
        test_performance_metrics,
        test_enhanced_health_check,
        test_salesforce_api_error_handling,
        test_optimized_query_integration,
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
        logger.info("🎉 All enhanced CRM agent tests passed!")
        return 0
    else:
        logger.error(f"💥 {failed} tests failed")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)