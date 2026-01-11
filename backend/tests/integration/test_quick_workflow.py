#!/usr/bin/env python3
"""
Quick test to see actual agent message content
"""
import asyncio
import json
import aiohttp
import websockets

async def test_quick_workflow():
    print("🧪 Quick Workflow Test")
    print("======================")
    
    # Submit task
    async with aiohttp.ClientSession() as session:
        async with session.post(
            "http://localhost:8000/api/v3/process_request",
            json={"description": "Find invoice INV-001 and check its status", "session_id": "test"}
        ) as response:
            data = await response.json()
            plan_id = data["plan_id"]
            print(f"📤 Task submitted: {plan_id}")
    
    # Connect to WebSocket and listen for messages
    ws_url = f"ws://localhost:8000/api/v3/socket/{plan_id}?user_id=test-user"
    
    try:
        async with websockets.connect(ws_url) as websocket:
            print("🔌 WebSocket connected")
            
            message_count = 0
            for _ in range(10):  # Listen for first 10 messages
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    data = json.loads(message)
                    message_count += 1
                    
                    msg_type = data.get("type", "unknown")
                    print(f"\n📨 Message {message_count}: {msg_type}")
                    
                    if msg_type == "agent_message_streaming":
                        content = data.get("data", {}).get("content", "")
                        if content:
                            print(f"   💬 Content: {content[:100]}...")
                    elif msg_type == "system_message":
                        message_text = data.get("data", {}).get("message", "")
                        print(f"   🔧 System: {message_text}")
                    elif msg_type == "agent_stream_start":
                        agent = data.get("data", {}).get("agent_name", "Unknown")
                        print(f"   🚀 Agent {agent} starting...")
                    elif msg_type == "agent_stream_end":
                        agent = data.get("data", {}).get("agent_name", "Unknown")
                        print(f"   ✅ Agent {agent} completed")
                    
                except asyncio.TimeoutError:
                    print("⏰ Timeout waiting for message")
                    break
                except Exception as e:
                    print(f"❌ Error: {e}")
                    break
            
            print(f"\n📊 Received {message_count} messages")
            
    except Exception as e:
        print(f"❌ WebSocket error: {e}")

if __name__ == "__main__":
    asyncio.run(test_quick_workflow())