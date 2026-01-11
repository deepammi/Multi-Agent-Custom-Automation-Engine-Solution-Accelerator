#!/usr/bin/env python3
"""
Test Gmail agent with TBI Corp search query to verify it chooses "search" action.

This test directly tests the Gmail agent with a proper websocket_manager
to ensure the LLM intent analysis works correctly.
"""

import asyncio
import logging
import sys
import os
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from app.agents.gmail_agent_node import GmailAgentNode
from app.services.websocket_service import get_websocket_manager

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class MockWebSocketManager:
    """Mock WebSocket manager for testing."""
    
    def __init__(self):
        self.messages = []
    
    async def send_message(self, plan_id: str, message: dict):
        """Mock send message."""
        self.messages.append(message)
        logger.info(f"📤 Mock WebSocket message: {message.get('type', 'unknown')}")


async def test_gmail_agent_tbi_search():
    """Test Gmail agent with TBI Corp search query."""
    logger.info("🧪 Testing Gmail Agent with TBI Corp search query")
    
    # Create Gmail agent
    gmail_agent = GmailAgentNode()
    
    # Create mock WebSocket manager
    websocket_manager = MockWebSocketManager()
    
    # Test query that should trigger "search" action
    test_query = "check all emails, bills and customer crm accounts with keywords TBI Corp or TBI-001 and analyze them"
    
    # Create test state with websocket_manager
    test_state = {
        "plan_id": "test-plan-123",
        "session_id": "test-session-123", 
        "task_description": test_query,
        "user_request": test_query,
        "task": test_query,
        "websocket_manager": websocket_manager,
        "messages": [],
        "collected_data": {},
        "execution_results": []
    }
    
    logger.info(f"📝 Test Query: {test_query}")
    logger.info(f"🔧 WebSocket Manager: {type(websocket_manager).__name__}")
    
    # Process the request
    logger.info("🚀 Processing Gmail agent request...")
    result = await gmail_agent.process(test_state)
    
    # Analyze the result
    gmail_result = result.get("gmail_result", "")
    
    logger.info("📊 Gmail Agent Result Analysis:")
    logger.info(f"   Result length: {len(gmail_result)} characters")
    
    # Check if TBI Corp was searched for
    if "TBI" in gmail_result:
        logger.info("✅ Result contains TBI-related content")
    else:
        logger.warning("⚠️ Result does not contain TBI-related content")
    
    # Check WebSocket messages
    logger.info(f"📤 WebSocket messages sent: {len(websocket_manager.messages)}")
    
    streaming_messages = [msg for msg in websocket_manager.messages if msg.get('type') == 'agent_message_streaming']
    logger.info(f"   Streaming messages: {len(streaming_messages)}")
    
    if streaming_messages:
        logger.info("✅ Gmail agent used streaming LLM calls (websocket_manager was available)")
    else:
        logger.warning("⚠️ Gmail agent did not use streaming LLM calls")
    
    # Print the full result
    logger.info("📄 Full Gmail Agent Result:")
    logger.info("=" * 80)
    logger.info(gmail_result)
    logger.info("=" * 80)
    
    return result


async def test_gmail_intent_analysis_directly():
    """Test Gmail agent intent analysis directly."""
    logger.info("🧪 Testing Gmail Agent intent analysis directly")
    
    # Create Gmail agent
    gmail_agent = GmailAgentNode()
    
    # Create mock WebSocket manager
    websocket_manager = MockWebSocketManager()
    
    # Test query that should trigger "search" action
    test_query = "check emails with keywords TBI Corp or TBI-001"
    
    # Create test state with websocket_manager
    test_state = {
        "plan_id": "test-plan-456",
        "websocket_manager": websocket_manager
    }
    
    logger.info(f"📝 Direct Intent Test Query: {test_query}")
    
    # Call the intent analysis method directly
    logger.info("🔍 Calling _analyze_user_intent directly...")
    
    try:
        intent_result = await gmail_agent._analyze_user_intent(test_query, test_state)
        
        logger.info("📊 Intent Analysis Result:")
        logger.info(f"   Action: {intent_result.get('action', 'unknown')}")
        logger.info(f"   Query: {intent_result.get('query', 'none')}")
        logger.info(f"   Max Results: {intent_result.get('max_results', 'none')}")
        
        # Check if it chose the correct action
        if intent_result.get('action') == 'search':
            logger.info("✅ CORRECT: Gmail agent chose 'search' action for TBI Corp query")
        else:
            logger.error(f"❌ INCORRECT: Gmail agent chose '{intent_result.get('action')}' instead of 'search'")
        
        # Check if the query contains TBI terms
        query = intent_result.get('query', '')
        if 'TBI' in query:
            logger.info("✅ CORRECT: Search query contains TBI terms")
        else:
            logger.warning(f"⚠️ Search query does not contain TBI terms: '{query}'")
        
        # Check WebSocket usage
        streaming_messages = [msg for msg in websocket_manager.messages if msg.get('type') == 'agent_message_streaming']
        if streaming_messages:
            logger.info("✅ CORRECT: Used streaming LLM calls (websocket_manager available)")
        else:
            logger.warning("⚠️ Did not use streaming LLM calls")
        
        return intent_result
        
    except Exception as e:
        logger.error(f"❌ Intent analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return None


async def main():
    """Main test function."""
    logger.info("🚀 Starting Gmail Agent TBI Search Tests")
    logger.info("=" * 80)
    
    # Test 1: Direct intent analysis
    logger.info("\n🧪 TEST 1: Direct Intent Analysis")
    intent_result = await test_gmail_intent_analysis_directly()
    
    # Test 2: Full agent processing
    logger.info("\n🧪 TEST 2: Full Agent Processing")
    agent_result = await test_gmail_agent_tbi_search()
    
    # Summary
    logger.info("\n📊 TEST SUMMARY")
    logger.info("=" * 80)
    
    if intent_result and intent_result.get('action') == 'search':
        logger.info("✅ Intent Analysis: PASSED - Chose 'search' action")
    else:
        logger.error("❌ Intent Analysis: FAILED - Did not choose 'search' action")
    
    if agent_result and 'TBI' in agent_result.get('gmail_result', ''):
        logger.info("✅ Agent Processing: PASSED - Result contains TBI content")
    else:
        logger.error("❌ Agent Processing: FAILED - Result does not contain TBI content")
    
    logger.info("🎉 Gmail Agent TBI Search Tests Completed")


if __name__ == "__main__":
    asyncio.run(main())