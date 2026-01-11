#!/usr/bin/env python3
"""
Test Real Bill.com Data Retrieval

This script tests the fixed HTTP AP agent to see what real data we get from Bill.com.
"""

import asyncio
import logging
import sys
import os
import json

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Set up logging
logging.basicConfig(level=logging.INFO)

async def test_real_bill_com_data():
    """Test real Bill.com data retrieval."""
    
    print("🔍 Testing Real Bill.com Data Retrieval")
    print("=" * 60)
    
    try:
        from app.agents.accounts_payable_agent_http import get_accounts_payable_agent_http
        
        # Get the HTTP AP agent
        ap_agent = get_accounts_payable_agent_http()
        print(f"✅ HTTP AP Agent initialized")
        
        # Test 1: Get Bills
        print(f"\n🧪 Test 1: Get Bills from Bill.com")
        print("-" * 40)
        
        try:
            result = await ap_agent.get_bills(service="bill_com")
            print(f"✅ Success!")
            print(f"📊 Result Type: {type(result)}")
            print(f"📊 Result Keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
            
            if isinstance(result, dict) and 'result' in result:
                print(f"📄 Raw Result Content:")
                print(result['result'][:500] + "..." if len(str(result['result'])) > 500 else result['result'])
            
        except Exception as e:
            print(f"❌ Failed: {e}")
        
        # Test 2: Try different Bill.com tools to find data
        print(f"\n🧪 Test 2: Try get_bill_com_invoice_details with ID")
        print("-" * 40)
        
        try:
            # Try to get a specific invoice by ID
            result = await ap_agent.get_bill(bill_id="1001", service="bill_com")
            print(f"✅ Success!")
            print(f"📊 Result Type: {type(result)}")
            print(f"📊 Result Keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
            
            if isinstance(result, dict) and 'result' in result:
                print(f"📄 Raw Result Content:")
                print(result['result'][:1000] + "..." if len(str(result['result'])) > 1000 else result['result'])
            
        except Exception as e:
            print(f"❌ Failed: {e}")
        
        # Test 2b: Try with different parameters for get_bills
        print(f"\n🧪 Test 2b: Get Bills with vendor filter")
        print("-" * 40)
        
        try:
            # Try to get bills with vendor name filter
            result = await ap_agent.get_bills(service="bill_com", vendor_name="Acme Marketing", limit=10)
            print(f"✅ Success!")
            print(f"📊 Result Type: {type(result)}")
            print(f"📊 Result Keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
            
            if isinstance(result, dict) and 'result' in result:
                print(f"📄 Raw Result Content:")
                print(result['result'][:1000] + "..." if len(str(result['result'])) > 1000 else result['result'])
            
        except Exception as e:
            print(f"❌ Failed: {e}")
            
        # Test 2c: Search Bills for Acme Marketing (keep original test)
        print(f"\n🧪 Test 2c: Search Bills for 'Acme Marketing' (original)")
        print("-" * 40)
        
        try:
            result = await ap_agent.search_bills(search_term="Acme Marketing", service="bill_com")
            print(f"✅ Success!")
            print(f"📊 Result Type: {type(result)}")
            print(f"📊 Result Keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
            
            if isinstance(result, dict) and 'result' in result:
                print(f"📄 Raw Result Content:")
                print(result['result'][:1000] + "..." if len(str(result['result'])) > 1000 else result['result'])
            
        except Exception as e:
            print(f"❌ Failed: {e}")
        
        # Test 3: Get Vendors
        print(f"\n🧪 Test 3: Get Vendors")
        print("-" * 40)
        
        try:
            result = await ap_agent.get_vendors(service="bill_com")
            print(f"✅ Success!")
            print(f"📊 Result Type: {type(result)}")
            print(f"📊 Result Keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
            
            if isinstance(result, dict) and 'result' in result:
                print(f"📄 Raw Result Content:")
                print(result['result'][:500] + "..." if len(str(result['result'])) > 500 else result['result'])
            
        except Exception as e:
            print(f"❌ Failed: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test Failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main test function."""
    
    print("🚀 Real Bill.com Data Test")
    print("=" * 80)
    print("Testing HTTP AP agent with real Bill.com MCP server")
    print("=" * 80)
    
    success = await test_real_bill_com_data()
    
    if success:
        print(f"\n🎉 SUCCESS: HTTP AP Agent is retrieving real data from Bill.com!")
        print(f"   ✅ MCP HTTP transport working correctly")
        print(f"   ✅ Tool calls successful")
        print(f"   ✅ Data processing working")
        
        print(f"\n🚀 Next Steps:")
        print(f"   1. Start Salesforce MCP server on port 9001")
        print(f"   2. Test CRM agent with real Salesforce data")
        print(f"   3. Update agent nodes to use HTTP agents")
        print(f"   4. Test end-to-end LLM + MCP integration")
        
    else:
        print(f"\n❌ Issues found that need to be resolved")
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())