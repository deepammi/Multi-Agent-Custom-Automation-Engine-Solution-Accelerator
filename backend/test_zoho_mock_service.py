"""Test Zoho MCP service with mock data (Phase 1)."""
import asyncio
import logging
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.zoho_mcp_service import get_zoho_service

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Colors
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
BOLD = '\033[1m'
RESET = '\033[0m'


def print_header(text):
    print(f"\n{BOLD}{BLUE}{text}{RESET}")
    print("=" * len(text))


def print_success(text):
    print(f"{GREEN}✅ {text}{RESET}")


def print_error(text):
    print(f"{RED}❌ {text}{RESET}")


def print_info(text):
    print(f"   {text}")


async def test_phase_1():
    """Test Phase 1: Mock Zoho Service."""
    print(f"\n{BOLD}🧪 Phase 1: Mock Zoho Service Test{RESET}")
    print("=" * 50)
    
    zoho_service = get_zoho_service()
    
    # Test 1: Initialize service
    print_header("Test 1: Service Initialization")
    await zoho_service.initialize()
    
    if zoho_service.is_mock_mode():
        print_success("Service initialized in MOCK mode")
    else:
        print_info("Service initialized in REAL mode")
    
    # Test 2: List all invoices
    print_header("Test 2: List All Invoices")
    result = await zoho_service.list_invoices()
    
    if result.get('success'):
        invoices = result.get('invoices', [])
        print_success(f"Retrieved {len(invoices)} invoice(s)")
        
        for i, invoice in enumerate(invoices, 1):
            print(f"\n  {i}. Invoice #{invoice.get('invoice_number')}")
            print(f"     Customer: {invoice.get('customer_name')}")
            print(f"     Amount: {invoice.get('currency_symbol', '$')}{invoice.get('total', 0):,.2f}")
            print(f"     Status: {invoice.get('status')}")
            print(f"     Due Date: {invoice.get('due_date')}")
    else:
        print_error(f"Failed: {result.get('error')}")
        return False
    
    # Test 3: Filter invoices by status
    print_header("Test 3: Filter Invoices by Status (paid)")
    result = await zoho_service.list_invoices(status='paid')
    
    if result.get('success'):
        paid_invoices = result.get('invoices', [])
        print_success(f"Found {len(paid_invoices)} paid invoice(s)")
        
        for invoice in paid_invoices:
            print(f"  - {invoice.get('invoice_number')}: {invoice.get('customer_name')}")
    else:
        print_error(f"Failed: {result.get('error')}")
        return False
    
    # Test 4: Get specific invoice
    print_header("Test 4: Get Specific Invoice")
    
    if invoices:
        test_invoice_id = invoices[0].get('invoice_id')
        print_info(f"Fetching invoice ID: {test_invoice_id}")
        
        result = await zoho_service.get_invoice(test_invoice_id)
        
        if result.get('success'):
            invoice = result.get('invoice', {})
            print_success("Invoice retrieved successfully")
            print(f"\n  Invoice Number: {invoice.get('invoice_number')}")
            print(f"  Customer: {invoice.get('customer_name')}")
            print(f"  Total: {invoice.get('currency_symbol', '$')}{invoice.get('total', 0):,.2f}")
            print(f"  Balance: {invoice.get('currency_symbol', '$')}{invoice.get('balance', 0):,.2f}")
            print(f"  Status: {invoice.get('status')}")
        else:
            print_error(f"Failed: {result.get('error')}")
            return False
    
    # Test 5: List customers
    print_header("Test 5: List Customers")
    result = await zoho_service.list_customers()
    
    if result.get('success'):
        customers = result.get('contacts', [])
        print_success(f"Retrieved {len(customers)} customer(s)")
        
        for i, customer in enumerate(customers, 1):
            print(f"\n  {i}. {customer.get('contact_name')}")
            print(f"     Email: {customer.get('email')}")
            print(f"     Phone: {customer.get('phone')}")
            print(f"     Status: {customer.get('status')}")
    else:
        print_error(f"Failed: {result.get('error')}")
        return False
    
    # Test 6: Get invoice summary
    print_header("Test 6: Get Invoice Summary")
    result = await zoho_service.get_invoice_summary()
    
    if result.get('success'):
        summary = result.get('summary', {})
        print_success("Summary retrieved successfully")
        print(f"\n  Total Invoices: {summary.get('total_invoices')}")
        print(f"  Total Amount: ${summary.get('total_amount', 0):,.2f}")
        print(f"  Total Outstanding: ${summary.get('total_outstanding', 0):,.2f}")
        print(f"\n  Status Breakdown:")
        for status, count in summary.get('status_breakdown', {}).items():
            print(f"    - {status}: {count}")
    else:
        print_error(f"Failed: {result.get('error')}")
        return False
    
    # Test 7: Error handling (invalid invoice ID)
    print_header("Test 7: Error Handling (Invalid Invoice)")
    result = await zoho_service.get_invoice("INVALID_ID")
    
    if not result.get('success'):
        print_success("Error handling works correctly")
        print_info(f"Error message: {result.get('error')}")
    else:
        print_error("Should have failed with invalid ID")
        return False
    
    return True


async def main():
    """Run Phase 1 tests."""
    print(f"\n{BOLD}{BLUE}{'='*50}{RESET}")
    print(f"{BOLD}{BLUE}Phase 1: Mock Zoho Service Testing{RESET}")
    print(f"{BOLD}{BLUE}{'='*50}{RESET}")
    
    # Check environment
    use_mock = os.getenv('ZOHO_USE_MOCK', 'true').lower() == 'true'
    
    if not use_mock:
        print(f"\n{YELLOW}⚠️  ZOHO_USE_MOCK is set to 'false'{RESET}")
        print(f"{YELLOW}   This test requires mock mode{RESET}")
        print(f"{YELLOW}   Set ZOHO_USE_MOCK=true in .env{RESET}\n")
        return
    
    print(f"\n{GREEN}✓ Running in MOCK mode{RESET}")
    print(f"{GREEN}✓ No OAuth required for this test{RESET}")
    
    try:
        success = await test_phase_1()
        
        if success:
            print(f"\n{BOLD}{GREEN}{'='*50}{RESET}")
            print(f"{BOLD}{GREEN}✅ Phase 1: ALL TESTS PASSED{RESET}")
            print(f"{BOLD}{GREEN}{'='*50}{RESET}")
            
            print(f"\n{BOLD}Next Steps:{RESET}")
            print("  1. ✅ Mock service works correctly")
            print("  2. 🔄 Ready for Phase 2: Zoho Agent Node")
            print("  3. 🔄 Then Phase 3: Frontend Testing")
            
            print(f"\n{BOLD}To proceed to Phase 2:{RESET}")
            print("  Run: python3 backend/test_zoho_agent.py")
        else:
            print(f"\n{BOLD}{RED}{'='*50}{RESET}")
            print(f"{BOLD}{RED}❌ Phase 1: TESTS FAILED{RESET}")
            print(f"{BOLD}{RED}{'='*50}{RESET}")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n{RED}❌ Test failed with error: {e}{RESET}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
