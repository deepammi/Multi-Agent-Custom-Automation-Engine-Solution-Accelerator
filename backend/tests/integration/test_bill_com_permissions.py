#!/usr/bin/env python3
"""
Bill.com Permissions Test

This test checks Bill.com API permissions and suggests solutions
for the "Forbidden" error when accessing invoices.
"""

import asyncio
import os
import sys
from datetime import datetime, timezone
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Force SSL bypass
os.environ["BILL_COM_SSL_VERIFY"] = "false"

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_bill_com_permissions():
    """Test Bill.com API permissions and diagnose issues."""
    print("🔐 Bill.com Permissions Test")
    print("=" * 50)
    print(f"🕒 Start Time: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC")
    print()
    
    # Show current configuration
    print("📋 Current Configuration:")
    print(f"  Username: {os.getenv('BILL_COM_USERNAME', 'Not set')}")
    print(f"  Organization ID: {os.getenv('BILL_COM_ORG_ID', 'Not set')}")
    print(f"  Environment: {os.getenv('BILL_COM_ENVIRONMENT', 'Not set')}")
    print(f"  Base URL: {os.getenv('BILL_COM_BASE_URL', 'https://gateway.stage.bill.com')}")
    print(f"  SSL Verify: {os.getenv('BILL_COM_SSL_VERIFY', 'true')}")
    print()
    
    try:
        # Import Bill.com service
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from src.mcp_server.services.bill_com_service import BillComAPIService
        
        async with BillComAPIService(plan_id="permissions-test") as service:
            print("✅ Connected to Bill.com service")
            print(f"   SSL verification disabled: {not service.config.ssl_verify}")
            print()
            
            # Test authentication
            print("🔐 Testing Authentication...")
            auth_success = await service.authenticate()
            
            if auth_success:
                print("✅ Authentication successful")
                print(f"   Session ID: {service.session.session_id[:8]}...")
                print(f"   Organization ID: {service.session.organization_id}")
                print(f"   User ID: {service.session.user_id}")
                print()
            else:
                print("❌ Authentication failed")
                return False
            
            # Test different API endpoints to check permissions
            print("🧪 Testing API Endpoint Permissions...")
            
            endpoints_to_test = [
                ("GET /v3/invoices", lambda: service.get_invoices(limit=1)),
                ("GET /v3/vendors", lambda: service.get_vendors(limit=1)),
                ("POST /v3/invoices/search", lambda: service.search_invoices_by_number("TEST")),
            ]
            
            permissions_summary = {}
            
            for endpoint_name, test_func in endpoints_to_test:
                print(f"  Testing {endpoint_name}...")
                
                try:
                    result = await test_func()
                    
                    if isinstance(result, list):
                        print(f"    ✅ Success - returned {len(result)} items")
                        permissions_summary[endpoint_name] = "allowed"
                    else:
                        print(f"    ⚠️  Unexpected result type: {type(result)}")
                        permissions_summary[endpoint_name] = "unknown"
                        
                except Exception as e:
                    error_msg = str(e)
                    if "Forbidden" in error_msg:
                        print(f"    ❌ Forbidden - insufficient permissions")
                        permissions_summary[endpoint_name] = "forbidden"
                    elif "Unauthorized" in error_msg:
                        print(f"    ❌ Unauthorized - authentication issue")
                        permissions_summary[endpoint_name] = "unauthorized"
                    else:
                        print(f"    ❌ Error: {error_msg}")
                        permissions_summary[endpoint_name] = "error"
            
            print()
            
            # Analyze results and provide recommendations
            print("📊 Permissions Analysis:")
            
            forbidden_count = sum(1 for status in permissions_summary.values() if status == "forbidden")
            allowed_count = sum(1 for status in permissions_summary.values() if status == "allowed")
            
            if forbidden_count > 0:
                print(f"❌ {forbidden_count} endpoints are forbidden")
                print(f"✅ {allowed_count} endpoints are accessible")
                print()
                
                print("💡 Possible Solutions:")
                print()
                
                print("1. **Check Bill.com Account Permissions:**")
                print("   - Log into Bill.com web interface with the same credentials")
                print("   - Verify you can see invoices and vendors in the web UI")
                print("   - Check if your user role has API access permissions")
                print()
                
                print("2. **Verify Environment Configuration:**")
                print("   - Current environment: sandbox")
                print("   - Sandbox environments may have limited data")
                print("   - Consider switching to production environment if you have access")
                print()
                
                print("3. **Check Developer Key Permissions:**")
                print("   - Verify the developer key is active and not expired")
                print("   - Check if the developer key has the required scopes:")
                print("     * Read invoices")
                print("     * Read vendors")
                print("     * Search functionality")
                print()
                
                print("4. **Organization ID Verification:**")
                print(f"   - Current Org ID: {service.session.organization_id}")
                print("   - Verify this matches your Bill.com organization")
                print("   - Check if you have access to this specific organization")
                print()
                
                print("5. **API Endpoint URLs:**")
                print(f"   - Current base URL: {service.config.base_url}")
                print("   - Sandbox URL: https://gateway.stage.bill.com")
                print("   - Production URL: https://gateway.bill.com")
                print("   - Verify the URL matches your environment")
                print()
                
                print("6. **Test with Bill.com Support:**")
                print("   - Contact Bill.com API support if permissions issues persist")
                print("   - Provide your developer key and organization ID")
                print("   - Ask them to verify API access permissions")
                
            elif allowed_count == len(endpoints_to_test):
                print("✅ All endpoints are accessible")
                print("🎯 The issue might be with specific invoice data or search parameters")
                
                print("\n💡 Next Steps for Invoice Search:")
                print("1. Check if INV-1001 exists in the Bill.com web interface")
                print("2. Verify the exact invoice number format")
                print("3. Check if there are date range filters affecting results")
                print("4. Try searching for other known invoice numbers")
                
            else:
                print("⚠️  Mixed permissions - some endpoints work, others don't")
                print("   This suggests partial API access")
            
            return allowed_count > 0
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main entry point."""
    success = await test_bill_com_permissions()
    
    if success:
        print(f"\n🎯 Summary: Bill.com connection is working but may have permission limitations")
    else:
        print(f"\n💥 Summary: Bill.com connection has significant issues")
    
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