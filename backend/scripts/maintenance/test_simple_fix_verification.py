#!/usr/bin/env python3
"""
Simple test to verify the WebSocket fix works.
"""

import asyncio
import logging
import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from app.services.langgraph_service import LangGraphService
from app.db.mongodb import MongoDB

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_simple_fix():
    """Simple test to verify the fix works."""
    try:
        logger.info("🔧 Testing simple fix verification")
        
        # Initialize database connection
        MongoDB.connect()
        logger.info("✅ Database connected")
        
        # Test parameters
        plan_id = "test-simple-fix"
        session_id = "test-session"
        task = "Find emails from Acme Marketing about Invoice number 1001 over the last 2 months"
        
        # Test: Execute WITHOUT WebSocket manager (should now work)
        logger.info("🚀 Testing execution WITHOUT WebSocket manager...")
        
        result = await LangGraphService.execute_task_with_ai_planner(
            plan_id=plan_id,
            session_id=session_id,
            task_description=task,
            websocket_manager=None  # No WebSocket
        )
        
        logger.info("✅ Execution completed!")
        logger.info(f"📊 Status: {result.get('status')}")
        logger.info(f"📊 Current Agent: {result.get('current_agent')}")
        logger.info(f"📊 Messages: {len(result.get('messages', []))}")
        logger.info(f"📊 Agent Sequence: {result.get('agent_sequence')}")
        
        if result.get('status') == 'error':
            logger.error(f"❌ Execution error: {result.get('error')}")
            return False
        
        # Check if we have messages (indicating agents executed)
        messages = result.get('messages', [])
        if len(messages) > 0:
            logger.info("✅ SUCCESS: Agents executed and produced messages!")
            logger.info(f"   First message: {messages[0][:100]}..." if messages[0] else "   Empty message")
            return True
        else:
            logger.warning("⚠️ No messages produced - agents may not have executed")
            return False
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_simple_fix())
    if success:
        print("\n🎉 FIX VERIFICATION: SUCCESS!")
        print("The WebSocket integration issue has been resolved.")
    else:
        print("\n❌ FIX VERIFICATION: FAILED!")
        print("The issue may still exist or there's another problem.")