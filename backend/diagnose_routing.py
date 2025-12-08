"""Diagnose routing issues."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.agents.nodes import planner_node
from app.agents.state import AgentState

# Test tasks
test_tasks = [
    "Show me invoices from Zoho",
    "List Zoho customers",
    "Get Zoho invoice INV-001",
    "Show me recent invoices",  # Should go to invoice agent
    "List invoices",  # Should go to invoice agent
]

print("\n" + "="*60)
print("Routing Diagnosis")
print("="*60 + "\n")

for task in test_tasks:
    state: AgentState = {
        "messages": [],
        "plan_id": "test",
        "session_id": "test",
        "task_description": task,
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
    
    result = planner_node(state)
    next_agent = result.get("next_agent")
    
    print(f"Task: {task}")
    print(f"  → Routes to: {next_agent}")
    print(f"  → Response: {result.get('messages', [''])[0][:80]}...")
    print()

print("="*60)
print("\nExpected Routing:")
print("  • Tasks with 'zoho' → zoho agent")
print("  • Tasks with 'invoice' (no 'zoho') → invoice agent")
print("  • Tasks with 'salesforce' → salesforce agent")
print("="*60 + "\n")
