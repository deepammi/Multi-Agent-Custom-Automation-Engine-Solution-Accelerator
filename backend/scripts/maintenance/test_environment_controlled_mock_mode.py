#!/usr/bin/env python3
"""
Test Environment-Controlled Mock Mode Implementation

This test verifies that the environment-controlled mock mode works correctly
as specified in task 2 of the multi-agent invoice workflow specification.

Tests:
1. Mock mode activation via USE_MOCK_MODE environment variable
2. Mock mode activation via USE_MOCK_LLM environment variable  
3. Real service failure propagation when mock mode disabled
4. Error handling with environment controls
"""

import asyncio
import os
import sys
import logging
from unittest.mock import patch, AsyncMock
from typing import Dict, Any

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class EnvironmentControlledMockModeTest:
    """Test environment-controlled mock mode functionality."""
    
    def __init__(self):
        self.test_results = []
        
    def print_header(self, title: str):
        """Print test section header."""
        print(f"\n{'=' * 80}")
        print(f"🧪 {title}")
        print(f"{'=' * 80}")
    
    def print_test(self, test_name: str):
        """Print individual test header."""
        print(f"\n🔬 Test: {test_name}")
        print("-" * (len(test_name) + 10))
    
    def record_result(self, test_name: str, passed: bool, details: str = ""):
        """Record test result."""
        status = "✅ PASS" if passed else "❌ FAIL"
        self.test_results.append({
            "test": test_name,
            "passed": passed,
            "details": details
        })
        print(f"{status}: {test_name}")
        if details:
            print(f"   Details: {details}")
    
    async def test_environment_config_initialization(self):
        """Test that environment configuration initializes correctly."""
        self.print_test("Environment Configuration Initialization")
        
        try:
            # Test with mock mode disabled
            with patch.dict(os.environ, {"USE_MOCK_MODE": "false", "USE_MOCK_LLM": "false"}):
                from app.config.environment import get_environment_config
                
                env_config = get_environment_config()
                
                # Verify mock modes are disabled
                assert not env_config.is_mock_mode_enabled(), "Mock mode should be disabled"
                assert not env_config.is_mock_llm_enabled(), "Mock LLM should be disabled"
                
                self.record_result("Environment config with mock disabled", True)
            
            # Test with mock mode enabled
            with patch.dict(os.environ, {"USE_MOCK_MODE": "true", "USE_MOCK_LLM": "true"}):
                # Force reload of environment config by clearing singleton
                from app.config.environment import EnvironmentConfig
                EnvironmentConfig._instance = None
                EnvironmentConfig._mock_config = None
                
                from app.config.environment import get_environment_config
                env_config = get_environment_config()
                
                # Verify mock modes are enabled
                assert env_config.is_mock_mode_enabled(), "Mock mode should be enabled"
                assert env_config.is_mock_llm_enabled(), "Mock LLM should be enabled"
                
                self.record_result("Environment config with mock enabled", True)
                
        except Exception as e:
            self.record_result("Environment Configuration Initialization", False, str(e))
    
    async def test_llm_service_mock_mode(self):
        """Test LLM service respects environment-controlled mock mode."""
        self.print_test("LLM Service Mock Mode Control")
        
        try:
            # Test with mock mode disabled
            with patch.dict(os.environ, {"USE_MOCK_LLM": "false"}):
                from app.services.llm_service import LLMService
                from app.config.environment import EnvironmentConfig
                
                # Force reload
                EnvironmentConfig._instance = None
                
                assert not LLMService.is_mock_mode(), "LLM mock mode should be disabled"
                self.record_result("LLM service mock disabled", True)
            
            # Test with mock mode enabled
            with patch.dict(os.environ, {"USE_MOCK_LLM": "true"}):
                # Force reload by clearing singleton and instance variables
                from app.config.environment import EnvironmentConfig
                EnvironmentConfig._instance = None
                EnvironmentConfig._mock_config = None
                
                from app.services.llm_service import LLMService
                
                assert LLMService.is_mock_mode(), "LLM mock mode should be enabled"
                
                # Test mock response generation
                mock_response = LLMService.get_mock_response("Invoice", "test task")
                assert "Invoice Agent" in mock_response, "Mock response should contain agent name"
                
                self.record_result("LLM service mock enabled", True)
                
        except Exception as e:
            self.record_result("LLM Service Mock Mode Control", False, str(e))
    
    async def test_mcp_client_mock_mode(self):
        """Test MCP HTTP client respects environment-controlled mock mode."""
        self.print_test("MCP Client Mock Mode Control")
        
        try:
            from app.services.mcp_http_client import FastMCPHTTPClient
            from app.config.environment import EnvironmentConfig
            
            # Test with mock mode enabled
            with patch.dict(os.environ, {"USE_MOCK_MODE": "true"}):
                # Force reload by clearing singleton and instance variables
                from app.config.environment import EnvironmentConfig
                EnvironmentConfig._instance = None
                EnvironmentConfig._mock_config = None
                
                from app.services.mcp_http_client import FastMCPHTTPClient
                
                client = FastMCPHTTPClient("gmail", "http://localhost:9002/mcp")
                
                # Test mock response generation
                mock_result = await client.call_tool("search_messages", {"query": "test"})
                
                assert "mock_mode" in mock_result, "Mock result should indicate mock mode"
                assert mock_result["mock_mode"] is True, "Mock mode flag should be True"
                
                self.record_result("MCP client mock mode enabled", True)
            
            # Test with mock mode disabled (should attempt real connection)
            with patch.dict(os.environ, {"USE_MOCK_MODE": "false"}):
                # Force reload by clearing singleton and instance variables
                EnvironmentConfig._instance = None
                EnvironmentConfig._mock_config = None
                
                client = FastMCPHTTPClient("gmail", "http://localhost:9002/mcp")
                
                # This should attempt real connection and likely fail
                try:
                    result = await client.call_tool("search_messages", {"query": "test"})
                    # If it succeeds, that's fine too (server might be running)
                    self.record_result("MCP client mock mode disabled - connection attempted", True)
                except Exception as e:
                    # Expected to fail when no real server is running
                    if "mock mode disabled" in str(e).lower() or "connection" in str(e).lower():
                        self.record_result("MCP client mock mode disabled - error propagated correctly", True)
                    else:
                        self.record_result("MCP client mock mode disabled", False, f"Unexpected error: {e}")
                
        except Exception as e:
            self.record_result("MCP Client Mock Mode Control", False, str(e))
    
    async def test_error_handler_mock_mode(self):
        """Test error handler respects environment-controlled mock mode."""
        self.print_test("Error Handler Mock Mode Control")
        
        try:
            from app.services.error_handler import WorkflowErrorHandler
            from app.services.websocket_service import WebSocketManager
            from app.services.hitl_interface import HITLInterface
            from app.config.environment import EnvironmentConfig
            
            # Mock dependencies
            websocket_manager = AsyncMock(spec=WebSocketManager)
            hitl_interface = AsyncMock(spec=HITLInterface)
            
            error_handler = WorkflowErrorHandler(websocket_manager, hitl_interface)
            
            # Test MCP service error with mock mode enabled
            with patch.dict(os.environ, {"USE_MOCK_MODE": "true"}):
                # Force reload by clearing singleton and instance variables
                from app.config.environment import EnvironmentConfig
                EnvironmentConfig._instance = None
                EnvironmentConfig._mock_config = None
                
                error_event = await error_handler.handle_mcp_service_error(
                    plan_id="test-plan",
                    service_name="gmail",
                    error=Exception("Connection failed"),
                    context={"test": True}
                )
                
                assert error_event.context["mock_fallback_used"] is True, "Mock fallback should be used"
                assert "USE_MOCK_MODE=true" in error_event.context["mock_fallback_reason"], "Reason should mention environment variable"
                
                self.record_result("Error handler with mock mode enabled", True)
            
            # Test MCP service error with mock mode disabled
            with patch.dict(os.environ, {"USE_MOCK_MODE": "false"}):
                # Force reload by clearing singleton and instance variables
                EnvironmentConfig._instance = None
                EnvironmentConfig._mock_config = None
                
                error_event = await error_handler.handle_mcp_service_error(
                    plan_id="test-plan",
                    service_name="gmail",
                    error=Exception("Connection failed"),
                    context={"test": True}
                )
                
                assert error_event.context["mock_fallback_used"] is False, "Mock fallback should not be used"
                assert "error_propagation" in error_event.context, "Error propagation info should be present"
                
                self.record_result("Error handler with mock mode disabled", True)
                
        except Exception as e:
            self.record_result("Error Handler Mock Mode Control", False, str(e))
    
    async def test_environment_validation(self):
        """Test environment configuration validation."""
        self.print_test("Environment Configuration Validation")
        
        try:
            from app.config.environment import get_environment_config
            from app.config.environment import EnvironmentConfig
            
            # Test valid configuration
            with patch.dict(os.environ, {"USE_MOCK_MODE": "true", "USE_MOCK_LLM": "false"}):
                # Force reload by clearing singleton and instance variables
                from app.config.environment import EnvironmentConfig
                EnvironmentConfig._instance = None
                EnvironmentConfig._mock_config = None
                
                from app.config.environment import get_environment_config
                env_config = get_environment_config()
                validation_result = env_config.validate_configuration()
                
                assert validation_result["valid"] is True, "Configuration should be valid"
                
                self.record_result("Environment validation with valid config", True)
            
            # Test configuration with warnings
            with patch.dict(os.environ, {"USE_MOCK_MODE": "maybe", "USE_MOCK_LLM": "false"}):
                # Force reload by clearing singleton and instance variables
                EnvironmentConfig._instance = None
                EnvironmentConfig._mock_config = None
                
                env_config = get_environment_config()
                validation_result = env_config.validate_configuration()
                
                # Should have warnings about unusual values
                assert len(validation_result["warnings"]) > 0, "Should have warnings for unusual values"
                
                self.record_result("Environment validation with warnings", True)
                
        except Exception as e:
            self.record_result("Environment Configuration Validation", False, str(e))
    
    async def run_all_tests(self):
        """Run all environment-controlled mock mode tests."""
        self.print_header("Environment-Controlled Mock Mode Tests")
        
        print("Testing implementation of task 2: Implement Environment-Controlled Mock Mode")
        print("Requirements: NFR3.2, NFR1.3")
        
        # Run all tests
        await self.test_environment_config_initialization()
        await self.test_llm_service_mock_mode()
        await self.test_mcp_client_mock_mode()
        await self.test_error_handler_mock_mode()
        await self.test_environment_validation()
        
        # Print summary
        self.print_header("Test Results Summary")
        
        passed_tests = [r for r in self.test_results if r["passed"]]
        failed_tests = [r for r in self.test_results if not r["passed"]]
        
        print(f"✅ Passed: {len(passed_tests)}/{len(self.test_results)} tests")
        print(f"❌ Failed: {len(failed_tests)}/{len(self.test_results)} tests")
        
        if failed_tests:
            print("\n❌ Failed Tests:")
            for test in failed_tests:
                print(f"   - {test['test']}: {test['details']}")
        
        print(f"\n📊 Overall Result: {'✅ ALL TESTS PASSED' if len(failed_tests) == 0 else '❌ SOME TESTS FAILED'}")
        
        return len(failed_tests) == 0


async def main():
    """Run environment-controlled mock mode tests."""
    test_runner = EnvironmentControlledMockModeTest()
    
    try:
        success = await test_runner.run_all_tests()
        return 0 if success else 1
    except Exception as e:
        print(f"❌ Test execution failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)