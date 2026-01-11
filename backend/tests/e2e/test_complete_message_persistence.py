#!/usr/bin/env python3
"""
Complete test for message persistence without WebSocket including plan creation.
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

from app.db.mongodb import MongoDB
from app.db.repositories import PlanRepository, MessageRepository
from app.models.plan import Plan, Step
from app.models.message import AgentMessage
from app.api.v3.routes import get_plan

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_complete_message_persistence():
    """Test complete message persistence flow without WebSocket."""
    try:
        logger.info("🔧 Testing complete message persistence without WebSocket")
        
        # Initialize database connection
        MongoDB.connect()
        logger.info("✅ Database connected")
        
        # Create test plan
        plan_id = f"test-persistence-{uuid.uuid4().hex[:8]}"
        session_id = f"test-session-{uuid.uuid4().hex[:8]}"
        
        logger.info(f"📋 Creating test plan: {plan_id}")
        
        # Create plan object
        plan = Plan(
            id=plan_id,
            session_id=session_id,
            user_id="test-user",
            description="Test plan for message persistence without WebSocket",
            status="in_progress",
            steps=[
                Step(
                    id="step-1",
                    description="Test step 1",
                    agent="planner",
                    status="completed",
                    result="Test result 1"
                )
            ],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Save plan to database
        await PlanRepository.create(plan)
        logger.info("✅ Plan created in database")
        
        # Create test messages
        logger.info("📝 Creating test messages")
        
        messages = [
            AgentMessage(
                plan_id=plan_id,
                agent_name="Planner",
                agent_type="planner",
                content="Test message 1 from planner agent",
                timestamp=datetime.utcnow()
            ),
            AgentMessage(
                plan_id=plan_id,
                agent_name="Gmail",
                agent_type="agent",
                content="Test message 2 from gmail agent",
                timestamp=datetime.utcnow()
            )
        ]
        
        # Save messages to database (simulating direct persistence without WebSocket)
        for message in messages:
            await MessageRepository.create(message)
        
        logger.info(f"✅ Created {len(messages)} test messages")
        
        # Test 1: Verify messages in database
        logger.info("🔍 Test 1: Verifying messages in database")
        db_messages = await MessageRepository.get_by_plan_id(plan_id)
        
        if len(db_messages) == len(messages):
            logger.info(f"✅ SUCCESS: Found {len(db_messages)} messages in database")
        else:
            logger.error(f"❌ FAILED: Expected {len(messages)} messages, found {len(db_messages)}")
            return False
        
        # Test 2: Test REST API retrieval
        logger.info("🌐 Test 2: Testing REST API retrieval")
        
        api_result = await get_plan(plan_id=plan_id)
        
        logger.info(f"📊 API result type: {type(api_result)}")
        logger.info(f"📊 API result: {api_result}")
        
        if hasattr(api_result, 'messages') and api_result.messages:
            api_messages = api_result.messages
            logger.info(f"✅ SUCCESS: API returned {len(api_messages)} messages")
            
            # Verify message content
            if len(api_messages) == len(messages):
                logger.info("✅ SUCCESS: Message count matches")
                
                # Check first message content
                first_msg = api_messages[0]
                logger.info(f"   First message agent: {first_msg.agent_name}")
                logger.info(f"   First message content: {first_msg.content[:50]}...")
                
                return True
            else:
                logger.error(f"❌ FAILED: API returned {len(api_messages)} messages, expected {len(messages)}")
                return False
        elif isinstance(api_result, dict) and 'messages' in api_result and api_result['messages']:
            api_messages = api_result['messages']
            logger.info(f"✅ SUCCESS: API returned {len(api_messages)} messages")
            
            # Verify message content
            if len(api_messages) == len(messages):
                logger.info("✅ SUCCESS: Message count matches")
                
                # Check first message content
                first_msg = api_messages[0]
                logger.info(f"   First message agent: {first_msg.agent_name}")
                logger.info(f"   First message content: {first_msg.content[:50]}...")
                
                return True
            else:
                logger.error(f"❌ FAILED: API returned {len(api_messages)} messages, expected {len(messages)}")
                return False
        else:
            logger.error("❌ FAILED: API did not return messages")
            return False
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_complete_message_persistence())
    if success:
        print("\n🎉 COMPLETE MESSAGE PERSISTENCE TEST: SUCCESS!")
        print("✅ Messages are persisted to database without WebSocket")
        print("✅ Messages can be retrieved via REST API")
        print("✅ End-to-end message persistence works correctly")
    else:
        print("\n❌ COMPLETE MESSAGE PERSISTENCE TEST: FAILED!")
        print("Message persistence or retrieval has issues.")