#!/usr/bin/env python3
"""
Bill.com Authorization Diagnosis Test

This test specifically diagnoses the "Forbidden" authorization issues
by examining the actual API responses and error handling.
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

async def diagnose_authorization_issues():
    """Diagnose Bill.com authorization issues by examining raw API responses."""
    print("🔍 Bill.com Authorization Diagnosis")
    print("=" * 60)
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
    
    # Check for environment/URL mismatch
    environment = os.getenv('BILL_COM_ENVIRONMENT', 'stage')
    base_url = os.getenv('BILL_COM_BASE_URL', 'https://gateway.stage.bill.com')
    
    print("🔍 Environment Configuration Analysis:")
    if environment == "sandbox" and "stage" in base_url:
        print("  ⚠️  POTENTIAL MISMATCH: Environment is 'sandbox' but URL contains 'stage'")
        print("     - Sandbox typically uses different endpoints than staging")
        print("     - This could cause permission issues")
    elif environment == "production" and "stage" in base_url:
        print("  ❌ MISMATCH: Environment is 'production' but URL is staging")
        print("     - This will definitely cause permission issues")
    else:
        print("  ✅ Environment and URL appear consistent")
    print()
    
    try:
        # Import Bill.com service
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from src.mcp_server.services.bill_com_service import BillComAPIService
        
        async with BillComAPIService(plan_id="auth-diagnosis") as service:
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
                print("❌ Authentication failed - cannot proceed with authorization tests")
                return False
            
            # Now test raw API responses to see the actual errors
            print("🧪 Testing Raw API Responses...")
            
            endpoints_to_test = [
                ("/v3/invoices", {"max": 1}),
                ("/v3/vendors", {"max": 1}),
                ("/v3/invoices/search", {"invoiceNumber": "TEST"}),
            ]
            
            authorization_issues = []
            
            for endpoint, params in endpoints_to_test:
                print(f"\n  Testing {endpoint}...")
                
                # Make raw API call to see the actual response
                raw_response = await service.make_api_call(endpoint, params=params)
                
                if raw_response is None:
                    print(f"    ❌ No response received")
                    authorization_issues.append(f"{endpoint}: No response")
                elif raw_response.get("error"):
                    error_type = raw_response.get("error_type", "unknown")
                    error_message = raw_response.get("message", "Unknown error")
                    status_code = raw_response.get("status_code", "unknown")
                    
                    print(f"    ❌ Error Response:")
                    print(f"       Status Code: {status_code}")
                    print(f"       Error Type: {error_type}")
                    print(f"       Message: {error_message}")
                    
                    if status_code == 403 or "Forbidden" in str(error_message):
                        authorization_issues.append(f"{endpoint}: 403 Forbidden - {error_message}")
                    else:
                        authorization_issues.append(f"{endpoint}: {status_code} - {error_message}")
                        
                elif "response_data" in raw_response:
                    data = raw_response["response_data"]
                    print(f"    ✅ Success - received {len(data) if isinstance(data, list) else 'data'}")
                else:
                    print(f"    ⚠️  Unexpected response format: {type(raw_response)}")
                    authorization_issues.append(f"{endpoint}: Unexpected response format")
            
            print(f"\n📊 Authorization Analysis:")
            
            if authorization_issues:
                print(f"❌ Found {len(authorization_issues)} authorization issues:")
                for issue in authorization_issues:
                    print(f"   - {issue}")
                
                print(f"\n💡 Diagnosis and Recommendations:")
                
                # Check if all issues are 403 Forbidden
                forbidden_count = sum(1 for issue in authorization_issues if "403 Forbidden" in issue)
                
                if forbidden_count == len(authorization_issues):
                    print(f"🎯 ROOT CAUSE: All endpoints return 403 Forbidden")
                    print(f"   This indicates a systematic authorization problem, not individual endpoint issues.")
                    print()
                    
                    print(f"🔧 Possible Solutions:")
                    print(f"1. **Developer Key Permissions:**")
                    print(f"   - Your developer key may not have the required scopes")
                    print(f"   - Contact Bill.com support to verify key permissions")
                    print(f"   - Request 'read invoices' and 'read vendors' scopes")
                    print()
                    
                    print(f"2. **Environment Configuration:**")
                    if environment == "sandbox" and "stage" in base_url:
                        print(f"   - Try changing BILL_COM_ENVIRONMENT to 'stage' to match the URL")
                        print(f"   - Or change BILL_COM_BASE_URL to sandbox-specific endpoint")
                    print(f"   - Verify you're using the correct environment for your account")
                    print()
                    
                    print(f"3. **Organization Access:**")
                    print(f"   - Verify organization ID {service.session.organization_id} is correct")
                    print(f"   - Check if your user has API access permissions in Bill.com")
                    print(f"   - Ensure your account is active and not suspended")
                    print()
                    
                    print(f"4. **Account Type:**")
                    print(f"   - Some Bill.com account types have limited API access")
                    print(f"   - Verify your account supports API operations")
                    print(f"   - Check if you need to upgrade your Bill.com plan")
                    
                else:
                    print(f"🎯 MIXED ISSUES: Some endpoints work, others don't")
                    print(f"   This suggests partial API access or endpoint-specific restrictions.")
                
                return False
                
            else:
                print(f"✅ No authorization issues detected")
                print(f"   All tested endpoints are accessible")
                return True
                
    except Exception as e:
        print(f"❌ Diagnosis failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main entry point."""
    success = await diagnose_authorization_issues()
    
    if success:
        print(f"\n🎯 Summary: Bill.com authorization is working correctly")
        print(f"   The issue may be with specific data or search parameters")
    else:
        print(f"\n💥 Summary: Bill.com has authorization issues that need to be resolved")
        print(f"   Follow the recommendations above to fix the problems")
    
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