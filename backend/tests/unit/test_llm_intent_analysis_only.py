#!/usr/bin/env python3
"""
Test LLM intent analysis for all agents without calling MCP tools.

This test focuses on verifying that agents choose the correct actions
for keyword queries like "TBI Corp" without needing MCP server connections.
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
from app.agents.crm_agent_node import CRMAgentNode
from app.agents.accounts_payable_agent_node_http import AccountsPayableAgentNodeHTTP

async def test_gmail_intent_analysis():
    """Test Gmail agent LLM intent analysis."""
    print("📧 Testing Gmail Agent LLM Intent Analysis")
    print("=" * 60)
    
    gmail_node = EmailAgentNode(service='gmail')
    
    test_queries = [
        "check all emails with keywords TBI Corp or TBI-001",
        "find emails from TBI Corporation",
        "search for messages containing TBI",
        "show recent emails",  # Should use list
        "latest 10 messages"   # Should use list
    ]
    
    for query in test_queries:
        print(f"\nQuery: '{query}'")
        try:
            action_analysis = await gmail_node._analyze_user_intent(query, {})
            action = action_analysis.get('action', 'MISSING')
            query_param = action_analysis.get('query', 'MISSING')
            
            print(f"  Action: {action}")
            print(f"  Query: '{query_param}'")
            
            # Check if correct action was chosen
            if "TBI" in query and action == "search":
                print("  ✅ CORRECT: Chose 'search' for keyword query")
                if "TBI" in query_param:
                    print("  ✅ CORRECT: Keywords preserved in query")
                else:
                    print("  ❌ ISSUE: Keywords missing from query")
            elif "recent" in query.lower() or "latest" in query.lower():
                if action == "list":
                    print("  ✅ CORRECT: Chose 'list' for recent/latest query")
                else:
                    print("  ⚠️ NOTE: Could use 'list' for recent query, but 'search' is also acceptable")
            elif action == "list":
                print("  ❌ ISSUE: Chose 'list' instead of 'search' for keyword query")
            else:
                print(f"  ⚠️ UNEXPECTED: Action '{action}' for this query")
                
        except Exception as e:
            print(f"  ❌ ERROR: {e}")

async def test_crm_intent_analysis():
    """Test CRM agent LLM intent analysis."""
    print("\n🏢 Testing CRM Agent LLM Intent Analysis")
    print("=" * 60)
    
    crm_node = CRMAgentNode()
    
    test_queries = [
        "find accounts for TBI Corp",
        "search for companies TBI Corporation", 
        "look for opportunities with TBI",
        "show recent accounts",  # Should use get_accounts
        "list all opportunities"  # Should use get_opportunities
    ]
    
    for query in test_queries:
        print(f"\nQuery: '{query}'")
        try:
            action_analysis = await crm_node._analyze_user_intent(query, {})
            action = action_analysis.get('action', 'MISSING')
            search_term = action_analysis.get('search_term', 'MISSING')
            
            print(f"  Action: {action}")
            print(f"  Search Term: '{search_term}'")
            
            # Check if correct action was chosen
            if "TBI" in query and action == "search_records":
                print("  ✅ CORRECT: Chose 'search_records' for keyword query")
                if "TBI" in search_term:
                    print("  ✅ CORRECT: Keywords preserved in search term")
                else:
                    print("  ❌ ISSUE: Keywords missing from search term")
            elif "recent" in query.lower() or "list all" in query.lower():
                if action in ["get_accounts", "get_opportunities", "get_contacts"]:
                    print(f"  ✅ CORRECT: Chose '{action}' for general listing query")
                else:
                    print(f"  ⚠️ NOTE: Could use get_* for listing, but '{action}' might also work")
            elif action in ["get_accounts", "get_opportunities", "get_contacts"]:
                print(f"  ❌ ISSUE: Chose '{action}' instead of 'search_records' for keyword query")
            else:
                print(f"  ⚠️ UNEXPECTED: Action '{action}' for this query")
                
        except Exception as e:
            print(f"  ❌ ERROR: {e}")

async def test_billcom_intent_analysis():
    """Test Bill.com agent LLM intent analysis."""
    print("\n💰 Testing Bill.com Agent LLM Intent Analysis")
    print("=" * 60)
    
    ap_node = AccountsPayableAgentNodeHTTP()
    
    test_queries = [
        "find bills from TBI Corp",
        "search for invoices TBI-001",
        "look for bills containing TBI",
        "show recent bills",  # Should use list_bills
        "list unpaid invoices"  # Should use list_bills
    ]
    
    for query in test_queries:
        print(f"\nQuery: '{query}'")
        try:
            action_analysis = await ap_node._analyze_user_intent(query, {})
            action = action_analysis.get('action', 'MISSING')
            search_term = action_analysis.get('search_term', 'MISSING')
            
            print(f"  Action: {action}")
            print(f"  Search Term: '{search_term}'")
            
            # Check if correct action was chosen
            if "TBI" in query and action == "search_bills":
                print("  ✅ CORRECT: Chose 'search_bills' for keyword query")
                if "TBI" in search_term:
                    print("  ✅ CORRECT: Keywords preserved in search term")
                else:
                    print("  ❌ ISSUE: Keywords missing from search term")
            elif "recent" in query.lower() or "list" in query.lower():
                if action == "list_bills":
                    print("  ✅ CORRECT: Chose 'list_bills' for general listing query")
                else:
                    print(f"  ⚠️ NOTE: Could use 'list_bills' for listing, but '{action}' might also work")
            elif action == "list_bills":
                print("  ❌ ISSUE: Chose 'list_bills' instead of 'search_bills' for keyword query")
            else:
                print(f"  ⚠️ UNEXPECTED: Action '{action}' for this query")
                
        except Exception as e:
            print(f"  ❌ ERROR: {e}")

async def main():
    """Run all LLM intent analysis tests."""
    print("🧠 LLM Intent Analysis Testing (No MCP Connections Required)")
    print("=" * 80)
    print()
    
    await test_gmail_intent_analysis()
    await test_crm_intent_analysis()
    await test_billcom_intent_analysis()
    
    print("\n🎯 SUMMARY")
    print("=" * 60)
    print("This test verifies that agents choose the correct actions:")
    print("✅ Gmail: 'search' action for keyword queries like 'TBI Corp'")
    print("✅ CRM: 'search_records' action for keyword queries like 'TBI Corp'") 
    print("✅ Bill.com: 'search_bills' action for keyword queries like 'TBI Corp'")
    print("✅ All agents: Preserve keywords in search parameters")
    print("✅ All agents: Use listing actions only for 'recent' or 'list all' queries")

if __name__ == "__main__":
    asyncio.run(main())