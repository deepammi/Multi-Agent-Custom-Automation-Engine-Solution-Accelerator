#!/usr/bin/env python3
"""
Invoice Search Diagnosis Test

This test diagnoses why INV-1001 is not being found in Bill.com
by testing different search strategies and examining all available invoices.
"""

import asyncio
import os
import sys
import subprocess
import signal
import json
from datetime import datetime, timezone
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Force SSL bypass
os.environ["BILL_COM_SSL_VERIFY"] = "false"

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

class InvoiceSearchDiagnosis:
    """Diagnose invoice search issues."""
    
    def __init__(self):
        self.mcp_server_process = None
        
    async def start_mcp_server(self) -> bool:
        """Start MCP server."""
        print("🔄 Starting MCP server...")
        
        try:
            from pathlib import Path
            
            # Kill existing processes
            try:
                subprocess.run(["pkill", "-f", "mcp_server.py"], check=False)
                await asyncio.sleep(2)
            except:
                pass
            
            # Start server
            project_root = os.path.dirname(os.getcwd())
            script_path = Path(project_root) / "src/mcp_server/mcp_server.py"
            
            if not script_path.exists():
                print(f"❌ MCP server script not found: {script_path}")
                return False
            
            env = os.environ.copy()
            env["BILL_COM_MCP_ENABLED"] = "true"
            env["BILL_COM_SSL_VERIFY"] = "false"
            
            cmd = ["python3", str(script_path), "--transport", "http", "--port", "9000"]
            
            self.mcp_server_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=project_root,
                env=env
            )
            
            # Wait for initialization
            for i in range(10):
                await asyncio.sleep(1)
                if self.mcp_server_process.poll() is not None:
                    stdout, stderr = self.mcp_server_process.communicate()
                    print(f"❌ Server failed: {stderr}")
                    return False
            
            print("✅ MCP server started")
            return True
            
        except Exception as e:
            print(f"❌ Failed to start server: {e}")
            return False
    
    async def stop_mcp_server(self):
        """Stop MCP server."""
        if self.mcp_server_process:
            try:
                self.mcp_server_process.terminate()
                self.mcp_server_process.wait(timeout=5)
            except:
                self.mcp_server_process.kill()
                self.mcp_server_process.wait()
            self.mcp_server_process = None
    
    async def get_bill_com_service(self):
        """Get Bill.com service instance."""
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from src.mcp_server.services.bill_com_service import BillComAPIService
        
        return BillComAPIService(plan_id="diagnosis-test", agent="diagnosis")
    
    async def diagnose_invoice_search(self):
        """Comprehensive diagnosis of invoice search."""
        print("\n🔍 Invoice Search Diagnosis")
        print("=" * 50)
        
        try:
            async with await self.get_bill_com_service() as service:
                print("✅ Connected to Bill.com service")
                
                # Test 1: Get all invoices to see what's available
                print("\n📋 Test 1: Retrieving all invoices...")
                all_invoices = await service.get_invoices(limit=100)
                
                print(f"Found {len(all_invoices)} total invoices")
                
                if all_invoices:
                    print("\n📄 Invoice Details:")
                    for i, invoice in enumerate(all_invoices[:10], 1):  # Show first 10
                        invoice_number = invoice.get('invoiceNumber', 'N/A')
                        vendor_name = invoice.get('vendorName', 'N/A')
                        amount = invoice.get('amount', 0)
                        status = invoice.get('approvalStatus', 'N/A')
                        
                        print(f"  {i}. {invoice_number} | {vendor_name} | ${amount} | {status}")
                        
                        # Check if this invoice contains INV-1001
                        if 'INV-1001' in invoice_number or 'inv-1001' in invoice_number.lower():
                            print(f"     🎯 FOUND INV-1001 MATCH: {invoice_number}")
                    
                    # Search for any invoice containing "1001"
                    print(f"\n🔍 Searching for invoices containing '1001':")
                    matches = []
                    for invoice in all_invoices:
                        invoice_number = invoice.get('invoiceNumber', '')
                        if '1001' in invoice_number:
                            matches.append(invoice)
                            print(f"  ✅ Match: {invoice_number}")
                    
                    if not matches:
                        print("  ❌ No invoices found containing '1001'")
                        
                        # Show all invoice numbers for reference
                        print(f"\n📝 All invoice numbers in system:")
                        for invoice in all_invoices:
                            print(f"  - {invoice.get('invoiceNumber', 'N/A')}")
                else:
                    print("❌ No invoices found in the system")
                
                # Test 2: Try exact search for INV-1001
                print(f"\n🔍 Test 2: Exact search for 'INV-1001'...")
                exact_results = await service.search_invoices_by_number("INV-1001")
                print(f"Exact search results: {len(exact_results)} invoices")
                
                for invoice in exact_results:
                    print(f"  - {invoice.get('invoiceNumber', 'N/A')}")
                
                # Test 3: Try different variations
                print(f"\n🔍 Test 3: Testing search variations...")
                variations = ["INV-1001", "inv-1001", "1001", "INV1001"]
                
                for variation in variations:
                    print(f"  Testing '{variation}'...")
                    results = await service.search_invoices_by_number(variation)
                    print(f"    Results: {len(results)} invoices")
                    
                    for invoice in results:
                        print(f"      - {invoice.get('invoiceNumber', 'N/A')}")
                
                # Test 4: Check if there are any authentication or permission issues
                print(f"\n🔐 Test 4: Authentication and permissions check...")
                
                # Try to get vendors to test API access
                vendors = await service.get_vendors(limit=5)
                print(f"Vendors accessible: {len(vendors)}")
                
                if vendors:
                    print("✅ API access is working")
                else:
                    print("⚠️  Limited API access - may affect invoice search")
                
                return len(all_invoices) > 0
                
        except Exception as e:
            print(f"❌ Diagnosis failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    async def test_mcp_search_tools(self):
        """Test MCP search tools directly."""
        print("\n🛠️  Testing MCP Search Tools")
        print("=" * 50)
        
        try:
            from fastmcp import Client
            
            client = Client("http://localhost:9000/mcp")
            
            async with client:
                print("✅ Connected to MCP server")
                
                # Test search tool
                print("\n🔍 Testing search_bill_com_invoices tool...")
                
                search_result = await client.call_tool(
                    "search_bill_com_invoices",
                    {"query": "INV-1001", "search_type": "invoice_number"}
                )
                
                print("Search result:")
                print(search_result.content[0].text if search_result.content else "No content")
                
                # Test get invoices tool
                print("\n📋 Testing get_bill_com_invoices tool...")
                
                get_result = await client.call_tool(
                    "get_bill_com_invoices",
                    {"limit": 20}
                )
                
                print("Get invoices result:")
                print(get_result.content[0].text if get_result.content else "No content")
                
        except Exception as e:
            print(f"❌ MCP tool test failed: {e}")
            import traceback
            traceback.print_exc()
    
    async def run_diagnosis(self):
        """Run complete diagnosis."""
        print("🚀 Invoice Search Diagnosis")
        print("=" * 50)
        print(f"🕒 Start Time: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC")
        print(f"🔒 SSL Bypass: {os.getenv('BILL_COM_SSL_VERIFY')}")
        print()
        
        try:
            # Start MCP server
            if not await self.start_mcp_server():
                print("💥 Cannot continue - MCP server failed")
                return False
            
            await asyncio.sleep(3)  # Let server initialize
            
            # Run diagnosis
            service_success = await self.diagnose_invoice_search()
            await self.test_mcp_search_tools()
            
            print(f"\n📊 Diagnosis Summary:")
            print(f"✅ Service connection: {'Working' if service_success else 'Failed'}")
            
            if service_success:
                print(f"\n💡 Recommendations:")
                print(f"1. Check if INV-1001 exists with exact case matching")
                print(f"2. Verify the invoice number format in Bill.com")
                print(f"3. Consider implementing fuzzy search for partial matches")
                print(f"4. Check if there are date range or status filters affecting results")
            
            return service_success
            
        finally:
            await self.stop_mcp_server()

async def main():
    """Main entry point."""
    diagnosis = InvoiceSearchDiagnosis()
    success = await diagnosis.run_diagnosis()
    return 0 if success else 1

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n⚠️ Interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)