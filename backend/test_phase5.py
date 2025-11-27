"""
Phase 5 Validation Tests
Tests multi-agent collaboration and supervisor routing.
"""
import asyncio
import sys
import httpx
import websockets
import json

BASE_URL = "http://localhost:8000"
WS_URL = "ws://localhost:8000"


async def test_invoice_agent_routing():
    """Test that invoice-related tasks route to Invoice Agent."""
    print("Testing Invoice Agent routing...")
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{BASE_URL}/api/v3/process_request",
                json={"description": "Analyze invoice for payment accuracy"}
            )
            plan_id = response.json().get("plan_id")
        
        # Wait for execution
        await asyncio.sleep(3)
        
        # Check messages
        async with httpx.AsyncClient() as client:
            plan_response = await client.get(f"{BASE_URL}/api/v3/plan?plan_id={plan_id}")
            messages = plan_response.json().get("messages", [])
        
        # Verify both Planner and Invoice agents were involved
        agent_names = [msg.get("agent_name") for msg in messages]
        
        if "Planner" in agent_names and "Invoice" in agent_names:
            print(f"✅ Invoice Agent routing successful")
            print(f"   Agents involved: {', '.join(set(agent_names))}")
            return True
        else:
            print(f"❌ Expected Planner and Invoice agents, got: {agent_names}")
            return False
            
    except Exception as e:
        print(f"❌ Invoice routing test error: {e}")
        return False


async def test_closing_agent_routing():
    """Test that closing-related tasks route to Closing Agent."""
    print("\nTesting Closing Agent routing...")
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{BASE_URL}/api/v3/process_request",
                json={"description": "Perform month-end reconciliation and journal entries"}
            )
            plan_id = response.json().get("plan_id")
        
        # Wait for execution
        await asyncio.sleep(3)
        
        # Check messages
        async with httpx.AsyncClient() as client:
            plan_response = await client.get(f"{BASE_URL}/api/v3/plan?plan_id={plan_id}")
            messages = plan_response.json().get("messages", [])
        
        # Verify both Planner and Closing agents were involved
        agent_names = [msg.get("agent_name") for msg in messages]
        
        if "Planner" in agent_names and "Closing" in agent_names:
            print(f"✅ Closing Agent routing successful")
            print(f"   Agents involved: {', '.join(set(agent_names))}")
            return True
        else:
            print(f"❌ Expected Planner and Closing agents, got: {agent_names}")
            return False
            
    except Exception as e:
        print(f"❌ Closing routing test error: {e}")
        return False


async def test_audit_agent_routing():
    """Test that audit-related tasks route to Audit Agent."""
    print("\nTesting Audit Agent routing...")
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{BASE_URL}/api/v3/process_request",
                json={"description": "Review audit evidence and detect exceptions"}
            )
            plan_id = response.json().get("plan_id")
        
        # Wait for execution
        await asyncio.sleep(3)
        
        # Check messages
        async with httpx.AsyncClient() as client:
            plan_response = await client.get(f"{BASE_URL}/api/v3/plan?plan_id={plan_id}")
            messages = plan_response.json().get("messages", [])
        
        # Verify both Planner and Audit agents were involved
        agent_names = [msg.get("agent_name") for msg in messages]
        
        if "Planner" in agent_names and "Audit" in agent_names:
            print(f"✅ Audit Agent routing successful")
            print(f"   Agents involved: {', '.join(set(agent_names))}")
            return True
        else:
            print(f"❌ Expected Planner and Audit agents, got: {agent_names}")
            return False
            
    except Exception as e:
        print(f"❌ Audit routing test error: {e}")
        return False


async def test_multi_agent_websocket_streaming():
    """Test that messages from multiple agents are streamed via WebSocket."""
    print("\nTesting multi-agent WebSocket streaming...")
    try:
        # Create a task
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{BASE_URL}/api/v3/process_request",
                json={"description": "Check invoice payment status"}
            )
            plan_id = response.json().get("plan_id")
        
        # Connect to WebSocket and collect messages
        uri = f"{WS_URL}/api/v3/socket/{plan_id}?user_id=test_user"
        messages_received = []
        agents_seen = set()
        
        async with websockets.connect(uri) as websocket:
            try:
                while len(messages_received) < 10:
                    message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    data = json.loads(message)
                    messages_received.append(data)
                    
                    if data.get("type") == "agent_message":
                        agent_name = data.get("data", {}).get("agent_name")
                        if agent_name:
                            agents_seen.add(agent_name)
                    
                    if data.get("type") == "final_result_message":
                        break
            except asyncio.TimeoutError:
                pass
        
        print(f"   Messages received: {len(messages_received)}")
        print(f"   Agents seen: {', '.join(agents_seen)}")
        
        # Should see at least Planner and one specialized agent
        if len(agents_seen) >= 2:
            print("✅ Multi-agent streaming successful")
            return True
        else:
            print(f"❌ Expected multiple agents, only saw: {agents_seen}")
            return False
            
    except Exception as e:
        print(f"❌ Multi-agent streaming test error: {e}")
        return False


async def test_supervisor_routing_logic():
    """Test supervisor routing logic directly."""
    print("\nTesting supervisor routing logic...")
    try:
        from app.agents.supervisor import supervisor_router
        from app.agents.state import AgentState
        
        # Test invoice routing
        state_invoice: AgentState = {
            "messages": [],
            "plan_id": "test",
            "session_id": "test",
            "task_description": "test",
            "current_agent": "Planner",
            "next_agent": "invoice",
            "final_result": ""
        }
        result = supervisor_router(state_invoice)
        
        if result != "invoice":
            print(f"❌ Expected 'invoice', got '{result}'")
            return False
        
        # Test closing routing
        state_closing: AgentState = {
            "messages": [],
            "plan_id": "test",
            "session_id": "test",
            "task_description": "test",
            "current_agent": "Planner",
            "next_agent": "closing",
            "final_result": ""
        }
        result = supervisor_router(state_closing)
        
        if result != "closing":
            print(f"❌ Expected 'closing', got '{result}'")
            return False
        
        # Test end routing
        state_end: AgentState = {
            "messages": [],
            "plan_id": "test",
            "session_id": "test",
            "task_description": "test",
            "current_agent": "Planner",
            "next_agent": None,
            "final_result": ""
        }
        result = supervisor_router(state_end)
        
        if result != "end":
            print(f"❌ Expected 'end', got '{result}'")
            return False
        
        print("✅ Supervisor routing logic works correctly")
        return True
        
    except Exception as e:
        print(f"❌ Supervisor routing test error: {e}")
        return False


async def run_all_tests():
    """Run all Phase 5 validation tests."""
    print("=" * 60)
    print("PHASE 5 VALIDATION TESTS")
    print("=" * 60)
    print("\n⚠️  Make sure the backend server is running:")
    print("   python -m app.main")
    print()
    
    results = []
    
    # Test 1: Supervisor Routing Logic
    results.append(await test_supervisor_routing_logic())
    
    # Test 2: Invoice Agent Routing
    results.append(await test_invoice_agent_routing())
    
    # Test 3: Closing Agent Routing
    results.append(await test_closing_agent_routing())
    
    # Test 4: Audit Agent Routing
    results.append(await test_audit_agent_routing())
    
    # Test 5: Multi-Agent WebSocket Streaming
    results.append(await test_multi_agent_websocket_streaming())
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Supervisor Routing Logic: {'✅ PASS' if results[0] else '❌ FAIL'}")
    print(f"Invoice Agent Routing: {'✅ PASS' if results[1] else '❌ FAIL'}")
    print(f"Closing Agent Routing: {'✅ PASS' if results[2] else '❌ FAIL'}")
    print(f"Audit Agent Routing: {'✅ PASS' if results[3] else '❌ FAIL'}")
    print(f"Multi-Agent WebSocket Streaming: {'✅ PASS' if results[4] else '❌ FAIL'}")
    print("=" * 60)
    
    all_passed = all(results)
    if all_passed:
        print("\n🎉 All Phase 5 tests PASSED!")
        print("✅ Ready to proceed to Phase 6")
    else:
        print("\n❌ Some tests FAILED. Please fix issues before proceeding.")
    
    return all_passed


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
