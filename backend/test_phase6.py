"""
Phase 6 Validation Tests
Tests human-in-the-loop plan approval flow.
"""
import asyncio
import sys
import httpx
import websockets
import json

BASE_URL = "http://localhost:8000"
WS_URL = "ws://localhost:8000"


async def test_plan_approval_request():
    """Test that plan approval request is sent via WebSocket."""
    print("Testing plan approval request...")
    try:
        # Create a task
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{BASE_URL}/api/v3/process_request",
                json={"description": "Test approval flow"}
            )
            plan_id = response.json().get("plan_id")
        
        # Connect to WebSocket and wait for approval request
        uri = f"{WS_URL}/api/v3/socket/{plan_id}?user_id=test_user"
        approval_received = False
        
        async with websockets.connect(uri) as websocket:
            try:
                for _ in range(10):
                    message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    data = json.loads(message)
                    
                    if data.get("type") == "plan_approval_request":
                        approval_received = True
                        print(f"   Approval request received for plan: {plan_id}")
                        break
            except asyncio.TimeoutError:
                pass
        
        if approval_received:
            print("✅ Plan approval request sent successfully")
            return True, plan_id
        else:
            print("❌ Plan approval request not received")
            return False, None
            
    except Exception as e:
        print(f"❌ Approval request test error: {e}")
        return False, None


async def test_plan_approval_endpoint():
    """Test POST /api/v3/plan_approval endpoint."""
    print("\nTesting plan approval endpoint...")
    try:
        # Create a task
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{BASE_URL}/api/v3/process_request",
                json={"description": "Test approval endpoint"}
            )
            plan_id = response.json().get("plan_id")
        
        # Wait for approval request
        await asyncio.sleep(2)
        
        # Send approval
        async with httpx.AsyncClient() as client:
            approval_response = await client.post(
                f"{BASE_URL}/api/v3/plan_approval",
                json={
                    "m_plan_id": plan_id,
                    "approved": True,
                    "feedback": "Looks good!"
                }
            )
            
            if approval_response.status_code == 200:
                data = approval_response.json()
                print(f"   Approval response: {data.get('status')}")
                print("✅ Plan approval endpoint works")
                return True
            else:
                print(f"❌ Approval endpoint failed: {approval_response.status_code}")
                return False
                
    except Exception as e:
        print(f"❌ Approval endpoint test error: {e}")
        return False


async def test_approval_resumes_execution():
    """Test that approval resumes execution."""
    print("\nTesting approval resumes execution...")
    try:
        # Create a task
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{BASE_URL}/api/v3/process_request",
                json={"description": "Check invoice payment status"}
            )
            plan_id = response.json().get("plan_id")
        
        # Connect to WebSocket
        uri = f"{WS_URL}/api/v3/socket/{plan_id}?user_id=test_user"
        messages_received = []
        
        async with websockets.connect(uri) as websocket:
            # Wait for approval request
            approval_received = False
            for _ in range(10):
                message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                data = json.loads(message)
                messages_received.append(data)
                
                if data.get("type") == "plan_approval_request":
                    approval_received = True
                    break
            
            if not approval_received:
                print("❌ No approval request received")
                return False
            
            # Send approval via HTTP
            async with httpx.AsyncClient() as client:
                await client.post(
                    f"{BASE_URL}/api/v3/plan_approval",
                    json={"m_plan_id": plan_id, "approved": True}
                )
            
            # Wait for execution to resume and complete
            final_received = False
            for _ in range(10):
                message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                data = json.loads(message)
                messages_received.append(data)
                
                if data.get("type") == "final_result_message":
                    final_received = True
                    break
        
        if final_received:
            print(f"   Total messages: {len(messages_received)}")
            print("✅ Execution resumed after approval")
            return True
        else:
            print("❌ Execution did not complete after approval")
            return False
            
    except Exception as e:
        print(f"❌ Resume execution test error: {e}")
        return False


async def test_rejection_stops_execution():
    """Test that rejection stops execution."""
    print("\nTesting rejection stops execution...")
    try:
        # Create a task
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{BASE_URL}/api/v3/process_request",
                json={"description": "Test rejection"}
            )
            plan_id = response.json().get("plan_id")
        
        # Wait for approval request
        await asyncio.sleep(2)
        
        # Send rejection
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{BASE_URL}/api/v3/plan_approval",
                json={
                    "m_plan_id": plan_id,
                    "approved": False,
                    "feedback": "Not approved"
                }
            )
        
        # Wait a bit
        await asyncio.sleep(2)
        
        # Check plan status
        async with httpx.AsyncClient() as client:
            plan_response = await client.get(f"{BASE_URL}/api/v3/plan?plan_id={plan_id}")
            plan_data = plan_response.json()
            status = plan_data.get("plan", {}).get("status")
            
            print(f"   Plan status after rejection: {status}")
            
            if status == "rejected":
                print("✅ Rejection stops execution correctly")
                return True
            else:
                print(f"❌ Expected 'rejected' status, got '{status}'")
                return False
                
    except Exception as e:
        print(f"❌ Rejection test error: {e}")
        return False


async def test_plan_status_updates():
    """Test that plan status updates correctly during approval flow."""
    print("\nTesting plan status updates...")
    try:
        # Create a task
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{BASE_URL}/api/v3/process_request",
                json={"description": "Test status updates"}
            )
            plan_id = response.json().get("plan_id")
        
        # Wait for approval request
        await asyncio.sleep(2)
        
        # Check status (should be pending_approval)
        async with httpx.AsyncClient() as client:
            plan_response = await client.get(f"{BASE_URL}/api/v3/plan?plan_id={plan_id}")
            status1 = plan_response.json().get("plan", {}).get("status")
            print(f"   Status before approval: {status1}")
            
            # Approve
            await client.post(
                f"{BASE_URL}/api/v3/plan_approval",
                json={"m_plan_id": plan_id, "approved": True}
            )
            
            # Wait for completion
            await asyncio.sleep(3)
            
            # Check final status
            plan_response = await client.get(f"{BASE_URL}/api/v3/plan?plan_id={plan_id}")
            status2 = plan_response.json().get("plan", {}).get("status")
            print(f"   Status after approval: {status2}")
            
            if status1 == "pending_approval" and status2 == "completed":
                print("✅ Plan status updates correctly")
                return True
            else:
                print(f"❌ Unexpected status progression: {status1} → {status2}")
                return False
                
    except Exception as e:
        print(f"❌ Status updates test error: {e}")
        return False


async def run_all_tests():
    """Run all Phase 6 validation tests."""
    print("=" * 60)
    print("PHASE 6 VALIDATION TESTS")
    print("=" * 60)
    print("\n⚠️  Make sure the backend server is running:")
    print("   python -m app.main")
    print()
    
    results = []
    
    # Test 1: Plan Approval Request
    success, plan_id = await test_plan_approval_request()
    results.append(success)
    
    # Test 2: Plan Approval Endpoint
    results.append(await test_plan_approval_endpoint())
    
    # Test 3: Approval Resumes Execution
    results.append(await test_approval_resumes_execution())
    
    # Test 4: Rejection Stops Execution
    results.append(await test_rejection_stops_execution())
    
    # Test 5: Plan Status Updates
    results.append(await test_plan_status_updates())
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Plan Approval Request: {'✅ PASS' if results[0] else '❌ FAIL'}")
    print(f"Plan Approval Endpoint: {'✅ PASS' if results[1] else '❌ FAIL'}")
    print(f"Approval Resumes Execution: {'✅ PASS' if results[2] else '❌ FAIL'}")
    print(f"Rejection Stops Execution: {'✅ PASS' if results[3] else '❌ FAIL'}")
    print(f"Plan Status Updates: {'✅ PASS' if results[4] else '❌ FAIL'}")
    print("=" * 60)
    
    all_passed = all(results)
    if all_passed:
        print("\n🎉 All Phase 6 tests PASSED!")
        print("✅ Prototype complete! Ready for frontend integration.")
    else:
        print("\n❌ Some tests FAILED. Please fix issues before proceeding.")
    
    return all_passed


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
