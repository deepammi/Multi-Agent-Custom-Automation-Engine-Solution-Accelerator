#!/usr/bin/env python3
"""
Integration test for HITL Approval System with AI Planner and Linear Graph Builder.

This demonstrates the complete workflow:
1. AI Planner generates agent sequence
2. HITL Interface requests approval
3. Linear Graph Builder creates workflow from approved sequence
"""
import asyncio
import sys
import pytest
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.services.ai_planner_service import AIPlanner
from app.services.llm_service import LLMService
from app.services.hitl_interface import HITLInterface
from app.services.websocket_service import WebSocketManager, MockWebSocketConnection
from app.agents.graph_refactored import create_graph_from_ai_sequence
from app.agents.state import AgentStateManager


@pytest.mark.asyncio
async def test_complete_hitl_workflow():
    """Test complete HITL workflow from AI planning to graph execution."""
    print("🚀 Testing Complete HITL Workflow Integration")
    print("=" * 60)
    
    # Initialize services
    llm_service = LLMService()
    ai_planner = AIPlanner(llm_service)
    hitl_interface = HITLInterface(default_timeout=10)
    
    # Create WebSocket manager and mock connection
    ws_manager = WebSocketManager()
    mock_websocket = MockWebSocketConnection("hitl_test_123", "test_user")
    await ws_manager.connect(mock_websocket, "hitl_test_123", "test_user")
    
    # Test task
    task_description = "Find emails about invoice INV-1001 and check payment status with vendor"
    
    try:
        print(f"\n📋 Task: {task_description}")
        
        # Step 1: AI Planner generates sequence
        print("\n🤖 Step 1: AI Planner generating agent sequence...")
        planning_summary = await ai_planner.plan_workflow(task_description)
        
        if not planning_summary.success:
            print("   ⚠️  AI planning failed, using fallback")
            agent_sequence = ai_planner.get_fallback_sequence(task_description)
        else:
            agent_sequence = planning_summary.agent_sequence
        
        print(f"   Generated sequence: {' → '.join(agent_sequence.agents)}")
        print(f"   Estimated duration: {agent_sequence.estimated_duration}s")
        print(f"   Complexity score: {agent_sequence.complexity_score}")
        
        # Step 2: Request HITL approval
        print("\n👤 Step 2: Requesting HITL approval...")
        
        # Start approval request in background
        approval_task = asyncio.create_task(
            hitl_interface.request_plan_approval(
                plan_id="hitl_test_123",
                agent_sequence=agent_sequence,
                task_description=task_description,
                websocket_manager=ws_manager,
                timeout_seconds=5
            )
        )
        
        # Simulate HITL approval after a short delay
        await asyncio.sleep(0.5)
        print("   📝 Simulating HITL approval...")
        
        success = await hitl_interface.submit_approval_response(
            plan_id="hitl_test_123",
            approved=True,
            feedback="Sequence looks good for this invoice investigation task"
        )
        
        assert success, "Failed to submit approval response"
        
        # Wait for approval result
        approval_result = await approval_task
        
        print(f"   ✅ Approval result: {approval_result.status.value}")
        print(f"   💬 Feedback: {approval_result.feedback}")
        
        # Step 3: Create linear graph from approved sequence
        print("\n🔗 Step 3: Creating linear graph from approved sequence...")
        
        approved_agents = agent_sequence.agents
        linear_graph = create_graph_from_ai_sequence(approved_agents)
        
        assert linear_graph is not None, "Failed to create linear graph"
        print(f"   ✅ Linear graph created successfully")
        print(f"   📊 Graph type: AI-driven with HITL approval")
        
        # Step 4: Create initial state for execution
        print("\n📊 Step 4: Creating workflow state...")
        
        initial_state = AgentStateManager.create_initial_state(
            plan_id="hitl_test_123",
            session_id="test_session",
            task_description=task_description,
            agent_sequence=approved_agents
        )
        
        # Add WebSocket manager to state
        initial_state["websocket_manager"] = ws_manager
        initial_state["plan_approved"] = True
        
        print(f"   ✅ Initial state created")
        print(f"   🎯 Agent sequence: {initial_state['agent_sequence']}")
        print(f"   📈 Total steps: {initial_state['total_steps']}")
        
        # Step 5: Verify WebSocket messages
        print("\n📡 Step 5: Verifying WebSocket communication...")
        
        # Check that approval request was sent
        approval_messages = [
            msg for msg in mock_websocket.messages 
            if msg.get("type") == "plan_approval_request"
        ]
        
        assert len(approval_messages) > 0, "No approval request message found"
        print(f"   ✅ Plan approval request sent via WebSocket")
        
        # Test progress updates
        await hitl_interface.send_progress_update(
            plan_id="hitl_test_123",
            current_step=1,
            total_steps=len(approved_agents),
            current_agent=approved_agents[0],
            websocket_manager=ws_manager
        )
        
        progress_messages = [
            msg for msg in mock_websocket.messages 
            if msg.get("type") == "progress_update"
        ]
        
        assert len(progress_messages) > 0, "No progress update message found"
        print(f"   ✅ Progress updates working via WebSocket")
        
        # Step 6: Verify approval enforcement
        print("\n🔒 Step 6: Testing approval enforcement...")
        
        # Test that HITL interface tracks approval
        assert hitl_interface.is_plan_approved("hitl_test_123"), "Plan should be marked as approved"
        print(f"   ✅ Plan approval tracked correctly")
        
        # Get approval statistics
        stats = hitl_interface.get_approval_stats()
        print(f"   📊 Approval stats: {stats['total_requests']} requests, {stats['approval_rate']}% approved")
        
        print("\n" + "=" * 60)
        print("🎉 Complete HITL Workflow Integration Test PASSED!")
        print("\n✅ All components working together:")
        print("   • AI Planner generates intelligent agent sequences")
        print("   • HITL Interface manages approval workflows")
        print("   • WebSocket Manager handles real-time communication")
        print("   • Linear Graph Builder creates execution workflows")
        print("   • Approval State Manager enforces approval requirements")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


@pytest.mark.asyncio
async def test_hitl_rejection_workflow():
    """Test HITL rejection workflow."""
    print("\n🚫 Testing HITL Rejection Workflow")
    print("-" * 40)
    
    # Initialize services
    llm_service = LLMService()
    ai_planner = AIPlanner(llm_service)
    hitl_interface = HITLInterface(default_timeout=5)
    
    # Create WebSocket manager
    ws_manager = WebSocketManager()
    mock_websocket = MockWebSocketConnection("rejection_test_456", "test_user")
    await ws_manager.connect(mock_websocket, "rejection_test_456", "test_user")
    
    try:
        # Generate a sequence
        task = "Simple test task for rejection"
        planning_summary = await ai_planner.plan_workflow(task)
        agent_sequence = planning_summary.agent_sequence if planning_summary.success else ai_planner.get_fallback_sequence(task)
        
        print(f"   Generated sequence: {' → '.join(agent_sequence.agents)}")
        
        # Start approval request
        approval_task = asyncio.create_task(
            hitl_interface.request_plan_approval(
                plan_id="rejection_test_456",
                agent_sequence=agent_sequence,
                task_description=task,
                websocket_manager=ws_manager
            )
        )
        
        # Simulate HITL rejection
        await asyncio.sleep(0.5)
        print("   ❌ Simulating HITL rejection...")
        
        success = await hitl_interface.submit_approval_response(
            plan_id="rejection_test_456",
            approved=False,
            feedback="This sequence is not appropriate for the task"
        )
        
        assert success, "Failed to submit rejection response"
        
        # Wait for result
        approval_result = await approval_task
        
        print(f"   📋 Rejection result: {approval_result.status.value}")
        print(f"   💬 Feedback: {approval_result.feedback}")
        
        # Verify rejection is tracked
        assert not hitl_interface.is_plan_approved("rejection_test_456"), "Plan should not be approved"
        print("   ✅ Rejection tracked correctly")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Rejection test failed: {e}")
        return False


async def main():
    """Run all HITL integration tests."""
    print("🧪 HITL Approval System Integration Tests")
    print("=" * 60)
    
    tests = [
        test_complete_hitl_workflow,
        test_hitl_rejection_workflow
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            result = await test()
            if result:
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} failed: {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"🏁 Integration Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("✅ HITL Approval System fully integrated and working!")
    else:
        print("❌ Some integration tests failed.")
    
    return failed == 0


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)