#!/usr/bin/env python3
"""
Test direct execution of LangGraph service to debug the issue.
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

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_direct_execution():
    """Test direct execution of LangGraph service."""
    try:
        logger.info("🚀 Testing direct LangGraph execution")
        
        # Test task
        task = "Find emails from Acme Marketing about Invoice number 1001 over the last 2 months"
        plan_id = "test-direct-execution"
        session_id = "test-session"
        
        logger.info(f"📝 Testing task: {task}")
        logger.info(f"📋 Plan ID: {plan_id}")
        
        # Execute directly without WebSocket manager to avoid serialization issues
        logger.info("🚀 Starting direct execution...")
        result = await LangGraphService.execute_task_with_ai_planner(
            plan_id=plan_id,
            session_id=session_id,
            task_description=task,
            websocket_manager=None  # No WebSocket to avoid issues
        )
        
        logger.info("✅ Direct execution completed!")
        logger.info(f"📊 Result status: {result.get('status')}")
        logger.info(f"📊 Current agent: {result.get('current_agent')}")
        logger.info(f"📊 Agent sequence: {result.get('agent_sequence')}")
        
        if result.get('status') == 'error':
            logger.error(f"❌ Execution error: {result.get('error')}")
        else:
            logger.info(f"✅ Final result: {result.get('final_result', 'No final result')[:100]}...")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Direct execution test failed: {e}", exc_info=True)
        return {"status": "error", "error": str(e)}


if __name__ == "__main__":
    asyncio.run(test_direct_execution())