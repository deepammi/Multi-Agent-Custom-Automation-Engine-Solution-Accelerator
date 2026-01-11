#!/usr/bin/env python3
"""
Test to verify the exact MCP search query issue.

This test checks if agents are passing empty queries to MCP search tools
instead of using the keywords from user requests.
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    # Load from the root directory (one level up from backend)
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
    load_dotenv(env_path)
    print(f"✅ Loaded environment variables from: {env_path}")
except ImportError:
    print("⚠️ python-dotenv not available, environment variables may not be loaded")

from app.agents.gmail_agent_node import EmailAgentNode
from app.agents.crm_agent import get_crm_agent
from app.agents.accounts_payable_agent_http import get_accounts_payable_agent_http

async def test_gmail_search_query_issue():
    """Test if Gmail agent passes proper search queries to MCP tools."""
    print("🔍 Testing Gmail Agent Search Query Issue")
    print("=" * 60)
    
    # Create Gmail agent
    gmail_agent = EmailAgentNode(service='gmail')
    
    # Test user request with specific keywords
    user_request = "check all emails with keywords TBI Corp or TBI-001"
    
    print(f"User Request: {user_request}")
    print()
    
    # Test the LLM intent analysis
    try:
        print("📧 Testing LLM Intent Analysis...")
        action_analysis = await gmail_agent._analyze_user_intent(user_request, {})
        
        print(f"Action Analysis Result:")
        print(f"  - Action: {action_analysis.get('action', 'MISSING')}")
        print(f"  - Query: '{action_analysis.get('query', 'MISSING')}'")
        print(f"  - Max Results: {action_analysis.get('max_results', 'MISSING')}")
        print()
        
        # Check if the issue exists
        action = action_analysis.get('action', '')
        query = action_analysis.get('query', '')
        
        if action == 'list':
            print("❌ ISSUE FOUND: LLM chose 'list' action instead of 'search'")
            print("   This will call list_messages() with no query parameter")
            print("   Result: Returns latest emails instead of filtered results")
        elif action == 'search' and not query.strip():
            print("❌ ISSUE FOUND: LLM chose 'search' but provided empty query")
            print("   This will call search_messages('') which returns all emails")
        elif action == 'search' and query.strip():
            print("✅ GOOD: LLM chose 'search' with proper query")
            print(f"   Query: '{query}'")
            
            # Check if keywords are preserved
            if 'TBI' in query and ('Corp' in query or '001' in query):
                print("✅ GOOD: Keywords preserved in search query")
            else:
                print("❌ ISSUE: Keywords missing from search query")
        else:
            print(f"⚠️  UNEXPECTED: Action '{action}' with query '{query}'")
            
    except Exception as e:
        print(f"❌ ERROR in Gmail intent analysis: {e}")
    
    print()

async def test_crm_search_query_issue():
    """Test if CRM agent uses search_records vs get_accounts."""
    print("🏢 Testing CRM Agent Search Query Issue")
    print("=" * 60)
    
    crm_agent = get_crm_agent()
    
    # Test with keywords
    search_term = "TBI Corp"
    
    print(f"Search Term: {search_term}")
    print()
    
    try:
        print("Testing search_records method...")
        # This should use the search tool
        result = await crm_agent.search_records(
            search_term=search_term,
            service='salesforce'
        )
        print("✅ search_records method works")
        print(f"   Result keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
        
    except Exception as e:
        print(f"❌ ERROR in CRM search_records: {e}")
    
    try:
        print("Testing get_accounts method...")
        # This uses the general listing tool
        result = await crm_agent.get_accounts(
            service='salesforce',
            account_name=search_term  # This might not work as expected
        )
        print("✅ get_accounts method works")
        print(f"   Result keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
        
    except Exception as e:
        print(f"❌ ERROR in CRM get_accounts: {e}")
    
    print()

async def test_billcom_search_query_issue():
    """Test if Bill.com agent uses search_bills vs get_bills."""
    print("💰 Testing Bill.com Agent Search Query Issue")
    print("=" * 60)
    
    ap_agent = get_accounts_payable_agent_http()
    
    # Test with keywords
    search_term = "TBI-001"
    
    print(f"Search Term: {search_term}")
    print()
    
    try:
        print("Testing search_bills method...")
        # This should use the search tool
        result = await ap_agent.search_bills(
            search_term=search_term,
            service='bill_com'
        )
        print("✅ search_bills method works")
        print(f"   Result keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
        
    except Exception as e:
        print(f"❌ ERROR in Bill.com search_bills: {e}")
    
    try:
        print("Testing get_bills method...")
        # This uses the general listing tool
        result = await ap_agent.get_bills(
            service='bill_com'
        )
        print("✅ get_bills method works")
        print(f"   Result keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
        
    except Exception as e:
        print(f"❌ ERROR in Bill.com get_bills: {e}")
    
    print()

async def test_mcp_tool_mapping():
    """Test the MCP tool mapping to verify which tools are being called."""
    print("🔧 Testing MCP Tool Mapping")
    print("=" * 60)
    
    # Gmail tools
    gmail_agent = EmailAgentNode(service='gmail')
    email_agent = gmail_agent.email_agent
    
    print("Gmail MCP Tools:")
    gmail_tools = email_agent.supported_services['gmail']['tools']
    for operation, tool_name in gmail_tools.items():
        print(f"  - {operation}: {tool_name}")
    print()
    
    # CRM tools
    crm_agent = get_crm_agent()
    print("Salesforce MCP Tools:")
    sf_tools = crm_agent.supported_services['salesforce']['tools']
    for operation, tool_name in sf_tools.items():
        print(f"  - {operation}: {tool_name}")
    print()
    
    # Bill.com tools
    ap_agent = get_accounts_payable_agent_http()
    print("Bill.com MCP Tools:")
    bc_tools = ap_agent.supported_services['bill_com']['tools']
    for operation, tool_name in bc_tools.items():
        print(f"  - {operation}: {tool_name}")
    print()

async def main():
    """Run all tests to identify the MCP search query issue."""
    print("🚀 MCP Search Query Issue Investigation")
    print("=" * 80)
    print()
    
    await test_mcp_tool_mapping()
    await test_gmail_search_query_issue()
    await test_crm_search_query_issue()
    await test_billcom_search_query_issue()
    
    print("🎯 SUMMARY")
    print("=" * 60)
    print("Expected Issues:")
    print("1. Gmail agent might choose 'list' instead of 'search' for keyword queries")
    print("2. Even if 'search' is chosen, query might be empty or incomplete")
    print("3. CRM and Bill.com agents might use general listing tools instead of search tools")
    print("4. Keywords like 'TBI Corp' and 'TBI-001' might not be preserved in queries")
    print()
    print("✅ Run this test to verify the exact issue before implementing the fix")

if __name__ == "__main__":
    asyncio.run(main())