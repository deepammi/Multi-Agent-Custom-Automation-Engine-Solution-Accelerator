#!/usr/bin/env python3
"""
Bill.com Integration Realistic Scenarios Test Suite

This test suite focuses on realistic business scenarios and workflows
that users would encounter when using the Bill.com integration.
"""

import os
import sys
import pytest
import asyncio
import json
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


class TestInvoiceProcessingWorkflows:
    """Test realistic invoice processing workflows."""
    
    def setup_method(self):
        """Set up test environment with realistic business data."""
        self.test_env = {
            "BILL_COM_USERNAME": "accounting@testcompany.com",
            "BILL_COM_PASSWORD": "SecurePassword123!",
            "BILL_COM_ORG_ID": "00D000000000000EAA",
            "BILL_COM_DEV_KEY": "abcd1234-5678-90ef-ghij-klmnopqrstuv",
            "BILL_COM_ENVIRONMENT": "sandbox"
        }
        
        for key, value in self.test_env.items():
            os.environ[key] = value
        
        # Realistic business data
        self.vendors = [
            {"id": "vendor_001", "name": "Office Supplies Inc", "email": "billing@officesupplies.com"},
            {"id": "vendor_002", "name": "Professional Services LLC", "email": "invoices@proservices.com"},
            {"id": "vendor_003", "name": "Utilities Company", "email": "billing@utilities.com"},
            {"id": "vendor_004", "name": "Software Solutions Corp", "email": "accounts@software.com"}
        ]
        
        self.invoices = [
            {
                "id": "inv_001",
                "invoiceNumber": "OS-2024-001",
                "vendorName": "Office Supplies Inc",
                "vendorId": "vendor_001",
                "amount": 245.67,
                "status": "NeedsApproval",
                "invoiceDate": "2024-01-15",
                "dueDate": "2024-02-14",
                "description": "Monthly office supplies order"
            },
            {
                "id": "inv_002", 
                "invoiceNumber": "PS-2024-002",
                "vendorName": "Professional Services LLC",
                "vendorId": "vendor_002",
                "amount": 5000.00,
                "status": "Approved",
                "invoiceDate": "2024-01-16",
                "dueDate": "2024-02-15",
                "description": "Q1 consulting services"
            },
            {
                "id": "inv_003",
                "invoiceNumber": "UT-2024-003", 
                "vendorName": "Utilities Company",
                "vendorId": "vendor_003",
                "amount": 1250.33,
                "status": "Paid",
                "invoiceDate": "2024-01-10",
                "dueDate": "2024-02-09",
                "description": "January utilities bill"
            },
            {
                "id": "inv_004",
                "invoiceNumber": "SW-2024-004",
                "vendorName": "Software Solutions Corp", 
                "vendorId": "vendor_004",
                "amount": 2999.99,
                "status": "NeedsApproval",
                "invoiceDate": "2024-01-20",
                "dueDate": "2024-02-19",
                "description": "Annual software license renewal"
            }
        ]
    
    def teardown_method(self):
        """Clean up test environment."""
        for key in self.test_env.keys():
            if key in os.environ:
                del os.environ[key]
    
    @pytest.mark.asyncio
    async def test_monthly_invoice_review_workflow(self):
        """Test monthly invoice review workflow scenario."""
        from core.bill_com_tools import get_bill_com_invoices, get_bill_com_invoice_details
        
        with patch('core.bill_com_tools.get_bill_com_service') as mock_get_service:
            mock_service = AsyncMock()
            
            # Mock getting invoices for the month
            mock_service.get_invoices.return_value = self.invoices
            mock_get_service.return_value = mock_service
            
            # Step 1: Get all invoices for January 2024
            result = await get_bill_com_invoices(
                limit=50,
                start_date="2024-01-01",
                end_date="2024-01-31"
            )
            
            response_data = json.loads(result)
            assert response_data["success"] is True
            assert response_data["details"]["count"] == 4
            
            # Step 2: Focus on invoices needing approval
            needs_approval = [
                inv for inv in response_data["details"]["invoices"]
                if inv["status"] == "NeedsApproval"
            ]
            
            assert len(needs_approval) == 2
            assert any(inv["invoice_number"] == "OS-2024-001" for inv in needs_approval)
            assert any(inv["invoice_number"] == "SW-2024-004" for inv in needs_approval)
            
            # Step 3: Get details for high-value invoice requiring approval
            high_value_invoice = next(
                inv for inv in needs_approval 
                if inv["total_amount"] > 1000
            )
            
            # Mock complete invoice details
            mock_complete_details = {
                "id": "inv_004",
                "invoice_number": "SW-2024-004",
                "vendor_name": "Software Solutions Corp",
                "total_amount": 2999.99,
                "status": "NeedsApproval",
                "line_items": [
                    {
                        "description": "Annual Software License",
                        "quantity": 1,
                        "unit_price": 2999.99,
                        "total_amount": 2999.99
                    }
                ],
                "attachments": [
                    {
                        "filename": "software_license_agreement.pdf",
                        "file_size": 1024000,
                        "content_type": "application/pdf"
                    }
                ],
                "data_completeness_score": 0.9
            }
            
            mock_service.get_complete_invoice_details.return_value = mock_complete_details
            
            details_result = await get_bill_com_invoice_details(high_value_invoice["id"])
            details_data = json.loads(details_result)
            
            assert details_data["success"] is True
            assert details_data["details"]["invoice"]["total_amount"] == 2999.99
            assert "Software License" in str(details_data["details"]["invoice"]["line_items"])
    
    @pytest.mark.asyncio
    async def test_vendor_analysis_workflow(self):
        """Test vendor analysis and spending pattern workflow."""
        from core.bill_com_tools import get_bill_com_invoices, get_bill_com_vendors
        
        with patch('core.bill_com_tools.get_bill_com_service') as mock_get_service:
            mock_service = AsyncMock()
            mock_service.get_invoices.return_value = self.invoices
            mock_service.get_vendors.return_value = self.vendors
            mock_get_service.return_value = mock_service
            
            # Step 1: Get all vendors
            vendors_result = await get_bill_com_vendors()
            vendors_data = json.loads(vendors_result)
            
            assert vendors_data["success"] is True
            assert vendors_data["details"]["count"] == 4
            
            # Step 2: Analyze spending by vendor
            invoices_result = await get_bill_com_invoices(limit=100)
            invoices_data = json.loads(invoices_result)
            
            # Calculate spending by vendor
            vendor_spending = {}
            for invoice in invoices_data["details"]["invoices"]:
                vendor = invoice["vendor_name"]
                amount = invoice["total_amount"]
                vendor_spending[vendor] = vendor_spending.get(vendor, 0) + amount
            
            # Verify spending calculations
            assert vendor_spending["Professional Services LLC"] == 5000.00
            assert vendor_spending["Software Solutions Corp"] == 2999.99
            assert vendor_spending["Utilities Company"] == 1250.33
            assert vendor_spending["Office Supplies Inc"] == 245.67
            
            # Step 3: Identify top spending vendor
            top_vendor = max(vendor_spending.items(), key=lambda x: x[1])
            assert top_vendor[0] == "Professional Services LLC"
            assert top_vendor[1] == 5000.00
    
    @pytest.mark.asyncio
    async def test_payment_due_analysis_workflow(self):
        """Test payment due date analysis workflow."""
        from core.bill_com_tools import get_bill_com_invoices
        from datetime import datetime, timedelta
        
        with patch('core.bill_com_tools.get_bill_com_service') as mock_get_service:
            mock_service = AsyncMock()
            mock_service.get_invoices.return_value = self.invoices
            mock_get_service.return_value = mock_service
            
            # Get all unpaid invoices
            result = await get_bill_com_invoices(limit=100)
            response_data = json.loads(result)
            
            # Filter unpaid invoices
            unpaid_invoices = [
                inv for inv in response_data["details"]["invoices"]
                if inv["status"] in ["NeedsApproval", "Approved"]
            ]
            
            assert len(unpaid_invoices) == 3  # Excluding "Paid" status
            
            # Analyze due dates
            today = datetime(2024, 1, 25)  # Simulate current date
            
            due_soon = []
            overdue = []
            
            for invoice in unpaid_invoices:
                due_date = datetime.strptime(invoice["due_date"], "%Y-%m-%d")
                days_until_due = (due_date - today).days
                
                if days_until_due < 0:
                    overdue.append(invoice)
                elif days_until_due <= 7:
                    due_soon.append(invoice)
            
            # Verify analysis results
            assert len(due_soon) >= 0  # Invoices due within 7 days
            assert len(overdue) == 0   # No overdue invoices in test data
            
            # Calculate total amounts
            total_due_soon = sum(inv["total_amount"] for inv in due_soon)
            total_overdue = sum(inv["total_amount"] for inv in overdue)
            
            assert total_overdue == 0  # No overdue amounts
    
    @pytest.mark.asyncio
    async def test_compliance_audit_workflow(self):
        """Test compliance audit workflow scenario."""
        from core.bill_com_tools import get_bill_com_invoices, get_bill_com_invoice_details
        
        with patch('core.bill_com_tools.get_bill_com_service') as mock_get_service:
            mock_service = AsyncMock()
            mock_service.get_invoices.return_value = self.invoices
            mock_get_service.return_value = mock_service
            
            # Step 1: Get all invoices for audit period
            result = await get_bill_com_invoices(
                limit=100,
                start_date="2024-01-01",
                end_date="2024-01-31"
            )
            
            response_data = json.loads(result)
            invoices = response_data["details"]["invoices"]
            
            # Step 2: Identify compliance issues
            compliance_issues = []
            
            for invoice in invoices:
                # Check for missing approvals on high-value invoices
                if invoice["total_amount"] > 1000 and invoice["status"] == "NeedsApproval":
                    compliance_issues.append({
                        "invoice_id": invoice["id"],
                        "issue": "High-value invoice pending approval",
                        "amount": invoice["total_amount"],
                        "vendor": invoice["vendor_name"]
                    })
                
                # Check for invoices approaching due date without approval
                due_date = datetime.strptime(invoice["due_date"], "%Y-%m-%d")
                days_until_due = (due_date - datetime(2024, 1, 25)).days
                
                if days_until_due <= 5 and invoice["status"] == "NeedsApproval":
                    compliance_issues.append({
                        "invoice_id": invoice["id"],
                        "issue": "Invoice due soon without approval",
                        "days_until_due": days_until_due,
                        "vendor": invoice["vendor_name"]
                    })
            
            # Step 3: Generate compliance report
            high_value_pending = [
                issue for issue in compliance_issues
                if "High-value" in issue["issue"]
            ]
            
            urgent_approvals = [
                issue for issue in compliance_issues
                if "due soon" in issue["issue"]
            ]
            
            # Verify compliance analysis
            assert len(high_value_pending) >= 1  # Software license invoice
            assert any(
                issue["vendor"] == "Software Solutions Corp"
                for issue in high_value_pending
            )


class TestAgentWorkflowIntegration:
    """Test agent workflow integration with realistic scenarios."""
    
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
    async def test_invoice_agent_monthly_review(self):
        """Test Invoice Agent handling monthly review request."""
        from app.agents.state import AgentState
        from app.agents.nodes import invoice_agent_node
        
        state = AgentState(
            task_description="Review all invoices from January 2024 and identify those needing approval",
            plan_id="monthly-review-001",
            messages=[],
            current_agent="Invoice"
        )
        
        result = await invoice_agent_node(state)
        
        # Verify agent response structure
        assert "messages" in result
        assert "current_agent" in result
        assert "final_result" in result
        assert result["current_agent"] == "Invoice"
        
        response = result["final_result"]
        
        # Should contain relevant keywords for invoice review
        assert any(keyword in response.lower() for keyword in [
            "invoice", "review", "approval", "january", "bill.com"
        ])
    
    @pytest.mark.asyncio
    async def test_invoice_agent_vendor_analysis(self):
        """Test Invoice Agent handling vendor spending analysis."""
        from app.agents.state import AgentState
        from app.agents.nodes import invoice_agent_node
        
        state = AgentState(
            task_description="Analyze spending by vendor and identify our top 5 vendors by amount",
            plan_id="vendor-analysis-001",
            messages=[],
            current_agent="Invoice"
        )
        
        result = await invoice_agent_node(state)
        
        response = result["final_result"]
        
        # Should contain relevant keywords for vendor analysis
        assert any(keyword in response.lower() for keyword in [
            "vendor", "spending", "analysis", "top", "amount"
        ])
    
    @pytest.mark.asyncio
    async def test_audit_agent_compliance_check(self):
        """Test Audit Agent handling compliance monitoring request."""
        from app.agents.state import AgentState
        from app.agents.nodes import audit_agent_node
        
        state = AgentState(
            task_description="Check for compliance issues in our invoice approval process",
            plan_id="compliance-check-001",
            messages=[],
            current_agent="Audit"
        )
        
        result = await audit_agent_node(state)
        
        response = result["final_result"]
        
        # Should contain relevant keywords for compliance
        assert any(keyword in response.lower() for keyword in [
            "compliance", "audit", "approval", "process", "monitoring"
        ])
    
    @pytest.mark.asyncio
    async def test_audit_agent_exception_detection(self):
        """Test Audit Agent handling exception detection request."""
        from app.agents.state import AgentState
        from app.agents.nodes import audit_agent_node
        
        state = AgentState(
            task_description="Detect any unusual patterns or exceptions in recent invoice processing",
            plan_id="exception-detection-001",
            messages=[],
            current_agent="Audit"
        )
        
        result = await audit_agent_node(state)
        
        response = result["final_result"]
        
        # Should contain relevant keywords for exception detection
        assert any(keyword in response.lower() for keyword in [
            "exception", "pattern", "unusual", "detection", "monitoring"
        ])


class TestBusinessProcessScenarios:
    """Test realistic business process scenarios."""
    
    @pytest.mark.asyncio
    async def test_month_end_closing_preparation(self):
        """Test month-end closing preparation workflow."""
        from core.bill_com_tools import get_bill_com_invoices
        
        # Mock month-end data
        month_end_invoices = [
            {
                "id": "inv_me_001",
                "invoiceNumber": "ME-2024-001",
                "vendorName": "Accrual Vendor A",
                "amount": 1500.00,
                "status": "NeedsApproval",
                "invoiceDate": "2024-01-31",
                "dueDate": "2024-02-29"
            },
            {
                "id": "inv_me_002",
                "invoiceNumber": "ME-2024-002", 
                "vendorName": "Accrual Vendor B",
                "amount": 2250.00,
                "status": "Approved",
                "invoiceDate": "2024-01-31",
                "dueDate": "2024-03-01"
            }
        ]
        
        with patch('core.bill_com_tools.get_bill_com_service') as mock_get_service:
            mock_service = AsyncMock()
            mock_service.get_invoices.return_value = month_end_invoices
            mock_get_service.return_value = mock_service
            
            # Get invoices for month-end accruals
            result = await get_bill_com_invoices(
                start_date="2024-01-31",
                end_date="2024-01-31"
            )
            
            response_data = json.loads(result)
            invoices = response_data["details"]["invoices"]
            
            # Calculate accrual amounts
            total_accruals = sum(inv["total_amount"] for inv in invoices)
            pending_approval_accruals = sum(
                inv["total_amount"] for inv in invoices
                if inv["status"] == "NeedsApproval"
            )
            
            assert total_accruals == 3750.00
            assert pending_approval_accruals == 1500.00
    
    @pytest.mark.asyncio
    async def test_cash_flow_analysis(self):
        """Test cash flow analysis workflow."""
        from core.bill_com_tools import get_bill_com_invoices
        
        # Mock cash flow data
        cash_flow_invoices = [
            {
                "id": "cf_001",
                "invoiceNumber": "CF-001",
                "vendorName": "Immediate Payment Vendor",
                "amount": 5000.00,
                "status": "Approved",
                "dueDate": "2024-01-26"  # Due tomorrow
            },
            {
                "id": "cf_002",
                "invoiceNumber": "CF-002",
                "vendorName": "Next Week Vendor",
                "amount": 3000.00,
                "status": "Approved", 
                "dueDate": "2024-02-01"  # Due next week
            },
            {
                "id": "cf_003",
                "invoiceNumber": "CF-003",
                "vendorName": "Next Month Vendor",
                "amount": 7500.00,
                "status": "Approved",
                "dueDate": "2024-02-25"  # Due next month
            }
        ]
        
        with patch('core.bill_com_tools.get_bill_com_service') as mock_get_service:
            mock_service = AsyncMock()
            mock_service.get_invoices.return_value = cash_flow_invoices
            mock_get_service.return_value = mock_service
            
            result = await get_bill_com_invoices(status="approved")
            response_data = json.loads(result)
            invoices = response_data["details"]["invoices"]
            
            # Analyze cash flow by due date buckets
            today = datetime(2024, 1, 25)
            
            immediate = []  # Due within 3 days
            short_term = []  # Due within 2 weeks
            long_term = []  # Due later
            
            for invoice in invoices:
                due_date = datetime.strptime(invoice["due_date"], "%Y-%m-%d")
                days_until_due = (due_date - today).days
                
                if days_until_due <= 3:
                    immediate.append(invoice)
                elif days_until_due <= 14:
                    short_term.append(invoice)
                else:
                    long_term.append(invoice)
            
            # Calculate cash flow requirements
            immediate_cash_need = sum(inv["total_amount"] for inv in immediate)
            short_term_cash_need = sum(inv["total_amount"] for inv in short_term)
            long_term_cash_need = sum(inv["total_amount"] for inv in long_term)
            
            assert immediate_cash_need == 5000.00
            assert short_term_cash_need == 3000.00
            assert long_term_cash_need == 7500.00
    
    @pytest.mark.asyncio
    async def test_vendor_performance_analysis(self):
        """Test vendor performance analysis workflow."""
        from core.bill_com_tools import get_bill_com_invoices, get_bill_com_vendors
        
        # Mock vendor performance data
        performance_invoices = [
            {
                "id": "vp_001",
                "invoiceNumber": "VP-001",
                "vendorName": "Reliable Vendor",
                "amount": 1000.00,
                "status": "Paid",
                "invoiceDate": "2024-01-01",
                "dueDate": "2024-01-31"
            },
            {
                "id": "vp_002", 
                "invoiceNumber": "VP-002",
                "vendorName": "Reliable Vendor",
                "amount": 1500.00,
                "status": "Paid",
                "invoiceDate": "2024-01-15",
                "dueDate": "2024-02-14"
            },
            {
                "id": "vp_003",
                "invoiceNumber": "VP-003",
                "vendorName": "Problem Vendor",
                "amount": 2000.00,
                "status": "NeedsApproval",
                "invoiceDate": "2024-01-10",
                "dueDate": "2024-01-20"  # Overdue
            }
        ]
        
        vendors = [
            {"id": "v_001", "name": "Reliable Vendor", "status": "Active"},
            {"id": "v_002", "name": "Problem Vendor", "status": "Active"}
        ]
        
        with patch('core.bill_com_tools.get_bill_com_service') as mock_get_service:
            mock_service = AsyncMock()
            mock_service.get_invoices.return_value = performance_invoices
            mock_service.get_vendors.return_value = vendors
            mock_get_service.return_value = mock_service
            
            # Get vendor and invoice data
            vendors_result = await get_bill_com_vendors()
            invoices_result = await get_bill_com_invoices(limit=100)
            
            vendors_data = json.loads(vendors_result)
            invoices_data = json.loads(invoices_result)
            
            # Analyze vendor performance
            vendor_metrics = {}
            
            for invoice in invoices_data["details"]["invoices"]:
                vendor = invoice["vendor_name"]
                if vendor not in vendor_metrics:
                    vendor_metrics[vendor] = {
                        "total_invoices": 0,
                        "total_amount": 0,
                        "paid_invoices": 0,
                        "pending_invoices": 0
                    }
                
                vendor_metrics[vendor]["total_invoices"] += 1
                vendor_metrics[vendor]["total_amount"] += invoice["total_amount"]
                
                if invoice["status"] == "Paid":
                    vendor_metrics[vendor]["paid_invoices"] += 1
                else:
                    vendor_metrics[vendor]["pending_invoices"] += 1
            
            # Verify performance metrics
            reliable_metrics = vendor_metrics["Reliable Vendor"]
            assert reliable_metrics["total_invoices"] == 2
            assert reliable_metrics["paid_invoices"] == 2
            assert reliable_metrics["pending_invoices"] == 0
            
            problem_metrics = vendor_metrics["Problem Vendor"]
            assert problem_metrics["total_invoices"] == 1
            assert problem_metrics["paid_invoices"] == 0
            assert problem_metrics["pending_invoices"] == 1


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short", "--asyncio-mode=auto"])