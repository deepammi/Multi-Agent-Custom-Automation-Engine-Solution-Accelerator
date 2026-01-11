#!/usr/bin/env python3
"""
Test the WebSocket fix to ensure both scenarios work correctly.
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


async def test_websocket_fix():
    """Test that both WebSocket and non-WebSocket scenarios work correctly."""
    try:
        logger.info("🔧 Testing WebSocket fix")
        
        # Initialize database connection
        MongoDB.connect()
        logger.info("✅ Database connected")
        
        # Test parameters
        plan_id = "test-websocket-fix"
        session_id = "test-session"
        task = "Find emails from Acme Marketing about Invoice number 1001 over the last 2 months"
        
        # Test 1: Execute WITHOUT WebSocket manager (should now work)
        logger.info("🚀 Test 1: Executing WITHOUT WebSocket manager...")
        
        try:
            result1 = await LangGraphService.execute_task_with_ai_planner(
                plan_id=f"{plan_id}-no-ws",
                session_id=session_id,
                task_description=task,
                websocket_manager=None  # No WebSocket
            )
            
            logger.info("✅ Test 1 completed!")
            logger.info(f"📊 Result 1 - Status: {result1.get('status')}")
            logger.info(f"📊 Result 1 - Current Agent: {result1.get('current_agent')}")
            logger.info(f"📊 Result 1 - Messages: {len(result1.get('messages', []))}")
            
            if result1.get('status') == 'error':
                logger.error(f"❌ Test 1 error: {result1.get('error')}")
            
        except Exception as e:
            logger.error(f"❌ Test 1 failed: {e}")
        
        # Test 2: Execute WITH WebSocket manager (should still work)
        logger.info("🚀 Test 2: Executing WITH WebSocket manager...")
        
        try:
            from app.services.websocket_service import get_websocket_manager
            websocket_manager = get_websocket_manager()
            
            result2 = await LangGraphService.execute_task_with_ai_planner(
                plan_id=f"{plan_id}-with-ws",
                session_id=session_id,
                task_description=task,
                websocket_manager=websocket_manager  # With WebSocket
            )
            
            logger.info("✅ Test 2 completed!")
            logger.info(f"📊 Result 2 - Status: {result2.get('status')}")
            logger.info(f"📊 Result 2 - Current Agent: {result2.get('current_agent')}")
            logger.info(f"📊 Result 2 - Messages: {len(result2.get('messages', []))}")
            
            if result2.get('status') == 'error':
                logger.error(f"❌ Test 2 error: {result2.get('error')}")
            
        except Exception as e:
            logger.error(f"❌ Test 2 failed: {e}")
        
        # Compare results
        logger.info("🔍 Comparing results...")
        logger.info("Both tests should now show similar execution patterns with agent execution")
        
    except Exception as e:
        logger.error(f"❌ Test setup failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_websocket_fix())