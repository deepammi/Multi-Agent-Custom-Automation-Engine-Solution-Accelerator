#!/usr/bin/env python3
"""
Test Bill.com API directly to debug authentication issues.
"""

import asyncio
import sys
import os
import logging
from pathlib import Path

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src" / "mcp_server"))

from src.mcp_server.services.bill_com_service import BillComAPIService


async def test_bill_com_direct():
    """Test Bill.com API directly."""
    
    print("🔧 Testing Bill.com API Direct Connection")
    print("=" * 50)
    
    try:
        # Create service instance
        async with BillComAPIService() as service:
            print("✅ Service created successfully")
            
            # Test authentication
            print("\n1️⃣ Testing Authentication...")
            auth_result = await service.authenticate()
            
            if auth_result:
                print("✅ Authentication successful!")
                print(f"   Session ID: {service.session.session_id[:8]}...")
                print(f"   User ID: {service.session.user_id}")
                print(f"   Org ID: {service.session.organization_id}")
                
                # Test getting bills
                print("\n2️⃣ Testing Get Bills...")
                bills = await service.get_bills(limit=5)
                print(f"✅ Bills retrieved: {len(bills)} bills")
                
                if bills:
                    print("   Sample bill:")
                    bill = bills[0]
                    print(f"     ID: {bill.get('id')}")
                    print(f"     Number: {bill.get('billNumber')}")
                    print(f"     Vendor: {bill.get('vendorName')}")
                    print(f"     Amount: {bill.get('amount')}")
                else:
                    print("   No bills found (empty sandbox)")
                
                # Test getting vendors
                print("\n3️⃣ Testing Get Vendors...")
                vendors = await service.get_vendors(limit=5)
                print(f"✅ Vendors retrieved: {len(vendors)} vendors")
                
                if vendors:
                    print("   Sample vendor:")
                    vendor = vendors[0]
                    print(f"     ID: {vendor.get('id')}")
                    print(f"     Name: {vendor.get('name')}")
                    print(f"     Email: {vendor.get('email')}")
                else:
                    print("   No vendors found (empty sandbox)")
                
                return True
            else:
                print("❌ Authentication failed")
                return False
                
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Main test function."""
    print("🚀 Starting Bill.com Direct API Test")
    
    # Check environment variables
    required_vars = [
        "BILL_COM_USERNAME",
        "BILL_COM_PASSWORD", 
        "BILL_COM_ORG_ID",
        "BILL_COM_DEV_KEY"
    ]
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {missing_vars}")
        return False
    
    print("✅ All required environment variables present")
    
    # Run the test
    success = await test_bill_com_direct()
    
    if success:
        print("\n🎯 Direct API test PASSED!")
    else:
        print("\n💥 Direct API test FAILED!")
    
    return success


if __name__ == "__main__":
    asyncio.run(main())