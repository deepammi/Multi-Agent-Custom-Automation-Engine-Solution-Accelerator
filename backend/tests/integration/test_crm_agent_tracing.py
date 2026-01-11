#!/usr/bin/env python3
"""
CRM Agent Tracing Script - Check for MCP Response Parsing Issues

This script tests the CRM agent to see if it has similar MCP response parsing
issues as the Gmail agent had.
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

logger = logging.getLogger("CRM_TRACE")


async def test_crm_agent_mcp_parsing():
    """Test CRM agent MCP response parsing."""
    
    print(f"\n🚀 TESTING CRM AGENT MCP RESPONSE PARSING")
    print(f"⏰ Started at: {datetime.now().isoformat()}")
    
    try:
        # Import required modules
        from app.agents.crm_agent import get_crm_agent
        
        # Get the CRM agent
        crm_agent = get_crm_agent()
        
        print(f"\n✅ CRM Agent initialized successfully")
        print(f"   - Supported services: {crm_agent.get_supported_services()}")
        
        # Test 1: Get accounts from Salesforce
        print(f"\n📊 TEST 1: Getting Salesforce accounts...")
        try:
            result = await crm_agent.get_accounts(service='salesforce', limit=5)
            
            print(f"✅ MCP call successful")
            print(f"   - Result type: {type(result)}")
            print(f"   - Result keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
            
            # Check for records
            if isinstance(result, dict):
                records = result.get('records', [])
                print(f"   - Records found: {len(records)}")
                
                if records:
                    print(f"   - First record keys: {list(records[0].keys()) if records else 'No records'}")
                    print(f"   - Sample record: {json.dumps(records[0], indent=2, default=str) if records else 'None'}")
                
                # Check for success field
                success = result.get('success')
                print(f"   - Success field: {success}")
                
                # Check for totalSize
                total_size = result.get('totalSize')
                print(f"   - Total size: {total_size}")
            
        except Exception as e:
            print(f"❌ MCP call failed: {e}")
            print(f"   - Error type: {type(e).__name__}")
        
        # Test 2: Get opportunities from Salesforce
        print(f"\n💼 TEST 2: Getting Salesforce opportunities...")
        try:
            result = await crm_agent.get_opportunities(service='salesforce', limit=5)
            
            print(f"✅ MCP call successful")
            print(f"   - Result type: {type(result)}")
            print(f"   - Result keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
            
            # Check for records
            if isinstance(result, dict):
                records = result.get('records', [])
                print(f"   - Records found: {len(records)}")
                
                if records:
                    print(f"   - First record keys: {list(records[0].keys()) if records else 'No records'}")
                
                # Check for success field
                success = result.get('success')
                print(f"   - Success field: {success}")
            
        except Exception as e:
            print(f"❌ MCP call failed: {e}")
            print(f"   - Error type: {type(e).__name__}")
        
        # Test 3: Search records
        print(f"\n🔍 TEST 3: Searching Salesforce records...")
        try:
            result = await crm_agent.search_records(
                search_term="test",
                service='salesforce'
            )
            
            print(f"✅ MCP call successful")
            print(f"   - Result type: {type(result)}")
            print(f"   - Result keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
            
            # Check for results
            if isinstance(result, dict):
                search_results = result.get('results', [])
                print(f"   - Search results found: {len(search_results)}")
                
                # Check for success field
                success = result.get('success')
                print(f"   - Success field: {success}")
            
        except Exception as e:
            print(f"❌ MCP call failed: {e}")
            print(f"   - Error type: {type(e).__name__}")
        
        print(f"\n✅ CRM AGENT TESTING COMPLETED")
        print(f"⏰ Completed at: {datetime.now().isoformat()}")
        
    except Exception as e:
        print(f"\n❌ CRM AGENT TEST FAILED: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Main function to run the CRM agent test."""
    
    print("🔍 CRM Agent MCP Response Parsing Test")
    print("=" * 60)
    print("This tool tests the CRM agent for MCP response parsing issues")
    print("similar to those found in the Gmail agent.")
    print("=" * 60)
    
    # Run the test
    await test_crm_agent_mcp_parsing()


if __name__ == "__main__":
    print("Starting CRM Agent MCP Response Parsing Test...")
    asyncio.run(main())