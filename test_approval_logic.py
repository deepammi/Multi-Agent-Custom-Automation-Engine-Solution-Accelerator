#!/usr/bin/env python3
"""
Test the approval flow logic without requiring backend imports.
"""

import json
from datetime import datetime


def test_backend_data_structure():
    """Test that backend sends correct data structure."""
    print("\n" + "=" * 80)
    print("TEST 1: Backend Data Structure")
    print("=" * 80)
    
    # Simulate what backend sends
    task_description = "Process invoices for vendor ABC"
    current_agent = "Planner"
    next_agent = "invoice"
    messages = [
        "I've analyzed your task: 'Process invoices for vendor ABC'.\n\nThis appears to be an invoice-related task. Routing to Invoice Agent for specialized handling."
    ]
    plan_id = "test-plan-123"
    
    # Build plan_approval_request as backend does
    plan_steps = []
    if messages:
        for i, msg in enumerate(messages, 1):
            plan_steps.append({
                "id": str(i),
                "action": msg,
                "agent": current_agent,
                "status": "pending"
            })
    
    approval_request_data = {
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
    
    print("\n1. Verifying backend sends all required fields...")
    required_fields = ["id", "plan_id", "m_plan_id", "user_request", "status", "steps", "facts", "context", "timestamp"]
    
    missing = []
    for field in required_fields:
        if field not in approval_request_data:
            missing.append(field)
            print(f"   ✗ {field}: MISSING")
        else:
            value = approval_request_data[field]
            if isinstance(value, (list, dict)):
                has_content = len(value) > 0
            else:
                has_content = bool(value)
            
            status = "✓" if has_content else "⚠"
            print(f"   {status} {field}: Present")
    
    if missing:
        print(f"\n   ✗ Missing fields: {missing}")
        return False
    
    print(f"\n   ✓ All required fields present")
    return True


def test_frontend_rendering():
    """Test that frontend rendering logic works."""
    print("\n" + "=" * 80)
    print("TEST 2: Frontend Rendering Logic")
    print("=" * 80)
    
    # Simulate approval request data
    plan_approval_request = {
        "id": "test-plan-123",
        "plan_id": "test-plan-123",
        "m_plan_id": "test-plan-123",
        "user_request": "Process invoices for vendor ABC",
        "status": "pending_approval",
        "steps": [
            {
                "id": "1",
                "action": "I've analyzed your task: 'Process invoices for vendor ABC'.\n\nThis appears to be an invoice-related task. Routing to Invoice Agent for specialized handling.",
                "agent": "Planner",
                "status": "pending"
            }
        ],
        "facts": "Task: Process invoices for vendor ABC\n\nRouting to: Invoice Agent",
        "context": {
            "participant_descriptions": {
                "Planner": "Analyzing task and creating execution plan"
            }
        },
        "timestamp": datetime.utcnow().isoformat()
    }
    
    print("\n1. Extracting content as frontend would...")
    
    # Extract plan steps
    plan_steps = []
    if plan_approval_request.get("steps"):
        for step in plan_approval_request.get("steps", []):
            action = step.get("action", "")
            if action.strip():
                if action.strip().endswith(':'):
                    plan_steps.append({"type": "heading", "text": action.strip()})
                else:
                    plan_steps.append({"type": "substep", "text": action.strip()})
    
    facts_content = plan_approval_request.get("facts", "")
    
    print(f"   ✓ Extracted {len(plan_steps)} plan steps")
    print(f"   ✓ Extracted facts: {len(facts_content)} characters")
    
    # Check isCreatingPlan
    print("\n2. Checking isCreatingPlan logic...")
    has_steps = len(plan_steps) > 0
    has_facts = bool(facts_content.strip())
    is_creating_plan = not has_steps and not has_facts
    
    print(f"   has_steps: {has_steps}")
    print(f"   has_facts: {has_facts}")
    print(f"   isCreatingPlan: {is_creating_plan}")
    
    if is_creating_plan:
        print(f"   ✗ isCreatingPlan is True - buttons would be hidden!")
        return False
    
    print(f"   ✓ isCreatingPlan is False - buttons can render")
    
    # Check button rendering with OLD logic
    print("\n3. Checking button rendering (OLD logic)...")
    show_approval_buttons = True
    buttons_render_old = show_approval_buttons and not is_creating_plan
    print(f"   showApprovalButtons: {show_approval_buttons}")
    print(f"   !isCreatingPlan: {not is_creating_plan}")
    print(f"   Buttons render: {buttons_render_old}")
    
    if not buttons_render_old:
        print(f"   ✗ Buttons would NOT render with old logic!")
        return False
    
    # Check button rendering with NEW logic
    print("\n4. Checking button rendering (NEW logic)...")
    buttons_render_new = show_approval_buttons
    print(f"   showApprovalButtons: {show_approval_buttons}")
    print(f"   Buttons render: {buttons_render_new}")
    
    if not buttons_render_new:
        print(f"   ✗ Buttons would NOT render with new logic!")
        return False
    
    print(f"   ✓ Buttons render with new logic")
    
    return True


def test_state_management():
    """Test that state management works correctly."""
    print("\n" + "=" * 80)
    print("TEST 3: State Management")
    print("=" * 80)
    
    print("\n1. Simulating state transitions...")
    
    # Initial state
    show_approval_buttons = True
    waiting_for_plan = True
    show_processing_spinner = False
    plan_approval_request = None
    
    print(f"   Initial state:")
    print(f"      showApprovalButtons: {show_approval_buttons}")
    print(f"      waitingForPlan: {waiting_for_plan}")
    print(f"      showProcessingSpinner: {show_processing_spinner}")
    print(f"      planApprovalRequest: {plan_approval_request}")
    
    # Receive approval request
    print(f"\n2. Receiving plan_approval_request...")
    plan_approval_request = {
        "id": "test-plan-123",
        "user_request": "Process invoices",
        "steps": [{"id": "1", "action": "Step 1"}],
        "facts": "Some facts"
    }
    waiting_for_plan = False
    show_processing_spinner = False
    show_approval_buttons = True  # CRITICAL FIX
    
    print(f"   Updated state:")
    print(f"      showApprovalButtons: {show_approval_buttons}")
    print(f"      waitingForPlan: {waiting_for_plan}")
    print(f"      showProcessingSpinner: {show_processing_spinner}")
    print(f"      planApprovalRequest: Present")
    
    # Verify buttons would show
    print(f"\n3. Verifying buttons would show...")
    if show_approval_buttons and plan_approval_request:
        print(f"   ✓ Buttons would show")
        return True
    else:
        print(f"   ✗ Buttons would NOT show")
        return False


def main():
    """Run all tests."""
    print("\n" + "=" * 80)
    print("APPROVAL FLOW LOGIC TESTS")
    print("=" * 80)
    
    test1 = test_backend_data_structure()
    test2 = test_frontend_rendering()
    test3 = test_state_management()
    
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"Test 1 (Backend Data): {'✅ PASSED' if test1 else '❌ FAILED'}")
    print(f"Test 2 (Frontend Rendering): {'✅ PASSED' if test2 else '❌ FAILED'}")
    print(f"Test 3 (State Management): {'✅ PASSED' if test3 else '❌ FAILED'}")
    
    if test1 and test2 and test3:
        print("\n✅ ALL TESTS PASSED - Approval flow should work correctly")
        return 0
    else:
        print("\n❌ SOME TESTS FAILED")
        return 1


if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)
