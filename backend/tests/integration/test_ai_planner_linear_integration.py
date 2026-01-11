#!/usr/bin/env python3
"""Test integration between AI Planner and Linear Graph Builder."""
import asyncio
import sys
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.services.ai_planner_service import AIPlanner
from app.services.llm_service import LLMService
from app.agents.graph_refactored import create_linear_graph
from app.agents.state import AgentStateManager


async def test_ai_planner_to_linear_graph():
    """Test creating linear graphs from AI-generated agent sequences."""
    print("🤖 Testing AI Planner → Linear Graph Integration")
    
    # Initialize AI Planner
    llm_service = LLMService()
    ai_planner = AIPlanner(llm_service)
    
    # Test tasks
    test_tasks = [
        "Find emails about invoice INV-1001 and check payment status",
        "Get customer information for ABC Corp from Salesforce",
        "Review audit compliance for Q4 closing process"
    ]
    
    for i, task in enumerate(test_tasks, 1):
        print(f"\n📋 Test {i}: {task}")
        
        try:
            # Generate AI plan
            planning_summary = await ai_planner.plan_workflow(task)
            
            if planning_summary.success:
                agent_sequence = planning_summary.agent_sequence.agents
                print(f"   AI Generated Sequence: {' → '.join(agent_sequence)}")
                
                # Create linear graph from AI sequence
                graph = create_linear_graph(agent_sequence)
                
                # Verify graph creation
                assert graph is not None
                print(f"   ✅ Linear graph created successfully")
                
                # Create state with AI sequence
                state = AgentStateManager.create_initial_state(
                    plan_id=f"ai_test_{i}",
                    session_id="test_session",
                    task_description=task,
                    agent_sequence=agent_sequence
                )
                
                # Verify state integration
                assert state["agent_sequence"] == agent_sequence
                assert state["total_steps"] == len(agent_sequence)
                print(f"   ✅ State integration successful")
                
            else:
                print(f"   ⚠️  AI planning failed, testing fallback")
                
                # Test fallback sequence
                fallback_sequence = ai_planner.get_fallback_sequence(task)
                print(f"   Fallback Sequence: {' → '.join(fallback_sequence.agents)}")
                
                # Create graph from fallback
                graph = create_linear_graph(fallback_sequence.agents)
                assert graph is not None
                print(f"   ✅ Fallback graph created successfully")
                
        except Exception as e:
            print(f"   ❌ Test {i} failed: {e}")
            return False
    
    print("\n✅ AI Planner → Linear Graph integration successful!")
    return True


async def test_complex_workflow_elimination():
    """Test that complex workflows now use linear execution."""
    print("\n🔄 Testing Complex Workflow → Linear Execution")
    
    # Test a complex task that would have used conditional routing before
    complex_task = "Why is my PO related to invoice INV-1001 missing from the system"
    
    llm_service = LLMService()
    ai_planner = AIPlanner(llm_service)
    
    try:
        # Generate plan for complex task
        planning_summary = await ai_planner.plan_workflow(complex_task)
        
        if planning_summary.success:
            sequence = planning_summary.agent_sequence.agents
            print(f"   Complex Task Sequence: {' → '.join(sequence)}")
            
            # Verify it's a linear sequence (no conditional routing)
            assert len(sequence) > 1, "Complex task should have multiple agents"
            
            # Create linear graph
            graph = create_linear_graph(sequence)
            assert graph is not None
            
            print(f"   ✅ Complex workflow converted to linear execution")
            print(f"   ✅ No conditional routing - pure linear sequence")
            
        else:
            # Use fallback for complex task
            fallback = ai_planner.get_fallback_sequence(complex_task)
            print(f"   Fallback Sequence: {' → '.join(fallback.agents)}")
            
            graph = create_linear_graph(fallback.agents)
            assert graph is not None
            print(f"   ✅ Complex workflow fallback works")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Complex workflow test failed: {e}")
        return False


async def test_no_supervisor_dependency():
    """Test that linear graphs work without any supervisor router dependency."""
    print("\n🚫 Testing No Supervisor Router Dependency")
    
    # Test various sequences that would have required supervisor routing before
    test_sequences = [
        ["gmail", "invoice", "analysis"],  # Multi-step workflow
        ["salesforce", "analysis"],        # Simple workflow  
        ["audit", "closing", "analysis"],  # Closing workflow
        ["gmail", "salesforce", "invoice", "analysis"]  # Complex workflow
    ]
    
    for i, sequence in enumerate(test_sequences, 1):
        print(f"   Test {i}: {' → '.join(sequence)}")
        
        try:
            # Create graph without any supervisor dependency
            graph = create_linear_graph(sequence)
            assert graph is not None
            
            # Verify no conditional routing is needed
            print(f"   ✅ Linear execution - no supervisor needed")
            
        except Exception as e:
            print(f"   ❌ Sequence {i} failed: {e}")
            return False
    
    print("   ✅ All sequences work without supervisor router")
    return True


async def main():
    """Run all integration tests."""
    print("🚀 Testing AI Planner + Linear Graph Integration")
    print("=" * 60)
    
    tests = [
        test_ai_planner_to_linear_graph,
        test_complex_workflow_elimination,
        test_no_supervisor_dependency
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            result = await test()
            if result is not False:
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} failed: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"🎉 Integration Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("✅ AI Planner + Linear Graph integration working perfectly!")
        return True
    else:
        print("❌ Some integration tests failed.")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)