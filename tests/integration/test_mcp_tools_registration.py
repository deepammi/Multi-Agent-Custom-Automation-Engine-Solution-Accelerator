#!/usr/bin/env python3
"""
MCP Tools Registration Test Suite
Tests MCP tool registration and invocation for Bill.com integration.
"""

import os
import sys
import pytest
import asyncio
import json
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

# Add project paths
project_root = Path(__file__).parent.parent.parent
mcp_server_path = project_root / "src" / "mcp_server"
sys.path.insert(0, str(mcp_server_path))


class TestMCPToolRegistration:
    """Test MCP tool registration and metadata."""
    
    def test_bill_com_tools_service_registration(self):
        """Test Bill.com tools service can be registered."""
        try:
            from core.bill_com_tools import BillComService
            
            service = BillComService()
            
            # Test service properties
            assert hasattr(service, "domain")
            assert service.domain == "bill_com"
            
            # Test that service has expected methods
            expected_methods = [
                "get_bill_com_invoices",
                "get_bill_com_invoice_details", 
                "search_bill_com_invoices",
                "get_bill_com_vendors"
            ]
            
            for method in expected_methods:
                assert hasattr(service, method), f"Missing method: {method}"
            
        except ImportError as e:
            pytest.skip(f"FastMCP not available: {e}")
    
    def test_health_tools_service_registration(self):
        """Test health tools service registration."""
        from services.bill_com_health_tools_service import BillComHealthToolsService
        
        service = BillComHealthToolsService()
        
        # Test service properties
        assert service.domain == "bill_com_health"
        
        # Test that service has expected methods
        expected_methods = [
            "bill_com_health_check",
            "bill_com_config_validation",
            "bill_com_setup_guide",
            "bill_com_connection_test",
            "bill_com_diagnostics"
        ]
        
        for method in expected_methods:
            assert hasattr(service, method), f"Missing method: {method}"
    
    def test_audit_tools_service_registration(self):
        """Test audit tools service registration."""
        from services.audit_tools_service import AuditToolsService
        
        service = AuditToolsService()
        
        # Test service properties
        assert service.domain == "audit"
        
        # Test that service has expected methods
        expected_methods = [
            "get_audit_trail",
            "get_modification_history", 
            "detect_audit_exceptions",
            "generate_audit_report",
            "get_audit_providers",
            "audit_health_check"
        ]
        
        for method in expected_methods:
            assert hasattr(service, method), f"Missing method: {method}"


class TestMCPToolInvocation:
    """Test MCP tool invocation and responses."""
    
    def setup_method(self):
        """Set up test environment."""
        self.test_env = {
            "BILL_COM_USERNAME": "test@example.com",
            "BILL_COM_PASSWORD": "test_password",
            "BILL_COM_ORG_ID": "test_org_123456789",
            "BILL_COM_DEV_KEY": "test_dev_key_12345",
            "BILL_COM_ENVIRONMENT": "sandbox"
        }
        
        for key, value in self.test_env.items():
            os.environ[key] = value
    
    def teardown_method(self):
        """Clean up test environment."""
        for key in self.test_env.keys():
            if key in os.environ:
                del os.environ[key]
    
    @pytest.mark.asyncio
    async def test_health_check_tool_invocation(self):
        """Test health check tool invocation."""
        from services.bill_com_health_tools_service import BillComHealthToolsService
        
        service = BillComHealthToolsService()
        
        # Test health check tool
        result = await service.bill_com_health_check(comprehensive=False)
        
        # Should return JSON string
        assert isinstance(result, str)
        
        # Should be valid JSON
        data = json.loads(result)
        assert isinstance(data, dict)
        assert "timestamp" in data or "error" in data
    
    @pytest.mark.asyncio
    async def test_config_validation_tool_invocation(self):
        """Test configuration validation tool invocation."""
        from services.bill_com_health_tools_service import BillComHealthToolsService
        
        service = BillComHealthToolsService()
        
        # Test config validation tool
        result = await service.bill_com_config_validation()
        
        # Should return JSON string
        assert isinstance(result, str)
        
        # Should be valid JSON
        data = json.loads(result)
        assert isinstance(data, dict)
        assert "valid" in data
        assert data["valid"] is True  # Should be valid with test config
    
    @pytest.mark.asyncio
    async def test_setup_guide_tool_invocation(self):
        """Test setup guide tool invocation."""
        from services.bill_com_health_tools_service import BillComHealthToolsService
        
        service = BillComHealthToolsService()
        
        # Test setup guide tool
        result = await service.bill_com_setup_guide()
        
        # Should return JSON string
        assert isinstance(result, str)
        
        # Should be valid JSON
        data = json.loads(result)
        assert isinstance(data, dict)
        assert "setup_instructions" in data
        assert len(data["setup_instructions"]) > 100
    
    @pytest.mark.asyncio
    async def test_audit_tools_invocation(self):
        """Test audit tools invocation."""
        from services.audit_tools_service import AuditToolsService
        
        service = AuditToolsService()
        
        # Test get audit providers tool
        result = await service.get_audit_providers()
        
        # Should return JSON string
        assert isinstance(result, str)
        
        # Should be valid JSON
        data = json.loads(result)
        assert isinstance(data, dict)
        assert "success" in data or "error" in data


class TestMCPToolParameters:
    """Test MCP tool parameter validation and handling."""
    
    def setup_method(self):
        """Set up test environment."""
        self.test_env = {
            "BILL_COM_USERNAME": "test@example.com",
            "BILL_COM_PASSWORD": "test_password",
            "BILL_COM_ORG_ID": "test_org_123456789",
            "BILL_COM_DEV_KEY": "test_dev_key_12345",
            "BILL_COM_ENVIRONMENT": "sandbox"
        }
        
        for key, value in self.test_env.items():
            os.environ[key] = value
    
    def teardown_method(self):
        """Clean up test environment."""
        for key in self.test_env.keys():
            if key in os.environ:
                del os.environ[key]
    
    @pytest.mark.asyncio
    async def test_health_check_parameters(self):
        """Test health check tool with different parameters."""
        from services.bill_com_health_tools_service import BillComHealthToolsService
        
        service = BillComHealthToolsService()
        
        # Test with comprehensive=False
        result1 = await service.bill_com_health_check(comprehensive=False)
        data1 = json.loads(result1)
        
        # Test with comprehensive=True
        result2 = await service.bill_com_health_check(comprehensive=True)
        data2 = json.loads(result2)
        
        # Both should return valid responses
        assert isinstance(data1, dict)
        assert isinstance(data2, dict)
    
    @pytest.mark.asyncio
    async def test_audit_trail_parameters(self):
        """Test audit trail tool with parameters."""
        from services.audit_tools_service import AuditToolsService
        
        service = AuditToolsService()
        
        # Test with entity parameters
        result = await service.get_audit_trail(
            entity_id="test_invoice_123",
            entity_type="invoice",
            limit=10
        )
        
        # Should return JSON string
        assert isinstance(result, str)
        
        # Should be valid JSON
        data = json.loads(result)
        assert isinstance(data, dict)
        # Will likely have an error due to no MCP server, but should not crash
        assert "success" in data or "error" in data


class TestMCPServerIntegration:
    """Test MCP server integration and startup."""
    
    def test_mcp_server_imports(self):
        """Test MCP server can import all required modules."""
        try:
            # Test that MCP server can import without errors
            from mcp_server import (
                validate_bill_com_configuration_startup,
                initialize_audit_services
            )
            
            # Functions should be callable
            assert callable(validate_bill_com_configuration_startup)
            assert callable(initialize_audit_services)
            
        except ImportError as e:
            # Some imports may fail without fastmcp, but core logic should work
            if "fastmcp" not in str(e).lower():
                raise
            pytest.skip(f"FastMCP dependency not available: {e}")
    
    def test_service_registration_in_factory(self):
        """Test that services are properly registered in the factory."""
        try:
            from core.factory import MCPToolFactory
            from services.bill_com_health_tools_service import BillComHealthToolsService
            from services.audit_tools_service import AuditToolsService
            
            factory = MCPToolFactory()
            
            # Register services
            factory.register_service(BillComHealthToolsService())
            factory.register_service(AuditToolsService())
            
            # Get summary
            summary = factory.get_tool_summary()
            
            assert "total_services" in summary
            assert summary["total_services"] >= 2
            assert "services" in summary
            
        except ImportError as e:
            if "fastmcp" not in str(e).lower():
                raise
            pytest.skip(f"FastMCP dependency not available: {e}")


class TestMCPToolErrorHandling:
    """Test MCP tool error handling and recovery."""
    
    @pytest.mark.asyncio
    async def test_tool_error_responses(self):
        """Test that tools return proper error responses."""
        from services.bill_com_health_tools_service import BillComHealthToolsService
        
        service = BillComHealthToolsService()
        
        # Test connection test (will fail without MCP server)
        result = await service.bill_com_connection_test()
        
        # Should return JSON string even on error
        assert isinstance(result, str)
        
        # Should be valid JSON
        data = json.loads(result)
        assert isinstance(data, dict)
        
        # Should have error information
        assert "error" in data or "connection_status" in data
    
    @pytest.mark.asyncio
    async def test_audit_tool_error_handling(self):
        """Test audit tool error handling."""
        from services.audit_tools_service import AuditToolsService
        
        service = AuditToolsService()
        
        # Test audit trail with invalid parameters
        result = await service.get_audit_trail(
            entity_id="",  # Invalid empty ID
            entity_type="invalid_type"
        )
        
        # Should return JSON string even on error
        assert isinstance(result, str)
        
        # Should be valid JSON
        data = json.loads(result)
        assert isinstance(data, dict)
        
        # Should have error information
        assert "error" in data or "success" in data
    
    def test_configuration_error_in_tools(self):
        """Test tool behavior with invalid configuration."""
        # Clear all Bill.com environment variables
        bill_com_vars = [k for k in os.environ.keys() if k.startswith("BILL_COM_")]
        original_values = {}
        
        for var in bill_com_vars:
            original_values[var] = os.environ[var]
            del os.environ[var]
        
        try:
            from services.bill_com_health_tools_service import BillComHealthToolsService
            
            service = BillComHealthToolsService()
            
            # Should be able to create service even with invalid config
            assert service.domain == "bill_com_health"
            
        finally:
            # Restore environment variables
            for var, value in original_values.items():
                os.environ[var] = value


# Test utilities
def create_mock_mcp_response(success: bool = True, data: dict = None):
    """Create a mock MCP response for testing."""
    if success:
        return {
            "jsonrpc": "2.0",
            "id": 1,
            "result": {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(data or {"success": True})
                    }
                ]
            }
        }
    else:
        return {
            "jsonrpc": "2.0",
            "id": 1,
            "error": {
                "code": -1,
                "message": "Test error"
            }
        }


@pytest.fixture
def mock_mcp_server():
    """Mock MCP server for testing."""
    with patch("aiohttp.ClientSession") as mock_session:
        mock_response = Mock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=create_mock_mcp_response())
        
        mock_session.return_value.__aenter__.return_value.post.return_value.__aenter__.return_value = mock_response
        
        yield mock_session


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])