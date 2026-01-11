#!/usr/bin/env python3
"""
Test Gmail HTTP workflow using FastMCP Client.

This script tests the complete Gmail workflow:
1. Start Gmail MCP server with HTTP transport
2. Connect Gmail agent using FastMCP Client
3. Test basic Gmail operations
"""

import asyncio
import logging
import subprocess
import time
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from app.agents.email_agent import get_email_agent

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_gmail_http_workflow():
    """Test complete Gmail HTTP workflow."""
    gmail_server_process = None
    
    try:
        logger.info("🚀 Starting Gmail HTTP workflow test")
        
        # Step 1: Start Gmail MCP server with HTTP transport
        logger.info("📡 Starting Gmail MCP server with HTTP transport...")
        gmail_server_process = subprocess.Popen([
            "python3", "../src/mcp_server/gmail_mcp_server.py",
            "--transport", "http",
            "--port", "9002",
            "--host", "0.0.0.0"
        ])
        
        # Wait for server to start
        logger.info("⏳ Waiting for Gmail server to start...")
        await asyncio.sleep(3)
        
        # Step 2: Test Gmail agent with HTTP transport
        logger.info("🔗 Testing Gmail agent with HTTP transport...")
        
        email_agent = get_email_agent()
        
        # Test 1: Get Gmail profile
        logger.info("📧 Testing Gmail profile retrieval...")
        try:
            profile_result = await email_agent.get_profile(service='gmail')
            logger.info(f"✅ Gmail profile: {profile_result}")
        except Exception as e:
            logger.error(f"❌ Gmail profile test failed: {e}")
        
        # Test 2: List recent messages
        logger.info("📬 Testing Gmail message listing...")
        try:
            messages_result = await email_agent.list_messages(service='gmail', max_results=5)
            logger.info(f"✅ Gmail messages: {len(messages_result.get('messages', []))} messages found")
        except Exception as e:
            logger.error(f"❌ Gmail messages test failed: {e}")
        
        # Test 3: Search messages
        logger.info("🔍 Testing Gmail message search...")
        try:
            search_result = await email_agent.search_messages(
                service='gmail', 
                query='acme', 
                max_results=3
            )
            logger.info(f"✅ Gmail search: {len(search_result.get('messages', []))} messages found")
        except Exception as e:
            logger.error(f"❌ Gmail search test failed: {e}")
        
        logger.info("🎉 Gmail HTTP workflow test completed!")
        
    except Exception as e:
        logger.error(f"❌ Gmail HTTP workflow test failed: {e}")
        raise
    
    finally:
        # Cleanup: Stop Gmail server
        if gmail_server_process:
            logger.info("🛑 Stopping Gmail MCP server...")
            gmail_server_process.terminate()
            gmail_server_process.wait()
            logger.info("✅ Gmail MCP server stopped")


if __name__ == "__main__":
    asyncio.run(test_gmail_http_workflow())