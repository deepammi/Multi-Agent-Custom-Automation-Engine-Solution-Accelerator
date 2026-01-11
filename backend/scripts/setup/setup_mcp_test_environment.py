#!/usr/bin/env python3
"""
Setup script for MCP testing environment.

This script sets up the proper environment for testing MCP servers
with correct paths, dependencies, and process management.
"""

import os
import sys
import subprocess
import asyncio
from pathlib import Path

# ANSI color codes
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
RESET = '\033[0m'
BOLD = '\033[1m'


def setup_python_path():
    """Setup Python path for MCP server imports."""
    current_dir = Path(__file__).parent
    project_root = current_dir.parent
    
    # Add paths that MCP servers need
    paths_to_add = [
        str(project_root),  # For 'backend' module
        str(current_dir),   # For 'app' module
        str(project_root / "src"),  # For MCP server modules
    ]
    
    for path in paths_to_add:
        if path not in sys.path:
            sys.path.insert(0, path)
    
    # Set PYTHONPATH environment variable for subprocesses
    current_pythonpath = os.environ.get("PYTHONPATH", "")
    new_pythonpath = ":".join(paths_to_add + [current_pythonpath] if current_pythonpath else paths_to_add)
    os.environ["PYTHONPATH"] = new_pythonpath
    
    print(f"{GREEN}✅ Python path configured{RESET}")
    print(f"PYTHONPATH: {new_pythonpath}")


def check_mcp_dependencies():
    """Check if MCP SDK is installed."""
    try:
        import mcp
        print(f"{GREEN}✅ MCP SDK available (version: {getattr(mcp, '__version__', 'unknown')}){RESET}")
        return True
    except ImportError:
        print(f"{RED}❌ MCP SDK not installed{RESET}")
        print(f"{YELLOW}Install with: pip install mcp{RESET}")
        return False


def check_server_files():
    """Check if MCP server files exist and are executable."""
    current_dir = Path(__file__).parent
    project_root = current_dir.parent
    
    servers_to_check = [
        project_root / "src" / "mcp_server" / "zoho_mcp_server.py",
        project_root / "src" / "mcp_server" / "gmail_mcp_server.py", 
        project_root / "src" / "mcp_server" / "salesforce_mcp_server.py",
    ]
    
    all_exist = True
    for server_path in servers_to_check:
        if server_path.exists():
            print(f"{GREEN}✅ {server_path.name} exists{RESET}")
        else:
            print(f"{RED}❌ {server_path.name} missing{RESET}")
            all_exist = False
    
    return all_exist


async def test_server_startup():
    """Test if MCP servers can start up properly."""
    current_dir = Path(__file__).parent
    project_root = current_dir.parent
    
    server_path = project_root / "src" / "mcp_server" / "zoho_mcp_server.py"
    
    if not server_path.exists():
        print(f"{RED}❌ Zoho MCP server not found{RESET}")
        return False
    
    try:
        print(f"{YELLOW}Testing Zoho MCP server startup...{RESET}")
        
        # Start server process
        process = await asyncio.create_subprocess_exec(
            "python3", str(server_path),
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(current_dir)
        )
        
        # Wait a moment for startup
        await asyncio.sleep(1)
        
        # Check if process is still running
        if process.returncode is None:
            print(f"{GREEN}✅ Zoho MCP server started successfully{RESET}")
            
            # Terminate the process
            process.terminate()
            await process.wait()
            return True
        else:
            # Process exited, check stderr
            stderr = await process.stderr.read()
            print(f"{RED}❌ Zoho MCP server failed to start{RESET}")
            print(f"Error: {stderr.decode()}")
            return False
            
    except Exception as e:
        print(f"{RED}❌ Failed to test server startup: {e}{RESET}")
        return False


def create_test_config():
    """Create test configuration for MCP services."""
    config = {
        "mcp_servers": {
            "zoho": {
                "command": "python3",
                "args": ["../src/mcp_server/zoho_mcp_server.py"],
                "env": {
                    "ZOHO_USE_MOCK": "true",
                    "ZOHO_MCP_ENABLED": "true"
                },
                "timeout": 30
            },
            "gmail": {
                "command": "python3", 
                "args": ["../src/mcp_server/gmail_mcp_server.py"],
                "env": {
                    "GMAIL_USE_MOCK": "true"
                },
                "timeout": 30
            }
        }
    }
    
    config_path = Path(__file__).parent / "mcp_test_config.json"
    
    import json
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"{GREEN}✅ Test configuration created: {config_path}{RESET}")
    return config_path


async def main():
    """Main setup function."""
    print(f"{BOLD}MCP Test Environment Setup{RESET}")
    print("=" * 50)
    
    # Setup Python path
    setup_python_path()
    
    # Check dependencies
    if not check_mcp_dependencies():
        print(f"\n{RED}❌ Setup failed: MCP SDK not available{RESET}")
        return False
    
    # Check server files
    if not check_server_files():
        print(f"\n{RED}❌ Setup failed: MCP server files missing{RESET}")
        return False
    
    # Test server startup
    if not await test_server_startup():
        print(f"\n{RED}❌ Setup failed: MCP server startup issues{RESET}")
        return False
    
    # Create test config
    config_path = create_test_config()
    
    print(f"\n{GREEN}✅ MCP test environment setup complete{RESET}")
    print(f"\n{BOLD}Next steps:{RESET}")
    print(f"1. Run: python3 test_mcp_mock_server.py")
    print(f"2. Run: python3 test_zoho_mcp_server_standalone.py") 
    print(f"3. Use config: {config_path}")
    
    return True


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)