"""
Phase 4 Validation Tests
Tests WebSocket streaming and real-time updates.
"""
import asyncio
import sys
import httpx
import websockets
import json

BASE_URL = "http://localhost:8000"
WS_URL = "ws://localhost:8000"


async def test_websocket_connection():
    """Test WebSocket connection establishment."""
    print("Testing WebSocket connection...")
    try:
        # Create a plan first
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{BASE_URL}/api/v3/process_request",
                json={"description": "Test WebSocket connection"}
            )
            plan_id = response.json().get("plan_id")
        
        # Connect to WebSocket
        uri = f"{WS_URL}/api/v3/socket/{plan_id}?user_id=test_user"
        async with websockets.connect(uri) as websocket:
            # Receive initial connection message
            message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
            data = json.loads(message)
            
            if data.get("type") == "agent_message":
                print(f"✅ WebSocket connection established")
                print(f"   Initial message: {data.get('data', {}).get('content', '')[:50]}...")
                return True
            else:
                print(f"❌ Unexpected message type: {data.get('type')}")
                return False
                
    except asyncio.TimeoutError:
        print("❌ WebSocket connection timeout")
        return False
    except Exception as e:
        print(f"❌ WebSocket connection error: {e}")
        return False


async def test_agent_message_streaming():
    """Test that agent messages are streamed via WebSocket."""
    print("\nTesting agent message streaming...")
    try:
        # Create a plan
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{BASE_URL}/api/v3/process_request",
                json={"description": "Test message streaming"}
            )
            plan_id = response.json().get("plan_id")
        
        # Connect to WebSocket and collect messages
        uri = f"{WS_URL}/api/v3/socket/{plan_id}?user_id=test_user"
        messages_received = []
        
        async with websockets.connect(uri) as websocket:
            # Collect messages for 5 seconds
            try:
                while len(messages_received) < 5:
                    message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    data = json.loads(message)
                    messages_received.append(data)
                    
                    if data.get("type") == "final_result_message":
                        break
            except asyncio.TimeoutError:
                pass
        
        # Verify we received messages
        agent_messages = [m for m in messages_received if m.get("type") == "agent_message"]
        final_messages = [m for m in messages_received if m.get("type") == "final_result_message"]
        
        print(f"   Received {len(agent_messages)} agent messages")
        print(f"   Received {len(final_messages)} final result messages")
        
        if len(agent_messages) > 0 and len(final_messages) > 0:
            print("✅ Agent messages streamed successfully")
            return True
        else:
            print("❌ Did not receive expected messages")
            return False
            
    except Exception as e:
        print(f"❌ Message streaming error: {e}")
        return False


async def test_final_result_message():
    """Test that final_result_message is sent on completion."""
    print("\nTesting final result message...")
    try:
        # Create a plan
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{BASE_URL}/api/v3/process_request",
                json={"description": "Test final result"}
            )
            plan_id = response.json().get("plan_id")
        
        # Connect and wait for final message
        uri = f"{WS_URL}/api/v3/socket/{plan_id}?user_id=test_user"
        
        async with websockets.connect(uri) as websocket:
            final_received = False
            
            try:
                for _ in range(10):  # Try up to 10 messages
                    message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    data = json.loads(message)
                    
                    if data.get("type") == "final_result_message":
                        final_received = True
                        content = data.get("data", {}).get("content", "")
                        status = data.get("data", {}).get("status", "")
                        print(f"   Final status: {status}")
                        print(f"   Content length: {len(content)} chars")
                        break
            except asyncio.TimeoutError:
                pass
        
        if final_received:
            print("✅ Final result message received")
            return True
        else:
            print("❌ Final result message not received")
            return False
            
    except Exception as e:
        print(f"❌ Final result test error: {e}")
        return False


async def test_multiple_connections():
    """Test multiple concurrent WebSocket connections."""
    print("\nTesting multiple concurrent connections...")
    try:
        # Create a plan
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{BASE_URL}/api/v3/process_request",
                json={"description": "Test multiple connections"}
            )
            plan_id = response.json().get("plan_id")
        
        # Connect with multiple clients
        uri = f"{WS_URL}/api/v3/socket/{plan_id}?user_id=test_user"
        
        async def connect_and_receive():
            async with websockets.connect(uri) as ws:
                message = await asyncio.wait_for(ws.recv(), timeout=5.0)
                return json.loads(message)
        
        # Create 3 concurrent connections
        results = await asyncio.gather(
            connect_and_receive(),
            connect_and_receive(),
            connect_and_receive(),
            return_exceptions=True
        )
        
        successful = sum(1 for r in results if isinstance(r, dict))
        
        print(f"   Successful connections: {successful}/3")
        
        if successful == 3:
            print("✅ Multiple connections work correctly")
            return True
        else:
            print("❌ Some connections failed")
            return False
            
    except Exception as e:
        print(f"❌ Multiple connections test error: {e}")
        return False


async def test_connection_cleanup():
    """Test that connections are cleaned up on disconnect."""
    print("\nTesting connection cleanup...")
    try:
        # Create a plan
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{BASE_URL}/api/v3/process_request",
                json={"description": "Test cleanup"}
            )
            plan_id = response.json().get("plan_id")
        
        # Connect and disconnect
        uri = f"{WS_URL}/api/v3/socket/{plan_id}?user_id=test_user"
        
        async with websockets.connect(uri) as websocket:
            await websocket.recv()  # Receive initial message
            # Connection will close when exiting context
        
        # Try to connect again (should work if cleanup is correct)
        async with websockets.connect(uri) as websocket:
            message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
            data = json.loads(message)
            
            if data.get("type") == "agent_message":
                print("✅ Connection cleanup works correctly")
                return True
            else:
                print("❌ Unexpected behavior after reconnection")
                return False
                
    except Exception as e:
        print(f"❌ Connection cleanup test error: {e}")
        return False


async def run_all_tests():
    """Run all Phase 4 validation tests."""
    print("=" * 60)
    print("PHASE 4 VALIDATION TESTS")
    print("=" * 60)
    print("\n⚠️  Make sure the backend server is running:")
    print("   python -m app.main")
    print()
    
    results = []
    
    # Test 1: WebSocket Connection
    results.append(await test_websocket_connection())
    
    # Test 2: Agent Message Streaming
    results.append(await test_agent_message_streaming())
    
    # Test 3: Final Result Message
    results.append(await test_final_result_message())
    
    # Test 4: Multiple Connections
    results.append(await test_multiple_connections())
    
    # Test 5: Connection Cleanup
    results.append(await test_connection_cleanup())
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"WebSocket Connection: {'✅ PASS' if results[0] else '❌ FAIL'}")
    print(f"Agent Message Streaming: {'✅ PASS' if results[1] else '❌ FAIL'}")
    print(f"Final Result Message: {'✅ PASS' if results[2] else '❌ FAIL'}")
    print(f"Multiple Connections: {'✅ PASS' if results[3] else '❌ FAIL'}")
    print(f"Connection Cleanup: {'✅ PASS' if results[4] else '❌ FAIL'}")
    print("=" * 60)
    
    all_passed = all(results)
    if all_passed:
        print("\n🎉 All Phase 4 tests PASSED!")
        print("✅ Ready to proceed to Phase 5")
    else:
        print("\n❌ Some tests FAILED. Please fix issues before proceeding.")
    
    return all_passed


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
