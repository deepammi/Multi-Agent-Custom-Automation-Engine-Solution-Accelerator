"""Test Zoho agent with specific invoice lookup."""
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


async def test_specific_invoice():
    """Test getting a specific invoice."""
    print("=" * 60)
    print("Testing Specific Invoice Lookup")
    print("=" * 60)
    
    state = AgentState(
        task_description="Show me invoice INV-000001",
        plan_id="test-plan-specific",
        messages=[],
        current_agent="Zoho Invoice",
        websocket_manager=None
    )
    
    result = await zoho_agent_node(state)
    print(result["final_result"])


if __name__ == "__main__":
    asyncio.run(test_specific_invoice())
