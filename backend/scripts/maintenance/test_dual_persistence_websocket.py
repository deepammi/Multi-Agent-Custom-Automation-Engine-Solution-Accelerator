#!/usr/bin/env python3
"""
Test dual persistence: both database and WebSocket message persistence.
"""

import asyncio
import logging
import sys
import os
import uuid
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from app.services.langgraph_service import LangGraphService
from app.services.websocket_service import get_websocket_manager, reset_websocket_manager
from app.db.mongodb import MongoDB
from app.db.repositories import MessageRepository, PlanRepository
from app.models.plan import Plan, Step

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestWebSocketManager:
    """Test WebSocket manager that integrates with the real system."""
    
    def __init__(self, plan_id: str):
        self.messages_sent = []
        self.connections = {plan_id: set(["mock-connection"])}
        self.connection_metadata = {}
        self.message_history = {}
        self.message_queue = {}
        self.progress_tracking = {}
        self.step_timings = {}
        self.plan_id = plan_id
    
    def get_connection_count(self, plan_id: str = None) -> int:
        """Return 1 for test plan to simulate active connection."""
        if plan_id:
            return len(self.connections.get(plan_id, set()))
        return sum(len(connections) for connections in self.connections.values())
    
    async def send_message(self, plan_id: str, message_data: dict, message_type: str = None, **kwargs):
        """Mock sending message via WebSocket - matches the real interface."""
        message = {
            "plan_id": plan_id,
            "message_data": message_data,
            "message_type": message_type,
            "timestamp": datetime.utcnow(),
            **kwargs
        }
        self.messages_sent.append(message)
        logger.info(f"📡 WebSocket: Sent {message_type} message for plan {plan_id}")
        
        # Extract and log content for debugging
        if isinstance(message_data, dict):
            data = message_data.get("data", {})
            content = data.get("content", "")
            agent_name = data.get("agent_name", "Unknown")
            if content:
                logger.info(f"   Content: {agent_name} - {content[:100]}...")
    
    async def send_agent_message(self, plan_id: str, agent_name: str, agent_type: str, content: str, **kwargs):
        """Mock sending agent message via WebSocket."""
        message_data = {
            "type": "agent_message",
            "data": {
                "plan_id": plan_id,
                "agent_name": agent_name,
                "agent_type": agent_type,
                "content": content,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        }
        await self.send_message(plan_id, message_data, "agent_message", **kwargs)
    
    async def send_final_result(self, plan_id: str, content: str, **kwargs):
        """Mock sending final result via WebSocket."""
        message_data = {
            "type": "final_result_message",
            "data": {
                "plan_id": plan_id,
                "content": content,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        }
        await self.send_message(plan_id, message_data, "final_result_message", **kwargs)
    
    def get_message_count(self):
        """Get number of messages sent via WebSocket."""
        return len(self.messages_sent)
    
    # Add other methods that might be called by the real system
    async def send_enhanced_progress_update(self, plan_id: str, current_step: int, total_steps: int, current_agent: str, **kwargs):
        """Mock progress update."""
        await self.send_message(plan_id, {
            "type": "progress_update",
            "data": {
                "plan_id": plan_id,
                "current_step": current_step,
                "total_steps": total_steps,
                "current_agent": current_agent,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        }, "progress_update")
    
    async def send_agent_streaming_start(self, plan_id: str, agent_name: str, **kwargs):
        """Mock streaming start."""
        await self.send_message(plan_id, {
            "type": "agent_stream_start",
            "data": {
                "plan_id": plan_id,
                "agent_name": agent_name,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        }, "agent_stream_start")
    
    async def send_agent_streaming_content(self, plan_id: str, agent_name: str, content: str, is_complete: bool = False):
        """Mock streaming content."""
        message_type = "agent_stream_end" if is_complete else "agent_message_streaming"
        await self.send_message(plan_id, {
            "type": message_type,
            "data": {
                "plan_id": plan_id,
                "agent_name": agent_name,
                "content": content,
                "is_complete": is_complete,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        }, message_type)


async def test_dual_persistence():
    """Test dual persistence: database + WebSocket."""
    try:
        logger.info("🔧 Testing dual persistence (database + WebSocket)")
        
        # Initialize database connection
        MongoDB.connect()
        logger.info("✅ Database connected")
        
        # Create test plan
        plan_id = f"test-dual-{uuid.uuid4().hex[:8]}"
        session_id = f"test-session-{uuid.uuid4().hex[:8]}"
        
        logger.info(f"📋 Creating test plan: {plan_id}")
        
        # Create plan object
        plan = Plan(
            id=plan_id,
            session_id=session_id,
            user_id="test-user",
            description="Test plan for dual persistence (database + WebSocket)",
            status="in_progress",
            steps=[
                Step(
                    id="step-1",
                    description="Test step 1",
                    agent="planner",
                    status="in_progress",
                    result=None
                )
            ],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Save plan to database
        await PlanRepository.create(plan)
        logger.info("✅ Plan created in database")
        
        # Replace the global WebSocket manager with our test manager
        test_websocket_manager = TestWebSocketManager(plan_id)
        
        # Monkey patch the global websocket manager
        import app.services.websocket_service
        original_get_websocket_manager = app.services.websocket_service.get_websocket_manager
        app.services.websocket_service.get_websocket_manager = lambda: test_websocket_manager
        
        logger.info("✅ Test WebSocket manager installed")
        
        try:
            # Test task
            task = "Find emails from Acme Marketing about Invoice number 1001 over the last 2 months"
            
            # Execute task without passing WebSocket manager in state (it will be retrieved globally)
            logger.info("🚀 Executing task with global WebSocket manager...")
            
            result = await LangGraphService.execute_task_with_ai_planner(
                plan_id=plan_id,
                session_id=session_id,
                task_description=task,
                websocket_manager=None  # Don't pass it to avoid serialization issues
            )
            
            logger.info("✅ Task execution completed!")
            logger.info(f"📊 Status: {result.get('status')}")
            logger.info(f"📊 Messages: {len(result.get('messages', []))}")
            
            # Test 1: Verify messages in database
            logger.info("🔍 Test 1: Verifying messages in database")
            db_messages = await MessageRepository.get_by_plan_id(plan_id)
            
            logger.info(f"📊 Found {len(db_messages)} messages in database")
            
            if len(db_messages) > 0:
                logger.info("✅ SUCCESS: Messages persisted to database")
                
                # Show database messages
                for i, msg in enumerate(db_messages, 1):
                    logger.info(f"   DB Message {i}: {msg.agent_name} - {msg.content[:50]}...")
            else:
                logger.error("❌ FAILED: No messages found in database")
                return False
            
            # Test 2: Verify messages sent via WebSocket
            logger.info("🔍 Test 2: Verifying messages sent via WebSocket")
            websocket_message_count = test_websocket_manager.get_message_count()
            
            logger.info(f"📊 Found {websocket_message_count} messages sent via WebSocket")
            
            if websocket_message_count > 0:
                logger.info("✅ SUCCESS: Messages sent via WebSocket")
                
                # Show WebSocket messages
                for i, msg in enumerate(test_websocket_manager.messages_sent, 1):
                    msg_data = msg.get('message_data', {})
                    data = msg_data.get('data', {})
                    agent_name = data.get('agent_name', 'Unknown')
                    content = data.get('content', '')
                    logger.info(f"   WS Message {i}: {agent_name} - {content[:50]}...")
            else:
                logger.error("❌ FAILED: No messages sent via WebSocket")
                return False
            
            # Test 3: Verify dual persistence worked (both methods have messages)
            logger.info("🔍 Test 3: Verifying dual persistence")
            
            if len(db_messages) > 0 and websocket_message_count > 0:
                logger.info("✅ SUCCESS: Dual persistence working!")
                logger.info(f"   Database messages: {len(db_messages)}")
                logger.info(f"   WebSocket messages: {websocket_message_count}")
                
                # Check if message counts are reasonable (they might not be exactly equal due to different message types)
                if len(db_messages) >= 2 and websocket_message_count >= 2:
                    logger.info("✅ SUCCESS: Both persistence methods have multiple messages")
                    return True
                else:
                    logger.warning("⚠️ Low message count, but dual persistence is working")
                    return True
            else:
                logger.error("❌ FAILED: Dual persistence not working")
                return False
        
        finally:
            # Restore original WebSocket manager
            app.services.websocket_service.get_websocket_manager = original_get_websocket_manager
            logger.info("✅ Original WebSocket manager restored")
        
    except Exception as e:
        logger.error(f"❌ Dual persistence test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_dual_persistence())
    if success:
        print("\n🎉 DUAL PERSISTENCE TEST: SUCCESS!")
        print("✅ Messages are persisted to both database and WebSocket")
        print("✅ Dual persistence functionality works correctly")
    else:
        print("\n❌ DUAL PERSISTENCE TEST: FAILED!")
        print("Dual persistence has issues.")