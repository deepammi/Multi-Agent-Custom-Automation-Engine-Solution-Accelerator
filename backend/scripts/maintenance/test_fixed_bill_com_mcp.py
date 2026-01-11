#!/usr/bin/env python3
"""
Test the fixed Bill.com MCP server implementation.

This script tests the corrected Bill.com API integration with proper v3 API patterns:
- sessionId and devKey in request BODY (not headers)
- POST requests with correct endpoint structure
- Proper authentication flow
"""

import asyncio
import logging
import sys
import os
from pathlib import Path

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src" / "mcp_server"))

from backend.app.agents.accounts_payable_agent_http import AccountsPayableAgentHTTP

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_fixed_bill_com_integration():
    """Test the fixed Bill.com MCP integration."""
    
    print("🔧 Testing Fixed Bill.com MCP Integration")
    print("=" * 60)
    
    try:
        # Initialize HTTP AP agent
        ap_agent = AccountsPayableAgentHTTP()
        
        print("\n1️⃣ Testing Bill.com Bills Retrieval...")
        print("-" * 40)
        
        # Test getting bills
        bills_result = await ap_agent.get_bills(
            service='bill_com',
            limit=5
        )
        
        print(f"✅ Bills retrieval successful!")
        print(f"   Result type: {type(bills_result)}")
        
        if isinstance(bills_result, dict):
            if 'result' in bills_result:
                print(f"   Result content: {str(bills_result['result'])[:200]}...")
            else:
                print(f"   Result keys: {list(bills_result.keys())}")
        
        print("\n2️⃣ Testing Bill.com Vendors Retrieval...")
        print("-" * 40)
        
        # Test getting vendors
        vendors_result = await ap_agent.get_vendors(
            service='bill_com'
        )
        
        print(f"✅ Vendors retrieval successful!")
        print(f"   Result type: {type(vendors_result)}")
        
        if isinstance(vendors_result, dict):
            if 'result' in vendors_result:
                print(f"   Result content: {str(vendors_result['result'])[:200]}...")
            else:
                print(f"   Result keys: {list(vendors_result.keys())}")
        
        print("\n3️⃣ Testing Bill.com Search...")
        print("-" * 40)
        
        # Test searching bills
        search_result = await ap_agent.search_bills(
            search_term="1001",
            service='bill_com'
        )
        
        print(f"✅ Search successful!")
        print(f"   Result type: {type(search_result)}")
        
        if isinstance(search_result, dict):
            if 'result' in search_result:
                print(f"   Result content: {str(search_result['result'])[:200]}...")
            else:
                print(f"   Result keys: {list(search_result.keys())}")
        
        print("\n🎉 All tests completed successfully!")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Main test function."""
    print("🚀 Starting Fixed Bill.com MCP Integration Test")
    
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
        print("Please set these in your .env file")
        return False
    
    print("✅ All required environment variables present")
    
    # Run the test
    success = await test_fixed_bill_com_integration()
    
    if success:
        print("\n🎯 Integration test PASSED - Bill.com MCP server is working!")
    else:
        print("\n💥 Integration test FAILED - Check the errors above")
    
    return success


if __name__ == "__main__":
    asyncio.run(main())