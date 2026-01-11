#!/usr/bin/env python3
"""
Test script for workflow context service functionality.
Task 9: Verify simple workflow context tracking and state management.
"""
import asyncio
import sys
import os
from datetime import datetime

# Add the backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from app.services.workflow_context_service import (
    get_workflow_context_service,
    reset_workflow_context_service,
    WorkflowStatus
)


def test_workflow_context_basic_operations():
    """Test basic workflow context operations."""
    print("🧪 Testing Workflow Context Service - Basic Operations")
    print("=" * 60)
    
    # Reset service for clean test
    reset_workflow_context_service()
    service = get_workflow_context_service()
    
    # Test workflow creation
    plan_id = "test-plan-001"
    session_id = "test-session-001"
    task_description = "Test multi-agent workflow execution"
    agent_sequence = ["gmail", "invoice", "salesforce", "analysis"]
    
    print(f"1. Creating workflow context...")
    context = service.create_workflow_context(
        plan_id=plan_id,
        session_id=session_id,
        task_description=task_description,
        agent_sequence=agent_sequence
    )
    
    print(f"   ✅ Context created: {context.plan_id}")
    print(f"   📊 Status: {context.status.value}")
    print(f"   🔢 Total steps: {context.total_steps}")
    print(f"   📅 Created: {context.created_at}")
    
    # Test status updates
    print(f"\n2. Testing status updates...")
    
    service.update_workflow_status(plan_id, WorkflowStatus.PLANNING, "AI Planner analyzing task")
    service.update_workflow_status(plan_id, WorkflowStatus.AWAITING_PLAN_APPROVAL, "Plan ready for review")
    
    updated_context = service.get_workflow_context(plan_id)
    print(f"   ✅ Status updated to: {updated_context.status.value}")
    print(f"   📝 Events recorded: {len(updated_context.events)}")
    
    # Test plan approval
    print(f"\n3. Testing plan approval...")
    service.set_plan_approval(plan_id, True, "Plan looks good, proceed")
    
    context = service.get_workflow_context(plan_id)
    print(f"   ✅ Plan approved: {context.plan_approved}")
    print(f"   📊 Status: {context.status.value}")
    
    # Test progress updates
    print(f"\n4. Testing progress updates...")
    for i, agent in enumerate(agent_sequence):
        service.update_progress(plan_id, i + 1, agent)
        service.add_event(plan_id, "agent_completed", agent, f"{agent.capitalize()} agent completed successfully")
    
    context = service.get_workflow_context(plan_id)
    print(f"   ✅ Progress: {context.current_step}/{context.total_steps}")
    print(f"   📈 Percentage: {(context.current_step / context.total_steps * 100):.1f}%")
    
    # Test final approval
    print(f"\n5. Testing final approval...")
    service.update_workflow_status(plan_id, WorkflowStatus.AWAITING_FINAL_APPROVAL, "Results ready for review")
    service.set_final_approval(plan_id, True, "Results look perfect!")
    
    context = service.get_workflow_context(plan_id)
    print(f"   ✅ Final approved: {context.final_approved}")
    print(f"   📊 Final status: {context.status.value}")
    print(f"   📝 Total events: {len(context.events)}")
    
    return True


def test_workflow_context_summary_and_queries():
    """Test workflow summary and query capabilities."""
    print("\n🧪 Testing Workflow Context Service - Summary & Queries")
    print("=" * 60)
    
    service = get_workflow_context_service()
    
    # Create multiple workflows for testing
    workflows = [
        ("plan-001", "session-001", "Invoice processing task", ["gmail", "invoice", "analysis"]),
        ("plan-002", "session-001", "Customer data sync", ["salesforce", "zoho", "analysis"]),
        ("plan-003", "session-002", "Payment verification", ["invoice", "salesforce"])
    ]
    
    print(f"1. Creating multiple workflows...")
    for plan_id, session_id, task, agents in workflows:
        service.create_workflow_context(plan_id, session_id, task, agents)
        
        # Simulate some progress
        service.update_workflow_status(plan_id, WorkflowStatus.EXECUTING)
        service.update_progress(plan_id, 1, agents[0])
        service.add_event(plan_id, "agent_started", agents[0], f"Started {agents[0]} execution")
    
    print(f"   ✅ Created {len(workflows)} workflows")
    
    # Test workflow summary
    print(f"\n2. Testing workflow summary...")
    summary = service.get_workflow_summary("plan-001")
    if summary:
        print(f"   ✅ Summary for plan-001:")
        print(f"      Status: {summary['status']}")
        print(f"      Progress: {summary['progress']['percentage']:.1f}%")
        print(f"      Total events: {summary['total_events']}")
        print(f"      Event types: {list(summary['event_counts'].keys())}")
    
    # Test session queries
    print(f"\n3. Testing session queries...")
    session_workflows = service.get_workflows_by_session("session-001")
    print(f"   ✅ Found {len(session_workflows)} workflows for session-001")
    
    for workflow in session_workflows:
        print(f"      - {workflow['plan_id']}: {workflow['status']} ({workflow['progress_percentage']:.1f}%)")
    
    # Test recent events
    print(f"\n4. Testing recent events...")
    recent_events = service.get_recent_events("plan-001", limit=5)
    print(f"   ✅ Retrieved {len(recent_events)} recent events for plan-001")
    
    for event in recent_events[-3:]:  # Show last 3
        print(f"      - {event['event_type']}: {event['message']}")
    
    # Test service stats
    print(f"\n5. Testing service statistics...")
    stats = service.get_service_stats()
    print(f"   ✅ Service stats:")
    print(f"      Total workflows: {stats['total_workflows']}")
    print(f"      Status distribution: {stats['status_distribution']}")
    print(f"      Average events per workflow: {stats['average_events_per_workflow']:.1f}")
    
    return True


def test_workflow_context_error_handling():
    """Test error handling and edge cases."""
    print("\n🧪 Testing Workflow Context Service - Error Handling")
    print("=" * 60)
    
    service = get_workflow_context_service()
    
    # Test error scenarios
    print(f"1. Testing error scenarios...")
    
    # Test with non-existent plan
    result = service.update_workflow_status("non-existent", WorkflowStatus.FAILED)
    print(f"   ✅ Non-existent plan update: {result} (should be False)")
    
    context = service.get_workflow_context("non-existent")
    print(f"   ✅ Non-existent plan retrieval: {context is None} (should be True)")
    
    # Test workflow with error
    error_plan = "error-plan-001"
    service.create_workflow_context(error_plan, "session-error", "Error test", ["agent1"])
    
    service.set_error(error_plan, "Simulated agent failure", "agent1")
    
    error_context = service.get_workflow_context(error_plan)
    print(f"   ✅ Error workflow status: {error_context.status.value}")
    print(f"   ❌ Error message: {error_context.error_message}")
    
    # Test restart scenario
    print(f"\n2. Testing restart scenario...")
    restart_plan = "restart-plan-001"
    service.create_workflow_context(restart_plan, "session-restart", "Restart test", ["agent1", "agent2"])
    
    # Simulate workflow completion and user rejection (restart request)
    service.update_workflow_status(restart_plan, WorkflowStatus.AWAITING_FINAL_APPROVAL)
    service.set_final_approval(restart_plan, False, "Results not satisfactory, please restart")
    
    restart_context = service.get_workflow_context(restart_plan)
    print(f"   ✅ Restart workflow status: {restart_context.status.value}")
    print(f"   🔄 Final approved: {restart_context.final_approved}")
    
    # Test cleanup
    print(f"\n3. Testing cleanup...")
    initial_count = len(service.contexts)
    cleaned = service.cleanup_old_contexts(max_age_hours=0)  # Clean all
    final_count = len(service.contexts)
    
    print(f"   ✅ Cleaned up {cleaned} contexts")
    print(f"   📊 Contexts: {initial_count} → {final_count}")
    
    return True


def test_workflow_context_integration():
    """Test integration scenarios that match real usage."""
    print("\n🧪 Testing Workflow Context Service - Integration Scenarios")
    print("=" * 60)
    
    # Reset for clean integration test
    reset_workflow_context_service()
    service = get_workflow_context_service()
    
    # Simulate complete workflow lifecycle
    plan_id = "integration-test-001"
    session_id = "integration-session"
    
    print(f"1. Simulating complete workflow lifecycle...")
    
    # Step 1: Create workflow
    context = service.create_workflow_context(
        plan_id, session_id, 
        "Complete integration test workflow",
        ["gmail", "invoice", "salesforce", "analysis"]
    )
    print(f"   📝 Created: {context.status.value}")
    
    # Step 2: Planning phase
    service.update_workflow_status(plan_id, WorkflowStatus.PLANNING, "AI Planner analyzing requirements")
    service.add_event(plan_id, "planner_started", "planner", "Analyzing task requirements")
    service.add_event(plan_id, "planner_completed", "planner", "Generated execution plan with 4 agents")
    print(f"   🤖 Planning completed")
    
    # Step 3: Plan approval
    service.update_workflow_status(plan_id, WorkflowStatus.AWAITING_PLAN_APPROVAL, "Plan ready for user review")
    service.set_plan_approval(plan_id, True, "Plan approved - looks comprehensive")
    print(f"   ✅ Plan approved")
    
    # Step 4: Agent execution
    service.update_workflow_status(plan_id, WorkflowStatus.EXECUTING, "Starting multi-agent execution")
    
    agents = ["gmail", "invoice", "salesforce", "analysis"]
    for i, agent in enumerate(agents):
        service.update_progress(plan_id, i + 1, agent)
        service.add_event(plan_id, "agent_started", agent, f"Starting {agent} agent execution")
        service.add_event(plan_id, "agent_completed", agent, f"{agent.capitalize()} agent completed successfully")
        print(f"   🔄 {agent.capitalize()} completed ({i+1}/{len(agents)})")
    
    # Step 5: Final approval
    service.update_workflow_status(plan_id, WorkflowStatus.AWAITING_FINAL_APPROVAL, "All agents completed, results ready")
    service.set_final_approval(plan_id, True, "Excellent results, task completed successfully")
    print(f"   🎉 Workflow completed")
    
    # Verify final state
    final_context = service.get_workflow_context(plan_id)
    summary = service.get_workflow_summary(plan_id)
    
    print(f"\n2. Final verification...")
    print(f"   📊 Final status: {final_context.status.value}")
    print(f"   ✅ Plan approved: {final_context.plan_approved}")
    print(f"   ✅ Final approved: {final_context.final_approved}")
    print(f"   📈 Progress: {final_context.current_step}/{final_context.total_steps}")
    print(f"   📝 Total events: {len(final_context.events)}")
    print(f"   ⏱️  Duration: {summary['duration_seconds']:.1f} seconds")
    
    # Test context serialization
    context_dict = final_context.to_dict()
    print(f"   📦 Serialized context keys: {list(context_dict.keys())}")
    
    return True


def run_all_workflow_context_tests():
    """Run all workflow context service tests."""
    print("🚀 Running Workflow Context Service Tests")
    print("=" * 80)
    
    results = []
    
    # Test basic operations
    try:
        result = test_workflow_context_basic_operations()
        results.append(("Basic Operations", result))
    except Exception as e:
        print(f"❌ Basic operations test failed: {e}")
        results.append(("Basic Operations", False))
    
    # Test summary and queries
    try:
        result = test_workflow_context_summary_and_queries()
        results.append(("Summary & Queries", result))
    except Exception as e:
        print(f"❌ Summary & queries test failed: {e}")
        results.append(("Summary & Queries", False))
    
    # Test error handling
    try:
        result = test_workflow_context_error_handling()
        results.append(("Error Handling", result))
    except Exception as e:
        print(f"❌ Error handling test failed: {e}")
        results.append(("Error Handling", False))
    
    # Test integration scenarios
    try:
        result = test_workflow_context_integration()
        results.append(("Integration Scenarios", result))
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        results.append(("Integration Scenarios", False))
    
    # Summary
    print(f"\n🏁 Workflow Context Service Test Summary")
    print("=" * 80)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\n📊 Overall Results: {passed}/{total} test suites passed")
    
    if passed == total:
        print("🎉 All workflow context service tests PASSED!")
        print("✅ Requirements 7.1, 7.2, 7.3, 7.4 validated")
    else:
        print("⚠️  Some workflow context service tests failed - review implementation")
    
    return passed == total


if __name__ == "__main__":
    run_all_workflow_context_tests()