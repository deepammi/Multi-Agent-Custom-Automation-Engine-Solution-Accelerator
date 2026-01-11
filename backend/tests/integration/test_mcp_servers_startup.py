#!/usr/bin/env python3
"""
Test MCP Servers Startup

Quick test to verify all MCP servers can start without errors.
"""

import subprocess
import sys
import os
import time
from pathlib import Path

def test_server_startup(server_path, server_name, timeout=10):
    """Test if a server can start without immediate errors."""
    print(f"\n🧪 Testing {server_name}")
    print(f"   Script: {server_path}")
    
    if not Path(server_path).exists():
        print(f"   ❌ Server script not found")
        return False
    
    try:
        # Start the server
        process = subprocess.Popen(
            ["python3", server_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=os.getcwd(),
            env={**os.environ, "SALESFORCE_MCP_ENABLED": "true"}  # Enable Salesforce for testing
        )
        
        # Wait a moment for server to initialize
        time.sleep(3)
        
        # Check if process is still running
        if process.poll() is None:
            print(f"   ✅ Server started successfully (PID: {process.pid})")
            
            # Stop the server
            process.terminate()
            try:
                process.wait(timeout=5)
                print(f"   ✅ Server stopped gracefully")
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
                print(f"   ⚠️  Server force stopped")
            
            return True
        else:
            # Process exited immediately
            stdout, stderr = process.communicate()
            print(f"   ❌ Server failed to start (exit code: {process.returncode})")
            if stderr:
                print(f"   Error: {stderr[:300]}...")
            if stdout:
                print(f"   Output: {stdout[:300]}...")
            return False
    
    except Exception as e:
        print(f"   ❌ Exception during startup test: {e}")
        return False

def main():
    """Test all MCP servers."""
    print("🚀 MCP Server Startup Test")
    print("=" * 50)
    
    servers = [
        ("src/mcp_server/gmail_mcp_server.py", "Gmail MCP Server"),
        ("src/mcp_server/salesforce_mcp_server.py", "Salesforce MCP Server"),
        ("src/mcp_server/mcp_server.py", "Bill.com MCP Server")
    ]
    
    results = {}
    
    for server_path, server_name in servers:
        results[server_name] = test_server_startup(server_path, server_name)
    
    # Summary
    print(f"\n📊 Test Results Summary")
    print("=" * 30)
    
    passed = 0
    for server_name, success in results.items():
        status_icon = "✅" if success else "❌"
        print(f"{status_icon} {server_name}: {'PASS' if success else 'FAIL'}")
        if success:
            passed += 1
    
    print(f"\n🏁 {passed}/{len(servers)} servers passed startup test")
    
    if passed == len(servers):
        print("🎉 All MCP servers can start successfully!")
        print("\nNext steps:")
        print("1. Use: python3 backend/start_mcp_servers.py start")
        print("2. Run agent tests: python3 backend/test_gmail_agent_debug.py")
    else:
        print("⚠️  Some servers failed to start. Check the errors above.")
    
    return passed == len(servers)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)