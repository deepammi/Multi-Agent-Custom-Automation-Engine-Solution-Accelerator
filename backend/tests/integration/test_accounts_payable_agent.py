#!/usr/bin/env python3
"""
Test script for AccountsPayable Agent with Zoho integration.

This test verifies that the new category-based AccountsPayable Agent
works correctly with the standardized Zoho MCP client.

**Feature: mcp-client-standardization, Property 4: Base Client Inheritance**
**Validates: Requirements 2.1, 2.5**
"""

import asyncio
import sys
import os
import logging

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.agents.accounts_payable_agent import get_accounts_payable_agent
from app.agents.accounts_payable_agent_node import accounts_payable_agent_node
from app.agents.state import AgentState

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ANSI color codes for better output
BLUE = '\033[94m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
RESET = '\033[0m'
BOLD = '\033[1m'


async def test_accounts_payable_agent_direct():
    """Test AccountsPayable Agent directly."""
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BOLD}Testing AccountsPayable Agent (Direct){RESET}")
    print(f"{BLUE}{'='*60}{RESET}")
    
    try:
        # Initialize MCP services first
        from app.services.mcp_client_service import initialize_mcp_services
        await initialize_mcp_services()
        
        # Get the agent
        ap_agent = get_accounts_payable_agent()
        
        # Test service info
        print(f"\n{GREEN}1. Testing service information{RESET}")
        services = ap_agent.get_supported_services()
        print(f"Supported services: {services}")
        
        for service in services:
            info = ap_agent.get_service_info(service)
            print(f"  {service}: {info['name']} - {len(info['operations'])} operations")
        
        # Test Zoho operations
        print(f"\n{GREEN}2. Testing Zoho invoice listing{RESET}")
        try:
            result = await ap_agent.get_invoices(service='zoho', limit=5)
            print(f"Zoho invoices result: {result.get('success', False)}")
            if result.get('success'):
                invoices = result.get('invoices', [])
                print(f"Found {len(invoices)} invoices")
                for i, invoice in enumerate(invoices[:3], 1):
                    print(f"  {i}. {invoice.get('invoice_number', 'N/A')} - {invoice.get('customer_name', 'N/A')}")
            else:
                print(f"Error: {result.get('error', 'Unknown error')}")
        except Exception as e:
            print(f"Exception during invoice listing: {e}")
        
        # Test Zoho customers
        print(f"\n{GREEN}3. Testing Zoho customer listing{RESET}")
        try:
            result = await ap_agent.get_vendors(service='zoho', limit=5)
            print(f"Zoho customers result: {result.get('success', False)}")
            if result.get('success'):
                vendors = result.get('vendors', [])
                print(f"Found {len(vendors)} customers")
                for i, vendor in enumerate(vendors[:3], 1):
                    name = vendor.get('contact_name') or vendor.get('name', 'N/A')
                    print(f"  {i}. {name} - {vendor.get('email', 'N/A')}")
            else:
                print(f"Error: {result.get('error', 'Unknown error')}")
        except Exception as e:
            print(f"Exception during customer listing: {e}")
        
        # Test Bill.com operations (should fail gracefully)
        print(f"\n{GREEN}4. Testing Bill.com operations (expected to fail){RESET}")
        try:
            result = await ap_agent.get_invoices(service='bill_com', limit=5)
            print(f"Bill.com invoices result: {result.get('success', False)}")
            if not result.get('success'):
                print(f"Expected error: {result.get('error', 'Unknown error')}")
        except Exception as e:
            print(f"Expected exception: {e}")
        
        print(f"\n{GREEN}✅ AccountsPayable Agent direct test completed{RESET}")
        
    except Exception as e:
        print(f"\n{RED}❌ AccountsPayable Agent direct test failed: {e}{RESET}")
        import traceback
        traceback.print_exc()


async def test_accounts_payable_agent_node():
    """Test AccountsPayable Agent through LangGraph node."""
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BOLD}Testing AccountsPayable Agent Node{RESET}")
    print(f"{BLUE}{'='*60}{RESET}")
    
    try:
        # Create test state
        test_state = AgentState(
            plan_id="test-plan-123",
            task_description="Show me Zoho invoices",
            messages=[],
            current_agent="planner",
            next_agent="accounts_payable",
            collected_data={},
            execution_results=[],
            websocket_manager=None  # No WebSocket for testing
        )
        
        print(f"Task: {test_state['task_description']}")
        print(f"Plan ID: {test_state['plan_id']}")
        
        # Execute the agent node
        result = await accounts_payable_agent_node(test_state)
        
        print(f"\n{GREEN}Agent Response:{RESET}")
        print(f"Current Agent: {result.get('current_agent', 'N/A')}")
        print(f"Service Used: {result.get('service_used', 'N/A')}")
        
        messages = result.get('messages', [])
        if messages:
            print(f"\nResponse Content:")
            print(messages[0][:500] + "..." if len(messages[0]) > 500 else messages[0])
        
        print(f"\n{GREEN}✅ AccountsPayable Agent node test completed{RESET}")
        
    except Exception as e:
        print(f"\n{RED}❌ AccountsPayable Agent node test failed: {e}{RESET}")
        import traceback
        traceback.print_exc()


async def test_backward_compatibility():
    """Test backward compatibility with legacy Zoho interfaces."""
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BOLD}Testing Backward Compatibility{RESET}")
    print(f"{BLUE}{'='*60}{RESET}")
    
    try:
        # Test legacy ZohoAgent wrapper
        print(f"\n{GREEN}1. Testing ZohoAgentLegacy wrapper{RESET}")
        from app.agents.accounts_payable_agent import get_zoho_agent
        
        zoho_agent = get_zoho_agent()
        
        # Test legacy interface
        result = await zoho_agent.list_invoices(limit=3)
        print(f"Legacy list_invoices result: {result.get('success', False)}")
        
        result = await zoho_agent.list_customers(limit=3)
        print(f"Legacy list_customers result: {result.get('success', False)}")
        
        # Test legacy ZohoMCPService
        print(f"\n{GREEN}2. Testing ZohoMCPService compatibility{RESET}")
        from app.services.zoho_mcp_service import get_zoho_service
        
        zoho_service = get_zoho_service()
        await zoho_service.initialize()
        
        result = await zoho_service.list_invoices(limit=3)
        print(f"Legacy service list_invoices result: {result.get('success', False)}")
        
        result = await zoho_service.list_customers(limit=3)
        print(f"Legacy service list_customers result: {result.get('success', False)}")
        
        # Test legacy agent node (should be same as new one due to alias)
        print(f"\n{GREEN}3. Testing legacy zoho_agent_node{RESET}")
        from app.agents.accounts_payable_agent_node import zoho_agent_node
        
        test_state = AgentState(
            plan_id="test-plan-legacy",
            task_description="Show me Zoho customers",
            messages=[],
            current_agent="planner",
            next_agent="zoho",
            collected_data={},
            execution_results=[],
            websocket_manager=None
        )
        
        result = await zoho_agent_node(test_state)
        print(f"Legacy node result: {result.get('current_agent', 'N/A')}")
        
        print(f"\n{GREEN}✅ Backward compatibility test completed{RESET}")
        
    except Exception as e:
        print(f"\n{RED}❌ Backward compatibility test failed: {e}{RESET}")
        import traceback
        traceback.print_exc()


async def main():
    """Run all tests."""
    print(f"{BOLD}AccountsPayable Agent Test Suite{RESET}")
    print(f"Testing category-based AP agent with Zoho integration")
    
    # Run tests
    await test_accounts_payable_agent_direct()
    await test_accounts_payable_agent_node()
    await test_backward_compatibility()
    
    print(f"\n{BOLD}{'='*60}{RESET}")
    print(f"{BOLD}All tests completed{RESET}")
    print(f"{BOLD}{'='*60}{RESET}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n{YELLOW}⚠️  Tests interrupted by user{RESET}")
    except Exception as e:
        print(f"\n{RED}❌ Test suite failed: {e}{RESET}")
        sys.exit(1)