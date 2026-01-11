"""Interactive workflow testing - Try different parameters."""
import asyncio
import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.agents.workflows.factory import WorkflowFactory


def print_menu():
    """Print workflow selection menu."""
    print("\n" + "=" * 60)
    print("🔧 Interactive Workflow Testing")
    print("=" * 60)
    print("\nAvailable Workflows:")
    print("1. Invoice Verification (ERP + CRM)")
    print("2. Payment Tracking (ERP + Email)")
    print("3. Customer 360 View (Multi-system)")
    print("4. List All Workflows")
    print("5. Exit")
    print("=" * 60)


async def test_invoice_verification():
    """Test invoice verification with custom parameters."""
    print("\n📋 Invoice Verification Workflow")
    print("-" * 60)
    
    # Show available invoices
    print("\nAvailable invoices in Zoho:")
    print("- INV-000001 (Test1Customer Co.)")
    print("- INV-000002 (University of Chicago)")
    
    invoice_id = input("\nEnter invoice ID (or press Enter for INV-000001): ").strip()
    if not invoice_id:
        invoice_id = "INV-000001"
    
    print(f"\n🔄 Running verification for {invoice_id}...")
    
    result = await WorkflowFactory.execute_workflow(
        workflow_name="invoice_verification",
        plan_id=f"test-{invoice_id}",
        session_id="interactive-session",
        parameters={
            "invoice_id": invoice_id,
            "erp_system": "zoho",
            "crm_system": "salesforce"
        }
    )
    
    print(f"\n✅ Status: {result.get('status')}")
    print("\n" + "=" * 60)
    print("VERIFICATION REPORT")
    print("=" * 60)
    print(result.get('final_result', 'No result'))
    print("=" * 60)


async def test_payment_tracking():
    """Test payment tracking with custom parameters."""
    print("\n💰 Payment Tracking Workflow")
    print("-" * 60)
    
    print("\nAvailable invoices:")
    print("- INV-000001 (Test1Customer Co.)")
    print("- INV-000002 (University of Chicago)")
    
    invoice_id = input("\nEnter invoice ID (or press Enter for INV-000002): ").strip()
    if not invoice_id:
        invoice_id = "INV-000002"
    
    print(f"\n🔄 Tracking payment for {invoice_id}...")
    
    result = await WorkflowFactory.execute_workflow(
        workflow_name="payment_tracking",
        plan_id=f"track-{invoice_id}",
        session_id="interactive-session",
        parameters={
            "invoice_id": invoice_id,
            "erp_system": "zoho"
        }
    )
    
    print(f"\n✅ Status: {result.get('status')}")
    print("\n" + "=" * 60)
    print("PAYMENT TRACKING REPORT")
    print("=" * 60)
    print(result.get('final_result', 'No result'))
    print("=" * 60)


async def test_customer_360():
    """Test customer 360 with custom parameters."""
    print("\n👥 Customer 360 View Workflow")
    print("-" * 60)
    
    print("\nAvailable customers:")
    print("- Test1Customer Co.")
    print("- University of Chicago")
    print("- Test2 Customer Co")
    
    customer_name = input("\nEnter customer name (or press Enter for 'University of Chicago'): ").strip()
    if not customer_name:
        customer_name = "University of Chicago"
    
    print(f"\n🔄 Generating 360 view for {customer_name}...")
    
    result = await WorkflowFactory.execute_workflow(
        workflow_name="customer_360",
        plan_id=f"360-{customer_name.replace(' ', '-')}",
        session_id="interactive-session",
        parameters={
            "customer_name": customer_name
        }
    )
    
    print(f"\n✅ Status: {result.get('status')}")
    print("\n" + "=" * 60)
    print("CUSTOMER 360 REPORT")
    print("=" * 60)
    print(result.get('final_result', 'No result'))
    print("=" * 60)


async def list_workflows():
    """List all available workflows."""
    print("\n📚 Available Workflows")
    print("=" * 60)
    
    workflows = WorkflowFactory.list_workflows()
    
    for i, wf in enumerate(workflows, 1):
        print(f"\n{i}. {wf['title']}")
        print(f"   Name: {wf['name']}")
        print(f"   Description: {wf['description']}")
        print(f"   Systems: {', '.join(wf['systems'])}")
        print(f"   Parameters: {', '.join(wf['parameters'])}")
    
    print("\n" + "=" * 60)


async def main():
    """Main interactive loop."""
    print("\n🎉 Welcome to Workflow Testing!")
    print("Test the 3 customer-facing workflows with real data")
    
    while True:
        print_menu()
        choice = input("\nSelect option (1-5): ").strip()
        
        try:
            if choice == "1":
                await test_invoice_verification()
            elif choice == "2":
                await test_payment_tracking()
            elif choice == "3":
                await test_customer_360()
            elif choice == "4":
                await list_workflows()
            elif choice == "5":
                print("\n👋 Thanks for testing! Goodbye.")
                break
            else:
                print("\n❌ Invalid choice. Please select 1-5.")
        except KeyboardInterrupt:
            print("\n\n👋 Interrupted. Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
        
        input("\nPress Enter to continue...")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
