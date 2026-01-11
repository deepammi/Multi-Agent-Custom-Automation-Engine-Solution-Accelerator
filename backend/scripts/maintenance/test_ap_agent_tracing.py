#!/usr/bin/env python3
"""
Accounts Payable Agent Tracing Script - Check for MCP Response Parsing Issues

This script tests the Accounts Payable agent to see if it has similar MCP response 
parsing issues as the Gmail agent had.
"""

import asyncio
import logging
import sys
import os
import json
from typing import Dict, Any
from datetime import datetime

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ Loaded .env file")
except ImportError:
    print("⚠️ python-dotenv not available, using system environment variables")
except Exception as e:
    print(f"⚠️ Could not load .env file: {e}")

# Set up detailed logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger("AP_TRACE")


async def test_ap_agent_mcp_parsing():
    """Test Accounts Payable agent MCP response parsing."""
    
    print(f"\n🚀 TESTING ACCOUNTS PAYABLE AGENT MCP RESPONSE PARSING")
    print(f"⏰ Started at: {datetime.now().isoformat()}")
    
    try:
        # Import required modules
        from app.agents.accounts_payable_agent import get_accounts_payable_agent
        
        # Get the AP agent
        ap_agent = get_accounts_payable_agent()
        
        print(f"\n✅ Accounts Payable Agent initialized successfully")
        print(f"   - Supported services: {ap_agent.get_supported_services()}")
        
        # Test 1: Get bills from Bill.com
        print(f"\n📋 TEST 1: Getting Bill.com bills...")
        try:
            result = await ap_agent.get_bills(service='bill_com', limit=5)
            
            print(f"✅ MCP call successful")
            print(f"   - Result type: {type(result)}")
            print(f"   - Result keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
            
            # Check for invoices (Bill.com uses 'invoices' for bills)
            if isinstance(result, dict):
                invoices = result.get('invoices', [])
                print(f"   - Invoices found: {len(invoices)}")
                
                if invoices:
                    print(f"   - First invoice keys: {list(invoices[0].keys()) if invoices else 'No invoices'}")
                    print(f"   - Sample invoice: {json.dumps(invoices[0], indent=2, default=str) if invoices else 'None'}")
                
                # Check for success field
                success = result.get('success')
                print(f"   - Success field: {success}")
            
        except Exception as e:
            print(f"❌ MCP call failed: {e}")
            print(f"   - Error type: {type(e).__name__}")
        
        # Test 2: Get vendors from Bill.com
        print(f"\n🏢 TEST 2: Getting Bill.com vendors...")
        try:
            result = await ap_agent.get_vendors(service='bill_com', limit=5)
            
            print(f"✅ MCP call successful")
            print(f"   - Result type: {type(result)}")
            print(f"   - Result keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
            
            # Check for vendors
            if isinstance(result, dict):
                vendors = result.get('vendors', [])
                print(f"   - Vendors found: {len(vendors)}")
                
                if vendors:
                    print(f"   - First vendor keys: {list(vendors[0].keys()) if vendors else 'No vendors'}")
                    print(f"   - Sample vendor: {json.dumps(vendors[0], indent=2, default=str) if vendors else 'None'}")
                
                # Check for success field
                success = result.get('success')
                print(f"   - Success field: {success}")
            
        except Exception as e:
            print(f"❌ MCP call failed: {e}")
            print(f"   - Error type: {type(e).__name__}")
        
        # Test 3: Search bills
        print(f"\n🔍 TEST 3: Searching Bill.com bills...")
        try:
            result = await ap_agent.search_bills(
                search_term="INV-",
                service='bill_com'
            )
            
            print(f"✅ MCP call successful")
            print(f"   - Result type: {type(result)}")
            print(f"   - Result keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
            
            # Check for invoices
            if isinstance(result, dict):
                invoices = result.get('invoices', [])
                print(f"   - Search results found: {len(invoices)}")
                
                # Check for success field
                success = result.get('success')
                print(f"   - Success field: {success}")
            
        except Exception as e:
            print(f"❌ MCP call failed: {e}")
            print(f"   - Error type: {type(e).__name__}")
        
        print(f"\n✅ ACCOUNTS PAYABLE AGENT TESTING COMPLETED")
        print(f"⏰ Completed at: {datetime.now().isoformat()}")
        
    except Exception as e:
        print(f"\n❌ ACCOUNTS PAYABLE AGENT TEST FAILED: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Main function to run the AP agent test."""
    
    print("🔍 Accounts Payable Agent MCP Response Parsing Test")
    print("=" * 60)
    print("This tool tests the AP agent for MCP response parsing issues")
    print("similar to those found in the Gmail agent.")
    print("=" * 60)
    
    # Run the test
    await test_ap_agent_mcp_parsing()


if __name__ == "__main__":
    print("Starting Accounts Payable Agent MCP Response Parsing Test...")
    asyncio.run(main())