"""Test Zoho Invoice integration with real API."""
import asyncio
import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.zoho_mcp_service import get_zoho_service


async def test_real_api():
    """Test Zoho Invoice API with real data."""
    print("=" * 60)
    print("Testing Zoho Invoice Real API Integration")
    print("=" * 60)
    
    service = get_zoho_service()
    await service.initialize()
    
    print(f"\n✓ Service initialized")
    print(f"  - Enabled: {service.is_enabled()}")
    print(f"  - Mock Mode: {service.is_mock_mode()}")
    print(f"  - Organization ID: {service.organization_id}")
    print(f"  - Data Center: {service.data_center}")
    
    # Test 1: List invoices
    print("\n" + "=" * 60)
    print("Test 1: List Invoices")
    print("=" * 60)
    
    result = await service.list_invoices(limit=5)
    
    if result.get("success"):
        invoices = result.get("invoices", [])
        print(f"\n✓ Found {len(invoices)} invoices")
        
        for i, invoice in enumerate(invoices, 1):
            print(f"\n{i}. Invoice: {invoice.get('invoice_number', 'N/A')}")
            print(f"   Customer: {invoice.get('customer_name', 'N/A')}")
            print(f"   Status: {invoice.get('status', 'N/A')}")
            print(f"   Date: {invoice.get('date', 'N/A')}")
            print(f"   Total: ${invoice.get('total', 0):,.2f}")
            print(f"   Balance: ${invoice.get('balance', 0):,.2f}")
    else:
        print(f"\n✗ Failed: {result.get('error')}")
    
    # Test 2: List customers
    print("\n" + "=" * 60)
    print("Test 2: List Customers")
    print("=" * 60)
    
    result = await service.list_customers(limit=5)
    
    if result.get("success"):
        customers = result.get("contacts", [])
        print(f"\n✓ Found {len(customers)} customers")
        
        for i, customer in enumerate(customers, 1):
            print(f"\n{i}. Customer: {customer.get('contact_name', 'N/A')}")
            print(f"   Company: {customer.get('company_name', 'N/A')}")
            print(f"   Email: {customer.get('email', 'N/A')}")
            print(f"   Status: {customer.get('status', 'N/A')}")
    else:
        print(f"\n✗ Failed: {result.get('error')}")
    
    # Test 3: Get invoice summary
    print("\n" + "=" * 60)
    print("Test 3: Invoice Summary")
    print("=" * 60)
    
    result = await service.get_invoice_summary()
    
    if result.get("success"):
        summary = result.get("summary", {})
        print(f"\n✓ Summary retrieved")
        print(f"   Total Invoices: {summary.get('total_invoices', 0)}")
        print(f"   Total Amount: ${summary.get('total_amount', 0):,.2f}")
        print(f"   Total Outstanding: ${summary.get('total_outstanding', 0):,.2f}")
        print(f"\n   Status Breakdown:")
        for status, count in summary.get('status_breakdown', {}).items():
            print(f"     - {status}: {count}")
    else:
        print(f"\n✗ Failed: {result.get('error')}")
    
    print("\n" + "=" * 60)
    print("Testing Complete")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_real_api())
