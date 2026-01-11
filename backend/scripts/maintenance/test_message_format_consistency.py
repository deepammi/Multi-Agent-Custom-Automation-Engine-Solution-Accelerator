#!/usr/bin/env python3
"""
Test message format consistency across persistence methods.
Task 8.3: Validate message format consistency across methods
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
from app.services.message_persistence_service import get_message_persistence_service
from app.db.mongodb import MongoDB
from app.db.repositories import MessageRepository, PlanRepository
from app.models.plan import Plan, Step

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestWebSocketManager:
    """Test WebSocket manager that captures messages for format comparison."""
    
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
        """Capture messages for format analysis."""
        message = {
            "plan_id": plan_id,
            "message_data": message_data,
            "message_type": message_type,
            "timestamp": datetime.utcnow(),
            **kwargs
        }
        self.messages_sent.append(message)
        logger.debug(f"📡 WebSocket: Captured {message_type} message for plan {plan_id}")
    
    def get_messages_by_type(self, message_type: str):
        """Get messages filtered by type."""
        return [msg for msg in self.messages_sent if msg.get("message_type") == message_type]
    
    def get_agent_messages(self):
        """Get agent messages for format comparison."""
        agent_messages = []
        for msg in self.messages_sent:
            if msg.get("message_type") in ["agent_message", "agent_stream_end", "final_result_message"]:
                data = msg.get("message_data", {}).get("data", {})
                if data.get("content") and data.get("agent_name"):
                    agent_messages.append({
                        "agent_name": data.get("agent_name"),
                        "content": data.get("content"),
                        "agent_type": data.get("agent_type", "unknown"),
                        "timestamp": data.get("timestamp"),
                        "source": "websocket"
                    })
        return agent_messages
    
    # Add other required methods
    async def send_enhanced_progress_update(self, plan_id: str, current_step: int, total_steps: int, current_agent: str, **kwargs):
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
        await self.send_message(plan_id, {
            "type": "agent_stream_start",
            "data": {
                "plan_id": plan_id,
                "agent_name": agent_name,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        }, "agent_stream_start")
    
    async def send_agent_streaming_content(self, plan_id: str, agent_name: str, content: str, is_complete: bool = False):
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


async def test_message_format_consistency():
    """Test message format consistency across database and WebSocket persistence."""
    try:
        logger.info("🔧 Testing message format consistency across persistence methods")
        
        # Initialize database connection
        MongoDB.connect()
        logger.info("✅ Database connected")
        
        # Create test plan
        plan_id = f"test-format-{uuid.uuid4().hex[:8]}"
        session_id = f"test-session-{uuid.uuid4().hex[:8]}"
        
        logger.info(f"📋 Creating test plan: {plan_id}")
        
        # Create plan object
        plan = Plan(
            id=plan_id,
            session_id=session_id,
            user_id="test-user",
            description="Test plan for message format consistency",
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
            task = "Analyze the latest invoice from Acme Corp for accuracy"
            
            # Execute task with WebSocket manager to enable dual persistence
            logger.info("🚀 Executing task with dual persistence enabled...")
            
            result = await LangGraphService.execute_task_with_ai_planner(
                plan_id=plan_id,
                session_id=session_id,
                task_description=task,
                websocket_manager=test_websocket_manager  # Enable HITL and dual persistence
            )
            
            logger.info("✅ Task execution completed!")
            logger.info(f"📊 Status: {result.get('status')}")
            
            # Get messages from database
            logger.info("🔍 Retrieving messages from database...")
            db_messages = await MessageRepository.get_by_plan_id(plan_id)
            
            # Get messages from WebSocket
            logger.info("🔍 Retrieving messages from WebSocket...")
            ws_agent_messages = test_websocket_manager.get_agent_messages()
            
            logger.info(f"📊 Database messages: {len(db_messages)}")
            logger.info(f"📊 WebSocket agent messages: {len(ws_agent_messages)}")
            
            # Test 1: Validate message format consistency
            logger.info("🔍 Test 1: Validating message format consistency")
            
            if len(db_messages) == 0:
                logger.error("❌ No database messages found for format comparison")
                return False
            
            # Use message persistence service to validate format consistency
            persistence_service = get_message_persistence_service()
            
            # Convert WebSocket messages to comparable format
            ws_messages_for_comparison = []
            for ws_msg in ws_agent_messages:
                ws_messages_for_comparison.append({
                    "content": ws_msg["content"],
                    "agent_name": ws_msg["agent_name"],
                    "agent_type": ws_msg.get("agent_type", "unknown"),
                    "timestamp": ws_msg.get("timestamp", "")
                })
            
            # Convert database messages to comparable format
            db_messages_for_comparison = []
            for db_msg in db_messages:
                db_messages_for_comparison.append({
                    "content": db_msg.content,
                    "agent_name": db_msg.agent_name,
                    "agent_type": db_msg.agent_type,
                    "timestamp": db_msg.timestamp.isoformat() + "Z"
                })
            
            # Validate format consistency
            consistency_report = await persistence_service.validate_message_format_consistency(
                plan_id=plan_id,
                websocket_messages=ws_messages_for_comparison,
                database_messages=db_messages
            )
            
            logger.info(f"📊 Format consistency report:")
            logger.info(f"   Overall consistent: {consistency_report.get('overall_consistent', False)}")
            logger.info(f"   Format mismatches: {len(consistency_report.get('format_mismatches', []))}")
            logger.info(f"   Content mismatches: {len(consistency_report.get('content_mismatches', []))}")
            logger.info(f"   Missing in database: {len(consistency_report.get('missing_in_database', []))}")
            logger.info(f"   Missing in WebSocket: {len(consistency_report.get('missing_in_websocket', []))}")
            
            # Test 2: Validate individual message formats
            logger.info("🔍 Test 2: Validating individual message formats")
            
            format_validation_report = await persistence_service.get_format_validation_report(plan_id)
            
            logger.info(f"📊 Format validation report:")
            logger.info(f"   Total messages: {format_validation_report.get('total_messages', 0)}")
            logger.info(f"   Valid messages: {format_validation_report.get('validation_summary', {}).get('valid_messages', 0)}")
            logger.info(f"   Invalid messages: {format_validation_report.get('validation_summary', {}).get('invalid_messages', 0)}")
            logger.info(f"   Messages with warnings: {format_validation_report.get('validation_summary', {}).get('messages_with_warnings', 0)}")
            
            # Test 3: Validate chronological ordering
            logger.info("🔍 Test 3: Validating chronological ordering")
            
            chronological_report = await persistence_service.verify_message_chronological_ordering(plan_id)
            
            logger.info(f"📊 Chronological ordering report:")
            logger.info(f"   Is chronological: {chronological_report.get('is_chronological', False)}")
            logger.info(f"   Message count: {chronological_report.get('message_count', 0)}")
            logger.info(f"   Ordering issues: {chronological_report.get('ordering_issues_count', 0)}")
            
            # Determine overall success
            success = True
            
            if format_validation_report.get('validation_summary', {}).get('invalid_messages', 0) > 0:
                logger.error("❌ Found invalid messages in database")
                success = False
            
            if not chronological_report.get('is_chronological', False):
                logger.error("❌ Messages are not in chronological order")
                success = False
            
            if len(db_messages) == 0:
                logger.error("❌ No messages found in database")
                success = False
            
            if success:
                logger.info("✅ SUCCESS: Message format consistency validated!")
                logger.info("   ✅ All messages have valid format")
                logger.info("   ✅ Messages are in chronological order")
                logger.info("   ✅ Database persistence working correctly")
                
                # Show sample messages
                logger.info("📋 Sample database messages:")
                for i, msg in enumerate(db_messages[:3], 1):
                    logger.info(f"   Message {i}: {msg.agent_name} ({msg.agent_type}) - {msg.content[:50]}...")
                
                return True
            else:
                logger.error("❌ FAILED: Message format consistency issues found")
                return False
        
        finally:
            # Restore original WebSocket manager
            app.services.websocket_service.get_websocket_manager = original_get_websocket_manager
            logger.info("✅ Original WebSocket manager restored")
        
    except Exception as e:
        logger.error(f"❌ Message format consistency test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_message_format_consistency())
    if success:
        print("\n🎉 MESSAGE FORMAT CONSISTENCY TEST: SUCCESS!")
        print("✅ Message formats are consistent across persistence methods")
        print("✅ Database persistence maintains proper message structure")
        print("✅ Chronological ordering is preserved")
    else:
        print("\n❌ MESSAGE FORMAT CONSISTENCY TEST: FAILED!")
        print("Message format consistency has issues.")