#!/usr/bin/env python3
"""
Standalone test for Zoho MCP Server.

This test runs the MCP server in a separate process and tests it via stdio.
"""

import asyncio
import subprocess
import json
import sys
import os
from typing import Dict, Any

# ANSI color codes
GREEN = '\033[92m'
RED = '\033[91m'
RESET = '\033[0m'
BOLD = '\033[1m'


async def test_mcp_server_standalone():
    """Test MCP server by running it as a subprocess."""
    print(f"\n{BOLD}Testing Zoho MCP Server (Standalone){RESET}")
    
    try:
        # Start MCP server as subprocess
        server_path = "../src/mcp_server/zoho_mcp_server.py"
        
        print(f"Starting MCP server: {server_path}")
        
        process = await asyncio.create_subprocess_exec(
            "python3", server_path,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )
        
        # Send MCP initialization message
        init_message = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "test-client", "version": "1.0.0"}
            }
        }
        
        message_bytes = (json.dumps(init_message) + "\n").encode()
        process.stdin.write(message_bytes)
        await process.stdin.drain()
        
        # Read response with timeout
        try:
            response_bytes = await asyncio.wait_for(
                process.stdout.readline(), 
                timeout=5.0
            )
            response = json.loads(response_bytes.decode().strip())
            
            print(f"{GREEN}✅ MCP server responded to initialization{RESET}")
            print(f"Response: {response}")
            
        except asyncio.TimeoutError:
            print(f"{RED}❌ MCP server initialization timeout{RESET}")
        
        # Clean up
        process.terminate()
        await process.wait()
        
    except Exception as e:
        print(f"{RED}❌ MCP server test failed: {e}{RESET}")


if __name__ == "__main__":
    asyncio.run(test_mcp_server_standalone())