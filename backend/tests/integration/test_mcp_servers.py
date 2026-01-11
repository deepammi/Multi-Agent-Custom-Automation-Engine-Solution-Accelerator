#!/usr/bin/env python3
"""
Test script for MCP servers.
Tests that our MCP servers can be started and provide the expected tools.
"""

import asyncio
import logging
import sys
import os
import subprocess
import time
import json
from pathlib import Path

# Add the backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_mcp_server_exists():
    """Test that MCP server files exist."""
    print("\n=== Testing MCP Server Files Exist ===")
    
    try:
        # Check main MCP server
        main_server = Path("src/mcp_server/mcp_server.py")
        if main_server.exists():
            print("✅ Main MCP server file exists")
        else:
            print("❌ Main MCP server file missing")
            return False
        
        # Check Salesforce MCP server
        salesforce_server = Path("src/mcp_server/salesforce_mcp_server.py")
        if salesforce_server.exists():
            print("✅ Salesforce MCP server file exists")
        else:
            print("❌ Salesforce MCP server file missing")
            return False
        
        # Check Gmail MCP server
        gmail_server = Path("src/mcp_server/gmail_mcp_server.py")
        if gmail_server.exists():
            print("✅ Gmail MCP server file exists")
        else:
            print("❌ Gmail MCP server file missing")
            return False
        
        # Check service files
        salesforce_service = Path("src/mcp_server/services/salesforce_service.py")
        if salesforce_service.exists():
            print("✅ Salesforce service file exists")
        else:
            print("❌ Salesforce service file missing")
            return False
        
        gmail_service = Path("src/mcp_server/services/gmail_service.py")
        if gmail_service.exists():
            print("✅ Gmail service file exists")
        else:
            print("❌ Gmail service file missing")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ MCP server files test failed: {e}")
        return False


async def test_mcp_server_syntax():
    """Test that MCP server files have valid Python syntax."""
    print("\n=== Testing MCP Server Syntax ===")
    
    try:
        # Test main server syntax
        result = subprocess.run([
            "python3", "-m", "py_compile", "src/mcp_server/mcp_server.py"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Main MCP server syntax is valid")
        else:
            print(f"❌ Main MCP server syntax error: {result.stderr}")
            return False
        
        # Test Salesforce server syntax
        result = subprocess.run([
            "python3", "-m", "py_compile", "src/mcp_server/salesforce_mcp_server.py"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Salesforce MCP server syntax is valid")
        else:
            print(f"❌ Salesforce MCP server syntax error: {result.stderr}")
            return False
        
        # Test Gmail server syntax
        result = subprocess.run([
            "python3", "-m", "py_compile", "src/mcp_server/gmail_mcp_server.py"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Gmail MCP server syntax is valid")
        else:
            print(f"❌ Gmail MCP server syntax error: {result.stderr}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ MCP server syntax test failed: {e}")
        return False


async def test_mcp_server_imports():
    """Test that MCP server files can import their dependencies."""
    print("\n=== Testing MCP Server Imports ===")
    
    try:
        # Test if we can import the services
        import sys
        sys.path.insert(0, "src/mcp_server")
        
        try:
            from services.salesforce_service import SalesforceService
            print("✅ Salesforce service imports successfully")
        except ImportError as e:
            print(f"❌ Salesforce service import failed: {e}")
            return False
        
        try:
            from services.gmail_service import GmailService
            print("✅ Gmail service imports successfully")
        except ImportError as e:
            print(f"❌ Gmail service import failed: {e}")
            return False
        
        # Test service instantiation
        try:
            salesforce_service = SalesforceService()
            print(f"✅ Salesforce service instantiated ({salesforce_service.tool_count} tools)")
        except Exception as e:
            print(f"❌ Salesforce service instantiation failed: {e}")
            return False
        
        try:
            gmail_service = GmailService()
            print(f"✅ Gmail service instantiated ({gmail_service.tool_count} tools)")
        except Exception as e:
            print(f"❌ Gmail service instantiation failed: {e}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ MCP server imports test failed: {e}")
        return False


async def test_mcp_server_help():
    """Test that MCP servers can show help information."""
    print("\n=== Testing MCP Server Help ===")
    
    try:
        # Test Salesforce server help
        result = subprocess.run([
            "python3", "src/mcp_server/salesforce_mcp_server.py", "--help"
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0 and "Salesforce MCP Server" in result.stdout:
            print("✅ Salesforce MCP server help works")
        else:
            print(f"❌ Salesforce MCP server help failed: {result.stderr}")
            return False
        
        # Test Gmail server help
        result = subprocess.run([
            "python3", "src/mcp_server/gmail_mcp_server.py", "--help"
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0 and "Gmail MCP Server" in result.stdout:
            print("✅ Gmail MCP server help works")
        else:
            print(f"❌ Gmail MCP server help failed: {result.stderr}")
            return False
        
        return True
        
    except subprocess.TimeoutExpired:
        print("❌ MCP server help test timed out")
        return False
    except Exception as e:
        print(f"❌ MCP server help test failed: {e}")
        return False


async def test_fastmcp_availability():
    """Test if FastMCP is available for the MCP servers."""
    print("\n=== Testing FastMCP Availability ===")
    
    try:
        # Try to import FastMCP
        result = subprocess.run([
            "python3", "-c", "from fastmcp import FastMCP; print('FastMCP available')"
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print("✅ FastMCP is available")
            return True
        else:
            print(f"❌ FastMCP not available: {result.stderr}")
            print("💡 Install with: pip install fastmcp")
            return False
        
    except subprocess.TimeoutExpired:
        print("❌ FastMCP availability test timed out")
        return False
    except Exception as e:
        print(f"❌ FastMCP availability test failed: {e}")
        return False


async def test_mcp_server_tool_registration():
    """Test that MCP servers can register their tools."""
    print("\n=== Testing MCP Server Tool Registration ===")
    
    try:
        # Create a test script to check tool registration
        test_script = """
import sys
sys.path.insert(0, "src/mcp_server")

try:
    from fastmcp import FastMCP
    from services.salesforce_service import SalesforceService
    from services.gmail_service import GmailService
    
    # Test Salesforce service
    mcp_server = FastMCP("Test Server")
    salesforce_service = SalesforceService()
    salesforce_service.register_tools(mcp_server)
    print(f"Salesforce tools registered: {salesforce_service.tool_count}")
    
    # Test Gmail service
    gmail_service = GmailService()
    gmail_service.register_tools(mcp_server)
    print(f"Gmail tools registered: {gmail_service.tool_count}")
    
    print("Tool registration successful")
    
except ImportError as e:
    print(f"Import error: {e}")
    exit(1)
except Exception as e:
    print(f"Registration error: {e}")
    exit(1)
"""
        
        # Write and run the test script
        with open("test_tool_registration.py", "w") as f:
            f.write(test_script)
        
        result = subprocess.run([
            "python3", "test_tool_registration.py"
        ], capture_output=True, text=True, timeout=15)
        
        # Clean up test script
        os.remove("test_tool_registration.py")
        
        if result.returncode == 0:
            print("✅ MCP server tool registration works")
            print(f"   Output: {result.stdout.strip()}")
            return True
        else:
            print(f"❌ MCP server tool registration failed: {result.stderr}")
            return False
        
    except subprocess.TimeoutExpired:
        print("❌ Tool registration test timed out")
        return False
    except Exception as e:
        print(f"❌ Tool registration test failed: {e}")
        return False


async def main():
    """Run all MCP server tests."""
    print("🚀 Starting MCP Server Tests")
    
    tests = [
        test_mcp_server_exists,
        test_mcp_server_syntax,
        test_mcp_server_imports,
        test_fastmcp_availability,
        test_mcp_server_tool_registration,
        test_mcp_server_help
    ]
    
    results = []
    for test in tests:
        try:
            result = await test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")
            results.append(False)
    
    # Summary
    passed = sum(results)
    total = len(results)
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All MCP server tests passed!")
        print("\n✅ MCP Servers Ready:")
        print("   • Salesforce MCP Server: src/mcp_server/salesforce_mcp_server.py")
        print("   • Gmail MCP Server: src/mcp_server/gmail_mcp_server.py")
        print("\n🚀 Usage:")
        print("   # Start Salesforce MCP server")
        print("   python3 src/mcp_server/salesforce_mcp_server.py")
        print("   ")
        print("   # Start Gmail MCP server")
        print("   python3 src/mcp_server/gmail_mcp_server.py")
        print("   ")
        print("   # Test with HTTP transport")
        print("   python3 src/mcp_server/salesforce_mcp_server.py --transport http --port 9001")
        return 0
    else:
        print("⚠️ Some MCP server tests failed. Check the output above for details.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)