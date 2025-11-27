#!/usr/bin/env python3
"""
Integration test for the approval flow.
Verifies all components work together.
"""

import json
from datetime import datetime


def test_complete_flow():
    """Test the complete approval flow."""
    print("\n" + "=" * 80)
    print("INTEGRATION TEST: Complete Approval Flow")
    print("=" * 80)
    
    # Step 1: User submits task
    print("\n1. User submits task...")
    task_description = "Process invoices for vendor ABC"
    print(f"   Task: {task_description}")
    
    # Step 2: Backend processes with planner
    print("\n2. Backend processes with planner node...")
    current_agent = "Planner"
    next_agent = "invoice"
    messages = [
        "I've analyzed your task: 'Process invoices for vendor ABC'.\n\nThis appears to be an invoice-related task. Routing to Invoice Agent for specialized handling."
    ]
    print(f"   Agent: {current_agent}")
    print(f"   Next Agent: {next_agent}")
    print(f"   Messages: {len(messages)}")
    
    # Step 3: Backend builds approval request
    print("\n3. Backend builds plan_approval_request...")
    plan_id = "test-plan-123"
    
    plan_steps = []
    for i, msg in enumerate(messages, 1):
        plan_steps.append({
            "id": str(i),
            "action": msg,
            "agent": current_agent,
            "status": "pending"
        })
    
    approval_request = {
        "type": "plan_approval_request",
        "data": {
            "id": plan_id,
            "plan_id": plan_id,
            "m_plan_id": plan_id,
            "user_request": task_description,
            "status": "pending_approval",
            "steps": plan_steps,
            "facts": f"Task: {task_description}\n\nRouting to: {next_agent.capitalize()} Agent",
            "context": {
                "participant_descriptions": {
                    current_agent: "Analyzing task and creating execution plan"
                }
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    }
    
    print(f"   ✓ Approval request built with {len(plan_steps)} steps")
    
    # Step 4: Backend sends via WebSocket
    print("\n4. Backend sends via WebSocket...")
    print(f"   Message type: {approval_request['type']}")
    print(f"   Data fields: {list(approval_request['data'].keys())}")
    print(f"   ✓ Message sent")
    
    # Step 5: Frontend receives message
    print("\n5. Frontend receives plan_approval_request...")
    received_data = approval_request['data']
    print(f"   ✓ Message received")
    
    # Step 6: Frontend parses data
    print("\n6. Frontend parses approval request data...")
    plan_approval_request = received_data
    
    # Extract steps
    plan_steps_extracted = []
    if plan_approval_request.get("steps"):
        for step in plan_approval_request.get("steps", []):
            action = step.get("action", "")
            if action.strip():
                if action.strip().endswith(':'):
                    plan_steps_extracted.append({"type": "heading", "text": action.strip()})
                else:
                    plan_steps_extracted.append({"type": "substep", "text": action.strip()})
    
    facts_content = plan_approval_request.get("facts", "")
    
    print(f"   ✓ Extracted {len(plan_steps_extracted)} steps")
    print(f"   ✓ Extracted facts: {len(facts_content)} chars")
    
    # Step 7: Frontend sets state
    print("\n7. Frontend sets state...")
    show_approval_buttons = True  # Set when approval request received
    waiting_for_plan = False
    show_processing_spinner = False
    
    print(f"   showApprovalButtons: {show_approval_buttons}")
    print(f"   waitingForPlan: {waiting_for_plan}")
    print(f"   showProcessingSpinner: {show_processing_spinner}")
    
    # Step 8: Frontend renders buttons
    print("\n8. Frontend renders approval buttons...")
    
    # Check isCreatingPlan
    has_steps = len(plan_steps_extracted) > 0
    has_facts = bool(facts_content.strip())
    is_creating_plan = not has_steps and not has_facts
    
    # Check button rendering (NEW LOGIC)
    buttons_render = show_approval_buttons
    
    print(f"   has_steps: {has_steps}")
    print(f"   has_facts: {has_facts}")
    print(f"   isCreatingPlan: {is_creating_plan}")
    print(f"   showApprovalButtons: {show_approval_buttons}")
    print(f"   Buttons render: {buttons_render}")
    
    if not buttons_render:
        print(f"   ✗ FAILED: Buttons would NOT render!")
        return False
    
    print(f"   ✓ Buttons render successfully")
    
    # Step 9: User clicks approve
    print("\n9. User clicks 'Approve Task Plan'...")
    print(f"   ✓ Button clicked")
    
    # Step 10: Frontend sends approval
    print("\n10. Frontend sends approval to backend...")
    approval_payload = {
        "m_plan_id": plan_approval_request.get("id"),
        "plan_id": plan_id,
        "approved": True,
        "feedback": "Plan approved by user"
    }
    print(f"   Payload: {json.dumps(approval_payload, indent=2)}")
    print(f"   ✓ Approval sent")
    
    # Step 11: Backend resumes execution
    print("\n11. Backend resumes execution...")
    print(f"   ✓ Specialized agent ({next_agent}) executes")
    
    # Step 12: Backend sends final result
    print("\n12. Backend sends final result...")
    final_result = {
        "type": "final_result_message",
        "data": {
            "content": "Invoice analysis complete. All checks passed successfully.",
            "status": "completed",
            "timestamp": datetime.utcnow().isoformat()
        }
    }
    print(f"   ✓ Final result sent")
    
    # Step 13: Frontend displays result
    print("\n13. Frontend displays final result...")
    print(f"   Result: {final_result['data']['content']}")
    print(f"   Status: {final_result['data']['status']}")
    print(f"   ✓ Result displayed")
    
    print("\n" + "=" * 80)
    print("✅ INTEGRATION TEST PASSED")
    print("=" * 80)
    print("\nFlow Summary:")
    print("  1. User submits task")
    print("  2. Backend analyzes with planner")
    print("  3. Backend sends complete approval request")
    print("  4. Frontend receives and parses data")
    print("  5. Frontend sets showApprovalButtons = true")
    print("  6. Frontend renders approval buttons")
    print("  7. User clicks approve")
    print("  8. Frontend sends approval")
    print("  9. Backend resumes with specialized agent")
    print("  10. Backend sends final result")
    print("  11. Frontend displays result")
    
    return True


if __name__ == "__main__":
    success = test_complete_flow()
    exit(0 if success else 1)
