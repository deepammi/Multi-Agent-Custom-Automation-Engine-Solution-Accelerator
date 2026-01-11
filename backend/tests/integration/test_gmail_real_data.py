#!/usr/bin/env python3
"""
Test Gmail HTTP workflow with real credentials and data.

This script tests the complete Gmail workflow with actual Gmail API calls:
1. Start Gmail MCP server with HTTP transport
2. Connect Gmail agent using FastMCP Client
3. Test real Gmail operations with actual data
"""

import asyncio
import logging
import subprocess
import time
import sys
import os
import json

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from app.agents.email_agent import get_email_agent

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def test_gmail_real_data():
    """Test complete Gmail HTTP workflow with real data."""
    gmail_server_process = None
    
    try:
        logger.info("🚀 Starting Gmail HTTP workflow test with REAL DATA")
        
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
        await asyncio.sleep(5)
        
        # Step 2: Test Gmail agent with HTTP transport and real data
        logger.info("🔗 Testing Gmail agent with HTTP transport and REAL DATA...")
        
        email_agent = get_email_agent()
        
        # Test 1: Get Gmail profile (real data)
        logger.info("👤 Testing Gmail profile retrieval with real credentials...")
        try:
            profile_result = await email_agent.get_profile(service='gmail')
            logger.info("✅ Gmail profile retrieved successfully!")
            
            # Parse the result to show clean data
            if 'result' in profile_result:
                result_str = str(profile_result['result'])
                if 'emailAddress' in result_str:
                    logger.info("📧 Profile contains email address - credentials are working!")
                else:
                    logger.warning("⚠️ Profile result format: %s", profile_result)
            
        except Exception as e:
            logger.error(f"❌ Gmail profile test failed: {e}")
            return False
        
        # Test 2: List recent messages (real data)
        logger.info("📬 Testing Gmail message listing with real data...")
        try:
            messages_result = await email_agent.list_messages(service='gmail', max_results=5)
            
            if 'messages' in messages_result:
                message_count = len(messages_result['messages'])
                logger.info(f"✅ Gmail messages: {message_count} real messages found")
                
                # Show details of first message if available
                if message_count > 0:
                    first_msg = messages_result['messages'][0]
                    logger.info("📧 First message details:")
                    
                    if 'payload' in first_msg and 'headers' in first_msg['payload']:
                        headers = first_msg['payload']['headers']
                        for header in headers:
                            if header.get('name') in ['From', 'Subject', 'Date']:
                                logger.info(f"   {header['name']}: {header['value']}")
                    
                    if 'snippet' in first_msg:
                        snippet = first_msg['snippet'][:100] + "..." if len(first_msg['snippet']) > 100 else first_msg['snippet']
                        logger.info(f"   Preview: {snippet}")
                        
            else:
                logger.warning("⚠️ No messages found or unexpected format: %s", messages_result)
                
        except Exception as e:
            logger.error(f"❌ Gmail messages test failed: {e}")
            return False
        
        # Test 3: Search messages with specific invoice number (real data)
        logger.info("🔍 Testing Gmail message search for invoice INV-1001...")
        try:
            search_result = await email_agent.search_messages(
                service='gmail', 
                query='subject:INV-1001', 
                max_results=10
            )
            
            # Parse the FastMCP result format
            messages = []
            if 'result' in search_result:
                result_str = str(search_result['result'])
                # Try to extract messages from the complex FastMCP result
                if 'messages' in result_str:
                    import json
                    import re
                    # Extract the JSON part from the result string
                    json_match = re.search(r'text=\'({.*?})\', annotations', result_str)
                    if json_match:
                        try:
                            json_data = json.loads(json_match.group(1))
                            messages = json_data.get('messages', [])
                        except json.JSONDecodeError:
                            logger.warning("Could not parse JSON from result")
            
            search_count = len(messages)
            logger.info(f"✅ Gmail search: {search_count} messages found for 'INV-1001' in subject")
            
            if search_count > 0:
                logger.info("📧 Found invoice emails:")
                # Show search results
                for i, msg in enumerate(messages[:5], 1):  # Show up to 5 results
                    if 'payload' in msg and 'headers' in msg['payload']:
                        headers = msg['payload']['headers']
                        subject = next((h['value'] for h in headers if h.get('name') == 'Subject'), 'No subject')
                        from_addr = next((h['value'] for h in headers if h.get('name') == 'From'), 'Unknown sender')
                        date = next((h['value'] for h in headers if h.get('name') == 'Date'), 'Unknown date')
                        
                        logger.info(f"   {i}. From: {from_addr}")
                        logger.info(f"      Subject: {subject}")
                        logger.info(f"      Date: {date}")
                        
                        # Show snippet if available
                        if 'snippet' in msg:
                            snippet = msg['snippet'][:150] + "..." if len(msg['snippet']) > 150 else msg['snippet']
                            logger.info(f"      Preview: {snippet}")
                        logger.info("")
            else:
                logger.info("📭 No emails found with 'INV-1001' in subject")
                logger.info("💡 This is normal if you don't have invoice emails with that specific number")
                
                # Fallback: Search for any invoice-related emails
                logger.info("🔍 Searching for any invoice-related emails as fallback...")
                fallback_result = await email_agent.search_messages(
                    service='gmail', 
                    query='subject:invoice OR subject:INV OR subject:bill', 
                    max_results=5
                )
                
                # Parse fallback results
                fallback_messages = []
                if 'result' in fallback_result:
                    result_str = str(fallback_result['result'])
                    if 'messages' in result_str:
                        json_match = re.search(r'text=\'({.*?})\', annotations', result_str)
                        if json_match:
                            try:
                                json_data = json.loads(json_match.group(1))
                                fallback_messages = json_data.get('messages', [])
                            except json.JSONDecodeError:
                                pass
                
                fallback_count = len(fallback_messages)
                logger.info(f"📧 Found {fallback_count} invoice-related emails")
                
                for i, msg in enumerate(fallback_messages[:3], 1):
                    if 'payload' in msg and 'headers' in msg['payload']:
                        headers = msg['payload']['headers']
                        subject = next((h['value'] for h in headers if h.get('name') == 'Subject'), 'No subject')
                        logger.info(f"   {i}. Subject: {subject}")
                        
        except Exception as e:
            logger.error(f"❌ Gmail search test failed: {e}")
            return False
                
        except Exception as e:
            logger.error(f"❌ Gmail search test failed: {e}")
            return False
        
        # Test 4: Test sending an email (optional - commented out to avoid spam)
        logger.info("📤 Email sending test (skipped to avoid spam)")
        logger.info("   To test sending, uncomment the send_message test below")
        
        # Uncomment to test sending (be careful not to spam):
        # try:
        #     send_result = await email_agent.send_message(
        #         service='gmail',
        #         to='your-test-email@example.com',  # Replace with your test email
        #         subject='FastMCP HTTP Transport Test',
        #         body='This is a test email sent via FastMCP HTTP transport. The migration is working!'
        #     )
        #     logger.info(f"✅ Email sent successfully: {send_result}")
        # except Exception as e:
        #     logger.error(f"❌ Email sending test failed: {e}")
        
        logger.info("🎉 Gmail HTTP workflow test with REAL DATA completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Gmail HTTP workflow test failed: {e}")
        return False
    
    finally:
        # Cleanup: Stop Gmail server
        if gmail_server_process:
            logger.info("🛑 Stopping Gmail MCP server...")
            gmail_server_process.terminate()
            gmail_server_process.wait()
            logger.info("✅ Gmail MCP server stopped")


async def test_concurrent_connections():
    """Test concurrent connections to the same Gmail server."""
    logger.info("🔄 Testing concurrent connections to Gmail server...")
    
    try:
        # Create multiple email agents (simulating concurrent clients)
        agents = [get_email_agent() for _ in range(3)]
        
        # Test concurrent profile requests
        tasks = []
        for i, agent in enumerate(agents):
            task = agent.get_profile(service='gmail')
            tasks.append(task)
        
        # Execute all requests concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        success_count = sum(1 for result in results if not isinstance(result, Exception))
        logger.info(f"✅ Concurrent connections test: {success_count}/{len(agents)} succeeded")
        
        return success_count == len(agents)
        
    except Exception as e:
        logger.error(f"❌ Concurrent connections test failed: {e}")
        return False


if __name__ == "__main__":
    async def main():
        # Test 1: Real data workflow
        success1 = await test_gmail_real_data()
        
        if success1:
            logger.info("=" * 60)
            # Test 2: Concurrent connections (server should still be running)
            logger.info("🚀 Starting Gmail MCP server for concurrent connection test...")
            gmail_server_process = subprocess.Popen([
                "python3", "../src/mcp_server/gmail_mcp_server.py",
                "--transport", "http",
                "--port", "9002",
                "--host", "0.0.0.0"
            ])
            
            await asyncio.sleep(3)
            success2 = await test_concurrent_connections()
            
            gmail_server_process.terminate()
            gmail_server_process.wait()
            
            if success1 and success2:
                logger.info("🎉 ALL TESTS PASSED! Gmail HTTP transport migration is successful!")
            else:
                logger.error("❌ Some tests failed")
        else:
            logger.error("❌ Basic workflow test failed, skipping concurrent test")
    
    asyncio.run(main())