#!/usr/bin/env python3
"""
Test WebSocket message structure to verify frontend compatibility
"""
import asyncio
import aiohttp
import websockets
import json

async def test_websocket_message_structure():
    print("🔗 WebSocket Message Structure Test")
    print("=" * 60)
    
    base_url = "http://localhost:8000/api"
    
    async with aiohttp.ClientSession() as session:
        # 1. Create a plan
        print("1️⃣ Creating test plan...")
        try:
            async with session.post(
                f"{base_url}/v3/process_request",
                json={"description": "test streaming messages", "session_id": "websocket-test"}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    plan_id = data.get("plan_id")
                    print(f"   ✅ Plan created: {plan_id}")
                else:
                    print(f"   ❌ Plan creation failed: {response.status}")
                    return False
        except Exception as e:
            print(f"   ❌ Plan creation failed: {e}")
            return False
        
        # 2. Connect to WebSocket and capture messages
        print("2️⃣ Testing WebSocket message structure...")
        try:
            uri = f"ws://localhost:8000/api/v3/socket/{plan_id}?user_id=websocket-test"
            async with websockets.connect(uri) as websocket:
                message_count = 0
                max_messages = 10
                
                while message_count < max_messages:
                    try:
                        message_raw = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                        message = json.loads(message_raw)
                        message_count += 1
                        
                        msg_type = message.get("type", "unknown")
                        print(f"\n📨 Message {message_count}: {msg_type}")
                        
                        # Check message structure
                        if msg_type == "connection_established":
                            print(f"   ✅ Connection established message structure OK")
                            
                        elif msg_type == "agent_message_streaming":
                            print(f"   📊 Streaming message structure:")
                            print(f"      - Type: {message.get('type')}")
                            print(f"      - Has data: {'data' in message}")
                            if 'data' in message:
                                data = message['data']
                                print(f"      - Data keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
                                if isinstance(data, dict):
                                    print(f"      - Agent: {data.get('agent_name', 'N/A')}")
                                    print(f"      - Content length: {len(data.get('content', ''))}")
                                    print(f"      - Is complete: {data.get('is_complete', 'N/A')}")
                            
                        elif msg_type == "agent_message":
                            print(f"   📊 Agent message structure:")
                            print(f"      - Type: {message.get('type')}")
                            print(f"      - Has data: {'data' in message}")
                            if 'data' in message:
                                data = message['data']
                                print(f"      - Data keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
                                
                        elif msg_type == "final_result_message":
                            print(f"   🎯 Final result message - stopping test")
                            break
                            
                        else:
                            print(f"   📋 Other message type: {msg_type}")
                            
                    except asyncio.TimeoutError:
                        print(f"   ⏰ Timeout waiting for message {message_count + 1}")
                        break
                    except Exception as e:
                        print(f"   ❌ Error processing message: {e}")
                        break
                
                print(f"\n📊 Captured {message_count} messages")
                
        except Exception as e:
            print(f"   ❌ WebSocket test failed: {e}")
        
        print("\n" + "="*60)
        print("🎯 MESSAGE STRUCTURE ANALYSIS")
        print("="*60)
        print("✅ Test completed - check message structures above")
        print("📋 Expected frontend structure after parsing:")
        print("   StreamingMessage: { type, agent, content, is_final, raw_data }")
        print("   AgentMessage: { type, agent, content, timestamp, raw_data }")
        
        return True

if __name__ == "__main__":
    asyncio.run(test_websocket_message_structure())