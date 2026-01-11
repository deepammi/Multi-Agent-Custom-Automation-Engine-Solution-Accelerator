#!/usr/bin/env python3
"""
Simple Test for Environment-Controlled Mock Mode

This test directly verifies the core functionality without complex singleton management.
"""

import os
import sys
import asyncio
from unittest.mock import patch

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_environment_parsing():
    """Test environment variable parsing directly."""
    print("🧪 Testing Environment Variable Parsing")
    
    # Test with mock mode enabled
    with patch.dict(os.environ, {"USE_MOCK_MODE": "true", "USE_MOCK_LLM": "true"}):
        # Import fresh instance
        from app.config.environment import EnvironmentConfig
        config = EnvironmentConfig()
        
        assert config.is_mock_mode_enabled(), "Mock mode should be enabled"
        assert config.is_mock_llm_enabled(), "Mock LLM should be enabled"
        print("✅ Mock mode enabled correctly")
    
    # Test with mock mode disabled
    with patch.dict(os.environ, {"USE_MOCK_MODE": "false", "USE_MOCK_LLM": "false"}):
        config = EnvironmentConfig()
        
        assert not config.is_mock_mode_enabled(), "Mock mode should be disabled"
        assert not config.is_mock_llm_enabled(), "Mock LLM should be disabled"
        print("✅ Mock mode disabled correctly")


async def test_mcp_mock_response():
    """Test MCP client mock response generation."""
    print("\n🧪 Testing MCP Mock Response Generation")
    
    from app.services.mcp_http_client import FastMCPHTTPClient
    
    client = FastMCPHTTPClient("gmail", "http://localhost:9002/mcp")
    
    # Test Gmail mock response
    gmail_mock = client._generate_gmail_mock_response("search_messages", {"query": "test"})
    assert "messages" in gmail_mock, "Gmail mock should have messages"
    assert gmail_mock["mock_mode"] is True, "Should indicate mock mode"
    print("✅ Gmail mock response generated correctly")
    
    # Test Salesforce mock response
    sf_mock = client._generate_salesforce_mock_response("search_records", {"search_term": "test"})
    assert "records" in sf_mock, "Salesforce mock should have records"
    assert sf_mock["mock_mode"] is True, "Should indicate mock mode"
    print("✅ Salesforce mock response generated correctly")
    
    # Test Bill.com mock response
    bill_mock = client._generate_bill_com_mock_response("get_bill_com_bills", {"vendor_name": "Test Vendor"})
    assert "bills" in bill_mock, "Bill.com mock should have bills"
    assert bill_mock["mock_mode"] is True, "Should indicate mock mode"
    print("✅ Bill.com mock response generated correctly")


def test_llm_mock_response():
    """Test LLM mock response generation."""
    print("\n🧪 Testing LLM Mock Response Generation")
    
    from app.services.llm_service import LLMService
    
    # Test Invoice agent mock
    invoice_mock = LLMService.get_mock_response("Invoice", "test task")
    assert "Invoice Agent" in invoice_mock, "Should contain agent name"
    assert "invoice accuracy" in invoice_mock.lower(), "Should contain relevant content"
    print("✅ Invoice agent mock response generated correctly")
    
    # Test Closing agent mock
    closing_mock = LLMService.get_mock_response("Closing", "test task")
    assert "Closing Agent" in closing_mock, "Should contain agent name"
    assert "reconciliation" in closing_mock.lower(), "Should contain relevant content"
    print("✅ Closing agent mock response generated correctly")


async def test_environment_controlled_behavior():
    """Test that services respect environment variables."""
    print("\n🧪 Testing Environment-Controlled Behavior")
    
    # Test with mock mode enabled
    with patch.dict(os.environ, {"USE_MOCK_MODE": "true"}):
        from app.config.environment import EnvironmentConfig
        config = EnvironmentConfig()
        
        # Should use mock data
        should_mock = config.should_use_mock_data("mcp")
        assert should_mock, "Should use mock data when USE_MOCK_MODE=true"
        print("✅ Mock mode correctly enabled via environment")
    
    # Test with mock mode disabled
    with patch.dict(os.environ, {"USE_MOCK_MODE": "false"}):
        config = EnvironmentConfig()
        
        # Should not use mock data
        should_mock = config.should_use_mock_data("mcp")
        assert not should_mock, "Should not use mock data when USE_MOCK_MODE=false"
        print("✅ Mock mode correctly disabled via environment")


def main():
    """Run simple mock mode tests."""
    print("🚀 Simple Environment-Controlled Mock Mode Tests")
    print("=" * 60)
    
    try:
        # Run tests
        test_environment_parsing()
        asyncio.run(test_mcp_mock_response())
        test_llm_mock_response()
        asyncio.run(test_environment_controlled_behavior())
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED - Environment-controlled mock mode working correctly!")
        return 0
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)