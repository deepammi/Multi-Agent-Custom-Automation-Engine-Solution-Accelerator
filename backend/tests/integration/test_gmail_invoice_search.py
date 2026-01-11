#!/usr/bin/env python3
"""
Test Gmail Invoice Search - Focused test for searching invoice emails.

This script specifically tests searching for emails with "INV-1001" in the subject
using the new HTTP transport.

It hardcodes use of method email_agent.search_messages() defined in email_agent.py file
which is easy as we are calling a prebuilt function. We need to test how a Planner agent decides which gmail tool to call ??
"""

import asyncio
import logging
import subprocess
import time
import sys
import os
import json
import re

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from app.agents.email_agent import get_email_agent

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def parse_fastmcp_result(result):
    """Parse FastMCP result to extract messages."""
    messages = []
    
    if 'result' in result:
        result_str = str(result['result'])
        if 'messages' in result_str:
            # Extract the JSON part from the FastMCP result string
            json_match = re.search(r'text=\'({.*?})\', annotations', result_str)
            if json_match:
                try:
                    json_data = json.loads(json_match.group(1))
                    messages = json_data.get('messages', [])
                except json.JSONDecodeError as e:
                    logger.warning(f"Could not parse JSON from result: {e}")
    
    return messages


async def test_invoice_search():
    """Test searching for specific invoice emails."""
    gmail_server_process = None
    
    try:
        logger.info("🚀 Starting Gmail Invoice Search Test")
        
        # Start Gmail MCP server with HTTP transport
        logger.info("📡 Starting Gmail MCP server...")
        gmail_server_process = subprocess.Popen([
            "python3", "../src/mcp_server/gmail_mcp_server.py",
            "--transport", "http",
            "--port", "9002",
            "--host", "0.0.0.0"
        ])
        
        # Wait for server to start
        await asyncio.sleep(3)
        
        # Create email agent
        email_agent = get_email_agent()
        
        # Test 1: Search for specific invoice number
        logger.info("🔍 Searching for emails with 'INV-1001' in subject...")
        
        search_result = await email_agent.search_messages(
            service='gmail', 
            query='subject:INV-1001', 
            max_results=10
        )
        
        messages = parse_fastmcp_result(search_result)
        
        logger.info(f"📧 Found {len(messages)} emails with 'INV-1001' in subject")
        
        if messages:
            logger.info("✅ Invoice emails found:")
            for i, msg in enumerate(messages, 1):
                if 'payload' in msg and 'headers' in msg['payload']:
                    headers = msg['payload']['headers']
                    subject = next((h['value'] for h in headers if h.get('name') == 'Subject'), 'No subject')
                    from_addr = next((h['value'] for h in headers if h.get('name') == 'From'), 'Unknown sender')
                    date = next((h['value'] for h in headers if h.get('name') == 'Date'), 'Unknown date')
                    
                    logger.info(f"\n📨 Email {i}:")
                    logger.info(f"   From: {from_addr}")
                    logger.info(f"   Subject: {subject}")
                    logger.info(f"   Date: {date}")
                    logger.info(f"   Message ID: {msg.get('id', 'Unknown')}")
                    
                    if 'snippet' in msg:
                        snippet = msg['snippet'][:200] + "..." if len(msg['snippet']) > 200 else msg['snippet']
                        logger.info(f"   Preview: {snippet}")
        else:
            logger.info("📭 No emails found with 'INV-1001' in subject")
            
            # Test 2: Search for general invoice patterns
            logger.info("\n🔍 Searching for general invoice patterns...")
            
            invoice_queries = [
                'subject:invoice',
                'subject:INV-',
                'subject:bill',
                'subject:"invoice number"',
                'invoice OR bill OR receipt'
            ]
            
            for query in invoice_queries:
                logger.info(f"\n🔎 Trying query: '{query}'")
                
                try:
                    result = await email_agent.search_messages(
                        service='gmail', 
                        query=query, 
                        max_results=5
                    )
                    
                    query_messages = parse_fastmcp_result(result)
                    logger.info(f"   Found {len(query_messages)} emails")
                    
                    if query_messages:
                        for i, msg in enumerate(query_messages[:2], 1):  # Show first 2
                            if 'payload' in msg and 'headers' in msg['payload']:
                                headers = msg['payload']['headers']
                                subject = next((h['value'] for h in headers if h.get('name') == 'Subject'), 'No subject')
                                logger.info(f"   {i}. {subject}")
                        
                        if len(query_messages) > 2:
                            logger.info(f"   ... and {len(query_messages) - 2} more")
                        break  # Found some results, stop searching
                        
                except Exception as e:
                    logger.warning(f"   Query failed: {e}")
        
        # Test 3: Search with different invoice number patterns
        logger.info("\n🔍 Testing different invoice number patterns...")
        
        test_patterns = [
            'INV-1001',
            'INV-1002', 
            'INV-2024',
            'Invoice 1001',
            'Bill 1001'
        ]
        
        for pattern in test_patterns:
            try:
                logger.info(f"\n🔎 Searching for: '{pattern}'")
                
                result = await email_agent.search_messages(
                    service='gmail', 
                    query=f'subject:"{pattern}"', 
                    max_results=3
                )
                
                pattern_messages = parse_fastmcp_result(result)
                
                if pattern_messages:
                    logger.info(f"   ✅ Found {len(pattern_messages)} emails with '{pattern}'")
                    for msg in pattern_messages[:1]:  # Show first result
                        if 'payload' in msg and 'headers' in msg['payload']:
                            headers = msg['payload']['headers']
                            subject = next((h['value'] for h in headers if h.get('name') == 'Subject'), 'No subject')
                            logger.info(f"      Subject: {subject}")
                else:
                    logger.info(f"   📭 No emails found with '{pattern}'")
                    
            except Exception as e:
                logger.warning(f"   Search for '{pattern}' failed: {e}")
        
        logger.info("\n🎉 Gmail Invoice Search Test completed!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Invoice search test failed: {e}")
        return False
    
    finally:
        # Cleanup: Stop Gmail server
        if gmail_server_process:
            logger.info("\n🛑 Stopping Gmail MCP server...")
            gmail_server_process.terminate()
            gmail_server_process.wait()
            logger.info("✅ Gmail MCP server stopped")


if __name__ == "__main__":
    asyncio.run(test_invoice_search())