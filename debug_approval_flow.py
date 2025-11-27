"""
Debug script to trace the approval flow and identify where it's hanging.
"""
import asyncio
import httpx
import websockets
import json
from datetime import datetime

BACKEND_URL = "http://localhost:8000"
WS_URL = "ws://localhost:8000"


async def debug_approval_flow():
    """Debug the complete approval flow step by step."""
    print("\n" + "="*70)
    print("DEBUGGING APPROVAL FLOW")
    print("="*70)
    
    try:
        # Step 1: Create task
        print("\n[STEP 1] Creating task...")
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{BACKEND_URL}/api/v3/process_request",
                json={"description": "I want to automate invoice analysis for accuracy and then submit for human validation"}
            )
            data = response.json()
            plan_id = data.get("plan_id")
            print(f"✅ Task created: {plan_id}")
        
        # Step 2: Connect to WebSocket
        print("\n[STEP 2] Connecting to WebSocket...")
        uri = f"{WS_URL}/api/v3/socket/{plan_id}?user_id=debug_user"
        
        messages_received = []
        approval_request_received = False
        
        async with websockets.connect(uri) as websocket:
            print(f"✅ WebSocket connected")
            
            # Step 3: Wait for messages
            print("\n[STEP 3] Waiting for messages (10 seconds timeout)...")
            try:
                for i in range(20):
                    message = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                    data = json.loads(message)
                    messages_received.append(data)
                    
                    msg_type = data.get("type")
                    print(f"   📨 Message {i+1}: {msg_type}")
                    
                    if msg_type == "plan_approval_request":
                        approval_request_received = True
                        print(f"   ✅ Approval request received!")
                        break
            except asyncio.TimeoutError:
                print(f"   ⏱️  Timeout after {len(messages_received)} messages")
            
            if not approval_request_received:
                print("\n❌ ERROR: Approval request not received!")
                print(f"   Messages received: {len(messages_received)}")
                for i, msg in enumerate(messages_received):
                    print(f"   {i+1}. {msg.get('type')}: {msg.get('data', {}).get('content', '')[:50]}")
                return False
            
            # Step 4: Send approval
            print("\n[STEP 4] Sending approval...")
            async with httpx.AsyncClient() as client:
                approval_response = await client.post(
                    f"{BACKEND_URL}/api/v3/plan_approval",
                    json={
                        "m_plan_id": plan_id,
                        "approved": True,
                        "feedback": "Approved for testing"
                    }
                )
                approval_data = approval_response.json()
                print(f"✅ Approval sent: {approval_data.get('status')}")
            
            # Step 5: Wait for specialized agent response
            print("\n[STEP 5] Waiting for specialized agent response (15 seconds timeout)...")
            agent_messages_received = 0
            final_result_received = False
            
            try:
                for i in range(30):
                    message = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                    data = json.loads(message)
                    messages_received.append(data)
                    
                    msg_type = data.get("type")
                    print(f"   📨 Message {len(messages_received)}: {msg_type}")
                    
                    if msg_type == "agent_message":
                        agent_name = data.get("data", {}).get("agent_name", "Unknown")
                        content = data.get("data", {}).get("content", "")[:60]
                        print(f"      Agent: {agent_name}")
                        print(f"      Content: {content}...")
                        agent_messages_received += 1
                    
                    elif msg_type == "final_result_message":
                        final_result_received = True
                        content = data.get("data", {}).get("content", "")[:100]
                        print(f"   ✅ Final result received!")
                        print(f"      Content: {content}...")
                        break
            except asyncio.TimeoutError:
                print(f"   ⏱️  Timeout after {agent_messages_received} agent messages")
            
            if not final_result_received:
                print("\n⚠️  WARNING: Final result not received!")
                print(f"   Agent messages received: {agent_messages_received}")
            else:
                print("\n✅ SUCCESS: Complete flow worked!")
        
        # Step 6: Verify plan status
        print("\n[STEP 6] Verifying final plan status...")
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{BACKEND_URL}/api/v3/plan?plan_id={plan_id}")
            plan_data = response.json()
            plan = plan_data.get("plan", {})
            messages = plan_data.get("messages", [])
            
            status = plan.get("status")
            print(f"   Plan status: {status}")
            print(f"   Total messages in DB: {len(messages)}")
            print(f"   Total WebSocket messages: {len(messages_received)}")
        
        # Summary
        print("\n" + "="*70)
        print("DEBUG SUMMARY")
        print("="*70)
        print(f"✅ Task created: {plan_id}")
        print(f"✅ WebSocket connected")
        print(f"✅ Planner message received")
        print(f"✅ Approval request received")
        print(f"✅ Approval sent")
        print(f"{'✅' if agent_messages_received > 0 else '❌'} Agent messages received: {agent_messages_received}")
        print(f"{'✅' if final_result_received else '❌'} Final result received: {final_result_received}")
        print(f"✅ Plan status: {status}")
        
        if final_result_received and status == "completed":
            print("\n🎉 FLOW WORKING CORRECTLY!")
            return True
        else:
            print("\n❌ FLOW HAS ISSUES - See details above")
            return False
            
    except Exception as e:
        print(f"\n❌ Error during debugging: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    import sys
    success = asyncio.run(debug_approval_flow())
    sys.exit(0 if success else 1)
