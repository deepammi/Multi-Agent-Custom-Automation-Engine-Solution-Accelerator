"""
End-to-End Integration Test
Comprehensive test that simulates a complete user workflow:
1. Create a task
2. Connect to WebSocket
3. Receive agent messages
4. Approve the plan
5. Verify final result is received
"""
import asyncio
import sys
import httpx
import websockets
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"
WS_URL = "ws://localhost:8000"


async def test_complete_workflow():
    """
    Complete end-to-end test simulating frontend interaction.
    Tests the full workflow from task creation to completion.
    """
    print("=" * 70)
    print("END-TO-END INTEGRATION TEST")
    print("=" * 70)
    print("\n📋 Simulating complete user workflow:")
    print("   1. Create task via REST API")
    print("   2. Connect to WebSocket for real-time updates")
    print("   3. Receive agent messages (Planner)")
    print("   4. Receive plan approval request")
    print("   5. Approve plan via REST API")
    print("   6. Receive specialized agent messages (Invoice/Closing/Audit)")
    print("   7. Receive final result message")
    print("   8. Verify plan completion\n")
    
    try:
        # Step 1: Create a task
        print("Step 1: Creating task...")
        task_description = "Check invoice payment status and verify due dates"
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{BASE_URL}/api/v3/process_request",
                json={"description": task_description}
            )
            
            if response.status_code != 200:
                print(f"❌ Failed to create task: {response.status_code}")
                return False
            
            data = response.json()
            plan_id = data.get("plan_id")
            session_id = data.get("session_id")
            
            print(f"   ✓ Task created successfully")
            print(f"   ✓ Plan ID: {plan_id}")
            print(f"   ✓ Session ID: {session_id}")
        
        # Step 2: Connect to WebSocket
        print("\nStep 2: Connecting to WebSocket...")
        uri = f"{WS_URL}/api/v3/socket/{plan_id}?user_id=test_user"
        
        messages_received = []
        approval_request_received = False
        final_result_received = False
        
        async with websockets.connect(uri) as websocket:
            print(f"   ✓ WebSocket connected to {uri}")
            
            # Step 3: Receive initial messages
            print("\nStep 3: Receiving agent messages...")
            
            # Collect messages until we get approval request
            for i in range(20):  # Max 20 messages
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    data = json.loads(message)
                    messages_received.append(data)
                    
                    msg_type = data.get("type")
                    
                    if msg_type == "agent_message":
                        agent_name = data.get("data", {}).get("agent_name", "Unknown")
                        content_preview = data.get("data", {}).get("content", "")[:60]
                        print(f"   ✓ [{agent_name}] {content_preview}...")
                    
                    elif msg_type == "plan_approval_request":
                        approval_request_received = True
                        print(f"\n   ✓ Plan approval request received")
                        break
                    
                except asyncio.TimeoutError:
                    print("   ⚠ Timeout waiting for messages")
                    break
            
            # Step 4: Verify approval request
            if not approval_request_received:
                print("\n❌ Plan approval request was not received")
                return False
            
            print("\nStep 4: Plan approval request received ✓")
            
            # Step 5: Approve the plan
            print("\nStep 5: Approving plan...")
            async with httpx.AsyncClient() as client:
                approval_response = await client.post(
                    f"{BASE_URL}/api/v3/plan_approval",
                    json={
                        "m_plan_id": plan_id,
                        "approved": True,
                        "feedback": "Approved via E2E test"
                    }
                )
                
                if approval_response.status_code != 200:
                    print(f"❌ Failed to approve plan: {approval_response.status_code}")
                    return False
                
                print(f"   ✓ Plan approved successfully")
            
            # Step 6: Receive specialized agent messages and final result
            print("\nStep 6: Receiving specialized agent messages...")
            
            for i in range(20):  # Max 20 more messages
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    data = json.loads(message)
                    messages_received.append(data)
                    
                    msg_type = data.get("type")
                    
                    if msg_type == "agent_message":
                        agent_name = data.get("data", {}).get("agent_name", "Unknown")
                        content_preview = data.get("data", {}).get("content", "")[:60]
                        print(f"   ✓ [{agent_name}] {content_preview}...")
                    
                    elif msg_type == "final_result_message":
                        final_result_received = True
                        content = data.get("data", {}).get("content", "")
                        print(f"\n   ✓ Final result received")
                        print(f"   ✓ Result: {content[:100]}...")
                        break
                    
                except asyncio.TimeoutError:
                    print("   ⚠ Timeout waiting for final result")
                    break
        
        # Step 7: Verify final result
        if not final_result_received:
            print("\n❌ Final result message was not received")
            return False
        
        print("\nStep 7: Final result received ✓")
        
        # Step 8: Verify plan completion via REST API
        print("\nStep 8: Verifying plan completion...")
        async with httpx.AsyncClient() as client:
            plan_response = await client.get(f"{BASE_URL}/api/v3/plan?plan_id={plan_id}")
            
            if plan_response.status_code != 200:
                print(f"❌ Failed to get plan: {plan_response.status_code}")
                return False
            
            plan_data = plan_response.json()
            plan = plan_data.get("plan", {})
            messages = plan_data.get("messages", [])
            
            status = plan.get("status")
            print(f"   ✓ Plan status: {status}")
            print(f"   ✓ Total messages stored: {len(messages)}")
            print(f"   ✓ Total WebSocket messages: {len(messages_received)}")
            
            if status != "completed":
                print(f"❌ Expected status 'completed', got '{status}'")
                return False
        
        # Summary
        print("\n" + "=" * 70)
        print("TEST SUMMARY")
        print("=" * 70)
        print(f"✅ Task created successfully")
        print(f"✅ WebSocket connection established")
        print(f"✅ Agent messages received ({len([m for m in messages_received if m.get('type') == 'agent_message'])} messages)")
        print(f"✅ Plan approval request received")
        print(f"✅ Plan approved successfully")
        print(f"✅ Specialized agent executed")
        print(f"✅ Final result received")
        print(f"✅ Plan marked as completed")
        print("=" * 70)
        print("\n🎉 END-TO-END TEST PASSED!")
        print("✅ Backend is ready for frontend integration")
        
        return True
        
    except Exception as e:
        print(f"\n❌ End-to-end test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_multiple_tasks():
    """Test handling multiple concurrent tasks."""
    print("\n" + "=" * 70)
    print("CONCURRENT TASKS TEST")
    print("=" * 70)
    print("\nTesting multiple concurrent task executions...")
    
    try:
        tasks = [
            "Check invoice payment status",
            "Perform closing reconciliation",
            "Review audit evidence"
        ]
        
        plan_ids = []
        
        # Create multiple tasks
        async with httpx.AsyncClient() as client:
            for task_desc in tasks:
                response = await client.post(
                    f"{BASE_URL}/api/v3/process_request",
                    json={"description": task_desc}
                )
                plan_id = response.json().get("plan_id")
                plan_ids.append(plan_id)
                print(f"   ✓ Created task: {task_desc[:40]}... (Plan: {plan_id})")
        
        # Wait for all to reach approval state
        await asyncio.sleep(3)
        
        # Approve all tasks
        async with httpx.AsyncClient() as client:
            for plan_id in plan_ids:
                await client.post(
                    f"{BASE_URL}/api/v3/plan_approval",
                    json={"m_plan_id": plan_id, "approved": True}
                )
                print(f"   ✓ Approved plan: {plan_id}")
        
        # Wait for completion
        await asyncio.sleep(3)
        
        # Verify all completed
        completed_count = 0
        async with httpx.AsyncClient() as client:
            for plan_id in plan_ids:
                response = await client.get(f"{BASE_URL}/api/v3/plan?plan_id={plan_id}")
                status = response.json().get("plan", {}).get("status")
                if status == "completed":
                    completed_count += 1
        
        print(f"\n   ✓ Completed tasks: {completed_count}/{len(plan_ids)}")
        
        if completed_count == len(plan_ids):
            print("\n✅ CONCURRENT TASKS TEST PASSED!")
            return True
        else:
            print(f"\n❌ Only {completed_count}/{len(plan_ids)} tasks completed")
            return False
            
    except Exception as e:
        print(f"\n❌ Concurrent tasks test failed: {e}")
        return False


async def test_session_persistence():
    """Test that sessions persist across multiple tasks."""
    print("\n" + "=" * 70)
    print("SESSION PERSISTENCE TEST")
    print("=" * 70)
    print("\nTesting session persistence across tasks...")
    
    try:
        # Create first task
        async with httpx.AsyncClient() as client:
            response1 = await client.post(
                f"{BASE_URL}/api/v3/process_request",
                json={"description": "First task"}
            )
            session_id1 = response1.json().get("session_id")
            print(f"   ✓ First task session: {session_id1}")
            
            # Create second task with same session
            response2 = await client.post(
                f"{BASE_URL}/api/v3/process_request",
                json={"description": "Second task", "session_id": session_id1}
            )
            session_id2 = response2.json().get("session_id")
            print(f"   ✓ Second task session: {session_id2}")
            
            if session_id1 == session_id2:
                print("\n✅ SESSION PERSISTENCE TEST PASSED!")
                return True
            else:
                print(f"\n❌ Session IDs don't match: {session_id1} != {session_id2}")
                return False
                
    except Exception as e:
        print(f"\n❌ Session persistence test failed: {e}")
        return False


async def run_all_tests():
    """Run all end-to-end tests."""
    print("\n" + "=" * 70)
    print("COMPREHENSIVE END-TO-END TEST SUITE")
    print("=" * 70)
    print("\n⚠️  Make sure the backend server is running:")
    print("   python -m app.main")
    print()
    
    results = []
    
    # Test 1: Complete workflow
    results.append(await test_complete_workflow())
    
    # Test 2: Multiple concurrent tasks
    results.append(await test_multiple_tasks())
    
    # Test 3: Session persistence
    results.append(await test_session_persistence())
    
    # Final summary
    print("\n" + "=" * 70)
    print("FINAL TEST SUMMARY")
    print("=" * 70)
    print(f"Complete Workflow Test: {'✅ PASS' if results[0] else '❌ FAIL'}")
    print(f"Concurrent Tasks Test: {'✅ PASS' if results[1] else '❌ FAIL'}")
    print(f"Session Persistence Test: {'✅ PASS' if results[2] else '❌ FAIL'}")
    print("=" * 70)
    
    all_passed = all(results)
    if all_passed:
        print("\n🎉 ALL END-TO-END TESTS PASSED!")
        print("✅ Backend is fully functional and ready for frontend integration")
        print("\nNext steps:")
        print("   1. Update frontend API URL to point to this backend")
        print("   2. Test frontend pages with real backend")
        print("   3. Proceed to Phase 7 (Tool Integration)")
    else:
        print("\n❌ SOME TESTS FAILED")
        print("Please review the failures above and fix issues before proceeding.")
    
    return all_passed


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
