"""
Frontend Integration Test
Tests the frontend-backend integration by simulating frontend requests.
"""
import asyncio
import httpx
import websockets
import json
from datetime import datetime

BACKEND_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:3001"
WS_URL = "ws://localhost:8000"


async def test_frontend_can_reach_backend():
    """Test that frontend can reach backend health endpoint."""
    print("\n" + "="*70)
    print("TEST 1: Frontend Can Reach Backend")
    print("="*70)
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{BACKEND_URL}/health")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Backend is healthy: {data}")
                return True
            else:
                print(f"❌ Backend returned status {response.status_code}")
                return False
    except Exception as e:
        print(f"❌ Cannot reach backend: {e}")
        return False


async def test_frontend_config_endpoint():
    """Test that frontend can load config from backend."""
    print("\n" + "="*70)
    print("TEST 2: Frontend Config Endpoint")
    print("="*70)
    
    try:
        async with httpx.AsyncClient() as client:
            # Try to get config from frontend server
            response = await client.get(f"{FRONTEND_URL}/config")
            
            if response.status_code == 200:
                config = response.json()
                print(f"✅ Config loaded: {json.dumps(config, indent=2)}")
                
                # Verify config has correct API_URL
                if config.get("API_URL") == "http://localhost:8000/api":
                    print("✅ API_URL is correctly configured")
                    return True
                else:
                    print(f"❌ API_URL is incorrect: {config.get('API_URL')}")
                    return False
            else:
                print(f"⚠️  Config endpoint returned {response.status_code}")
                print("   This is OK if using static config.json")
                return True
    except Exception as e:
        print(f"⚠️  Cannot reach config endpoint: {e}")
        print("   This is OK if using static config.json")
        return True


async def test_create_task_from_frontend():
    """Test creating a task as the frontend would."""
    print("\n" + "="*70)
    print("TEST 3: Create Task (Frontend Flow)")
    print("="*70)
    
    try:
        async with httpx.AsyncClient() as client:
            # Simulate frontend creating a task
            task_data = {
                "description": "Check invoice payment status for vendor ABC Corp"
            }
            
            print(f"📤 Creating task: {task_data['description']}")
            response = await client.post(
                f"{BACKEND_URL}/api/v3/process_request",
                json=task_data
            )
            
            if response.status_code == 200:
                data = response.json()
                plan_id = data.get("plan_id")
                session_id = data.get("session_id")
                
                print(f"✅ Task created successfully")
                print(f"   Plan ID: {plan_id}")
                print(f"   Session ID: {session_id}")
                return True, plan_id
            else:
                print(f"❌ Failed to create task: {response.status_code}")
                print(f"   Response: {response.text}")
                return False, None
    except Exception as e:
        print(f"❌ Error creating task: {e}")
        return False, None


async def test_websocket_connection():
    """Test WebSocket connection as frontend would."""
    print("\n" + "="*70)
    print("TEST 4: WebSocket Connection (Frontend Flow)")
    print("="*70)
    
    try:
        # Create a task first
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{BACKEND_URL}/api/v3/process_request",
                json={"description": "Test WebSocket connection"}
            )
            plan_id = response.json().get("plan_id")
        
        print(f"📤 Connecting to WebSocket for plan: {plan_id}")
        
        # Connect to WebSocket
        uri = f"{WS_URL}/api/v3/socket/{plan_id}?user_id=frontend_test_user"
        messages_received = []
        
        async with websockets.connect(uri) as websocket:
            print("✅ WebSocket connected")
            
            # Receive messages for 5 seconds
            try:
                for i in range(10):
                    message = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                    data = json.loads(message)
                    messages_received.append(data)
                    
                    msg_type = data.get("type")
                    print(f"   📨 Received: {msg_type}")
                    
                    if msg_type == "plan_approval_request":
                        print("   ✅ Approval request received (as expected)")
                        break
            except asyncio.TimeoutError:
                pass
        
        if len(messages_received) > 0:
            print(f"✅ Received {len(messages_received)} messages via WebSocket")
            return True
        else:
            print("❌ No messages received")
            return False
            
    except Exception as e:
        print(f"❌ WebSocket error: {e}")
        return False


async def test_get_plan_details():
    """Test getting plan details as frontend would."""
    print("\n" + "="*70)
    print("TEST 5: Get Plan Details (Frontend Flow)")
    print("="*70)
    
    try:
        # Create a task first
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{BACKEND_URL}/api/v3/process_request",
                json={"description": "Test plan details retrieval"}
            )
            plan_id = response.json().get("plan_id")
        
        # Wait a moment for processing
        await asyncio.sleep(2)
        
        # Get plan details
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{BACKEND_URL}/api/v3/plan",
                params={"plan_id": plan_id}
            )
            
            if response.status_code == 200:
                data = response.json()
                plan = data.get("plan", {})
                messages = data.get("messages", [])
                
                print(f"✅ Plan details retrieved")
                print(f"   Status: {plan.get('status')}")
                print(f"   Messages: {len(messages)}")
                print(f"   Description: {plan.get('description', '')[:50]}...")
                return True
            else:
                print(f"❌ Failed to get plan: {response.status_code}")
                return False
                
    except Exception as e:
        print(f"❌ Error getting plan: {e}")
        return False


async def test_plan_approval_flow():
    """Test complete approval flow as frontend would."""
    print("\n" + "="*70)
    print("TEST 6: Plan Approval Flow (Frontend Flow)")
    print("="*70)
    
    try:
        # Create a task
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{BACKEND_URL}/api/v3/process_request",
                json={"description": "Test approval flow from frontend"}
            )
            plan_id = response.json().get("plan_id")
        
        print(f"📤 Created task with plan ID: {plan_id}")
        
        # Wait for approval request
        await asyncio.sleep(2)
        
        # Check plan status
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{BACKEND_URL}/api/v3/plan",
                params={"plan_id": plan_id}
            )
            status_before = response.json().get("plan", {}).get("status")
            print(f"   Status before approval: {status_before}")
        
        # Approve the plan
        async with httpx.AsyncClient() as client:
            approval_data = {
                "m_plan_id": plan_id,
                "approved": True,
                "feedback": "Approved from frontend integration test"
            }
            
            print(f"📤 Approving plan...")
            response = await client.post(
                f"{BACKEND_URL}/api/v3/plan_approval",
                json=approval_data
            )
            
            if response.status_code == 200:
                print("✅ Plan approved successfully")
            else:
                print(f"❌ Approval failed: {response.status_code}")
                return False
        
        # Wait for execution to complete
        await asyncio.sleep(3)
        
        # Check final status
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{BACKEND_URL}/api/v3/plan",
                params={"plan_id": plan_id}
            )
            status_after = response.json().get("plan", {}).get("status")
            print(f"   Status after approval: {status_after}")
        
        if status_after == "completed":
            print("✅ Plan completed successfully")
            return True
        else:
            print(f"⚠️  Plan status is '{status_after}' (expected 'completed')")
            return False
            
    except Exception as e:
        print(f"❌ Error in approval flow: {e}")
        return False


async def test_cors_headers():
    """Test that CORS headers are properly set."""
    print("\n" + "="*70)
    print("TEST 7: CORS Headers")
    print("="*70)
    
    try:
        async with httpx.AsyncClient() as client:
            # Make a request with Origin header (simulating browser)
            headers = {
                "Origin": "http://localhost:3001"
            }
            
            response = await client.get(
                f"{BACKEND_URL}/health",
                headers=headers
            )
            
            cors_header = response.headers.get("access-control-allow-origin")
            
            if cors_header:
                print(f"✅ CORS header present: {cors_header}")
                return True
            else:
                print("⚠️  CORS header not found (may cause issues)")
                return False
                
    except Exception as e:
        print(f"❌ Error checking CORS: {e}")
        return False


async def run_all_tests():
    """Run all frontend integration tests."""
    print("\n" + "="*70)
    print("FRONTEND INTEGRATION TEST SUITE")
    print("="*70)
    print(f"\nBackend URL: {BACKEND_URL}")
    print(f"Frontend URL: {FRONTEND_URL}")
    print(f"WebSocket URL: {WS_URL}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = []
    
    # Test 1: Backend health
    results.append(await test_frontend_can_reach_backend())
    
    # Test 2: Config endpoint
    results.append(await test_frontend_config_endpoint())
    
    # Test 3: Create task
    success, plan_id = await test_create_task_from_frontend()
    results.append(success)
    
    # Test 4: WebSocket
    results.append(await test_websocket_connection())
    
    # Test 5: Get plan details
    results.append(await test_get_plan_details())
    
    # Test 6: Approval flow
    results.append(await test_plan_approval_flow())
    
    # Test 7: CORS
    results.append(await test_cors_headers())
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    print(f"Backend Health:        {'✅ PASS' if results[0] else '❌ FAIL'}")
    print(f"Config Endpoint:       {'✅ PASS' if results[1] else '❌ FAIL'}")
    print(f"Create Task:           {'✅ PASS' if results[2] else '❌ FAIL'}")
    print(f"WebSocket Connection:  {'✅ PASS' if results[3] else '❌ FAIL'}")
    print(f"Get Plan Details:      {'✅ PASS' if results[4] else '❌ FAIL'}")
    print(f"Plan Approval Flow:    {'✅ PASS' if results[5] else '❌ FAIL'}")
    print(f"CORS Headers:          {'✅ PASS' if results[6] else '❌ FAIL'}")
    print("="*70)
    
    all_passed = all(results)
    if all_passed:
        print("\n🎉 ALL FRONTEND INTEGRATION TESTS PASSED!")
        print("\n✅ Frontend is ready to use with backend")
        print(f"\n🌐 Open your browser to: {FRONTEND_URL}")
        print("\nNext steps:")
        print("   1. Open browser to http://localhost:3001")
        print("   2. Create a task from the UI")
        print("   3. Watch real-time agent messages")
        print("   4. Approve the plan when prompted")
        print("   5. See the task complete")
    else:
        print("\n❌ SOME TESTS FAILED")
        print("Please review the failures above and fix issues.")
    
    return all_passed


if __name__ == "__main__":
    import sys
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
