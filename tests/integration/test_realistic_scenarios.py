#!/usr/bin/env python3
"""
Realistic Scenario Tests for Bill.com Integration
Tests agent integration with Bill.com tools in realistic user scenarios.
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


class TestInvoiceAgentScenarios:
    """Test realistic Invoice Agent scenarios."""
    
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
    async def test_invoice_list_request(self):
        """Test: User asks 'Show me recent invoices from Bill.com'"""
        from app.agents.state import AgentState
        from app.agents.nodes import invoice_agent_node
        
        state = AgentState(
            task_description="Show me recent invoices from Bill.com",
            plan_id="scenario-invoice-list",
            messages=[],
            current_agent="Invoice"
        )
        
        result = await invoice_agent_node(state)
        
        # Verify response structure
        assert "final_result" in result
        assert "current_agent" in result
        assert result["current_agent"] == "Invoice"
        
        response = result["final_result"]
        
        # Should mention Bill.com integration
        assert any(keyword in response for keyword in ["Bill.com", "billcom", "invoice"])
        
        # Should handle service unavailability gracefully
        if "unavailable" in response.lower() or "error" in response.lower():
            # Should provide helpful guidance
            assert any(keyword in response for keyword in ["MCP", "server", "configuration"])
        else:
            # Should show invoice-related content
            assert any(keyword in response for keyword in ["invoice", "recent", "list"])
    
    @pytest.mark.asyncio
    async def test_invoice_search_request(self):
        """Test: User asks 'Find invoice INV-12345 in Bill.com'"""
        from app.agents.state import AgentState
        from app.agents.nodes import invoice_agent_node
        
        state = AgentState(
            task_description="Find invoice INV-12345 in Bill.com",
            plan_id="scenario-invoice-search",
            messages=[],
            current_agent="Invoice"
        )
        
        result = await invoice_agent_node(state)
        
        response = result["final_result"]
        
        # Should recognize search intent
        assert any(keyword in response for keyword in ["search", "find", "INV-12345"])
        
        # Should mention Bill.com
        assert "Bill.com" in response or "billcom" in response.lower()
    
    @pytest.mark.asyncio
    async def test_vendor_information_request(self):
        """Test: User asks 'Get vendor information from Bill.com'"""
        from app.agents.state import AgentState
        from app.agents.nodes import invoice_agent_node
        
        state = AgentState(
            task_description="Get vendor information from Bill.com",
            plan_id="scenario-vendor-info",
            messages=[],
            current_agent="Invoice"
        )
        
        result = await invoice_agent_node(state)
        
        response = result["final_result"]
        
        # Should recognize vendor request
        assert "vendor" in response.lower()
        
        # Should mention Bill.com
        assert "Bill.com" in response or "billcom" in response.lower()
    
    @pytest.mark.asyncio
    async def test_non_billcom_request(self):
        """Test: User asks for invoice extraction (not Bill.com)"""
        from app.agents.state import AgentState
        from app.agents.nodes import invoice_agent_node
        
        state = AgentState(
            task_description="Extract data from this invoice text: Invoice #123...",
            plan_id="scenario-extraction",
            messages=[],
            current_agent="Invoice"
        )
        
        result = await invoice_agent_node(state)
        
        response = result["final_result"]
        
        # Should handle non-Bill.com requests appropriately
        assert len(response) > 0
        
        # Should not force Bill.com integration for extraction tasks
        # (May mention it as an option, but should handle the extraction request)


class TestAuditAgentScenarios:
    """Test realistic Audit Agent scenarios."""
    
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
    async def test_compliance_check_request(self):
        """Test: User asks 'Check for compliance exceptions'"""
        from app.agents.state import AgentState
        from app.agents.nodes import audit_agent_node
        
        state = AgentState(
            task_description="Check for compliance exceptions",
            plan_id="scenario-compliance-check",
            messages=[],
            current_agent="Audit"
        )
        
        result = await audit_agent_node(state)
        
        response = result["final_result"]
        
        # Should mention audit/compliance functionality
        assert any(keyword in response.lower() for keyword in ["audit", "compliance", "exception"])
        
        # Should handle service unavailability gracefully
        if "unavailable" in response.lower():
            assert "fallback" in response.lower() or "simulated" in response.lower()
    
    @pytest.mark.asyncio
    async def test_audit_trail_request(self):
        """Test: User asks 'Get audit trail for invoice INV-12345'"""
        from app.agents.state import AgentState
        from app.agents.nodes import audit_agent_node
        
        state = AgentState(
            task_description="Get audit trail for invoice INV-12345",
            plan_id="scenario-audit-trail",
            messages=[],
            current_agent="Audit"
        )
        
        result = await audit_agent_node(state)
        
        response = result["final_result"]
        
        # Should recognize audit trail request
        assert any(keyword in response.lower() for keyword in ["audit", "trail", "history"])
        
        # Should mention the specific invoice
        assert "INV-12345" in response or "invoice" in response.lower()
    
    @pytest.mark.asyncio
    async def test_exception_detection_request(self):
        """Test: User asks 'Detect audit exceptions in recent invoices'"""
        from app.agents.state import AgentState
        from app.agents.nodes import audit_agent_node
        
        state = AgentState(
            task_description="Detect audit exceptions in recent invoices",
            plan_id="scenario-exception-detection",
            messages=[],
            current_agent="Audit"
        )
        
        result = await audit_agent_node(state)
        
        response = result["final_result"]
        
        # Should recognize exception detection request
        assert any(keyword in response.lower() for keyword in ["exception", "detect", "anomal"])
        
        # Should mention invoices
        assert "invoice" in response.lower()
    
    @pytest.mark.asyncio
    async def test_audit_report_request(self):
        """Test: User asks 'Generate audit report for invoices INV-001, INV-002'"""
        from app.agents.state import AgentState
        from app.agents.nodes import audit_agent_node
        
        state = AgentState(
            task_description="Generate audit report for invoices INV-001, INV-002",
            plan_id="scenario-audit-report",
            messages=[],
            current_agent="Audit"
        )
        
        result = await audit_agent_node(state)
        
        response = result["final_result"]
        
        # Should recognize report generation request
        assert any(keyword in response.lower() for keyword in ["report", "generate", "audit"])
        
        # Should mention the specific invoices
        assert any(invoice in response for invoice in ["INV-001", "INV-002"])


class TestClosingAgentScenarios:
    """Test Closing Agent scenarios (future enhancement)."""
    
    def test_closing_process_request(self):
        """Test: User asks 'Perform month-end closing'"""
        from app.agents.state import AgentState
        from app.agents.nodes import closing_agent_node
        
        state = AgentState(
            task_description="Perform month-end closing",
            plan_id="scenario-closing",
            messages=[],
            current_agent="Closing"
        )
        
        result = closing_agent_node(state)
        
        response = result["final_result"]
        
        # Should show future enhancement message
        assert any(keyword in response.lower() for keyword in ["development", "coming soon", "progress"])
        
        # Should mention Bill.com integration
        assert "Bill.com" in response or "billcom" in response.lower()
        
        # Should provide helpful information about future capabilities
        assert any(keyword in response.lower() for keyword in ["reconciliation", "variance", "journal"])
    
    def test_reconciliation_request(self):
        """Test: User asks 'Reconcile accounts with Bill.com data'"""
        from app.agents.state import AgentState
        from app.agents.nodes import closing_agent_node
        
        state = AgentState(
            task_description="Reconcile accounts with Bill.com data",
            plan_id="scenario-reconciliation",
            messages=[],
            current_agent="Closing"
        )
        
        result = closing_agent_node(state)
        
        response = result["final_result"]
        
        # Should show future enhancement message
        assert any(keyword in response.lower() for keyword in ["development", "coming soon"])
        
        # Should mention reconciliation
        assert "reconcil" in response.lower()


class TestMultiAgentWorkflows:
    """Test multi-agent workflow scenarios."""
    
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
    async def test_invoice_to_audit_workflow(self):
        """Test: Get invoice data, then audit it"""
        from app.agents.state import AgentState
        from app.agents.nodes import invoice_agent_node, audit_agent_node
        
        # Step 1: Get invoice data
        invoice_state = AgentState(
            task_description="Get details for invoice INV-12345 from Bill.com",
            plan_id="workflow-invoice-audit-1",
            messages=[],
            current_agent="Invoice"
        )
        
        invoice_result = await invoice_agent_node(invoice_state)
        
        # Step 2: Audit the invoice
        audit_state = AgentState(
            task_description="Get audit trail for invoice INV-12345",
            plan_id="workflow-invoice-audit-2",
            messages=[invoice_result["final_result"]],
            current_agent="Audit"
        )
        
        audit_result = await audit_agent_node(audit_state)
        
        # Both should complete successfully
        assert "final_result" in invoice_result
        assert "final_result" in audit_result
        
        # Both should mention the invoice
        assert "INV-12345" in invoice_result["final_result"] or "invoice" in invoice_result["final_result"].lower()
        assert "INV-12345" in audit_result["final_result"] or "audit" in audit_result["final_result"].lower()
    
    @pytest.mark.asyncio
    async def test_comprehensive_analysis_workflow(self):
        """Test: Comprehensive invoice analysis workflow"""
        from app.agents.state import AgentState
        from app.agents.nodes import invoice_agent_node, audit_agent_node, closing_agent_node
        
        base_task = "Analyze invoice INV-12345 comprehensively"
        
        # Step 1: Invoice Agent - Get invoice data
        invoice_state = AgentState(
            task_description=f"{base_task} - get invoice details from Bill.com",
            plan_id="workflow-comprehensive-1",
            messages=[],
            current_agent="Invoice"
        )
        
        invoice_result = await invoice_agent_node(invoice_state)
        
        # Step 2: Audit Agent - Check compliance
        audit_state = AgentState(
            task_description=f"{base_task} - check audit trail and compliance",
            plan_id="workflow-comprehensive-2",
            messages=[invoice_result["final_result"]],
            current_agent="Audit"
        )
        
        audit_result = await audit_agent_node(audit_state)
        
        # Step 3: Closing Agent - Check impact on closing
        closing_state = AgentState(
            task_description=f"{base_task} - assess impact on month-end closing",
            plan_id="workflow-comprehensive-3",
            messages=[invoice_result["final_result"], audit_result["final_result"]],
            current_agent="Closing"
        )
        
        closing_result = closing_agent_node(closing_state)
        
        # All should complete
        assert all("final_result" in result for result in [invoice_result, audit_result, closing_result])
        
        # Each should provide relevant information
        assert any(keyword in invoice_result["final_result"].lower() for keyword in ["invoice", "bill.com"])
        assert any(keyword in audit_result["final_result"].lower() for keyword in ["audit", "compliance"])
        assert any(keyword in closing_result["final_result"].lower() for keyword in ["closing", "development"])


class TestErrorRecoveryScenarios:
    """Test error recovery and fallback scenarios."""
    
    @pytest.mark.asyncio
    async def test_service_unavailable_scenario(self):
        """Test: Bill.com service is unavailable"""
        from app.agents.state import AgentState
        from app.agents.nodes import invoice_agent_node, audit_agent_node
        
        # Test Invoice Agent with service unavailable
        invoice_state = AgentState(
            task_description="Get recent invoices from Bill.com",
            plan_id="error-service-unavailable-1",
            messages=[],
            current_agent="Invoice"
        )
        
        invoice_result = await invoice_agent_node(invoice_state)
        
        # Should handle gracefully
        assert "final_result" in invoice_result
        response = invoice_result["final_result"]
        
        # Should mention the issue and provide guidance
        if "unavailable" in response.lower() or "error" in response.lower():
            assert any(keyword in response.lower() for keyword in ["mcp", "server", "configuration", "troubleshooting"])
        
        # Test Audit Agent with service unavailable
        audit_state = AgentState(
            task_description="Check compliance exceptions",
            plan_id="error-service-unavailable-2",
            messages=[],
            current_agent="Audit"
        )
        
        audit_result = await audit_agent_node(audit_state)
        
        # Should handle gracefully
        assert "final_result" in audit_result
        audit_response = audit_result["final_result"]
        
        # Should provide fallback information
        if "unavailable" in audit_response.lower():
            assert any(keyword in audit_response.lower() for keyword in ["fallback", "simulated", "configuration"])
    
    def test_invalid_configuration_scenario(self):
        """Test: Invalid Bill.com configuration"""
        # Clear environment variables
        bill_com_vars = [k for k in os.environ.keys() if k.startswith("BILL_COM_")]
        original_values = {}
        
        for var in bill_com_vars:
            original_values[var] = os.environ.get(var, "")
            if var in os.environ:
                del os.environ[var]
        
        try:
            from app.agents.state import AgentState
            from app.agents.nodes import invoice_agent_node
            
            state = AgentState(
                task_description="Get invoices from Bill.com",
                plan_id="error-invalid-config",
                messages=[],
                current_agent="Invoice"
            )
            
            # Should not crash, should handle gracefully
            result = asyncio.run(invoice_agent_node(state))
            
            assert "final_result" in result
            response = result["final_result"]
            
            # Should mention configuration issues
            assert any(keyword in response.lower() for keyword in ["configuration", "credentials", "setup"])
            
        finally:
            # Restore environment variables
            for var, value in original_values.items():
                if value:
                    os.environ[var] = value


class TestUserExperienceScenarios:
    """Test user experience scenarios."""
    
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
    async def test_natural_language_requests(self):
        """Test natural language requests"""
        from app.agents.state import AgentState
        from app.agents.nodes import invoice_agent_node, audit_agent_node
        
        natural_requests = [
            "Show me what invoices we have in Bill.com",
            "I need to check if there are any compliance issues",
            "Can you find invoice number 12345?",
            "What's the audit trail for our recent invoices?",
            "Are there any suspicious transactions?"
        ]
        
        for i, request in enumerate(natural_requests):
            # Alternate between agents
            agent_node = invoice_agent_node if i % 2 == 0 else audit_agent_node
            agent_name = "Invoice" if i % 2 == 0 else "Audit"
            
            state = AgentState(
                task_description=request,
                plan_id=f"natural-language-{i}",
                messages=[],
                current_agent=agent_name
            )
            
            result = await agent_node(state)
            
            # Should handle all natural language requests
            assert "final_result" in result
            assert len(result["final_result"]) > 0
            
            # Should provide helpful responses
            response = result["final_result"]
            assert not any(unhelpful in response.lower() for unhelpful in ["error", "failed", "cannot"])
    
    @pytest.mark.asyncio
    async def test_help_and_guidance_requests(self):
        """Test help and guidance requests"""
        from app.agents.state import AgentState
        from app.agents.nodes import invoice_agent_node, audit_agent_node
        
        help_requests = [
            "What can you do with Bill.com?",
            "How do I check audit compliance?",
            "What Bill.com operations are available?",
            "Help me understand audit capabilities"
        ]
        
        for i, request in enumerate(help_requests):
            agent_node = invoice_agent_node if "bill.com" in request.lower() else audit_agent_node
            agent_name = "Invoice" if "bill.com" in request.lower() else "Audit"
            
            state = AgentState(
                task_description=request,
                plan_id=f"help-guidance-{i}",
                messages=[],
                current_agent=agent_name
            )
            
            result = await agent_node(state)
            
            # Should provide helpful guidance
            assert "final_result" in result
            response = result["final_result"]
            
            # Should mention available operations or capabilities
            assert any(keyword in response.lower() for keyword in ["available", "can", "operations", "capabilities"])


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])