#!/usr/bin/env python3
"""
Simple Gmail Test
Test Gmail functionality using a simple approach
"""

import asyncio
import json
import subprocess
import sys
import os

async def test_gmail_simple():
    """Simple test of Gmail functionality."""
    print("Simple Gmail MCP Test")
    print("=" * 30)
    
    # Check if we have OAuth credentials
    from pathlib import Path
    config_dir = Path.home() / ".gmail-mcp"
    credentials_path = config_dir / "credentials.json"
    
    if not credentials_path.exists():
        print("❌ No Gmail credentials found")
        print("   Run: python3 backend/setup_gmail_oauth.py")
        return False
    
    print("✅ Gmail credentials found")
    
    # Try to use the Gmail MCP server with a simple command
    try:
        # Set environment to use different port
        env = os.environ.copy()
        env["PORT"] = "3001"
        env["AUTH_SERVER_PORT"] = "3001"
        
        # Create a simple MCP request for listing messages
        mcp_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "list_messages",
                "arguments": {
                    "maxResults": 3
                }
            }
        }
        
        input_data = json.dumps(mcp_request)
        
        print("🔄 Testing Gmail MCP server...")
        
        # Try with npx first
        result = subprocess.run(
            ["npx", "@shinzolabs/gmail-mcp"],
            input=input_data,
            text=True,
            capture_output=True,
            timeout=30,
            env=env
        )
        
        print(f"Return code: {result.returncode}")
        
        if result.stdout:
            print(f"✅ Got stdout: {len(result.stdout)} chars")
            print(f"First 200 chars: {result.stdout[:200]}")
            
            # Try to find JSON in the output
            lines = result.stdout.split('\\n')
            for line in lines:
                if line.strip().startswith('{'):
                    try:
                        response = json.loads(line.strip())
                        print(f"📄 Found JSON response: {response.get('id', 'no-id')}")
                        
                        if "result" in response:
                            print("🎯 Found result in response!")
                            return True
                        elif "error" in response:
                            print(f"❌ Error in response: {response['error']}")
                            return False
                    except json.JSONDecodeError:
                        continue
        
        if result.stderr:
            stderr_text = result.stderr
            print(f"⚠️  Stderr: {stderr_text[:200]}...")
            
            # Check for specific errors
            if "EADDRINUSE" in stderr_text:
                print("🔧 Port conflict - trying alternative approach...")
                return await test_with_different_port()
            elif "Authentication" in stderr_text or "OAuth" in stderr_text:
                print("🔐 Authentication issue detected")
                return False
        
        return False
        
    except subprocess.TimeoutExpired:
        print("⏰ Command timed out")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

async def test_with_different_port():
    """Try with a completely different port."""
    print("\\n🔧 Trying with port 3002...")
    
    try:
        env = os.environ.copy()
        env["PORT"] = "3002"
        env["AUTH_SERVER_PORT"] = "3002"
        
        # Simple profile request
        mcp_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "get_profile",
                "arguments": {}
            }
        }
        
        input_data = json.dumps(mcp_request)
        
        result = subprocess.run(
            ["npx", "@shinzolabs/gmail-mcp"],
            input=input_data,
            text=True,
            capture_output=True,
            timeout=20,
            env=env
        )
        
        if result.stdout:
            print(f"✅ Got response with port 3002")
            return True
        
        return False
        
    except Exception as e:
        print(f"❌ Port 3002 also failed: {e}")
        return False

async def main():
    """Run the simple Gmail test."""
    success = await test_gmail_simple()
    
    print("\\n" + "=" * 30)
    if success:
        print("🎉 Gmail MCP is working!")
    else:
        print("⚠️  Gmail MCP test failed")
        print("\\n💡 Try running the OAuth setup:")
        print("   python3 backend/setup_gmail_oauth.py")
    
    return success

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\\n⚠️  Test interrupted")
        sys.exit(1)