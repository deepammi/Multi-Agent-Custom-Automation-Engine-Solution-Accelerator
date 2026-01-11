#!/usr/bin/env python3
"""
Quick TBI Analysis Test - Shows real agent response
"""
import asyncio
import json
import aiohttp
import websockets

async def test_tbi_analysis():
    print("🔍 TBI Analysis Test")
    print("=" * 50)
    
    # Submit the TBI query
    query = "analyze all bills and communications with keyword TBI-001 or TBI Corp"
    
    async with aiohttp.ClientSession() as session:
        async with session.post(
            "http://localhost:8000/api/v3/process_request",
            json={"description": query, "session_id": "tbi-test"}
        ) as response:
            data = await response.json()
            plan_id = data["plan_id"]
            print(f"📤 Query: {query}")
            print(f"📋 Plan ID: {plan_id}")
    
    # Connect to WebSocket and capture the agent response
    ws_url = f"ws://localhost:8000/api/v3/socket/{plan_id}?user_id=tbi-user"
    
    try:
        async with websockets.connect(ws_url) as websocket:
            print("🔌 Connected - waiting for agent response...")
            
            agent_response = ""
            capturing = False
            
            for _ in range(50):  # Listen for up to 50 messages
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=3.0)
                    data = json.loads(message)
                    msg_type = data.get("type", "")
                    
                    if msg_type == "agent_stream_start":
                        print("🚀 Agent starting analysis...")
                        capturing = True
                        agent_response = ""
                    
                    elif msg_type == "agent_message_streaming" and capturing:
                        content = data.get("data", {}).get("content", "")
                        agent_response += content
                    
                    elif msg_type == "agent_stream_end" and capturing:
                        print("✅ Agent analysis complete!")
                        break
                        
                except asyncio.TimeoutError:
                    if not capturing:
                        print(".", end="", flush=True)
                    continue
                except Exception as e:
                    print(f"Error: {e}")
                    break
            
            # Display the agent's analysis
            if agent_response:
                print("\n" + "="*80)
                print("🤖 AGENT ANALYSIS RESPONSE")
                print("="*80)
                
                # Extract key sections
                lines = agent_response.split('\n')
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                    
                    # Highlight important information
                    if 'TBI-001' in line or 'TBI Corp' in line:
                        print(f"🔍 {line}")
                    elif line.startswith('###') or line.startswith('**'):
                        print(f"\n📋 {line.replace('###', '').replace('**', '').strip()}")
                    elif line.startswith('*') and ('Missing' in line or 'Pricing' in line or 'Duplicate' in line):
                        print(f"⚠️  {line}")
                    elif 'Required Information' in line or 'My Analysis Focus' in line:
                        print(f"📊 {line}")
                    elif len(line) > 50:  # Long descriptive lines
                        print(f"   {line}")
                
                print("="*80)
                print(f"📈 Response Length: {len(agent_response)} characters")
                print("✅ TBI analysis completed successfully!")
            else:
                print("❌ No agent response captured")
    
    except Exception as e:
        print(f"❌ WebSocket error: {e}")

if __name__ == "__main__":
    asyncio.run(test_tbi_analysis())