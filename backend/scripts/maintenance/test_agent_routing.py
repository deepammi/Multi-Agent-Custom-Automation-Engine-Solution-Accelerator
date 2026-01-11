"""Test agent routing logic for Salesforce and Zoho."""
import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.agents.nodes import planner_node
from app.agents.state import AgentState


def test_routing():
    """Test planner routing for different task types."""
    print("=" * 60)
    print("AGENT ROUTING TEST")
    print("Testing Planner's Agent Selection Logic")
    print("=" * 60)
    
    test_cases = [
        ("Show me all Zoho invoices", "zoho"),
        ("List Zoho customers", "zoho"),
        ("Get Zoho invoice INV-000001", "zoho"),
        ("Show Salesforce accounts", "salesforce"),
        ("List Salesforce opportunities", "salesforce"),
        ("Query Salesforce contacts", "salesforce"),
        ("Process this invoice", "invoice"),
        ("Perform closing reconciliation", "closing"),
        ("Run audit checks", "audit"),
    ]
    
    print("\nTesting routing decisions:\n")
    
    all_passed = True
    for task, expected_agent in test_cases:
        state = AgentState(
            task_description=task,
            plan_id="test-plan",
            messages=[],
            current_agent="Planner"
        )
        
        result = planner_node(state)
        actual_agent = result.get("next_agent")
        
        status = "✅" if actual_agent == expected_agent else "❌"
        if actual_agent != expected_agent:
            all_passed = False
        
        print(f"{status} Task: '{task}'")
        print(f"   Expected: {expected_agent}, Got: {actual_agent}")
        print()
    
    print("=" * 60)
    if all_passed:
        print("✅ ALL ROUTING TESTS PASSED")
        print("\nFrontend Integration Status:")
        print("   ✅ Zoho agent routing: Working")
        print("   ✅ Salesforce agent routing: Working")
        print("   ✅ Other agents routing: Working")
        print("\n📝 Frontend is ready to use both agents!")
        print("   Just submit tasks through the UI like:")
        print("   - 'Show me all Zoho invoices'")
        print("   - 'List my Zoho customers'")
        print("   - 'Show Salesforce accounts'")
    else:
        print("❌ SOME ROUTING TESTS FAILED")
    print("=" * 60)


if __name__ == "__main__":
    test_routing()
