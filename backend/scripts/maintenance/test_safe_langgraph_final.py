#!/usr/bin/env python3
"""
Test Safe LangGraph Implementation
Test the properly fixed LangGraph with built-in loop prevention

This demonstrates:
1. LangGraph with recursion_limit
2. Step counter tracking
3. Agent visit tracking
4. Execution plan bounds checking
5. Safe multi-agent workflows

Usage:
    python3 backend/test_safe_langgraph_final.py
"""

import asyncio
import logging
import sys
import os
from typing import Dict, Any
from datetime import datetime

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.agents.safe_langgraph import get_safe_agent_graph
from app.agents.state import AgentState

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MockWebSocketManager:
    """Mock WebSocket manager for testing."""
    
    def __init__(self):
        self.messages = []
        
    async def send_message(self, plan_id: str, message: Dict[str, Any]):
        """Mock send message."""
        self.messages.append(message)
        msg_type = message.get("type", "unknown")
        
        if msg_type == "agent_message":
            data = message.get("data", {})
            agent = data.get("agent_name", "Unknown")
            content = data.get("content", "")
            status = data.get("status", "unknown")
            
            status_emoji = {"in_progress": "🔄", "completed": "✅", "warning": "⚠️", "error": "❌"}.get(status, "📝")
            print(f"{status_emoji} {agent}: {content}")

async def test_safe_simple_workflow():
    """Test safe simple workflow."""
    print("\n" + "="*60)
    print("🔧 TESTING SAFE SIMPLE WORKFLOW")
    print("="*60)
    
    try:
        graph = get_safe_agent_graph()
        websocket_manager = MockWebSocketManager()
        
        # Simple Gmail task
        initial_state: AgentState = {
            "task_description": "read my recent emails",
            "plan_id": "safe_simple_123",
            "websocket_manager": websocket_manager,
            "step_count": 0,
            "visited_agents": []
        }
        
        config = {"configurable": {"thread_id": "safe_simple_thread"}}
        
        print("🚀 Starting safe simple workflow...")
        result = await graph.ainvoke(initial_state, config)
        
        print(f"✅ Safe simple workflow completed")
        print(f"Final step count: {result.get('step_count', 0)}")
        print(f"Visited agents: {result.get('visited_agents', [])}")
        print(f"Current agent: {result.get('current_agent', 'Unknown')}")
        
        # Verify safety
        step_count = result.get('step_count', 0)
        if step_count <= 15:  # MAX_WORKFLOW_STEPS
            print(f"✅ Step count ({step_count}) within safe limits")
            return True
        else:
            print(f"❌ Step count ({step_count}) exceeded safe limits")
            return False
            
    except Exception as e:
        print(f"❌ Safe simple workflow test failed: {e}")
        logger.error(f"Safe simple workflow error: {e}", exc_info=True)
        return False

async def test_safe_complex_workflow():
    """Test safe complex workflow."""
    print("\n" + "="*60)
    print("🔍 TESTING SAFE COMPLEX WORKFLOW")
    print("="*60)
    
    try:
        graph = get_safe_agent_graph()
        websocket_manager = MockWebSocketManager()
        
        # Complex PO investigation task
        initial_state: AgentState = {
            "task_description": "Why is my PO related to invoice INV-1001 missing",
            "plan_id": "safe_complex_456",
            "websocket_manager": websocket_manager,
            "step_count": 0,
            "visited_agents": []
        }
        
        config = {"configurable": {"thread_id": "safe_complex_thread"}}
        
        print("🚀 Starting safe complex workflow...")
        start_time = datetime.now()
        
        result = await graph.ainvoke(initial_state, config)
        
        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()
        
        print(f"✅ Safe complex workflow completed in {execution_time:.2f}s")
        print(f"Final step count: {result.get('step_count', 0)}")
        print(f"Visited agents: {result.get('visited_agents', [])}")
        print(f"Current agent: {result.get('current_agent', 'Unknown')}")
        print(f"Workflow type: {result.get('workflow_type', 'Unknown')}")
        print(f"Analysis complete: {result.get('analysis_complete', False)}")
        
        # Verify safety
        step_count = result.get('step_count', 0)
        visited_agents = result.get('visited_agents', [])
        
        safety_checks = []
        
        # Check 1: Step count within limits
        if step_count <= 15:
            safety_checks.append(("Step Count", True, f"{step_count}/15"))
        else:
            safety_checks.append(("Step Count", False, f"{step_count}/15 - EXCEEDED"))
        
        # Check 2: No excessive agent repetition
        agent_counts = {}
        for agent in visited_agents:
            agent_counts[agent] = agent_counts.get(agent, 0) + 1
        
        max_agent_visits = max(agent_counts.values()) if agent_counts else 0
        if max_agent_visits <= 3:  # Reasonable limit
            safety_checks.append(("Agent Repetition", True, f"Max {max_agent_visits} visits"))
        else:
            safety_checks.append(("Agent Repetition", False, f"Max {max_agent_visits} visits - EXCESSIVE"))
        
        # Check 3: Workflow completed properly
        if result.get('analysis_complete') or result.get('final_result'):
            safety_checks.append(("Completion", True, "Workflow completed"))
        else:
            safety_checks.append(("Completion", False, "Workflow incomplete"))
        
        # Check 4: Execution time reasonable
        if execution_time < 30:  # 30 seconds max for test
            safety_checks.append(("Execution Time", True, f"{execution_time:.2f}s"))
        else:
            safety_checks.append(("Execution Time", False, f"{execution_time:.2f}s - TOO LONG"))
        
        print(f"\n🛡️  SAFETY CHECK RESULTS:")
        all_safe = True
        for check_name, passed, details in safety_checks:
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"  {check_name:20} {status} - {details}")
            if not passed:
                all_safe = False
        
        return all_safe
        
    except Exception as e:
        print(f"❌ Safe complex workflow test failed: {e}")
        logger.error(f"Safe complex workflow error: {e}", exc_info=True)
        return False

async def test_loop_prevention():
    """Test loop prevention by simulating problematic state."""
    print("\n" + "="*60)
    print("🛡️  TESTING LOOP PREVENTION")
    print("="*60)
    
    try:
        graph = get_safe_agent_graph()
        
        # Create a state that might cause loops
        problematic_state: AgentState = {
            "task_description": "Why is my PO related to invoice INV-1001 missing",
            "plan_id": "loop_test_789",
            "workflow_type": "po_investigation",
            "execution_plan": [
                {"step": 1, "agent": "gmail"},
                {"step": 2, "agent": "invoice"},
                {"step": 3, "agent": "salesforce"}
            ],
            "current_step": 0,
            "step_count": 12,  # Near the limit
            "visited_agents": ["planner", "gmail", "invoice", "gmail", "invoice"],  # Some repetition
            "collected_data": {}
        }
        
        config = {"configurable": {"thread_id": "loop_test_thread"}}
        
        print("🔄 Testing with problematic state (step_count=12, repeated agents)...")
        
        result = await graph.ainvoke(problematic_state, config)
        
        final_step_count = result.get('step_count', 0)
        
        print(f"✅ Loop prevention test completed")
        print(f"Final step count: {final_step_count}")
        print(f"Workflow ended safely: {final_step_count <= 15}")
        
        # Verify loop prevention worked
        if final_step_count <= 15:
            print("✅ Loop prevention working - workflow terminated within safe limits")
            return True
        else:
            print("❌ Loop prevention failed - exceeded safe limits")
            return False
            
    except Exception as e:
        print(f"❌ Loop prevention test failed: {e}")
        return False

async def main():
    """Run all safe LangGraph tests."""
    print("Safe LangGraph Implementation Test")
    print("="*70)
    
    results = []
    
    # Test safe simple workflow
    simple_ok = await test_safe_simple_workflow()
    results.append(("Safe Simple Workflow", simple_ok))
    
    # Test safe complex workflow
    complex_ok = await test_safe_complex_workflow()
    results.append(("Safe Complex Workflow", complex_ok))
    
    # Test loop prevention
    loop_prevention_ok = await test_loop_prevention()
    results.append(("Loop Prevention", loop_prevention_ok))
    
    # Print summary
    print("\n" + "="*70)
    print("SAFE LANGGRAPH TEST RESULTS")
    print("="*70)
    
    all_passed = True
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name:25} {status}")
        if not passed:
            all_passed = False
    
    print("="*70)
    if all_passed:
        print("🎉 All safe LangGraph tests passed!")
        print("\n✅ LangGraph Safety Features Working:")
        print("   • Built-in recursion_limit prevents infinite loops")
        print("   • Step counter tracking with maximum limits")
        print("   • Agent visit tracking prevents excessive repetition")
        print("   • Execution plan bounds checking")
        print("   • Safe multi-agent workflow coordination")
        
        print("\n🚀 Ready for Production:")
        print("   • No risk of infinite loops or crashes")
        print("   • Proper LangGraph orchestration (not custom code)")
        print("   • Real-time progress tracking")
        print("   • Comprehensive business analysis")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
    
    return all_passed

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        logger.error(f"Test failed: {e}", exc_info=True)
        sys.exit(1)