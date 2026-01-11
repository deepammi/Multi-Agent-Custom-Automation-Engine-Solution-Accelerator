#!/usr/bin/env python3
"""
Fixed Bill.com Curl vs Python Comparison

This test fixes the configuration issues and properly compares
curl vs Python requests.
"""

import asyncio
import os
import sys
import json
import subprocess
from datetime import datetime, timezone
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Force SSL bypass
os.environ["BILL_COM_SSL_VERIFY"] = "false"

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def fix_base_url():
    """Fix the base URL if it includes the login endpoint."""
    base_url = os.getenv('BILL_COM_BASE_URL', 'https://gateway.stage.bill.com/connect')
    
    # Remove any endpoint paths from base URL
    if '/v3/login' in base_url:
        base_url = base_url.replace('/v3/login', '')
        print(f"🔧 Fixed base URL: {base_url}")
    
    return base_url

async def test_curl_authentication():
    """Test authentication using curl with correct URL construction."""
    print("🌐 Testing authentication with curl")
    print("-" * 50)
    
    # Get credentials from environment
    username = os.getenv('BILL_COM_USERNAME')
    password = os.getenv('BILL_COM_PASSWORD')
    org_id = os.getenv('BILL_COM_ORG_ID')
    dev_key = os.getenv('BILL_COM_DEV_KEY')
    base_url = fix_base_url()
    
    print(f"Using credentials:")
    print(f"   Username: {username}")
    print(f"   Org ID: {org_id}")
    print(f"   Dev Key: {dev_key[:8]}...{dev_key[-4:] if len(dev_key) > 12 else dev_key}")
    print(f"   Base URL: {base_url}")
    
    if not all([username, password, org_id, dev_key]):
        print("❌ Missing credentials in environment variables")
        return None
    
    # Prepare curl command for authentication
    login_url = f"{base_url}/v3/login"
    login_data = {
        "username": username,
        "password": password,
        "organizationId": org_id,
        "devKey": dev_key
    }
    
    curl_cmd = [
        "curl", "-X", "POST",
        "-H", "Content-Type: application/json",
        "-H", "Accept: application/json",
        "-k",  # Skip SSL verification
        "-d", json.dumps(login_data),
        login_url
    ]
    
    try:
        print(f"Curl login URL: {login_url}")
        
        result = subprocess.run(
            curl_cmd,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        print(f"Curl exit code: {result.returncode}")
        print(f"Curl stdout: {result.stdout[:200]}...")
        if result.stderr:
            print(f"Curl stderr: {result.stderr}")
        
        if result.returncode == 0:
            try:
                response_data = json.loads(result.stdout)
                
                if "sessionId" in response_data:
                    print("✅ Curl authentication successful")
                    print(f"   Session ID: {response_data['sessionId'][:8]}...")
                    print(f"   Organization ID: {response_data.get('organizationId', 'N/A')}")
                    print(f"   User ID: {response_data.get('userId', 'N/A')}")
                    return response_data['sessionId']
                else:
                    print(f"❌ Curl authentication failed: {response_data}")
                    return None
                    
            except json.JSONDecodeError as e:
                print(f"❌ Curl response not valid JSON: {e}")
                print(f"Raw response: {result.stdout}")
                return None
        else:
            print(f"❌ Curl failed with exit code {result.returncode}")
            return None
            
    except subprocess.TimeoutExpired:
        print("❌ Curl request timed out")
        return None
    except Exception as e:
        print(f"❌ Curl error: {e}")
        return None

async def test_python_authentication():
    """Test authentication using Python with fixed configuration."""
    print("\n🐍 Testing authentication with Python")
    print("-" * 50)
    
    # Temporarily fix the base URL in environment
    base_url = fix_base_url()
    original_base_url = os.getenv('BILL_COM_BASE_URL')
    os.environ['BILL_COM_BASE_URL'] = base_url
    
    try:
        # Import Bill.com service (need to reimport to pick up fixed URL)
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        # Force reload of the service module
        import importlib
        if 'src.mcp_server.services.bill_com_service' in sys.modules:
            importlib.reload(sys.modules['src.mcp_server.services.bill_com_service'])
        
        from src.mcp_server.services.bill_com_service import BillComAPIService
        
        async with BillComAPIService(plan_id="fixed-comparison-test") as service:
            print(f"Python config:")
            print(f"   Base URL: {service.config.base_url}")
            print(f"   Username: {service.config.username}")
            print(f"   Organization ID: {service.config.organization_id}")
            print(f"   Dev Key: {service.config.dev_key[:8]}...{service.config.dev_key[-4:] if len(service.config.dev_key) > 12 else service.config.dev_key}")
            print(f"   SSL Verify: {service.config.ssl_verify}")
            
            # Test authentication
            auth_success = await service.authenticate()
            
            if auth_success:
                print("✅ Python authentication successful")
                print(f"   Session ID: {service.session.session_id[:8]}...")
                print(f"   Organization ID: {service.session.organization_id}")
                print(f"   User ID: {service.session.user_id}")
                return service.session.session_id
            else:
                print("❌ Python authentication failed")
                return None
                
    except Exception as e:
        print(f"❌ Python error: {e}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        # Restore original base URL
        if original_base_url:
            os.environ['BILL_COM_BASE_URL'] = original_base_url

async def test_curl_data_access(session_id):
    """Test data access using curl with the session ID."""
    print(f"\n🌐 Testing data access with curl")
    print("-" * 50)
    
    base_url = fix_base_url()
    dev_key = os.getenv('BILL_COM_DEV_KEY')
    
    # Test bills endpoint using headers (like your working command)
    bills_url = f"{base_url}/v3/bills?max=1"
    
    curl_cmd = [
        "curl", "--request", "GET",
        bills_url,
        "--header", f"devKey: {dev_key}",
        "--header", f"sessionId: {session_id}",
        "--header", "Accept: application/json",
        "-k"  # Skip SSL verification
    ]
    
    try:
        print(f"Testing: {bills_url}")
        print(f"Headers: devKey: {dev_key[:8]}..., sessionId: {session_id[:8]}...")
        
        result = subprocess.run(
            curl_cmd,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        print(f"Curl exit code: {result.returncode}")
        print(f"Curl stdout: {result.stdout[:200]}...")
        
        if result.returncode == 0:
            try:
                response_data = json.loads(result.stdout)
                
                if "results" in response_data:
                    bills = response_data["results"]
                    print(f"✅ Curl data access successful - {len(bills)} bills")
                    if bills:
                        # Bill.com uses different field names
                        bill_number = bills[0].get('invoice', {}).get('invoiceNumber', 'N/A')
                        vendor_name = bills[0].get('vendorName', 'N/A')
                        amount = bills[0].get('amount', 0)
                        print(f"   First bill: {bill_number} from {vendor_name} (${amount})")
                    return True
                elif "response_data" in response_data:
                    bills = response_data["response_data"]
                    print(f"✅ Curl data access successful - {len(bills)} bills")
                    if bills:
                        print(f"   First bill: {bills[0].get('billNumber', 'N/A')}")
                    return True
                elif "message" in response_data and "Forbidden" in str(response_data["message"]):
                    print(f"❌ Curl data access forbidden: {response_data}")
                    return False
                elif "message" in response_data and "Unauthorized" in str(response_data["message"]):
                    print(f"❌ Curl data access unauthorized: {response_data}")
                    return False
                else:
                    print(f"⚠️  Curl unexpected response: {response_data}")
                    return False
                    
            except json.JSONDecodeError as e:
                print(f"❌ Curl response not valid JSON: {e}")
                print(f"Raw response: {result.stdout}")
                return False
        else:
            print(f"❌ Curl failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Curl error: {e}")
        return False

async def test_python_data_access():
    """Test data access using Python with fixed configuration."""
    print(f"\n🐍 Testing data access with Python")
    print("-" * 50)
    
    # Temporarily fix the base URL in environment
    base_url = fix_base_url()
    original_base_url = os.getenv('BILL_COM_BASE_URL')
    os.environ['BILL_COM_BASE_URL'] = base_url
    
    try:
        # Import Bill.com service
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        # Force reload of the service module
        import importlib
        if 'src.mcp_server.services.bill_com_service' in sys.modules:
            importlib.reload(sys.modules['src.mcp_server.services.bill_com_service'])
        
        from src.mcp_server.services.bill_com_service import BillComAPIService
        
        async with BillComAPIService(plan_id="fixed-comparison-test") as service:
            # Authenticate first
            auth_success = await service.authenticate()
            
            if not auth_success:
                print("❌ Python authentication failed")
                return False
            
            # Test data access (changed from invoices to bills)
            print(f"Testing: GET /v3/bills")
            
            response = await service.make_api_call("/v3/bills", params={"max": 1})
            
            if response is None:
                print("❌ Python no response received")
                return False
            elif response.get("error"):
                error_message = response.get("message", "Unknown error")
                status_code = response.get("status_code", "unknown")
                print(f"❌ Python data access error: {status_code} - {error_message}")
                return False
            elif "response_data" in response:
                data = response["response_data"]
                print(f"✅ Python data access successful - {len(data)} bills")
                if data:
                    print(f"   First bill: {data[0].get('billNumber', 'N/A')}")
                return True
            elif "results" in response:
                data = response["results"]
                print(f"✅ Python data access successful - {len(data)} bills")
                if data:
                    # Bill.com uses different field names
                    bill_number = data[0].get('invoice', {}).get('invoiceNumber', 'N/A')
                    vendor_name = data[0].get('vendorName', 'N/A')
                    amount = data[0].get('amount', 0)
                    print(f"   First bill: {bill_number} from {vendor_name} (${amount})")
                return True
            else:
                print(f"⚠️  Python unexpected response format: {type(response)}")
                print(f"   Response keys: {list(response.keys()) if isinstance(response, dict) else 'Not a dict'}")
                return False
                
    except Exception as e:
        print(f"❌ Python error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Restore original base URL
        if original_base_url:
            os.environ['BILL_COM_BASE_URL'] = original_base_url

async def main():
    """Main entry point."""
    print("🔍 Fixed Bill.com Curl vs Python Comparison")
    print("=" * 60)
    print(f"🕒 Start Time: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC")
    print()
    
    # Test authentication with both methods
    curl_session = await test_curl_authentication()
    python_session = await test_python_authentication()
    
    print(f"\n📊 Authentication Results:")
    print(f"   Curl:   {'✅ Success' if curl_session else '❌ Failed'}")
    print(f"   Python: {'✅ Success' if python_session else '❌ Failed'}")
    
    if curl_session and python_session:
        print(f"   Sessions match: {'✅ Yes' if curl_session == python_session else '❌ No'}")
    
    # Test data access if authentication succeeded
    curl_data_success = False
    python_data_success = False
    
    if curl_session:
        curl_data_success = await test_curl_data_access(curl_session)
    
    if python_session:
        python_data_success = await test_python_data_access()
    
    print(f"\n📊 Data Access Results:")
    print(f"   Curl:   {'✅ Success' if curl_data_success else '❌ Failed'}")
    print(f"   Python: {'✅ Success' if python_data_success else '❌ Failed'}")
    
    # Final analysis
    print(f"\n🎯 Final Analysis:")
    
    if curl_data_success and python_data_success:
        print("🎉 SUCCESS: Both curl and Python can access Bill.com data!")
        print("   The issue was the incorrect base URL configuration.")
        print("   Update your .env file to fix BILL_COM_BASE_URL")
        return True
    elif curl_data_success and not python_data_success:
        print("⚠️  PARTIAL SUCCESS: Curl works but Python fails")
        print("   There may be additional differences in the Python implementation")
        return False
    elif not curl_data_success and not python_data_success:
        print("❌ BOTH FAILED: The issue is with Bill.com permissions")
        print("   Contact Bill.com support for API access permissions")
        return False
    else:
        print("⚠️  UNEXPECTED: Python works but curl fails")
        return True

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