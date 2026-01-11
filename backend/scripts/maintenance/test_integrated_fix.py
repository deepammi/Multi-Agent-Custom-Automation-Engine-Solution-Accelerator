#!/usr/bin/env python3
"""
Test the integrated workflow fix to ensure the frontend integration works.
"""

import asyncio
import logging
import sys
import os
import json
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

import requests
import websockets
from app.db.mongodb import MongoDB

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def test_integrated_fix():
    """Test the complete integrated workflow after the fix."""
    
    try:
        logger.info("🚀 Testing integrated workflow after WebSocket fix")
        logger.info("📡 Using existing backend at http://localhost:8000")
        
        # Initialize database connection
        logger.info("🔗 Connecting to database...")
        MongoDB.connect()
        logger.info("✅ Database connected")
        
        # Test task that should trigger Planner -> Email workflow
        test_task = "Find emails from Acme Marketing about Invoice number 1001 over the last 2 months"
        
        logger.info(f"📝 Testing task: {test_task}")
        
        # Step 1: Submit task to process_request endpoint
        logger.info("📤 Step 1: Submitting task to /api/v3/process_request...")
        
        process_request_data = {
            "description": test_task,
            "session_id": None,
            "team_id": None
        }
        
        response = requests.post(
            "http://localhost:8000/api/v3/process_request",
            json=process_request_data,
            timeout=30
        )
        
        if response.status_code != 200:
            logger.error(f"❌ Process request failed: {response.status_code} - {response.text}")
            return
        
        result = response.json()
        plan_id = result.get("plan_id")
        session_id = result.get("session_id")
        
        logger.info(f"✅ Task submitted successfully")
        logger.info(f"   Plan ID: {plan_id}")
        logger.info(f"   Session ID: {session_id}")
        logger.info(f"   Status: {result.get('status')}")
        
        # Step 2: Monitor WebSocket for real-time updates
        logger.info("🔌 Step 2: Connecting to WebSocket for real-time updates...")
        
        websocket_url = f"ws://localhost:8000/api/v3/socket/{plan_id}?user_id=test_user"
        
        try:
            async with websockets.connect(websocket_url) as websocket:
                logger.info("✅ WebSocket connected")
                
                # Listen for messages for up to 60 seconds
                timeout_seconds = 60
                start_time = asyncio.get_event_loop().time()
                
                messages_received = []
                agents_executed = []
                
                while (asyncio.get_event_loop().time() - start_time) < timeout_seconds:
                    try:
                        # Wait for message with timeout
                        message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                        
                        try:
                            parsed_message = json.loads(message)
                            messages_received.append(parsed_message)
                            
                            msg_type = parsed_message.get("type", "unknown")
                            
                            if msg_type == "agent_message":
                                data = parsed_message.get("data", {})
                                agent_name = data.get("agent_name", "Unknown")
                                content = data.get("content", "")
                                status = data.get("status", "unknown")
                                
                                logger.info(f"📨 {agent_name} Agent: {status}")
                                if agent_name not in agents_executed:
                                    agents_executed.append(agent_name)
                                
                                if content:
                                    # Truncate long content for readability
                                    display_content = content[:200] + "..." if len(content) > 200 else content
                                    logger.info(f"   Content: {display_content}")
                            
                            elif msg_type == "final_result_message":
                                data = parsed_message.get("data", {})
                                logger.info("🎯 Final Result Received!")
                                logger.info(f"   Content: {data.get('content', '')[:300]}...")
                                break
                            
                            elif msg_type == "agent_stream_start":
                                data = parsed_message.get("data", {})
                                agent_name = data.get("agent_name", "Unknown")
                                logger.info(f"🌊 {agent_name} Agent: Starting stream...")
                            
                            elif msg_type == "agent_stream_end":
                                data = parsed_message.get("data", {})
                                agent_name = data.get("agent_name", "Unknown")
                                logger.info(f"🏁 {agent_name} Agent: Stream ended")
                            
                            else:
                                logger.info(f"📩 Message type: {msg_type}")
                        
                        except json.JSONDecodeError:
                            logger.warning(f"⚠️ Received non-JSON message: {message}")
                    
                    except asyncio.TimeoutError:
                        # No message received in timeout period, continue listening
                        continue
                    except websockets.exceptions.ConnectionClosed:
                        logger.info("🔌 WebSocket connection closed")
                        break
                
                logger.info(f"📊 Total messages received: {len(messages_received)}")
                logger.info(f"📊 Agents executed: {' → '.join(agents_executed)}")
        
        except Exception as e:
            logger.error(f"❌ WebSocket connection failed: {e}")
        
        # Step 3: Get final plan details
        logger.info("📋 Step 3: Retrieving final plan details...")
        
        plan_response = requests.get(
            f"http://localhost:8000/api/v3/plan?plan_id={plan_id}",
            timeout=10
        )
        
        if plan_response.status_code == 200:
            plan_data = plan_response.json()
            
            logger.info("✅ Final plan retrieved")
            logger.info(f"   Plan status: {plan_data.get('plan', {}).get('status', 'unknown')}")
            
            messages = plan_data.get('messages', [])
            logger.info(f"   Total messages: {len(messages)}")
            
            # Show agent execution sequence
            agents_executed_final = []
            for msg in messages:
                agent_name = msg.get('agent_name', 'Unknown')
                if agent_name not in agents_executed_final:
                    agents_executed_final.append(agent_name)
            
            logger.info(f"   Final agents executed: {' → '.join(agents_executed_final)}")
            
            # Check if Planner was executed first
            if agents_executed_final and agents_executed_final[0] == "Planner":
                logger.info("✅ Planner Agent executed first (correct routing)")
            else:
                logger.warning(f"⚠️ Expected Planner first, got: {agents_executed_final[0] if agents_executed_final else 'None'}")
            
            # Check if Email agent was executed
            if "Email" in agents_executed_final or "Gmail" in agents_executed_final:
                logger.info("✅ Email/Gmail Agent executed (correct for email task)")
            else:
                logger.warning("⚠️ Email/Gmail Agent not executed for email task")
            
            # Show final result if available
            final_result = plan_data.get('streaming_message')
            if final_result:
                logger.info("📄 Final streaming result:")
                logger.info(f"   {final_result[:500]}...")
        
        else:
            logger.error(f"❌ Failed to retrieve plan: {plan_response.status_code}")
        
        logger.info("🎉 Integrated workflow test completed!")
        
    except Exception as e:
        logger.error(f"❌ Integrated workflow test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_integrated_fix())