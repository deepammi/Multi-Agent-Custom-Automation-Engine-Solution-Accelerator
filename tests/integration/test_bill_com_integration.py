#!/usr/bin/env python3
"""
Bill.com Integration Test Suite
Comprehensive integration tests for Bill.com API service, MCP tools, and agent integration.
"""

import os
import sys
import pytest
import asyncio
import json
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta

# Add project paths
project_root = Path(__file__).parent.parent.parent
mcp_server_path = project_root / "src" / "mcp_server"
backend_path = project_root / "backend"

sys.path.insert(0, str(mcp_server_path))
sys.path.insert(0, str(backend_path))


class TestBillComConfiguration:
    """Test Bill.com configuration and validation."""
    
    def setup_method(self):
        """Set up test environment variables."""
        self.test_env = {
            "BILL_COM_USERNAME": "test@example.com",
            "BILL_COM_PASSWORD": "test_password_123",
            "BILL_COM_ORG_ID": "test_org_123456789",
            "BILL_COM_DEV_KEY": "test_dev_key_abcdef123456",
            "BILL_COM_ENVIRONMENT": "sandbox"
        }
        
        # Set test environment
        for key, value in self.test_env.items():
            os.environ[key] = value
    
    def teardown_method(self):
        """Clean up test environment variables."""
        for key in self.test_env.keys():
            if key in os.environ:
                del os.environ[key]
    
    def test_configuration_creation(self):
        """Test Bill.com configuration creation from environment."""
        from config.bill_com_config import BillComConfig, BillComEnvironment
        
        config = BillComConfig.from_env()
        
        assert config.username == "test@example.com"
        assert config.organization_id == "test_org_123456789"
        assert config.environment == BillComEnvironment.SANDBOX
        assert config.base_url == "https://api-stage.bill.com/api/v2"
        assert config.timeout == 30
        assert config.max_retries == 3
    
    def test_configuration_validation(self):
        """Test configuration validation."""
        from config.bill_com_config import validate_bill_com_setup
        
        result = validate_bill_com_setup()
        
        assert result["valid"] is True
        assert "config" in result
        assert len(result.get("missing_required", [])) == 0
    
    def test_production_environment(self):
        """Test production environment configuration."""
        from config.bill_com_config import BillComConfig, BillComEnvironment
        
        os.environ["BILL_COM_ENVIRONMENT"] = "production"
        
        config = BillComConfig.from_env()
        
        assert config.environment == BillComEnvironment.PRODUCTION
        assert config.base_url == "https://api.bill.com/api/v2"
    
    def test_missing_required_variables(self):
        """Test validation with missing required variables."""
        from config.bill_com_config import validate_bill_com_setup
        
        # Remove required variable
        del os.environ["BILL_COM_USERNAME"]
        
        result = validate_bill_com_setup()
        
        assert result["valid"] is False
        assert "BILL_COM_USERNAME" in result.get("missing_required", [])
    
    def test_invalid_configuration(self):
        """Test validation with invalid configuration."""
        from config.bill_com_config import BillComConfig
        
        # Set invalid email
        os.environ["BILL_COM_USERNAME"] = "invalid_email"
        
        with pytest.raises(ValueError, match="Username should be a valid email address"):
            BillComConfig.from_env()


class TestHealthMonitoring:
    """Test health monitoring system."""
    
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
    
    def test_health_service_creation(self):
        """Test health service creation."""
        from services.bill_com_health_service import BillComHealthService, get_health_service
        
        service1 = get_health_service()
        service2 = get_health_service()
        
        assert isinstance(service1, BillComHealthService)
        assert service1 is service2  # Should be singleton
    
    @pytest.mark.asyncio
    async def test_configuration_check(self):
        """Test configuration health check."""
        from services.bill_com_health_service import get_health_service
        
        health_service = get_health_service()
        result = await health_service._check_configuration()
        
        assert result["status"] == "healthy"
        assert "environment" in result["details"]
        assert result["details"]["environment"] == "sandbox"
    
    @pytest.mark.asyncio
    async def test_health_tools(self):
        """Test health check tools."""
        from core.bill_com_health_tools import (
            bill_com_config_validation,
            bill_com_setup_guide,
            bill_com_diagnostics
        )
        
        # Test config validation tool
        config_result = await bill_com_config_validation()
        config_data = json.loads(config_result)
        assert config_data["valid"] is True
        
        # Test setup guide tool
        setup_result = await bill_com_setup_guide()
        setup_data = json.loads(setup_result)
        assert "setup_instructions" in setup_data
        assert len(setup_data["setup_instructions"]) > 100
        
        # Test diagnostics tool
        diag_result = await bill_com_diagnostics()
        diag_data = json.loads(diag_result)
        assert "configuration" in diag_data
        assert "troubleshooting" in diag_data


class TestAuditSystem:
    """Test generic audit system."""
    
    def test_audit_interface(self):
        """Test audit provider interface."""
        from interfaces.audit_provider import (
            AuditProvider, AuditEvent, AuditException, AuditReport,
            AuditEventType, ExceptionSeverity, ProviderMetadata
        )
        
        # Test enums
        assert len(list(AuditEventType)) == 8
        assert len(list(ExceptionSeverity)) == 4
        
        # Test data classes
        event = AuditEvent(
            event_id="test-001",
            entity_id="invoice-123",
            entity_type="invoice",
            event_type=AuditEventType.CREATED,
            timestamp=datetime.utcnow(),
            user_id="user-123",
            user_name="Test User",
            description="Test event"
        )
        
        assert event.event_id == "test-001"
        assert event.event_type == AuditEventType.CREATED
    
    def test_audit_service(self):
        """Test audit service manager."""
        from services.audit_service import AuditService
        
        service = AuditService()
        
        # Initially no providers
        assert len(service.get_available_providers()) == 0
        
        # Test provider registration would go here
        # (requires mock provider implementation)
    
    def test_billcom_audit_adapter(self):
        """Test Bill.com audit adapter."""
        from adapters.billcom_audit_adapter import BillComAuditAdapter
        from services.bill_com_service import BillComAPIService, BillComConfig
        
        # Create mock Bill.com service
        config = BillComConfig(
            username="test@example.com",
            password="test_password",
            organization_id="test_org",
            dev_key="test_key"
        )
        
        mock_service = Mock(spec=BillComAPIService)
        adapter = BillComAuditAdapter(mock_service)
        
        assert adapter.metadata.name == "Bill.com"
        assert adapter.metadata.capabilities.supports_audit_trail is True
        assert adapter.metadata.capabilities.supports_exception_detection is True


class TestAgentIntegration:
    """Test agent integration with Bill.com."""
    
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
    async def test_invoice_agent_billcom_integration(self):
        """Test Invoice Agent with Bill.com integration request."""
        from app.agents.state import AgentState
        from app.agents.nodes import invoice_agent_node
        
        state = AgentState(
            task_description="Get recent invoices from Bill.com",
            plan_id="test-invoice-001",
            messages=[],
            current_agent="Invoice"
        )
        
        result = await invoice_agent_node(state)
        
        assert "messages" in result
        assert "current_agent" in result
        assert "final_result" in result
        assert result["current_agent"] == "Invoice"
        
        # Should contain Bill.com integration response
        response = result["final_result"]
        assert "Bill.com" in response or "billcom" in response.lower()
    
    @pytest.mark.asyncio
    async def test_audit_agent_integration(self):
        """Test Audit Agent with audit request."""
        from app.agents.state import AgentState
        from app.agents.nodes import audit_agent_node
        
        state = AgentState(
            task_description="Check for compliance exceptions",
            plan_id="test-audit-001",
            messages=[],
            current_agent="Audit"
        )
        
        result = await audit_agent_node(state)
        
        assert "messages" in result
        assert "current_agent" in result
        assert "final_result" in result
        assert result["current_agent"] == "Audit"
        
        # Should contain audit functionality
        response = result["final_result"]
        assert any(keyword in response.lower() for keyword in ["audit", "compliance", "exception"])
    
    def test_closing_agent_future_message(self):
        """Test Closing Agent shows future enhancement message."""
        from app.agents.state import AgentState
        from app.agents.nodes import closing_agent_node
        
        state = AgentState(
            task_description="Perform month-end closing",
            plan_id="test-closing-001",
            messages=[],
            current_agent="Closing"
        )
        
        result = closing_agent_node(state)
        
        assert "messages" in result
        assert "current_agent" in result
        assert "final_result" in result
        assert result["current_agent"] == "Closing"
        
        # Should contain future enhancement message
        response = result["final_result"]
        assert any(keyword in response.lower() for keyword in ["development", "coming soon", "progress"])


class TestIntegrationService:
    """Test Bill.com integration service."""
    
    def test_service_creation(self):
        """Test integration service creation."""
        from app.services.bill_com_integration_service import (
            BillComIntegrationService, get_bill_com_service
        )
        
        service1 = get_bill_com_service()
        service2 = get_bill_com_service()
        
        assert isinstance(service1, BillComIntegrationService)
        assert service1 is service2  # Should be singleton
        assert service1.mcp_server_url == "http://localhost:9000"
    
    @pytest.mark.asyncio
    async def test_service_methods(self):
        """Test integration service methods."""
        from app.services.bill_com_integration_service import get_bill_com_service
        
        service = get_bill_com_service()
        
        # Test that methods exist and are callable
        assert hasattr(service, "get_invoices")
        assert hasattr(service, "get_invoice_details")
        assert hasattr(service, "search_invoices")
        assert hasattr(service, "get_vendors")
        assert hasattr(service, "get_audit_trail")
        assert hasattr(service, "detect_audit_exceptions")
        
        # Test method calls (will fail without MCP server, but should not crash)
        try:
            result = await service.get_invoices(limit=1)
            # If MCP server is running, result should be a dict
            assert isinstance(result, dict)
        except Exception as e:
            # Expected if MCP server is not running
            assert "error" in str(e).lower() or "connect" in str(e).lower()
        
        await service.close()


class TestMCPToolsIntegration:
    """Test MCP tools integration."""
    
    def test_billcom_tools_service(self):
        """Test Bill.com tools service."""
        try:
            from core.bill_com_tools import BillComService
            
            service = BillComService()
            assert service.domain == "bill_com"
            
        except ImportError:
            # Expected if fastmcp is not available
            pytest.skip("FastMCP not available for MCP tools testing")
    
    def test_health_tools_service(self):
        """Test health tools service."""
        from services.bill_com_health_tools_service import BillComHealthToolsService
        
        service = BillComHealthToolsService()
        assert service.domain == "bill_com_health"
        
        # Test that methods exist
        assert hasattr(service, "bill_com_health_check")
        assert hasattr(service, "bill_com_config_validation")
        assert hasattr(service, "bill_com_setup_guide")
    
    def test_audit_tools_service(self):
        """Test audit tools service."""
        from services.audit_tools_service import AuditToolsService
        
        service = AuditToolsService()
        assert service.domain == "audit"
        
        # Test that methods exist
        assert hasattr(service, "get_audit_trail")
        assert hasattr(service, "get_modification_history")
        assert hasattr(service, "detect_audit_exceptions")


class TestErrorHandling:
    """Test error handling and recovery mechanisms."""
    
    def test_configuration_error_handling(self):
        """Test configuration error handling."""
        from config.bill_com_config import validate_bill_com_setup
        
        # Clear all environment variables
        bill_com_vars = [k for k in os.environ.keys() if k.startswith("BILL_COM_")]
        for var in bill_com_vars:
            del os.environ[var]
        
        result = validate_bill_com_setup()
        
        assert result["valid"] is False
        assert len(result.get("missing_required", [])) > 0
        assert "errors" in result or "missing_required" in result
    
    @pytest.mark.asyncio
    async def test_service_unavailable_handling(self):
        """Test handling when services are unavailable."""
        from app.services.bill_com_integration_service import get_bill_com_service
        
        service = get_bill_com_service()
        
        # Test health check when service is unavailable
        result = await service.check_bill_com_health()
        
        # Should return error result, not crash
        assert isinstance(result, dict)
        assert "error" in result or "success" in result
        
        await service.close()
    
    @pytest.mark.asyncio
    async def test_agent_fallback_behavior(self):
        """Test agent fallback behavior when services are unavailable."""
        from app.agents.state import AgentState
        from app.agents.nodes import invoice_agent_node, audit_agent_node
        
        # Test Invoice Agent fallback
        invoice_state = AgentState(
            task_description="Get invoices from Bill.com",
            plan_id="test-fallback-001",
            messages=[],
            current_agent="Invoice"
        )
        
        result = await invoice_agent_node(invoice_state)
        
        # Should return a response, not crash
        assert "final_result" in result
        assert len(result["final_result"]) > 0
        
        # Test Audit Agent fallback
        audit_state = AgentState(
            task_description="Check compliance",
            plan_id="test-fallback-002",
            messages=[],
            current_agent="Audit"
        )
        
        result = await audit_agent_node(audit_state)
        
        # Should return a response, not crash
        assert "final_result" in result
        assert len(result["final_result"]) > 0


# Test fixtures and utilities
@pytest.fixture
def mock_bill_com_service():
    """Create a mock Bill.com service for testing."""
    from services.bill_com_service import BillComAPIService
    
    mock_service = Mock(spec=BillComAPIService)
    mock_service.get_invoices = AsyncMock(return_value=[])
    mock_service.get_vendors = AsyncMock(return_value=[])
    mock_service.authenticate = AsyncMock(return_value=True)
    
    return mock_service


@pytest.fixture
def sample_invoice_data():
    """Sample invoice data for testing."""
    return {
        "id": "invoice_123",
        "invoiceNumber": "INV-001",
        "vendorName": "Test Vendor",
        "amount": 1000.00,
        "dueDate": "2024-01-15",
        "approvalStatus": "NeedsApproval",
        "createdTime": "2024-01-01T10:00:00Z"
    }


@pytest.fixture
def sample_audit_event():
    """Sample audit event for testing."""
    from interfaces.audit_provider import AuditEvent, AuditEventType
    
    return AuditEvent(
        event_id="event_123",
        entity_id="invoice_123",
        entity_type="invoice",
        event_type=AuditEventType.CREATED,
        timestamp=datetime.utcnow(),
        user_id="user_123",
        user_name="Test User",
        description="Invoice created"
    )


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])