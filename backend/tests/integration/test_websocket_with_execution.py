#!/usr/bin/env python3
"""
Test WebSocket with actual agent execution
"""
import asyncio
import aiohttp
import websockets
import json

async def test_websocket_with_execution():
    print("🔍 Testing WebSocket with Agent Execution")
    print("=" * 60)
    
    base_url = "http://localhost:8000/api"
    
    async with aiohttp.ClientSession() as session:
        # 1. Create a plan using the v2 endpoint (same as frontend)
        print("1️⃣ Creating plan with v2 endpoint...")
        try:
            async with session.post(
                f"{base_url}/v3/process_request_v2",
                json={"description": "analyze TBI-001 communications", "session_id": "websocket-execution-test"}
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
        
        # 2. Connect to WebSocket immediately
        print("2️⃣ Connecting to WebSocket...")
        try:
            uri = f"ws://localhost:8000/api/v3/socket/{plan_id}?user_id=websocket-execution-test"
            async with websockets.connect(uri) as websocket:
                message_count = 0
                agent_messages = 0
                streaming_messages = 0
                
                print("   📡 Listening for messages...")
                
                while message_count < 30:  # Listen for more messages
                    try:
                        message_raw = await asyncio.wait_for(websocket.recv(), timeout=15.0)
                        message = json.loads(message_raw)
                        message_count += 1
                        
                        msg_type = message.get("type", "unknown")
                        
                        if msg_type == "agent_message":
                            agent_messages += 1
                            data = message.get("data", {})
                            agent = data.get("agent_name", "unknown")
                            content_len = len(data.get("content", ""))
                            print(f"📨 Agent Message {agent_messages}: {agent} ({content_len} chars)")
                            
                            # Show structure for debugging
                            print(f"   📊 Structure: {list(message.keys())}")
                            if 'data' in message:
                                print(f"   📊 Data keys: {list(message['data'].keys())}")
                            
                        elif msg_type == "agent_message_streaming":
                            streaming_messages += 1
                            data = message.get("data", {})
                            agent = data.get("agent_name", "unknown")
                            content = data.get("content", "")
                            is_complete = data.get("is_complete", False)
                            print(f"📡 Streaming {streaming_messages}: {agent} - {len(content)} chars - Complete: {is_complete}")
                            
                        elif msg_type == "final_result_message":
                            print(f"🎯 Final result received")
                            break
                            
                        elif msg_type == "comprehensive_results_ready":
                            print(f"📋 Comprehensive results ready")
                            
                        elif msg_type not in ["connection_established", "ping"]:
                            print(f"📋 Other: {msg_type}")
                            
                    except asyncio.TimeoutError:
                        print(f"   ⏰ Timeout after {message_count} messages")
                        break
                    except Exception as e:
                        print(f"   ❌ Error: {e}")
                        break
                
                print(f"\n📊 Summary:")
                print(f"   - Total messages: {message_count}")
                print(f"   - Agent messages: {agent_messages}")
                print(f"   - Streaming messages: {streaming_messages}")
                
        except Exception as e:
            print(f"   ❌ WebSocket error: {e}")
        
        print("\n" + "="*60)
        print("🎯 WEBSOCKET EXECUTION TEST RESULTS")
        print("="*60)
        print("📋 Check if WebSocket receives agent execution messages")
        
        return True

if __name__ == "__main__":
    asyncio.run(test_websocket_with_execution())