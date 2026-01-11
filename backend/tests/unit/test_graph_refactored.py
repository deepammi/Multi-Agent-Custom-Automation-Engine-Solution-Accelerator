"""Test refactored LangGraph workflow."""
import asyncio
import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.agents.graph_refactored import get_agent_graph
from app.agents.state import AgentState


async def test_graph_structure():
    """Test basic graph structure and routing."""
    print("=" * 60)
    print("Testing Refactored LangGraph Workflow")
    print("=" * 60)
    
    try:
        # Get graph
        print("\n1. Initializing graph...")
        graph = get_agent_graph()
        print(f"   ✅ Graph initialized: {type(graph).__name__}")
        
        # Check graph structure
        print("\n2. Checking graph structure...")
        nodes = list(graph.nodes.keys())
        print(f"   Nodes: {nodes}")
        print(f"   ✅ Found {len(nodes)} nodes")
        
        # Test with a simple state
        print("\n3. Testing graph execution...")
        initial_state = {
            "plan_id": "test-plan-001",
            "session_id": "test-session-001",
            "task_description": "List Zoho invoices",
            "messages": [],
            "current_agent": "",
            "next_agent": None,
            "final_result": "",
            "iteration_count": 0,
            "execution_history": [],
            "approval_required": False,
            "approved": None,
            "awaiting_user_input": False,
            "websocket_manager": None,
        }
        
        # Create config with thread ID
        config = {"configurable": {"thread_id": "test-thread-001"}}
        
        print("   Invoking graph with test state...")
        result = await graph.ainvoke(initial_state, config)
        
        print(f"\n   ✅ Graph executed successfully!")
        print(f"   Current agent: {result.get('current_agent', 'N/A')}")
        print(f"   Next agent: {result.get('next_agent', 'N/A')}")
        print(f"   Messages: {len(result.get('messages', []))} messages")
        
        if result.get('final_result'):
            print(f"\n   Final result preview:")
            preview = result['final_result'][:200]
            print(f"   {preview}...")
        
        print("\n" + "=" * 60)
        print("✅ All Graph Tests Passed!")
        print("=" * 60)
        print("\nGraph is ready for use!")
        print("Next step: Create workflow templates (Phase 3)")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


async def test_graph_routing():
    """Test routing to different agents."""
    print("\n" + "=" * 60)
    print("Testing Agent Routing")
    print("=" * 60)
    
    test_cases = [
        ("List Zoho invoices", "zoho"),
        ("Show Salesforce accounts", "salesforce"),
        ("Process invoice", "invoice"),
        ("Perform closing", "closing"),
        ("Run audit", "audit"),
    ]
    
    graph = get_agent_graph()
    
    for task, expected_agent in test_cases:
        print(f"\n  Task: '{task}'")
        
        initial_state = {
            "plan_id": f"test-{expected_agent}",
            "session_id": "test-session",
            "task_description": task,
            "messages": [],
            "current_agent": "",
            "websocket_manager": None,
        }
        
        config = {"configurable": {"thread_id": f"test-{expected_agent}"}}
        
        try:
            result = await graph.ainvoke(initial_state, config)
            actual_agent = result.get("current_agent", "unknown")
            
            # Check if routing worked
            if expected_agent.lower() in actual_agent.lower():
                print(f"  ✅ Routed to: {actual_agent}")
            else:
                print(f"  ⚠️  Expected: {expected_agent}, Got: {actual_agent}")
        except Exception as e:
            print(f"  ❌ Error: {e}")
    
    print("\n" + "=" * 60)
    print("Routing tests complete")
    print("=" * 60)


async def main():
    """Run all tests."""
    await test_graph_structure()
    await test_graph_routing()


if __name__ == "__main__":
    asyncio.run(main())
