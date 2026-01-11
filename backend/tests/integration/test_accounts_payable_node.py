#!/usr/bin/env python3
"""
Test script for AccountsPayable Agent Node functionality.

This test verifies that the new accounts payable agent node works correctly
with mock data and maintains backward compatibility.
"""

import asyncio
import sys
import os
import logging

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.agents.accounts_payable_agent_node import accounts_payable_agent_node, zoho_agent_node
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


async def test_accounts_payable_node():
    """Test AccountsPayable Agent Node with various tasks."""
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BOLD}Testing AccountsPayable Agent Node{RESET}")
    print(f"{BLUE}{'='*60}{RESET}")
    
    # Disable standardized MCP to use mock data
    os.environ["ZOHO_USE_STANDARDIZED_MCP"] = "false"
    
    test_cases = [
        {
            "description": "List Zoho invoices",
            "task": "Show me Zoho invoices",
            "expected_service": "zoho"
        },
        {
            "description": "List Zoho customers", 
            "task": "Show me Zoho customers",
            "expected_service": "zoho"
        },
        {
            "description": "Get specific invoice",
            "task": "Show me details for invoice INV-00001",
            "expected_service": "zoho"
        },
        {
            "description": "List unpaid invoices",
            "task": "Show me unpaid invoices from Zoho",
            "expected_service": "zoho"
        },
        {
            "description": "Bill.com invoices",
            "task": "Show me Bill.com invoices",
            "expected_service": "bill_com"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{GREEN}{i}. {test_case['description']}{RESET}")
        
        try:
            # Create test state
            test_state = AgentState(
                plan_id=f"test-plan-{i}",
                task_description=test_case["task"],
                messages=[],
                current_agent="planner",
                next_agent="accounts_payable",
                collected_data={},
                execution_results=[],
                websocket_manager=None  # No WebSocket for testing
            )
            
            print(f"   Task: {test_case['task']}")
            
            # Execute the agent node
            result = await accounts_payable_agent_node(test_state)
            
            # Check results
            current_agent = result.get('current_agent', 'N/A')
            service_used = result.get('service_used', 'N/A')
            messages = result.get('messages', [])
            
            print(f"   Agent: {current_agent}")
            print(f"   Service: {service_used}")
            
            # Verify expected service
            if service_used == test_case['expected_service']:
                print(f"   ✅ Correct service selected")
            else:
                print(f"   ❌ Wrong service (expected {test_case['expected_service']})")
            
            # Check if we got a response
            if messages and len(messages[0]) > 0:
                print(f"   ✅ Response generated ({len(messages[0])} chars)")
                # Show first line of response
                first_line = messages[0].split('\n')[0]
                print(f"   Preview: {first_line[:80]}...")
            else:
                print(f"   ❌ No response generated")
            
        except Exception as e:
            print(f"   ❌ Test failed: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n{GREEN}✅ AccountsPayable Agent Node tests completed{RESET}")


async def test_backward_compatibility_node():
    """Test backward compatibility with legacy zoho_agent_node."""
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BOLD}Testing Backward Compatibility Node{RESET}")
    print(f"{BLUE}{'='*60}{RESET}")
    
    # Disable standardized MCP to use mock data
    os.environ["ZOHO_USE_STANDARDIZED_MCP"] = "false"
    
    try:
        print(f"\n{GREEN}Testing legacy zoho_agent_node alias{RESET}")
        
        # Create test state
        test_state = AgentState(
            plan_id="test-plan-legacy",
            task_description="Show me Zoho invoices",
            messages=[],
            current_agent="planner", 
            next_agent="zoho",
            collected_data={},
            execution_results=[],
            websocket_manager=None
        )
        
        print(f"Task: {test_state['task_description']}")
        
        # Test that zoho_agent_node is the same as accounts_payable_agent_node
        print(f"Functions are same: {zoho_agent_node is accounts_payable_agent_node}")
        
        # Execute the legacy node
        result = await zoho_agent_node(test_state)
        
        # Check results
        current_agent = result.get('current_agent', 'N/A')
        service_used = result.get('service_used', 'N/A')
        messages = result.get('messages', [])
        
        print(f"Agent: {current_agent}")
        print(f"Service: {service_used}")
        
        if messages and len(messages[0]) > 0:
            print(f"✅ Legacy node works correctly")
            print(f"Response length: {len(messages[0])} chars")
        else:
            print(f"❌ Legacy node failed to generate response")
        
        print(f"\n{GREEN}✅ Backward compatibility node test completed{RESET}")
        
    except Exception as e:
        print(f"\n{RED}❌ Backward compatibility node test failed: {e}{RESET}")
        import traceback
        traceback.print_exc()


async def test_error_handling():
    """Test error handling in the agent node."""
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BOLD}Testing Error Handling{RESET}")
    print(f"{BLUE}{'='*60}{RESET}")
    
    try:
        print(f"\n{GREEN}Testing with invalid task{RESET}")
        
        # Create test state with potentially problematic task
        test_state = AgentState(
            plan_id="test-plan-error",
            task_description="",  # Empty task
            messages=[],
            current_agent="planner",
            next_agent="accounts_payable", 
            collected_data={},
            execution_results=[],
            websocket_manager=None
        )
        
        # Execute the agent node
        result = await accounts_payable_agent_node(test_state)
        
        # Should handle gracefully
        current_agent = result.get('current_agent', 'N/A')
        messages = result.get('messages', [])
        
        print(f"Agent: {current_agent}")
        
        if messages:
            print(f"✅ Error handled gracefully")
            print(f"Response: {messages[0][:100]}...")
        else:
            print(f"❌ No error response generated")
        
        print(f"\n{GREEN}✅ Error handling test completed{RESET}")
        
    except Exception as e:
        print(f"\n{RED}❌ Error handling test failed: {e}{RESET}")
        import traceback
        traceback.print_exc()


async def main():
    """Run all tests."""
    print(f"{BOLD}AccountsPayable Agent Node Test Suite{RESET}")
    print(f"Testing agent node functionality with mock data")
    
    # Run tests
    await test_accounts_payable_node()
    await test_backward_compatibility_node()
    await test_error_handling()
    
    print(f"\n{BOLD}{'='*60}{RESET}")
    print(f"{BOLD}All node tests completed{RESET}")
    print(f"{BOLD}{'='*60}{RESET}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n{YELLOW}⚠️  Tests interrupted by user{RESET}")
    except Exception as e:
        print(f"\n{RED}❌ Test suite failed: {e}{RESET}")
        sys.exit(1)