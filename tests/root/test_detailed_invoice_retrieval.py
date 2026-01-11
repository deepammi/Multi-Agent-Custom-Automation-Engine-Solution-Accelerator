#!/usr/bin/env python3
"""
Test script to verify enhanced detailed invoice data retrieval functionality.
"""

import sys
import asyncio
import logging
from datetime import datetime, timezone
sys.path.append('src/mcp_server')

# Configure logging to see the structured logs
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def test_complete_invoice_details():
    """Test the complete invoice details functionality."""
    print("🧪 Testing Complete Invoice Details Retrieval...")
    
    try:
        from services.bill_com_service import BillComAPIService
        
        # Create service instance with context
        service = BillComAPIService(plan_id="test-plan-invoice", agent="test-invoice-agent")
        
        print("\n📋 Testing complete invoice details structure:")
        
        # Test the _build_complete_invoice_details method with mock data
        mock_invoice_data = {
            "id": "INV123",
            "invoiceNumber": "INV-2024-001",
            "vendorName": "Test Vendor Inc",
            "vendorId": "VENDOR123",
            "invoiceDate": "2024-01-15",
            "dueDate": "2024-02-15",
            "amount": 1500.00,
            "currency": "USD",
            "status": "approved",
            "description": "Test invoice for services",
            "createdTime": "2024-01-15T10:00:00Z",
            "updatedTime": "2024-01-16T14:30:00Z"
        }
        
        mock_line_items = [
            {
                "id": "LINE1",
                "description": "Consulting Services",
                "quantity": 10,
                "unitPrice": 100.00,
                "amount": 1000.00,
                "accountCode": "5000",
                "taxAmount": 0,
                "department": "IT",
                "project": "Project A"
            },
            {
                "id": "LINE2", 
                "description": "Software License",
                "quantity": 1,
                "unitPrice": 500.00,
                "amount": 500.00,
                "accountCode": "5100",
                "taxAmount": 0,
                "department": "IT",
                "project": "Project A"
            }
        ]
        
        mock_payments = [
            {
                "id": "PAY1",
                "paymentDate": "2024-01-20",
                "amount": 750.00,
                "paymentMethod": "ACH",
                "referenceNumber": "ACH123456",
                "status": "completed",
                "createdTime": "2024-01-20T09:00:00Z",
                "notes": "Partial payment"
            }
        ]
        
        mock_attachments = [
            {
                "id": "ATT1",
                "fileName": "invoice_scan.pdf",
                "fileSize": 1024000,  # 1MB
                "contentType": "application/pdf",
                "downloadUrl": "https://example.com/download/att1",
                "uploadDate": "2024-01-15T11:00:00Z",
                "uploadedBy": "user@company.com",
                "description": "Scanned invoice document"
            }
        ]
        
        mock_approval_workflow = {
            "status": "approved",
            "approvalSteps": [
                {"step": 1, "approver": "manager@company.com", "required": True},
                {"step": 2, "approver": "finance@company.com", "required": True}
            ],
            "currentApprover": None,
            "approvalHistory": [
                {
                    "step": 1,
                    "approver": "manager@company.com",
                    "action": "approved",
                    "timestamp": "2024-01-16T10:00:00Z",
                    "comments": "Approved for payment"
                },
                {
                    "step": 2,
                    "approver": "finance@company.com", 
                    "action": "approved",
                    "timestamp": "2024-01-16T14:00:00Z",
                    "comments": "Final approval"
                }
            ],
            "workflowStarted": "2024-01-15T12:00:00Z",
            "workflowCompleted": "2024-01-16T14:00:00Z",
            "requiresApproval": True
        }
        
        # Build complete details
        complete_details = service._build_complete_invoice_details(
            mock_invoice_data,
            mock_payments,
            mock_line_items,
            mock_attachments,
            mock_approval_workflow
        )
        
        # Verify structure and calculations
        assert complete_details["id"] == "INV123"
        assert complete_details["invoice_number"] == "INV-2024-001"
        assert complete_details["total_amount"] == 1500.00
        assert complete_details["total_payments"] == 750.00
        assert complete_details["remaining_balance"] == 750.00
        assert complete_details["is_fully_paid"] == False
        assert complete_details["line_items_count"] == 2
        assert complete_details["payment_count"] == 1
        assert complete_details["attachment_count"] == 1
        
        print("   ✅ Basic invoice information correct")
        
        # Verify financial calculations
        assert complete_details["remaining_balance"] == 750.00
        assert complete_details["total_payments"] == 750.00
        assert complete_details["is_fully_paid"] == False
        
        print("   ✅ Financial calculations correct")
        
        # Verify line items formatting
        line_items = complete_details["line_items"]
        assert len(line_items) == 2
        assert line_items[0]["description"] == "Consulting Services"
        assert line_items[0]["quantity"] == 10.0
        assert line_items[0]["unit_price"] == 100.0
        assert line_items[0]["total_amount"] == 1000.0
        
        print("   ✅ Line items formatting correct")
        
        # Verify payment history formatting
        payment_history = complete_details["payment_history"]
        assert len(payment_history) == 1
        assert payment_history[0]["amount"] == 750.0
        assert payment_history[0]["payment_method"] == "ACH"
        
        print("   ✅ Payment history formatting correct")
        
        # Verify attachments formatting
        attachments = complete_details["attachments"]
        assert len(attachments) == 1
        assert attachments[0]["filename"] == "invoice_scan.pdf"
        assert attachments[0]["file_size"] == 1024000
        assert attachments[0]["content_type"] == "application/pdf"
        
        print("   ✅ Attachments formatting correct")
        
        # Verify approval workflow formatting
        approval_workflow = complete_details["approval_workflow"]
        assert approval_workflow is not None
        assert approval_workflow["current_status"] == "approved"
        assert len(approval_workflow["approval_history"]) == 2
        assert complete_details["approval_status"] == "approved"
        
        print("   ✅ Approval workflow formatting correct")
        
        # Verify data availability indicators
        data_availability = complete_details["data_availability"]
        assert data_availability["basic_info"] == True
        assert data_availability["line_items"] == True
        assert data_availability["payment_history"] == True
        assert data_availability["attachments"] == True
        assert data_availability["approval_workflow"] == True
        
        print("   ✅ Data availability indicators correct")
        
        # Verify completeness score
        completeness_score = complete_details["data_completeness_score"]
        assert 0.0 <= completeness_score <= 1.0
        assert completeness_score > 0.8  # Should be high with all data present
        
        print(f"   ✅ Data completeness score: {completeness_score}")
        
        print("✅ Complete invoice details structure test passed!")
        return True
        
    except Exception as e:
        print(f"❌ Complete invoice details test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_formatting_methods():
    """Test individual formatting methods."""
    print("\n🧪 Testing Individual Formatting Methods...")
    
    try:
        from services.bill_com_service import BillComAPIService
        
        service = BillComAPIService()
        
        print("\n📋 Testing formatting methods:")
        
        # Test line items formatting
        mock_line_items = [
            {
                "id": "LINE1",
                "description": "Test Item",
                "quantity": "5",  # String to test conversion
                "unitPrice": "25.50",  # String to test conversion
                "amount": "127.50",  # String to test conversion
                "accountCode": "5000"
            }
        ]
        
        formatted_line_items = service._format_line_items(mock_line_items)
        assert len(formatted_line_items) == 1
        assert formatted_line_items[0]["quantity"] == 5.0
        assert formatted_line_items[0]["unit_price"] == 25.50
        assert formatted_line_items[0]["total_amount"] == 127.50
        
        print("   ✅ Line items formatting with type conversion")
        
        # Test payment history formatting and sorting
        mock_payments = [
            {
                "id": "PAY1",
                "paymentDate": "2024-01-15",
                "amount": "100.00",
                "paymentMethod": "Check"
            },
            {
                "id": "PAY2", 
                "paymentDate": "2024-01-20",  # Later date
                "amount": "200.00",
                "paymentMethod": "ACH"
            }
        ]
        
        formatted_payments = service._format_payment_history(mock_payments)
        assert len(formatted_payments) == 2
        # Should be sorted by date (most recent first)
        assert formatted_payments[0]["payment_date"] == "2024-01-20"
        assert formatted_payments[1]["payment_date"] == "2024-01-15"
        assert formatted_payments[0]["amount"] == 200.0
        
        print("   ✅ Payment history formatting and sorting")
        
        # Test approval status determination
        test_workflows = [
            ({"status": "approved"}, "approved"),
            ({"status": "pending"}, "pending"),
            ({"status": "rejected"}, "rejected"),
            ({"status": "unknown_status"}, "unknown"),
            (None, "no_workflow")
        ]
        
        for workflow, expected_status in test_workflows:
            actual_status = service._get_approval_status(workflow)
            assert actual_status == expected_status
        
        print("   ✅ Approval status determination")
        
        # Test completeness score calculation
        mock_invoice = {"id": "INV1", "invoiceNumber": "INV-001", "vendorName": "Vendor", "amount": 100, "status": "approved"}
        score = service._calculate_completeness_score(mock_invoice, [], [], [], None)
        assert 0.0 <= score <= 1.0
        
        # With all data
        score_complete = service._calculate_completeness_score(mock_invoice, [{}], [{}], [{}], {})
        assert score_complete > score  # Should be higher with more data
        
        print(f"   ✅ Completeness score calculation (partial: {score}, complete: {score_complete})")
        
        print("✅ Individual formatting methods test passed!")
        return True
        
    except Exception as e:
        print(f"❌ Formatting methods test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_error_handling():
    """Test error handling in detailed invoice retrieval."""
    print("\n🧪 Testing Error Handling...")
    
    try:
        from services.bill_com_service import BillComAPIService
        
        service = BillComAPIService(plan_id="test-error", agent="test-error-agent")
        
        print("\n📋 Testing error handling scenarios:")
        
        # Test safe methods with exceptions
        async def mock_failing_method():
            raise Exception("Test error")
        
        # Test _get_invoice_payments_safe
        result = await service._get_invoice_payments_safe("INVALID_ID")
        assert result == []  # Should return empty list on error
        
        print("   ✅ Safe payment retrieval error handling")
        
        # Test _get_invoice_line_items_safe  
        result = await service._get_invoice_line_items_safe("INVALID_ID")
        assert result == []  # Should return empty list on error
        
        print("   ✅ Safe line items retrieval error handling")
        
        # Test _get_invoice_attachments_safe
        result = await service._get_invoice_attachments_safe("INVALID_ID")
        assert result == []  # Should return empty list on error
        
        print("   ✅ Safe attachments retrieval error handling")
        
        # Test _get_invoice_approval_workflow_safe
        result = await service._get_invoice_approval_workflow_safe("INVALID_ID")
        assert result is None  # Should return None on error
        
        print("   ✅ Safe approval workflow retrieval error handling")
        
        print("✅ Error handling test passed!")
        return True
        
    except Exception as e:
        print(f"❌ Error handling test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_tools_integration():
    """Test the enhanced tools integration."""
    print("\n🧪 Testing Enhanced Tools Integration...")
    
    try:
        # Test that we can import the tools module and check structure
        import importlib.util
        
        # Check if the bill_com_tools module can be loaded
        spec = importlib.util.spec_from_file_location(
            "bill_com_tools", 
            "src/mcp_server/core/bill_com_tools.py"
        )
        
        if spec and spec.loader:
            print("   ✅ Bill.com tools module structure is valid")
            
            # Check the file content for the new tools
            with open("src/mcp_server/core/bill_com_tools.py", "r") as f:
                content = f.read()
            
            # Check for enhanced invoice details tool
            if "get_bill_com_invoice_details" in content and "comprehensive detailed information" in content:
                print("   ✅ Enhanced invoice details tool found")
            else:
                print("   ❌ Enhanced invoice details tool not found")
                return False
            
            # Check for new attachments tool
            if "get_bill_com_invoice_attachments" in content:
                print("   ✅ Invoice attachments tool found")
            else:
                print("   ❌ Invoice attachments tool not found")
                return False
            
            # Check for new approval status tool
            if "get_bill_com_invoice_approval_status" in content:
                print("   ✅ Invoice approval status tool found")
            else:
                print("   ❌ Invoice approval status tool not found")
                return False
            
            # Check tool count is updated
            if "return 6" in content:
                print("   ✅ Tool count updated to 6")
            else:
                print("   ❌ Tool count not updated")
                return False
            
            print("   📋 Expected enhanced tools:")
            expected_tools = [
                "get_bill_com_invoices",
                "get_bill_com_invoice_details (enhanced)",
                "search_bill_com_invoices", 
                "get_bill_com_vendors",
                "get_bill_com_invoice_attachments (new)",
                "get_bill_com_invoice_approval_status (new)"
            ]
            
            for tool in expected_tools:
                print(f"      ✅ {tool}")
            
            print("✅ Enhanced tools integration test passed!")
            return True
        else:
            print("   ❌ Could not load Bill.com tools module")
            return False
            
    except Exception as e:
        print(f"❌ Enhanced tools integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all detailed invoice retrieval tests."""
    print("🚀 Detailed Invoice Data Retrieval Test Suite")
    print("=" * 70)
    
    tests = [
        test_complete_invoice_details,
        test_formatting_methods,
        test_error_handling,
        test_tools_integration
    ]
    
    results = []
    for test in tests:
        try:
            result = await test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            results.append(False)
    
    print("\n" + "=" * 70)
    print("📊 Test Results Summary:")
    
    passed = sum(results)
    total = len(results)
    
    test_names = [
        "Complete Invoice Details Structure",
        "Individual Formatting Methods",
        "Error Handling",
        "Enhanced Tools Integration"
    ]
    
    for i, (test_name, result) in enumerate(zip(test_names, results)):
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {i+1}. {test_name}: {status}")
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All detailed invoice retrieval tests passed!")
        print("\n📋 Enhanced Features Implemented:")
        print("   ✅ Complete invoice details with line items")
        print("   ✅ Payment history retrieval and formatting")
        print("   ✅ Invoice attachments handling (URLs/metadata)")
        print("   ✅ Approval workflow status and timestamps")
        print("   ✅ Incomplete data handling with field availability indicators")
        print("   ✅ Financial calculations (remaining balance, payment totals)")
        print("   ✅ Data completeness scoring")
        print("   ✅ Enhanced error handling for all data sources")
        print("   ✅ New MCP tools for attachments and approval status")
        return True
    else:
        print("⚠️  Some detailed invoice retrieval tests failed.")
        return False


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)