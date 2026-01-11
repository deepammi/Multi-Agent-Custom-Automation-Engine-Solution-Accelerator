#!/usr/bin/env python3
"""
Simple test to check what endpoints are available on the Salesforce MCP server.
"""

import subprocess
import sys
import time
import requests
import os

def start_server():
    """Start the MCP server and capture output."""
    server_dir = os.path.join(os.path.dirname(__file__), "..", "src", "mcp_server")
    
    cmd = [
        sys.executable, "mcp_server.py",
        "--transport", "http",
        "--host", "127.0.0.1",
        "--port", "9001"
    ]
    
    print(f"Starting server with command: {' '.join(cmd)}")
    print(f"Working directory: {server_dir}")
    
    process = subprocess.Popen(
        cmd,
        cwd=server_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        universal_newlines=True
    )
    
    # Read initial output
    print("Server output:")
    print("-" * 50)
    
    # Give server time to start and capture output
    for i in range(10):
        time.sleep(1)
        if process.poll() is not None:
            # Process has terminated
            output, _ = process.communicate()
            print(output)
            print(f"Process exited with code: {process.returncode}")
            return None
        
        # Try to read some output
        try:
            import select
            if select.select([process.stdout], [], [], 0.1)[0]:
                line = process.stdout.readline()
                if line:
                    print(line.strip())
        except:
            pass
    
    return process

def test_endpoints():
    """Test various endpoints to see what's available."""
    base_url = "http://127.0.0.1:9001"
    
    endpoints_to_test = [
        "/",
        "/health",
        "/mcp",
        "/mcp/",
        "/docs",
        "/openapi.json",
        "/tools",
        "/mcp/tools"
    ]
    
    print("\nTesting endpoints:")
    print("-" * 50)
    
    for endpoint in endpoints_to_test:
        url = base_url + endpoint
        try:
            response = requests.get(url, timeout=5)
            print(f"{endpoint}: {response.status_code} - {response.text[:100]}...")
        except Exception as e:
            print(f"{endpoint}: ERROR - {e}")

def main():
    print("🚀 Simple Salesforce MCP Server Test")
    
    # Start server
    process = start_server()
    
    if process is None:
        print("❌ Server failed to start")
        return
    
    try:
        # Test endpoints
        test_endpoints()
        
    finally:
        # Stop server
        print("\nStopping server...")
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
        print("✅ Server stopped")

if __name__ == "__main__":
    main()