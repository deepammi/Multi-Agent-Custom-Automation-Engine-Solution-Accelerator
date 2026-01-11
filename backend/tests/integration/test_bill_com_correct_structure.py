#!/usr/bin/env python3
"""
Test Bill.com API fixes - Verify authentication and data fetching.

This script tests:
1. Correct authentication with credentials in request body
2. Correct API call structure with sessionId in body
3. Actual data fetching from sandbox account
"""

import asyncio
import sys
import os
from pathlib import Path

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "mcp_server"))

from services.bill_com_service import BillComAPIService, BillComConfig
import logging

# Setup detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_billcom_authentication():
    """Test 1: Authentication with correct request structure."""
    print("\n" + "="*70)
    print("TEST 1: Bill.com Authentication")
    print("="*70)
    
    config = BillComConfig.from_env()
    print(f"\n📋 Configuration:")
    print(f"   Base URL: {config.base_url}")
    print(f"   Environment: {config.environment}")
    print(f"   Org ID: {config.organization_id}")
    print(f"   Username: {config.username}")
    print(f"   Has Dev Key: {'Yes' if config.dev_key else 'No'}")
    
    if not config.validate():
        print(f"\n❌ Configuration invalid - check environment variables")
        return False
    
    async with BillComAPIService() as service:
        success = await service.authenticate()
        
        if success:
            print(f"\n✅ Authentication successful!")
            print(f"   Session ID: {service.session.session_id[:16]}...")
            print(f"   User ID: {service.session.user_id}")
            print(f"   Org ID: {service.session.organization_id}")
            return True
        else:
            print(f"\n❌ Authentication failed")
            return False


async def test_billcom_get_bills():
    """Test 2: Get bills with correct API structure."""
    print("\n" + "="*70)
    print("TEST 2: Get Bills from Bill.com")
    print("="*70)
    
    async with BillComAPIService() as service:
        # Authenticate first
        if not await service.authenticate():
            print(f"❌ Authentication failed - cannot proceed")
            return False
        
        print(f"\n📋 Fetching bills...")
        
        # Try to get bills with different limits
        for limit in [5, 10, 20]:
            print(f"\n🔍 Attempting to fetch {limit} bills...")
            bills = await service.get_bills(limit=limit)
            
            if bills:
                print(f"✅ Retrieved {len(bills)} bills")
                
                # Show first bill details
                if len(bills) > 0:
                    first_bill = bills[0]
                    print(f"\n📄 Sample Bill:")
                    print(f"   ID: {first_bill.get('id', 'N/A')}")
                    print(f"   Invoice Number: {first_bill.get('invoiceNumber', 'N/A')}")
                    print(f"   Vendor: {first_bill.get('vendorName', 'N/A')}")
                    print(f"   Amount: ${first_bill.get('amount', 0):.2f}")
                    print(f"   Status: {first_bill.get('status', 'N/A')}")
                    print(f"   Date: {first_bill.get('invoiceDate', 'N/A')}")
                    
                    # Show all available fields
                    print(f"\n🔧 Available fields in bill object:")
                    for key in sorted(first_bill.keys()):
                        value = first_bill[key]
                        if isinstance(value, str) and len(value) > 50:
                            print(f"      {key}: {value[:50]}...")
                        else:
                            print(f"      {key}: {value}")
                
                return True
            else:
                print(f"⚠️  No bills returned (limit={limit})")
        
        print(f"\n❌ Could not retrieve any bills")
        print(f"   This could mean:")
        print(f"   1. Your sandbox account has no bills")
        print(f"   2. API permissions are insufficient")
        print(f"   3. API endpoint/structure is still incorrect")
        return False


async def test_billcom_get_vendors():
    """Test 3: Get vendors to verify API is working."""
    print("\n" + "="*70)
    print("TEST 3: Get Vendors from Bill.com")
    print("="*70)
    
    async with BillComAPIService() as service:
        if not await service.authenticate():
            print(f"❌ Authentication failed")
            return False
        
        print(f"\n👥 Fetching vendors...")
        vendors = await service.get_vendors(limit=10)
        
        if vendors:
            print(f"✅ Retrieved {len(vendors)} vendors")
            
            for i, vendor in enumerate(vendors[:3], 1):
                print(f"\n📇 Vendor {i}:")
                print(f"   ID: {vendor.get('id', 'N/A')}")
                print(f"   Name: {vendor.get('name', 'N/A')}")
                print(f"   Email: {vendor.get('email', 'N/A')}")
                print(f"   Status: {'Active' if vendor.get('isActive') else 'Inactive'}")
            
            if len(vendors) > 3:
                print(f"\n   ... and {len(vendors) - 3} more vendors")
            
            return True
        else:
            print(f"⚠️  No vendors found")
            return False


async def test_billcom_search():
    """Test 4: Search functionality."""
    print("\n" + "="*70)
    print("TEST 4: Search Bills by Invoice Number")
    print("="*70)
    
    async with BillComAPIService() as service:
        if not await service.authenticate():
            print(f"❌ Authentication failed")
            return False
        
        # First get some bills to know what to search for
        print(f"\n📋 Getting sample bills first...")
        bills = await service.get_bills(limit=5)
        
        if not bills:
            print(f"⚠️  No bills to search - skipping test")
            return False
        
        # Try searching for the first bill's invoice number
        sample_invoice_number = bills[0].get('invoiceNumber', '')
        if not sample_invoice_number:
            print(f"⚠️  Sample bill has no invoice number - skipping test")
            return False
        
        print(f"\n🔍 Searching for invoice number: {sample_invoice_number}")
        results = await service.search_bills_by_number(sample_invoice_number)
        
        if results:
            print(f"✅ Search found {len(results)} matching bills")
            for result in results:
                print(f"   - Invoice: {result.get('invoiceNumber')} | Amount: ${result.get('amount', 0):.2f}")
            return True
        else:
            print(f"❌ Search returned no results")
            return False


async def test_billcom_raw_api_response():
    """Test 5: Show raw API response for debugging."""
    print("\n" + "="*70)
    print("TEST 5: Raw API Response Analysis")
    print("="*70)
    
    async with BillComAPIService() as service:
        if not await service.authenticate():
            print(f"❌ Authentication failed")
            return False
        
        print(f"\n🔧 Making raw API call to /v3/list/Bill...")
        response = await service.make_api_call(
            "/v3/list/Bill",
            method="POST",
            filters={"max": 5}
        )
        
        if response:
            print(f"\n📊 Raw Response Structure:")
            print(f"   Response type: {type(response)}")
            print(f"   Response keys: {list(response.keys())}")
            
            # Show response in formatted JSON
            import json
            print(f"\n📄 Full Response (formatted):")
            print(json.dumps(response, indent=2)[:1000])  # First 1000 chars
            
            if "response_data" in response:
                data = response["response_data"]
                print(f"\n✅ Found 'response_data' key")
                print(f"   Type: {type(data)}")
                if isinstance(data, list):
                    print(f"   Length: {len(data)}")
                    if len(data) > 0:
                        print(f"   First item keys: {list(data[0].keys())}")
            else:
                print(f"\n⚠️  No 'response_data' key found")
                print(f"   Available keys: {list(response.keys())}")
            
            return True
        else:
            print(f"\n❌ No response received")
            return False


async def main():
    """Run all tests."""
    print("\n" + "="*70)
    print("🧪 Bill.com API Integration Tests")
    print("="*70)
    
    print("\nThese tests verify:")
    print("  1. Authentication with credentials in request body")
    print("  2. API calls with sessionId in request body")
    print("  3. Correct endpoint structure (/v3/list/Bill)")
    print("  4. Data retrieval from sandbox account")
    
    tests = [
        ("Authentication", test_billcom_authentication),
        ("Get Bills", test_billcom_get_bills),
        ("Get Vendors", test_billcom_get_vendors),
        ("Search Bills", test_billcom_search),
        ("Raw API Response", test_billcom_raw_api_response),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results[test_name] = result
        except Exception as e:
            print(f"\n❌ Test '{test_name}' crashed: {e}")
            import traceback
            traceback.print_exc()
            results[test_name] = False
        
        # Small delay between tests
        await asyncio.sleep(1)
    
    # Summary
    print("\n" + "="*70)
    print("📊 Test Summary")
    print("="*70)
    
    passed = sum(1 for r in results.values() if r)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status} - {test_name}")
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print(f"\n✅ All tests passed! Bill.com integration is working correctly.")
    elif passed == 0:
        print(f"\n❌ All tests failed. Check:")
        print(f"   1. Environment variables are set correctly")
        print(f"   2. Bill.com sandbox credentials are valid")
        print(f"   3. Sandbox account has some test data")
    else:
        print(f"\n⚠️  Partial success. Review failed tests above.")


if __name__ == "__main__":
    asyncio.run(main())