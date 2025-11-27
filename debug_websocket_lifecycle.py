"""
WebSocket Connection Lifecycle Debugging Script
Traces the complete WebSocket connection lifecycle from task creation through approval and agent execution.
"""
import asyncio
import httpx
import websockets
import json
from datetime import datetime
import time

BACKEND_URL = "http://localhost:8000"
WS_URL = "ws://localhost:8000"


class WebSocketLifecycleDebugger:
    """Debug WebSocket connection lifecycle."""
    
    def __init__(self):
        self.connection_events = []
        self.message_events = []
        self.start_time = time.time()
    
    def log_event(self, event_type, message, details=None):
        """Log an event with timestamp."""
        elapsed = time.time() - self.start_time
        event = {
            "timestamp": elapsed,
            "type": event_type,
            "message": message,
            "details": details
        }
        self.connection_events.append(event)
        print(f"[{elapsed:6.2f}s] {event_type:20s} | {message}")
        if details:
            print(f"{'':20s} | Details: {details}")
    
    def log_message(self, msg_type, content_preview):
        """Log a message event."""
        elapsed = time.time() - self.start_time
        event = {
            "timestamp": elapsed,
            "type": "MESSAGE",
            "msg_type": msg_type,
            "content": content_preview
        }
        self.message_events.append(event)
        print(f"[{elapsed:6.2f}s] {'MESSAGE':20s} | {msg_type:30s} | {content_preview}")
    
    def print_summary(self):
        """Print summary of connection lifecycle."""
        print("\n" + "="*80)
        print("CONNECTION LIFECYCLE SUMMARY")
        print("="*80)
        print(f"\nTotal Duration: {self.connection_events[-1]['timestamp']:.2f}s")
        print(f"Total Events: {len(self.connection_events)}")
        print(f"Total Messages: {len(self.message_events)}")
        
        print("\n--- Connection Events ---")
        for event in self.connection_events:
            print(f"[{event['timestamp']:6.2f}s] {event['type']:20s} | {event['message']}")
        
        print("\n--- Messages Received ---")
        for msg in self.message_events:
            print(f"[{msg['timestamp']:6.2f}s] {msg['msg_type']:30s}")


async def debug_websocket_lifecycle():
    """Debug the complete WebSocket lifecycle."""
    debugger = WebSocketLifecycleDebugger()
    
    print("\n" + "="*80)
    print("WEBSOCKET CONNECTION LIFECYCLE DEBUG")
    print("="*80)
    
    try:
        # Step 1: Create task
        debugger.log_event("STEP", "Creating task...")
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{BACKEND_URL}/api/v3/process_request",
                json={"description": "I want to automate invoice analysis for accuracy"}
            )
            data = response.json()
            plan_id = data.get("plan_id")
            debugger.log_event("TASK_CREATED", f"Plan ID: {plan_id}")
        
        # Step 2: Connect to WebSocket
        debugger.log_event("STEP", "Connecting to WebSocket...")
        uri = f"{WS_URL}/api/v3/socket/{plan_id}?user_id=debug_user"
        
        connection_established = False
        approval_sent_time = None
        last_message_time = None
        
        async with websockets.connect(uri) as websocket:
            debugger.log_event("WS_CONNECTED", "WebSocket connection established")
            connection_established = True
            
            # Step 3: Receive initial messages (planner + approval request)
            debugger.log_event("STEP", "Waiting for planner and approval request (10s timeout)...")
            
            try:
                for i in range(20):
                    message = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                    data = json.loads(message)
                    last_message_time = time.time()
                    
                    msg_type = data.get("type")
                    content_preview = data.get("data", {}).get("content", "")[:40]
                    debugger.log_message(msg_type, content_preview)
                    
                    if msg_type == "plan_approval_request":
                        debugger.log_event("APPROVAL_REQUEST", "Approval request received")
                        break
            except asyncio.TimeoutError:
                debugger.log_event("TIMEOUT", "No more messages in initial phase")
            
            # Step 4: Send approval
            debugger.log_event("STEP", "Sending approval...")
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{BACKEND_URL}/api/v3/plan_approval",
                    json={
                        "m_plan_id": plan_id,
                        "approved": True,
                        "feedback": "Approved for testing"
                    }
                )
                approval_sent_time = time.time()
                debugger.log_event("APPROVAL_SENT", f"Response: {response.json().get('status')}")
            
            # Step 5: Wait for agent messages after approval
            debugger.log_event("STEP", "Waiting for agent messages after approval (20s timeout)...")
            
            agent_messages_received = 0
            final_result_received = False
            
            try:
                for i in range(40):
                    try:
                        message = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                        data = json.loads(message)
                        last_message_time = time.time()
                        
                        msg_type = data.get("type")
                        content_preview = data.get("data", {}).get("content", "")[:40]
                        debugger.log_message(msg_type, content_preview)
                        
                        if msg_type == "agent_message":
                            agent_messages_received += 1
                        elif msg_type == "final_result_message":
                            final_result_received = True
                            debugger.log_event("FINAL_RESULT", "Final result received")
                            break
                    
                    except asyncio.TimeoutError:
                        if i > 0:  # Only log after first iteration
                            debugger.log_event("TIMEOUT", f"No message for {i+1} seconds")
                        continue
            
            except Exception as e:
                debugger.log_event("ERROR", f"Error receiving messages: {str(e)}")
            
            # Step 6: Check connection status
            debugger.log_event("STEP", "Checking WebSocket connection status...")
            try:
                # Try to send a ping
                await websocket.send(json.dumps({"type": "ping"}))
                debugger.log_event("PING_SENT", "Ping sent successfully")
                
                # Try to receive pong
                pong = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                pong_data = json.loads(pong)
                debugger.log_event("PONG_RECEIVED", f"Pong received: {pong_data.get('type')}")
            except asyncio.TimeoutError:
                debugger.log_event("PING_TIMEOUT", "No pong received - connection may be dead")
            except Exception as e:
                debugger.log_event("PING_ERROR", f"Error sending ping: {str(e)}")
        
        # Connection closed
        debugger.log_event("WS_CLOSED", "WebSocket connection closed")
        
        # Step 7: Verify backend state
        debugger.log_event("STEP", "Verifying backend state...")
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{BACKEND_URL}/api/v3/plan?plan_id={plan_id}")
            plan_data = response.json()
            plan = plan_data.get("plan", {})
            messages = plan_data.get("messages", [])
            
            status = plan.get("status")
            debugger.log_event("PLAN_STATUS", f"Status: {status}, Messages in DB: {len(messages)}")
        
        # Print summary
        debugger.print_summary()
        
        # Analysis
        print("\n" + "="*80)
        print("ANALYSIS")
        print("="*80)
        
        if approval_sent_time and last_message_time:
            time_after_approval = last_message_time - approval_sent_time
            print(f"\n✅ Time from approval to last message: {time_after_approval:.2f}s")
        else:
            print(f"\n❌ No messages received after approval")
        
        if agent_messages_received > 0:
            print(f"✅ Agent messages received: {agent_messages_received}")
        else:
            print(f"❌ No agent messages received")
        
        if final_result_received:
            print(f"✅ Final result received")
        else:
            print(f"❌ Final result NOT received")
        
        if connection_established:
            print(f"✅ WebSocket connection established")
        else:
            print(f"❌ WebSocket connection failed")
        
        # Recommendations
        print("\n" + "="*80)
        print("RECOMMENDATIONS")
        print("="*80)
        
        if not agent_messages_received:
            print("\n⚠️  No agent messages received after approval. Possible causes:")
            print("   1. Backend not sending messages after approval")
            print("   2. WebSocket connection closing after approval")
            print("   3. Messages being sent but not received by client")
            print("   4. Backend background task not executing")
        
        if final_result_received and agent_messages_received == 0:
            print("\n⚠️  Final result received but no agent messages. This is unusual.")
            print("   Check if messages are being buffered or skipped.")
        
        if not final_result_received and agent_messages_received > 0:
            print("\n⚠️  Agent messages received but no final result.")
            print("   Check if backend is sending final_result_message.")
        
        return {
            "connection_established": connection_established,
            "agent_messages_received": agent_messages_received,
            "final_result_received": final_result_received,
            "plan_status": status,
            "messages_in_db": len(messages)
        }
        
    except Exception as e:
        debugger.log_event("FATAL_ERROR", f"Fatal error: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    import sys
    result = asyncio.run(debug_websocket_lifecycle())
    
    if result:
        print("\n" + "="*80)
        print("FINAL RESULT")
        print("="*80)
        print(f"Connection Established: {result['connection_established']}")
        print(f"Agent Messages Received: {result['agent_messages_received']}")
        print(f"Final Result Received: {result['final_result_received']}")
        print(f"Plan Status: {result['plan_status']}")
        print(f"Messages in DB: {result['messages_in_db']}")
        
        success = (result['connection_established'] and 
                  result['agent_messages_received'] > 0 and 
                  result['final_result_received'])
        
        if success:
            print("\n🎉 WEBSOCKET LIFECYCLE WORKING CORRECTLY!")
            sys.exit(0)
        else:
            print("\n❌ WEBSOCKET LIFECYCLE HAS ISSUES")
            sys.exit(1)
    else:
        print("\n❌ FATAL ERROR - Could not complete test")
        sys.exit(1)
