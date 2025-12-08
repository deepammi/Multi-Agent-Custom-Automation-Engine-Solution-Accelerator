"""Test Zoho agent with real API data."""
import asyncio
import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.agents.zoho_agent_node import zoho_agent_node
from app.agents.state import AgentState


async def test_agent():
    """Test Zoho agent with different queries."""
    print("=" * 60)
    print("Testing Zoho Agent with Real API")
    print("=" * 60)
    
    # Test 1: List all invoices
    print("\n" + "=" * 60)
    print("Test 1: List All Invoices")
    print("=" * 60)
    
    state = AgentState(
        task_description="Show me all invoices",
        plan_id="test-plan-1",
        messages=[],
        current_agent="Zoho Invoice",
        websocket_manager=None
    )
    
    result = await zoho_agent_node(state)
    print(result["final_result"])
    
    # Test 2: List customers
    print("\n" + "=" * 60)
    print("Test 2: List Customers")
    print("=" * 60)
    
    state = AgentState(
        task_description="Show me all customers",
        plan_id="test-plan-2",
        messages=[],
        current_agent="Zoho Invoice",
        websocket_manager=None
    )
    
    result = await zoho_agent_node(state)
    print(result["final_result"])
    
    # Test 3: Filter by status
    print("\n" + "=" * 60)
    print("Test 3: Filter Unpaid Invoices")
    print("=" * 60)
    
    state = AgentState(
        task_description="Show me unpaid invoices",
        plan_id="test-plan-3",
        messages=[],
        current_agent="Zoho Invoice",
        websocket_manager=None
    )
    
    result = await zoho_agent_node(state)
    print(result["final_result"])
    
    print("\n" + "=" * 60)
    print("Testing Complete")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_agent())
