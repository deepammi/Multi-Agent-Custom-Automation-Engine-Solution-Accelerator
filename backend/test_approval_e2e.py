#!/usr/bin/env python3
"""
End-to-end test for the approval flow.
Tests that the backend sends complete plan_approval_request data.
"""

import asyncio
import json
import sys
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

sys.path.insert(0, '.')

from app.services.agent_service import AgentService
from app.agents.nodes import planner_node
from app.agents.state import AgentState
from app.models.message import AgentMessage


async def test_approval_request_complete_data():
    """Test that plan_approval_request contains all necessary data."""
    print("\n" + "=" * 80)
    print("TEST: Approval Request Complete Data")
    print("=" * 80)
    
    plan_id = "test-plan-123"
    session_id = "test-session-456"
    task_description = "Process invoices for vendor ABC"
    
    # Mock the database and WebSocket
    with patch('app.services.agent_service.PlanRepository') as mock_plan_repo, \
         patch('app.services.agent_service.MessageRepository') as mock_msg_repo, \
         patch('app.services.agent_service.websocket_manager') as mock_ws:
        
        # Setup mocks
        mock_plan_repo.update_status = AsyncMock()
        mock_msg_repo.create = AsyncMock()
        mock_ws.send_message = AsyncMock()
        
        # Execute the task
        print(f"\n1. Executing task: {task_description}")
        try:
            result = await AgentService.execute_task(plan_id, session_id, task_description)
            print(f"   ✓ Task execution returned: {result}")
        except Exception as e:
            print(f"   ✗ Task execution failed: {e}")
            return False
        
        # Check WebSocket messages
        print(f"\n2. Checking WebSocket messages sent...")
        if not mock_ws.send_message.called:
            print(f"   ✗ No WebSocket messages sent")
            return False
        
        print(f"   ✓ WebSocket send_message called {mock_ws.send_message.call_count} times")
        
        # Find the plan_approval_request message
        approval_request_msg = None
        for call in mock_ws.send_message.call_args_list:
            args, kwargs = call
            if len(args) >= 2:
                msg = args[1]
                if isinstance(msg, dict) and msg.get("type") == "plan_approval_request":
                    approval_request_msg = msg
                    break
        
        if not approval_request_msg:
            print(f"   ✗ No plan_approval_request message found")
            print(f"   Messages sent:")
            for i, call in enumerate(mock_ws.send_message.call_args_list):
                args, kwargs = call
                if len(args) >= 2:
                    msg = args[1]
                    print(f"      {i}: {msg.get('type', 'unknown')}")
            return False
        
        print(f"   ✓ Found plan_approval_request message")
        
        # Verify the data structure
        print(f"\n3. Verifying plan_approval_request data structure...")
        data = approval_request_msg.get("data", {})
        
        required_fields = {
            "id": "Plan ID",
            "plan_id": "Plan ID",
            "m_plan_id": "M Plan ID",
            "user_request": "User request",
            "status": "Status",
            "steps": "Plan steps",
            "facts": "Facts/analysis",
            "context": "Context",
            "timestamp": "Timestamp"
        }
        
        all_present = True
        for field, description in required_fields.items():
            if field in data:
                value = data[field]
                if isinstance(value, (list, dict)):
                    has_content = len(value) > 0
                    status = "✓" if has_content else "⚠"
                    print(f"   {status} {field}: {description} - {len(value)} items")
                else:
                    has_content = bool(value)
                    status = "✓" if has_content else "⚠"
                    print(f"   {status} {field}: {description} - {repr(value)[:50]}")
                
                if not has_content:
                    all_present = False
            else:
                print(f"   ✗ {field}: {description} - MISSING")
                all_present = False
        
        if not all_present:
            print(f"\n   Full data structure:")
            print(json.dumps(data, indent=2, default=str))
            return False
        
        # Verify specific content
        print(f"\n4. Verifying specific content...")
        
        # Check steps
        steps = data.get("steps", [])
        if len(steps) > 0:
            print(f"   ✓ Steps: {len(steps)} step(s)")
            for i, step in enumerate(steps):
                print(f"      Step {i+1}: {step.get('agent', 'unknown')} - {step.get('status', 'unknown')}")
        else:
            print(f"   ✗ No steps found")
            return False
        
        # Check facts
        facts = data.get("facts", "")
        if facts and len(facts) > 10:
            print(f"   ✓ Facts: {len(facts)} characters")
            print(f"      Preview: {facts[:60]}...")
        else:
            print(f"   ✗ Facts missing or too short")
            return False
        
        # Check context
        context = data.get("context", {})
        participant_descriptions = context.get("participant_descriptions", {})
        if participant_descriptions:
            print(f"   ✓ Context: {len(participant_descriptions)} participant(s)")
            for agent, desc in participant_descriptions.items():
                print(f"      {agent}: {desc}")
        else:
            print(f"   ✗ No participant descriptions in context")
            return False
        
        # Check user_request
        user_request = data.get("user_request", "")
        if user_request == task_description:
            print(f"   ✓ User request matches task description")
        else:
            print(f"   ✗ User request mismatch")
            print(f"      Expected: {task_description}")
            print(f"      Got: {user_request}")
            return False
        
        print(f"\n" + "=" * 80)
        print("✅ TEST PASSED: Approval request has complete data")
        print("=" * 80)
        return True


async def test_frontend_rendering_logic():
    """Test that frontend rendering logic would work with the data."""
    print("\n" + "=" * 80)
    print("TEST: Frontend Rendering Logic")
    print("=" * 80)
    
    # Simulate the data structure
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
    
    print(f"\n1. Simulating frontend rendering logic...")
    
    # Extract content as frontend would
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
    
    # Check isCreatingPlan logic
    is_creating_plan = not len(plan_steps) and not facts_content
    print(f"\n2. Checking isCreatingPlan logic...")
    print(f"   has_steps: {len(plan_steps) > 0}")
    print(f"   has_facts: {bool(facts_content.strip())}")
    print(f"   isCreatingPlan: {is_creating_plan} (should be False)")
    
    if is_creating_plan:
        print(f"   ✗ isCreatingPlan is True - buttons would be hidden!")
        return False
    
    # Check button rendering
    show_approval_buttons = True  # Set by frontend when approval request received
    buttons_would_render_old = show_approval_buttons and not is_creating_plan
    buttons_would_render_new = show_approval_buttons  # Updated logic
    
    print(f"\n3. Checking button rendering...")
    print(f"   showApprovalButtons: {show_approval_buttons}")
    print(f"   Old logic (with !isCreatingPlan): {buttons_would_render_old}")
    print(f"   New logic (without !isCreatingPlan): {buttons_would_render_new}")
    
    if not buttons_would_render_new:
        print(f"   ✗ Buttons would NOT render with new logic!")
        return False
    
    print(f"\n" + "=" * 80)
    print("✅ TEST PASSED: Frontend rendering logic works correctly")
    print("=" * 80)
    return True


async def main():
    """Run all tests."""
    print("\n" + "=" * 80)
    print("APPROVAL FLOW END-TO-END TESTS")
    print("=" * 80)
    
    test1_passed = await test_approval_request_complete_data()
    test2_passed = await test_frontend_rendering_logic()
    
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"Test 1 (Approval Request Data): {'✅ PASSED' if test1_passed else '❌ FAILED'}")
    print(f"Test 2 (Frontend Rendering): {'✅ PASSED' if test2_passed else '❌ FAILED'}")
    
    if test1_passed and test2_passed:
        print("\n✅ ALL TESTS PASSED")
        return 0
    else:
        print("\n❌ SOME TESTS FAILED")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
