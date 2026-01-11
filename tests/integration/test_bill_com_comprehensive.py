#!/usr/bin/env python3
"""
Comprehensive Bill.com Integration Test Suite

This test suite provides comprehensive integration testing for the Bill.com API service,
MCP tools, and agent integration with realistic scenarios and error handling.
"""

import os
import sys
import pytest
import asyncio
import json
import httpx
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
from typing import Dict, List, Any

# Add project paths
project_root = Path(__file__).parent.parent.parent
mcp_server_path = project_root / "src" / "mcp_server"
backend_path = project_root / "backend"

sys.path.insert(0, str(mcp_server_path))
sys.path.insert(0, str(backend_path))


class TestBillComServiceIntegration:
    """Test Bill.com API service with realistic scenarios."""
    
    def setup_method(self):
        """Set up test environment with realistic test data."""
        self.test_env = {
            "BILL_COM_USERNAME": "test@example.com",
            "BILL_COM_PASSWORD": "test_password_123",
            "BILL_COM_ORG_ID": "test_org_123456789",
            "BILL_COM_DEV_KEY": "test_dev_key_abcdef123456",
            "BILL_COM_ENVIRONMENT": "sandbox",
            "BILL_COM_TIMEOUT": "30",
            "BILL_COM_MAX_RETRIES": "3"
        }
        
        # Set test environment
        for key, value in self.test_env.items():
            os.environ[key] = value
    
    def teardown_method(self):
        """Clean up test environment."""
        for key in self.test_env.keys():
            if key in os.environ:
                del os.environ[key]
    
    @pytest.mark.asyncio
    async def test_service_lifecycle(self):
        """Test complete service lifecycle with context manager."""
        from services.bill_com_service import BillComAPIService
        
        async with BillComAPIService(plan_id="test-001", agent="test") as service:
            # Test service initialization
            assert service.plan_id == "test-001"
            assert service.agent == "test"
            assert service.config is not None
            assert service._http_client is not None
            
            # Test configuration validation
            assert service.config.validate() is True
            assert service.config.username == "test@example.com"
            assert service.config.environment == "sandbox"
    
    @pytest.mark.asyncio
    async def test_authentication_flow(self):
        """Test authentication flow with mock responses."""
        from services.bill_com_service import BillComAPIService
        
        # Mock successful authentication response
        mock_response_data = {
            "sessionId": "test_session_123",
            "organizationId": "test_org_123456789",
            "userId": "test_user_456"
        }
        
        async with BillComAPIService() as service:
            with patch.object(service._http_client, 'post') as mock_post:
                # Mock successful response
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.json.return_value = mock_response_data
                mock_post.return_value.__aenter__.return_value = mock_response
                
                # Test authentication
                result = await service.authenticate()
                
                assert result is True
                assert service.session is not None
                assert service.session.session_id == "test_session_123"
                assert service.session.organization_id == "test_org_123456789"
                assert service.session.user_id == "test_user_456"
    
    @pytest.mark.asyncio
    async def test_authentication_failure_handling(self):
        """Test authentication failure scenarios."""
        from services.bill_com_service import BillComAPIService
        
        async with BillComAPIService() as service:
            with patch.object(service._http_client, 'post') as mock_post:
                # Mock 401 Unauthorized response
                mock_response = Mock()
                mock_response.status_code = 401
                mock_response.text = "Invalid credentials"
                mock_post.return_value.__aenter__.return_value = mock_response
                
                # Test authentication failure
                result = await service.authenticate()
                
                assert result is False
                assert service.session is None
    
    @pytest.mark.asyncio
    async def test_api_call_with_retry_logic(self):
        """Test API call retry logic with various failure scenarios."""
        from services.bill_com_service import BillComAPIService
        
        async with BillComAPIService() as service:
            # Mock successful authentication
            service.session = Mock()
            service.session.session_id = "test_session"
            service.session.is_expired.return_value = False
            
            with patch.object(service._http_client, 'request') as mock_request:
                # Mock network error followed by success
                mock_error_response = Mock()
                mock_error_response.side_effect = httpx.NetworkError("Connection failed")
                
                mock_success_response = Mock()
                mock_success_response.status_code = 200
                mock_success_response.json.return_value = {"response_data": []}
                
                mock_request.side_effect = [
                    mock_error_response,  # First attempt fails
                    mock_success_response.__aenter__.return_value  # Second attempt succeeds
                ]
                
                # Test API call with retry
                result = await service.make_api_call("/v3/invoices", max_retries=2)
                
                assert result is not None
                assert "response_data" in result
                assert mock_request.call_count == 2  # One retry
    
    @pytest.mark.asyncio
    async def test_session_expiration_handling(self):
        """Test automatic session renewal on expiration."""
        from services.bill_com_service import BillComAPIService, BillComSession
        from datetime import timezone
        
        async with BillComAPIService() as service:
            # Create expired session
            expired_session = BillComSession(
                session_id="expired_session",
                organization_id="test_org",
                user_id="test_user",
                expires_at=datetime.now(timezone.utc) - timedelta(hours=1)
            )
            service.session = expired_session
            
            with patch.object(service, 'authenticate') as mock_auth:
                mock_auth.return_value = True
                
                # Test ensure_authenticated with expired session
                result = await service.ensure_authenticated()
                
                assert result is True
                mock_auth.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_invoice_operations(self):
        """Test invoice-related operations with realistic data."""
        from services.bill_com_service import BillComAPIService
        
        # Mock invoice data
        mock_invoices = [
            {
                "id": "inv_001",
                "invoiceNumber": "INV-2024-001",
                "vendorName": "Test Vendor Inc",
                "amount": 1500.00,
                "status": "NeedsApproval",
                "invoiceDate": "2024-01-15",
                "dueDate": "2024-02-15"
            },
            {
                "id": "inv_002", 
                "invoiceNumber": "INV-2024-002",
                "vendorName": "Another Vendor LLC",
                "amount": 750.50,
                "status": "Approved",
                "invoiceDate": "2024-01-16",
                "dueDate": "2024-02-16"
            }
        ]
        
        async with BillComAPIService() as service:
            with patch.object(service, 'make_api_call') as mock_api_call:
                mock_api_call.return_value = {"response_data": mock_invoices}
                
                # Test get_invoices
                invoices = await service.get_invoices(limit=10)
                
                assert len(invoices) == 2
                assert invoices[0]["invoiceNumber"] == "INV-2024-001"
                assert invoices[1]["amount"] == 750.50
                
                # Verify API call parameters
                mock_api_call.assert_called_with("/v3/invoices", params={"max": 10})
    
    @pytest.mark.asyncio
    async def test_complete_invoice_details(self):
        """Test complete invoice details retrieval with all related data."""
        from services.bill_com_service import BillComAPIService
        
        # Mock complete invoice data
        mock_invoice = {
            "id": "inv_001",
            "invoiceNumber": "INV-2024-001",
            "vendorName": "Test Vendor Inc",
            "amount": 1500.00,
            "status": "Approved"
        }
        
        mock_payments = [
            {
                "id": "pay_001",
                "amount": 1500.00,
                "paymentDate": "2024-01-20",
                "paymentMethod": "ACH"
            }
        ]
        
        mock_line_items = [
            {
                "id": "line_001",
                "description": "Professional Services",
                "quantity": 1,
                "unitPrice": 1500.00,
                "amount": 1500.00
            }
        ]
        
        async with BillComAPIService() as service:
            with patch.object(service, 'make_api_call') as mock_api_call:
                # Mock different API calls
                def mock_api_side_effect(endpoint, **kwargs):
                    if "/invoices/inv_001" in endpoint and "payments" not in endpoint:
                        return {"response_data": mock_invoice}
                    elif "payments" in endpoint:
                        return {"response_data": mock_payments}
                    elif "lineItems" in endpoint:
                        return {"response_data": mock_line_items}
                    else:
                        return {"response_data": []}
                
                mock_api_call.side_effect = mock_api_side_effect
                
                # Test complete invoice details
                details = await service.get_complete_invoice_details("inv_001")
                
                assert details is not None
                assert details["invoice_number"] == "INV-2024-001"
                assert details["total_amount"] == 1500.00
                assert details["is_fully_paid"] is True
                assert details["line_items_count"] == 1
                assert details["payment_count"] == 1
                assert details["data_completeness_score"] > 0.8


class TestMCPToolsIntegration:
    """Test MCP tools integration with Bill.com service."""
    
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
    async def test_get_bill_com_invoices_tool(self):
        """Test get_bill_com_invoices MCP tool."""
        from core.bill_com_tools import get_bill_com_invoices
        
        # Mock service response
        mock_invoices = [
            {
                "id": "inv_001",
                "invoiceNumber": "INV-001",
                "vendorName": "Test Vendor",
                "amount": 1000.00,
                "status": "approved"
            }
        ]
        
        with patch('core.bill_com_tools.get_bill_com_service') as mock_get_service:
            mock_service = AsyncMock()
            mock_service.get_invoices.return_value = mock_invoices
            mock_get_service.return_value = mock_service
            
            # Test tool function
            result = await get_bill_com_invoices(limit=10, vendor_name="Test")
            
            # Parse JSON response
            response_data = json.loads(result)
            
            assert response_data["success"] is True
            assert response_data["details"]["count"] == 1
            assert response_data["details"]["invoices"][0]["invoice_number"] == "INV-001"
            assert "Test Vendor" in response_data["summary"]
    
    @pytest.mark.asyncio
    async def test_search_bill_com_invoices_tool(self):
        """Test search_bill_com_invoices MCP tool with different search types."""
        from core.bill_com_tools import search_bill_com_invoices
        
        mock_invoices = [
            {
                "id": "inv_001",
                "invoiceNumber": "INV-001",
                "vendorName": "Test Vendor",
                "amount": 1000.00
            }
        ]
        
        with patch('core.bill_com_tools.get_bill_com_service') as mock_get_service:
            mock_service = AsyncMock()
            mock_service.search_invoices_by_number.return_value = mock_invoices
            mock_get_service.return_value = mock_service
            
            # Test invoice number search
            result = await search_bill_com_invoices("INV-001", "invoice_number")
            response_data = json.loads(result)
            
            assert response_data["success"] is True
            assert response_data["details"]["count"] == 1
            assert response_data["details"]["search_type"] == "invoice_number"
    
    @pytest.mark.asyncio
    async def test_get_bill_com_invoice_details_tool(self):
        """Test get_bill_com_invoice_details MCP tool."""
        from core.bill_com_tools import get_bill_com_invoice_details
        
        mock_complete_details = {
            "id": "inv_001",
            "invoice_number": "INV-001",
            "vendor_name": "Test Vendor",
            "total_amount": 1000.00,
            "remaining_balance": 0.00,
            "is_fully_paid": True,
            "line_items_count": 2,
            "payment_count": 1,
            "attachment_count": 1,
            "data_completeness_score": 0.95
        }
        
        with patch('core.bill_com_tools.get_bill_com_service') as mock_get_service:
            mock_service = AsyncMock()
            mock_service.get_complete_invoice_details.return_value = mock_complete_details
            mock_get_service.return_value = mock_service
            
            # Test tool function
            result = await get_bill_com_invoice_details("inv_001")
            response_data = json.loads(result)
            
            assert response_data["success"] is True
            assert response_data["details"]["invoice"]["invoice_number"] == "INV-001"
            assert response_data["details"]["financial_summary"]["is_fully_paid"] is True
            assert "Fully paid" in response_data["summary"]
    
    @pytest.mark.asyncio
    async def test_tool_error_handling(self):
        """Test MCP tool error handling."""
        from core.bill_com_tools import get_bill_com_invoices
        
        with patch('core.bill_com_tools.get_bill_com_service') as mock_get_service:
            mock_service = AsyncMock()
            mock_service.get_invoices.side_effect = Exception("API connection failed")
            mock_get_service.return_value = mock_service
            
            # Test error handling
            result = await get_bill_com_invoices()
            response_data = json.loads(result)
            
            assert response_data["success"] is False
            assert "API connection failed" in response_data["error"]


class TestAgentIntegrationScenarios:
    """Test realistic agent integration scenarios."""
    
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
    async def test_invoice_agent_bill_com_workflow(self):
        """Test Invoice Agent with Bill.com integration workflow."""
        from app.agents.state import AgentState
        from app.agents.nodes import invoice_agent_node
        
        # Test various Bill.com related requests
        test_scenarios = [
            "Get recent invoices from Bill.com",
            "Show me Bill.com vendor information", 
            "Find invoice INV-12345 in Bill.com",
            "Check payment status for Bill.com invoices",
            "List all approved invoices from Bill.com"
        ]
        
        for task_description in test_scenarios:
            state = AgentState(
                task_description=task_description,
                plan_id=f"test-invoice-{hash(task_description)}",
                messages=[],
                current_agent="Invoice"
            )
            
            result = await invoice_agent_node(state)
            
            # Verify response structure
            assert "messages" in result
            assert "current_agent" in result
            assert "final_result" in result
            assert result["current_agent"] == "Invoice"
            
            # Should contain Bill.com integration response or fallback
            response = result["final_result"]
            assert len(response) > 0
            
            # Should mention Bill.com or provide helpful guidance
            assert any(keyword in response.lower() for keyword in [
                "bill.com", "billcom", "invoice", "integration", "service"
            ])
    
    @pytest.mark.asyncio
    async def test_audit_agent_compliance_workflow(self):
        """Test Audit Agent with compliance and audit scenarios."""
        from app.agents.state import AgentState
        from app.agents.nodes import audit_agent_node
        
        test_scenarios = [
            "Check for compliance exceptions in Bill.com",
            "Generate audit report for invoice processing",
            "Detect anomalies in payment patterns",
            "Review approval workflows for compliance",
            "Monitor continuous compliance status"
        ]
        
        for task_description in test_scenarios:
            state = AgentState(
                task_description=task_description,
                plan_id=f"test-audit-{hash(task_description)}",
                messages=[],
                current_agent="Audit"
            )
            
            result = await audit_agent_node(state)
            
            # Verify response structure
            assert "messages" in result
            assert "current_agent" in result
            assert "final_result" in result
            assert result["current_agent"] == "Audit"
            
            # Should contain audit-related response
            response = result["final_result"]
            assert len(response) > 0
            
            # Should mention audit concepts
            assert any(keyword in response.lower() for keyword in [
                "audit", "compliance", "exception", "monitoring", "report"
            ])
    
    def test_closing_agent_future_development(self):
        """Test Closing Agent shows appropriate future development message."""
        from app.agents.state import AgentState
        from app.agents.nodes import closing_agent_node
        
        state = AgentState(
            task_description="Perform month-end closing with Bill.com data",
            plan_id="test-closing-001",
            messages=[],
            current_agent="Closing"
        )
        
        result = closing_agent_node(state)
        
        # Verify response structure
        assert "messages" in result
        assert "current_agent" in result
        assert "final_result" in result
        assert result["current_agent"] == "Closing"
        
        # Should contain future development message
        response = result["final_result"]
        assert any(keyword in response.lower() for keyword in [
            "development", "coming soon", "progress", "future", "enhancement"
        ])


class TestErrorRecoveryScenarios:
    """Test error recovery and resilience scenarios."""
    
    @pytest.mark.asyncio
    async def test_network_failure_recovery(self):
        """Test recovery from network failures."""
        from services.bill_com_service import BillComAPIService
        
        async with BillComAPIService() as service:
            service.session = Mock()
            service.session.session_id = "test_session"
            service.session.is_expired.return_value = False
            
            with patch.object(service._http_client, 'request') as mock_request:
                # Simulate network failures followed by success
                mock_request.side_effect = [
                    httpx.NetworkError("Network unreachable"),
                    httpx.TimeoutException("Request timeout"),
                    Mock(status_code=200, json=lambda: {"response_data": []})
                ]
                
                # Should recover after retries
                result = await service.make_api_call("/v3/invoices", max_retries=3)
                
                assert result is not None
                assert mock_request.call_count == 3
    
    @pytest.mark.asyncio
    async def test_authentication_recovery(self):
        """Test recovery from authentication failures."""
        from services.bill_com_service import BillComAPIService
        
        async with BillComAPIService() as service:
            with patch.object(service._http_client, 'request') as mock_request:
                with patch.object(service, 'authenticate') as mock_auth:
                    # First call fails with 401, then succeeds after re-auth
                    mock_request.side_effect = [
                        Mock(status_code=401, text="Unauthorized"),
                        Mock(status_code=200, json=lambda: {"response_data": []})
                    ]
                    
                    mock_auth.return_value = True
                    service.session = Mock()
                    service.session.session_id = "new_session"
                    
                    # Should recover by re-authenticating
                    result = await service.make_api_call("/v3/invoices")
                    
                    assert result is not None
                    mock_auth.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_rate_limit_handling(self):
        """Test rate limit handling and backoff."""
        from services.bill_com_service import BillComAPIService
        
        async with BillComAPIService() as service:
            service.session = Mock()
            service.session.session_id = "test_session"
            service.session.is_expired.return_value = False
            
            with patch.object(service._http_client, 'request') as mock_request:
                with patch('asyncio.sleep') as mock_sleep:
                    # Simulate rate limit followed by success
                    rate_limit_response = Mock()
                    rate_limit_response.status_code = 429
                    rate_limit_response.headers = {"Retry-After": "60"}
                    
                    success_response = Mock()
                    success_response.status_code = 200
                    success_response.json.return_value = {"response_data": []}
                    
                    mock_request.side_effect = [
                        rate_limit_response,
                        success_response
                    ]
                    
                    # Should handle rate limit with proper delay
                    result = await service.make_api_call("/v3/invoices")
                    
                    assert result is not None
                    mock_sleep.assert_called_with(60.0)


class TestPerformanceScenarios:
    """Test performance-related scenarios."""
    
    @pytest.mark.asyncio
    async def test_concurrent_requests(self):
        """Test handling of concurrent requests."""
        from services.bill_com_service import get_bill_com_service
        
        async def make_request(request_id):
            service = await get_bill_com_service(plan_id=f"test-{request_id}")
            
            with patch.object(service, 'make_api_call') as mock_api_call:
                mock_api_call.return_value = {"response_data": [{"id": f"inv_{request_id}"}]}
                return await service.get_invoices(limit=1)
        
        # Test concurrent requests
        tasks = [make_request(i) for i in range(5)]
        results = await asyncio.gather(*tasks)
        
        # All requests should succeed
        assert len(results) == 5
        for i, result in enumerate(results):
            assert len(result) == 1
            assert result[0]["id"] == f"inv_{i}"
    
    @pytest.mark.asyncio
    async def test_large_dataset_handling(self):
        """Test handling of large datasets with pagination."""
        from services.bill_com_service import BillComAPIService
        
        # Mock large dataset
        large_dataset = [
            {"id": f"inv_{i:04d}", "amount": i * 100}
            for i in range(1000)
        ]
        
        async with BillComAPIService() as service:
            with patch.object(service, 'make_api_call') as mock_api_call:
                mock_api_call.return_value = {"response_data": large_dataset}
                
                # Test with large limit
                result = await service.get_invoices(limit=1000)
                
                assert len(result) == 1000
                assert result[0]["id"] == "inv_0000"
                assert result[-1]["id"] == "inv_0999"


# Test fixtures and utilities
@pytest.fixture
def mock_bill_com_config():
    """Mock Bill.com configuration for testing."""
    from config.bill_com_config import BillComConfig
    
    return BillComConfig(
        username="test@example.com",
        password="test_password",
        organization_id="test_org_123",
        dev_key="test_dev_key_456",
        environment="sandbox"
    )


@pytest.fixture
def sample_invoice_data():
    """Sample invoice data for testing."""
    return {
        "id": "invoice_123",
        "invoiceNumber": "INV-2024-001",
        "vendorName": "Test Vendor Inc",
        "vendorId": "vendor_456",
        "amount": 1500.00,
        "currency": "USD",
        "status": "NeedsApproval",
        "invoiceDate": "2024-01-15",
        "dueDate": "2024-02-15",
        "description": "Professional services",
        "createdTime": "2024-01-01T10:00:00Z",
        "updatedTime": "2024-01-15T14:30:00Z"
    }


@pytest.fixture
def sample_complete_invoice():
    """Sample complete invoice with all related data."""
    return {
        "id": "invoice_123",
        "invoice_number": "INV-2024-001",
        "vendor_name": "Test Vendor Inc",
        "total_amount": 1500.00,
        "remaining_balance": 0.00,
        "is_fully_paid": True,
        "line_items": [
            {
                "id": "line_001",
                "description": "Consulting Services",
                "quantity": 10.0,
                "unit_price": 150.00,
                "total_amount": 1500.00
            }
        ],
        "payment_history": [
            {
                "id": "payment_001",
                "payment_date": "2024-01-20",
                "amount": 1500.00,
                "payment_method": "ACH"
            }
        ],
        "attachments": [
            {
                "id": "attach_001",
                "filename": "invoice.pdf",
                "file_size": 245760,
                "content_type": "application/pdf"
            }
        ],
        "data_completeness_score": 0.95
    }


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short", "--asyncio-mode=auto"])