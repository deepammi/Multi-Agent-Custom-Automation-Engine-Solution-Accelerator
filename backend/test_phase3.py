"""
Phase 3 Validation Tests
Tests LangGraph agent execution and integration.
"""
import asyncio
import sys
import httpx
import time

BASE_URL = "http://localhost:8000"


async def test_langgraph_execution():
    """Test LangGraph workflow execution via process_request."""
    print("Testing LangGraph agent execution...")
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Create a task
            payload = {
                "description": "Analyze invoice for accuracy and payment status"
            }
            response = await client.post(f"{BASE_URL}/api/v3/process_request", json=payload)
            
            if response.status_code != 200:
                print(f"❌ Failed to create task: {response.status_code}")
                return False, None
            
            data = response.json()
            plan_id = data.get("plan_id")
            print(f"✅ Task created with plan_id: {plan_id}")
            
            # Wait for agent execution (background task)
            print("   Waiting for agent execution...")
            await asyncio.sleep(3)
            
            # Retrieve the plan to check execution
            plan_response = await client.get(f"{BASE_URL}/api/v3/plan?plan_id={plan_id}")
            
            if plan_response.status_code != 200:
                print(f"❌ Failed to retrieve plan: {plan_response.status_code}")
                return False, None
            
            plan_data = plan_response.json()
            plan = plan_data.get("plan", {})
            messages = plan_data.get("messages", [])
            
            print(f"   Plan status: {plan.get('status')}")
            print(f"   Messages received: {len(messages)}")
            
            return True, {"plan": plan, "messages": messages}
            
    except Exception as e:
        print(f"❌ LangGraph execution error: {e}")
        return False, None


async def test_agent_messages_stored():
    """Test that agent messages are stored in database."""
    print("\nTesting agent message storage...")
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Create a task
            payload = {
                "description": "Test message storage"
            }
            response = await client.post(f"{BASE_URL}/api/v3/process_request", json=payload)
            
            if response.status_code != 200:
                print(f"❌ Failed to create task")
                return False
            
            plan_id = response.json().get("plan_id")
            
            # Wait for execution
            await asyncio.sleep(3)
            
            # Check messages
            plan_response = await client.get(f"{BASE_URL}/api/v3/plan?plan_id={plan_id}")
            messages = plan_response.json().get("messages", [])
            
            if len(messages) > 0:
                print(f"✅ Agent messages stored successfully ({len(messages)} messages)")
                print(f"   Sample message: {messages[0].get('content', '')[:100]}...")
                return True
            else:
                print("❌ No messages found in database")
                return False
                
    except Exception as e:
        print(f"❌ Message storage test error: {e}")
        return False


async def test_plan_status_updates():
    """Test that plan status updates correctly during execution."""
    print("\nTesting plan status updates...")
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Create a task
            payload = {
                "description": "Test status updates"
            }
            response = await client.post(f"{BASE_URL}/api/v3/process_request", json=payload)
            
            if response.status_code != 200:
                print(f"❌ Failed to create task")
                return False
            
            plan_id = response.json().get("plan_id")
            
            # Check initial status
            plan_response = await client.get(f"{BASE_URL}/api/v3/plan?plan_id={plan_id}")
            initial_status = plan_response.json().get("plan", {}).get("status")
            print(f"   Initial status: {initial_status}")
            
            # Wait for execution
            await asyncio.sleep(3)
            
            # Check final status
            plan_response = await client.get(f"{BASE_URL}/api/v3/plan?plan_id={plan_id}")
            final_status = plan_response.json().get("plan", {}).get("status")
            print(f"   Final status: {final_status}")
            
            if final_status in ["completed", "in_progress"]:
                print(f"✅ Plan status updated correctly")
                return True
            else:
                print(f"❌ Unexpected final status: {final_status}")
                return False
                
    except Exception as e:
        print(f"❌ Status update test error: {e}")
        return False


async def test_graph_state_transitions():
    """Test that LangGraph state transitions work correctly."""
    print("\nTesting graph state transitions...")
    try:
        from app.agents.graph import agent_graph
        from app.agents.state import AgentState
        
        # Create test state
        test_state: AgentState = {
            "messages": [],
            "plan_id": "test-123",
            "session_id": "session-123",
            "task_description": "Test task",
            "current_agent": "",
            "final_result": ""
        }
        
        # Execute graph
        result = agent_graph.invoke(test_state)
        
        # Verify result
        if result.get("messages") and result.get("final_result"):
            print(f"✅ Graph executed successfully")
            print(f"   Current agent: {result.get('current_agent')}")
            print(f"   Messages: {len(result.get('messages', []))}")
            return True
        else:
            print(f"❌ Graph execution incomplete")
            return False
            
    except Exception as e:
        print(f"❌ Graph state test error: {e}")
        return False


async def run_all_tests():
    """Run all Phase 3 validation tests."""
    print("=" * 60)
    print("PHASE 3 VALIDATION TESTS")
    print("=" * 60)
    print("\n⚠️  Make sure the backend server is running:")
    print("   python -m app.main")
    print()
    
    results = []
    
    # Test 1: Graph State Transitions
    results.append(await test_graph_state_transitions())
    
    # Test 2: LangGraph Execution
    success, execution_data = await test_langgraph_execution()
    results.append(success)
    
    # Test 3: Agent Messages Stored
    results.append(await test_agent_messages_stored())
    
    # Test 4: Plan Status Updates
    results.append(await test_plan_status_updates())
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Graph State Transitions: {'✅ PASS' if results[0] else '❌ FAIL'}")
    print(f"LangGraph Execution: {'✅ PASS' if results[1] else '❌ FAIL'}")
    print(f"Agent Messages Stored: {'✅ PASS' if results[2] else '❌ FAIL'}")
    print(f"Plan Status Updates: {'✅ PASS' if results[3] else '❌ FAIL'}")
    print("=" * 60)
    
    all_passed = all(results)
    if all_passed:
        print("\n🎉 All Phase 3 tests PASSED!")
        print("✅ Ready to proceed to Phase 4")
    else:
        print("\n❌ Some tests FAILED. Please fix issues before proceeding.")
    
    return all_passed


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
