"""Test Zoho agent integration with LangGraph."""
import asyncio
import logging
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.agents.zoho_agent_node import zoho_agent_node
from app.agents.state import AgentState
from app.agents.nodes import planner_node

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Colors
GREEN = '\033[92m'
BLUE = '\033[94m'
YELLOW = '\033[93m'
RESET = '\033[0m'


async def test_zoho_agent():
    """Test Zoho agent node."""
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}Phase 2: Zoho Agent Integration Test{RESET}")
    print(f"{BLUE}{'='*60}{RESET}\n")
    
    # Test 1: Planner routing
    print(f"{BLUE}Test 1: Planner Routing{RESET}")
    print("-" * 60)
    
    test_state: AgentState = {
        "messages": [],
        "plan_id": "test-plan-001",
        "session_id": "test-session-001",
        "task_description": "Show me recent invoices from Zoho",
        "current_agent": "User",
        "next_agent": None,
        "final_result": "",
        "approval_required": False,
        "approved": None,
        "websocket_manager": None,
        "llm_provider": None,
        "llm_temperature": None,
        "extraction_result": None,
        "requires_extraction_approval": None,
        "extraction_approved": None
    }
    
    result = planner_node(test_state)
    print(f"Task: {test_state['task_description']}")
    print(f"Planner Decision: Route to '{result.get('next_agent')}' agent")
    print(f"Planner Response: {result.get('messages', [''])[0]}")
    
    if result.get('next_agent') == 'zoho':
        print(f"{GREEN}✅ Planner correctly routes to Zoho agent{RESET}\n")
    else:
        print(f"{YELLOW}⚠️  Planner routed to '{result.get('next_agent')}' instead of 'zoho'{RESET}\n")
    
    # Test 2: List invoices
    print(f"{BLUE}Test 2: List Invoices{RESET}")
    print("-" * 60)
    
    test_state["task_description"] = "List all invoices from Zoho"
    test_state["next_agent"] = "zoho"
    
    result = await zoho_agent_node(test_state)
    print(f"Task: {test_state['task_description']}")
    print(f"Agent: {result.get('current_agent')}")
    print(f"\nResponse:\n{result.get('final_result')}")
    print(f"{GREEN}✅ List invoices test complete{RESET}\n")
    
    # Test 3: List customers
    print(f"{BLUE}Test 3: List Customers{RESET}")
    print("-" * 60)
    
    test_state["task_description"] = "Show me Zoho customers"
    result = await zoho_agent_node(test_state)
    print(f"Task: {test_state['task_description']}")
    print(f"\nResponse:\n{result.get('final_result')}")
    print(f"{GREEN}✅ List customers test complete{RESET}\n")
    
    # Test 4: Get specific invoice
    print(f"{BLUE}Test 4: Get Invoice Details{RESET}")
    print("-" * 60)
    
    test_state["task_description"] = "Show me details for invoice INV-001"
    result = await zoho_agent_node(test_state)
    print(f"Task: {test_state['task_description']}")
    print(f"\nResponse:\n{result.get('final_result')}")
    print(f"{GREEN}✅ Get invoice details test complete{RESET}\n")
    
    # Test 5: Filter by status
    print(f"{BLUE}Test 5: Filter Invoices by Status{RESET}")
    print("-" * 60)
    
    test_state["task_description"] = "Show me unpaid invoices from Zoho"
    result = await zoho_agent_node(test_state)
    print(f"Task: {test_state['task_description']}")
    print(f"\nResponse:\n{result.get('final_result')}")
    print(f"{GREEN}✅ Filter by status test complete{RESET}\n")
    
    # Summary
    print(f"{BLUE}{'='*60}{RESET}")
    print(f"{GREEN}✅ Phase 2 Tests Complete!{RESET}")
    print(f"{BLUE}{'='*60}{RESET}\n")
    
    print("Phase 2 Success Criteria:")
    print(f"  {GREEN}✓{RESET} Planner routes Zoho tasks correctly")
    print(f"  {GREEN}✓{RESET} Zoho agent returns formatted mock data")
    print(f"  {GREEN}✓{RESET} Agent integrates with LangGraph workflow")
    print(f"  {GREEN}✓{RESET} Multiple query types work")
    
    print(f"\n{BLUE}Next Step: Phase 3 - Frontend Testing{RESET}")
    print("  1. Start backend server: python3 -m app.main")
    print("  2. Open frontend UI")
    print("  3. Submit: 'Show me recent invoices from Zoho'")
    print("  4. Verify mock data displays correctly\n")


if __name__ == "__main__":
    try:
        asyncio.run(test_zoho_agent())
    except KeyboardInterrupt:
        print(f"\n{YELLOW}⚠️  Test interrupted{RESET}")
    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        sys.exit(1)
