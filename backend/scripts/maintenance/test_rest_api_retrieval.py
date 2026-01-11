#!/usr/bin/env python3
"""
Test REST API retrieval of persisted messages.
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

from app.api.v3.routes import get_plan
from app.db.mongodb import MongoDB

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_rest_api_retrieval():
    """Test REST API retrieval of persisted messages."""
    try:
        logger.info("🌐 Testing REST API message retrieval")
        
        # Initialize database connection
        MongoDB.connect()
        logger.info("✅ Database connected")
        
        # Test parameters
        plan_id = "test-simple-fix"
        
        # Test REST API retrieval
        logger.info(f"📡 Calling GET /api/v3/plan for plan: {plan_id}")
        
        # Call the API endpoint directly
        result = await get_plan(plan_id=plan_id)
        
        logger.info(f"📊 API Response Status: {type(result)}")
        
        # Check if we got messages
        if hasattr(result, 'messages') and result.messages:
            logger.info(f"✅ SUCCESS: API returned {len(result.messages)} messages!")
            
            # Show first message
            first_message = result.messages[0]
            logger.info(f"   First message agent: {first_message.agent_name}")
            logger.info(f"   First message content: {first_message.content[:100]}...")
            
            return True
        elif isinstance(result, dict) and 'messages' in result:
            messages = result['messages']
            logger.info(f"✅ SUCCESS: API returned {len(messages)} messages!")
            
            # Show first message
            if messages:
                first_message = messages[0]
                logger.info(f"   First message agent: {first_message.get('agent_name', 'Unknown')}")
                logger.info(f"   First message content: {first_message.get('content', '')[:100]}...")
            
            return True
        else:
            logger.warning("⚠️ No messages found in API response")
            logger.info(f"   Response type: {type(result)}")
            logger.info(f"   Response content: {str(result)[:200]}...")
            return False
        
    except Exception as e:
        logger.error(f"❌ REST API test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_rest_api_retrieval())
    if success:
        print("\n🎉 REST API RETRIEVAL: SUCCESS!")
        print("Messages can be retrieved via REST API from database.")
    else:
        print("\n❌ REST API RETRIEVAL: FAILED!")
        print("Messages could not be retrieved via REST API.")