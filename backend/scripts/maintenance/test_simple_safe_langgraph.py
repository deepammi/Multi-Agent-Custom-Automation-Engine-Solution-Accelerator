#!/usr/bin/env python3
"""
Simple Safe LangGraph Test
Basic test to verify the safe LangGraph implementation works without infinite loops
"""

import asyncio
import logging
import sys
import os
from datetime import datetime

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.agents.safe_langgraph import get_safe_agent_graph
from app.agents.state import AgentState

# Setup logging
logging.basicConfig(level=logging.WARNING)  # Reduce log noise
logger = logging.getLogger(__name__)

async def test_basic_functionality():
    """Test basic LangGraph functionality."""
    print("🔧 Testing Basic Safe LangGraph Functionality")
    print("-" * 50)
    
    try:
        # Get the graph
        graph = get_safe_agent_graph()
        print("✅ Graph compiled successfully")
        
        # Test simple workflow
        initial_state: AgentState = {
            "task_description": "read my recent emails",
            "plan_id": "basic_test_123",
            "step_count": 0,
            "visited_agents": []
        }
        
        config = {"configurable": {"thread_id": "basic_test_thread"}}
        
        print("🚀 Starting basic workflow...")
        start_time = datetime.now()
        
        # Set a timeout to prevent hanging
        try:
            result = await asyncio.wait_for(
                graph.ainvoke(initial_state, config),
                timeout=30.0  # 30 second timeout
            )
            
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()
            
            print(f"✅ Workflow completed in {execution_time:.2f}s")
            print(f"Final step count: {result.get('step_count', 0)}")
            print(f"Visited agents: {result.get('visited_agents', [])}")
            print(f"Current agent: {result.get('current_agent', 'Unknown')}")
            
            # Check if it completed safely
            step_count = result.get('step_count', 0)
            if step_count <= 15:
                print(f"✅ Completed within safe step limit ({step_count}/15)")
                return True
            else:
                print(f"❌ Exceeded safe step limit ({step_count}/15)")
                return False
                
        except asyncio.TimeoutError:
            print("❌ Workflow timed out after 30 seconds - possible infinite loop")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        logger.error(f"Basic test error: {e}", exc_info=True)
        return False

async def test_complex_workflow_with_timeout():
    """Test complex workflow with timeout protection."""
    print("\n🔍 Testing Complex Workflow with Timeout")
    print("-" * 50)
    
    try:
        graph = get_safe_agent_graph()
        
        # Complex PO investigation task
        initial_state: AgentState = {
            "task_description": "Why is my PO related to invoice INV-1001 missing",
            "plan_id": "complex_test_456",
            "step_count": 0,
            "visited_agents": []
        }
        
        config = {"configurable": {"thread_id": "complex_test_thread"}}
        
        print("🚀 Starting complex workflow with 45s timeout...")
        start_time = datetime.now()
        
        try:
            result = await asyncio.wait_for(
                graph.ainvoke(initial_state, config),
                timeout=45.0  # 45 second timeout
            )
            
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()
            
            print(f"✅ Complex workflow completed in {execution_time:.2f}s")
            print(f"Final step count: {result.get('step_count', 0)}")
            print(f"Workflow type: {result.get('workflow_type', 'Unknown')}")
            
            # Check safety
            step_count = result.get('step_count', 0)
            if step_count <= 15:
                print(f"✅ Completed within safe step limit ({step_count}/15)")
                return True
            else:
                print(f"❌ Exceeded safe step limit ({step_count}/15)")
                return False
                
        except asyncio.TimeoutError:
            print("❌ Complex workflow timed out after 45 seconds - possible infinite loop")
            return False
            
    except Exception as e:
        print(f"❌ Complex test failed: {e}")
        return False

async def main():
    """Run simple safe tests."""
    print("Simple Safe LangGraph Test")
    print("=" * 50)
    
    results = []
    
    # Test basic functionality
    basic_ok = await test_basic_functionality()
    results.append(("Basic Functionality", basic_ok))
    
    # Test complex workflow
    complex_ok = await test_complex_workflow_with_timeout()
    results.append(("Complex Workflow", complex_ok))
    
    # Print summary
    print("\n" + "=" * 50)
    print("TEST RESULTS")
    print("=" * 50)
    
    all_passed = True
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name:20} {status}")
        if not passed:
            all_passed = False
    
    if all_passed:
        print("\n🎉 All tests passed! Safe LangGraph is working.")
    else:
        print("\n⚠️  Some tests failed.")
    
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
        sys.exit(1)