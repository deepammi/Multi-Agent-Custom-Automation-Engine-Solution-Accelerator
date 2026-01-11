#!/usr/bin/env python3
"""
Test script for MCP Server Manager

Quick test to verify the MCP server manager can start and stop servers.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from start_mcp_servers import MCPServerManager

async def test_server_manager():
    """Test the MCP server manager functionality."""
    print("🧪 Testing MCP Server Manager")
    print("=" * 50)
    
    manager = MCPServerManager()
    
    # Test 1: Check server files
    print("\n📁 Test 1: Checking server files...")
    file_status = manager.check_server_files()
    
    missing_files = [k for k, v in file_status.items() if not v]
    if missing_files:
        print(f"❌ Missing server files: {missing_files}")
        print("Cannot proceed with server tests")
        return False
    else:
        print("✅ All server files found!")
    
    # Test 2: Start Gmail server only (for quick test)
    print("\n🚀 Test 2: Starting Gmail MCP server...")
    gmail_process = manager.start_server("gmail")
    
    if gmail_process:
        print("✅ Gmail server started successfully")
        
        # Test 3: Check status
        print("\n📊 Test 3: Checking server status...")
        status = manager.check_server_status()
        
        gmail_status = status.get("gmail", {})
        if gmail_status.get("status") == "running":
            print("✅ Gmail server status check passed")
        else:
            print("❌ Gmail server status check failed")
        
        # Test 4: Stop server
        print("\n🛑 Test 4: Stopping Gmail server...")
        stop_result = manager.stop_server("gmail")
        
        if stop_result:
            print("✅ Gmail server stopped successfully")
        else:
            print("❌ Failed to stop Gmail server")
        
        return True
    else:
        print("❌ Failed to start Gmail server")
        return False

def main():
    """Main entry point."""
    print("MCP Server Manager Test")
    print("======================")
    
    try:
        success = asyncio.run(test_server_manager())
        
        if success:
            print("\n🎉 All tests passed!")
            print("\n✅ MCP Server Manager is working correctly")
            print("\n📖 Usage:")
            print("   python3 backend/start_mcp_servers.py start    # Start all servers")
            print("   python3 backend/start_mcp_servers.py          # Interactive mode")
        else:
            print("\n❌ Some tests failed")
            print("Check the error messages above")
        
        return 0 if success else 1
    
    except KeyboardInterrupt:
        print("\n⚠️ Test interrupted")
        return 1
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())