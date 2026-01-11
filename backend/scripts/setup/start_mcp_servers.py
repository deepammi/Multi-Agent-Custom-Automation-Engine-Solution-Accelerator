#!/usr/bin/env python3
"""
Start MCP Servers for Testing

This script starts the MCP servers needed for AP and CRM agent testing:
- Bill.com MCP Server (for AccountsPayable agent)
- Salesforce MCP Server (for CRM agent)
- Gmail MCP Server (for Email agent)

Usage:
    python3 start_mcp_servers.py
"""

import asyncio
import subprocess
import sys
import os
import time
import signal
from typing import List, Dict, Any

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


class MCPServerManager:
    """Manages MCP server processes for testing."""
    
    def __init__(self):
        self.processes: Dict[str, subprocess.Popen] = {}
        self.server_configs = {
            "bill_com": {
                "name": "Bill.com MCP Server",
                "command": ["python3", "src/mcp_server/mcp_server.py"],
                "port": 9000,
                "health_endpoint": None
            },
            "gmail": {
                "name": "Gmail MCP Server", 
                "command": ["python3", "src/mcp_server/gmail_mcp_server.py"],
                "port": 9002,
                "health_endpoint": None
            },
            "salesforce": {
                "name": "Salesforce MCP Server",
                "command": ["python3", "src/mcp_server/salesforce_mcp_server.py"],
                "port": 9001,
                "health_endpoint": None
            }
        }
    
    def start_server(self, server_name: str) -> bool:
        """Start a specific MCP server."""
        if server_name not in self.server_configs:
            print(f"❌ Unknown server: {server_name}")
            return False
        
        config = self.server_configs[server_name]
        
        print(f"🚀 Starting {config['name']}...")
        print(f"   Command: {' '.join(config['command'])}")
        
        try:
            # Start the server process
            process = subprocess.Popen(
                config["command"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            self.processes[server_name] = process
            
            # Give the server a moment to start
            time.sleep(2)
            
            # Check if process is still running
            if process.poll() is None:
                print(f"✅ {config['name']} started successfully (PID: {process.pid})")
                return True
            else:
                stdout, stderr = process.communicate()
                print(f"❌ {config['name']} failed to start")
                print(f"   stdout: {stdout}")
                print(f"   stderr: {stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Failed to start {config['name']}: {e}")
            return False
    
    def stop_server(self, server_name: str) -> bool:
        """Stop a specific MCP server."""
        if server_name not in self.processes:
            print(f"⚠️ Server {server_name} is not running")
            return True
        
        config = self.server_configs[server_name]
        process = self.processes[server_name]
        
        print(f"🛑 Stopping {config['name']}...")
        
        try:
            # Try graceful shutdown first
            process.terminate()
            
            # Wait up to 5 seconds for graceful shutdown
            try:
                process.wait(timeout=5)
                print(f"✅ {config['name']} stopped gracefully")
            except subprocess.TimeoutExpired:
                # Force kill if graceful shutdown fails
                process.kill()
                process.wait()
                print(f"⚠️ {config['name']} force killed")
            
            del self.processes[server_name]
            return True
            
        except Exception as e:
            print(f"❌ Failed to stop {config['name']}: {e}")
            return False
    
    def start_all_servers(self) -> bool:
        """Start all MCP servers."""
        print("🚀 Starting All MCP Servers...")
        print("=" * 50)
        
        success_count = 0
        total_count = len(self.server_configs)
        
        for server_name in self.server_configs.keys():
            if self.start_server(server_name):
                success_count += 1
            print()  # Add spacing between servers
        
        print(f"📊 Server Start Summary:")
        print(f"   - Started: {success_count}/{total_count}")
        print(f"   - Success Rate: {(success_count/total_count)*100:.1f}%")
        
        if success_count == total_count:
            print(f"✅ All MCP servers started successfully!")
            return True
        else:
            print(f"⚠️ Some MCP servers failed to start")
            return False
    
    def stop_all_servers(self) -> bool:
        """Stop all running MCP servers."""
        print("\n🛑 Stopping All MCP Servers...")
        print("=" * 50)
        
        if not self.processes:
            print("ℹ️ No servers are currently running")
            return True
        
        success_count = 0
        total_count = len(self.processes)
        
        # Create a copy of the keys since we'll be modifying the dict
        server_names = list(self.processes.keys())
        
        for server_name in server_names:
            if self.stop_server(server_name):
                success_count += 1
        
        print(f"\n📊 Server Stop Summary:")
        print(f"   - Stopped: {success_count}/{total_count}")
        print(f"   - Success Rate: {(success_count/total_count)*100:.1f}%")
        
        return success_count == total_count
    
    def get_server_status(self) -> Dict[str, Any]:
        """Get status of all servers."""
        status = {}
        
        for server_name, config in self.server_configs.items():
            if server_name in self.processes:
                process = self.processes[server_name]
                if process.poll() is None:
                    status[server_name] = {
                        "status": "running",
                        "pid": process.pid,
                        "name": config["name"]
                    }
                else:
                    status[server_name] = {
                        "status": "stopped",
                        "pid": None,
                        "name": config["name"]
                    }
                    # Clean up dead process
                    del self.processes[server_name]
            else:
                status[server_name] = {
                    "status": "not_started",
                    "pid": None,
                    "name": config["name"]
                }
        
        return status
    
    def print_server_status(self):
        """Print current status of all servers."""
        print("\n📊 MCP Server Status:")
        print("=" * 40)
        
        status = self.get_server_status()
        
        for server_name, info in status.items():
            status_emoji = {
                "running": "✅",
                "stopped": "❌", 
                "not_started": "⚪"
            }.get(info["status"], "❓")
            
            pid_info = f" (PID: {info['pid']})" if info["pid"] else ""
            print(f"   {status_emoji} {info['name']}: {info['status'].upper()}{pid_info}")
    
    def cleanup(self):
        """Cleanup all processes on exit."""
        if self.processes:
            print("\n🧹 Cleaning up MCP servers...")
            self.stop_all_servers()


def signal_handler(signum, frame, manager: MCPServerManager):
    """Handle shutdown signals gracefully."""
    print(f"\n🛑 Received signal {signum}, shutting down...")
    manager.cleanup()
    sys.exit(0)


async def main():
    """Main function to manage MCP servers."""
    
    print("🔧 MCP Server Manager")
    print("=" * 30)
    print("This script manages MCP servers for AP and CRM agent testing")
    print()
    
    # Check if we're in the right directory
    if not os.path.exists("src/mcp_server"):
        print("❌ Error: src/mcp_server directory not found")
        print("   Please run this script from the project root directory")
        sys.exit(1)
    
    # Create server manager
    manager = MCPServerManager()
    
    # Set up signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, lambda s, f: signal_handler(s, f, manager))
    signal.signal(signal.SIGTERM, lambda s, f: signal_handler(s, f, manager))
    
    try:
        # Start all servers
        success = manager.start_all_servers()
        
        if success:
            print("\n🎉 All MCP servers are running!")
            print("\n📝 You can now run the integration tests:")
            print("   python3 backend/test_ap_crm_integration_with_mcp_fixed.py")
            print("\n⚠️ Press Ctrl+C to stop all servers")
            
            # Keep the script running and monitor servers
            try:
                while True:
                    # Check server status every 30 seconds
                    await asyncio.sleep(30)
                    
                    # Check if any servers have died
                    status = manager.get_server_status()
                    running_count = sum(1 for info in status.values() if info["status"] == "running")
                    total_count = len(status)
                    
                    if running_count < total_count:
                        print(f"\n⚠️ Warning: Only {running_count}/{total_count} servers are running")
                        manager.print_server_status()
                        
                        # Optionally restart failed servers
                        for server_name, info in status.items():
                            if info["status"] != "running":
                                print(f"🔄 Attempting to restart {info['name']}...")
                                manager.start_server(server_name)
            
            except KeyboardInterrupt:
                print(f"\n🛑 Shutdown requested by user")
        
        else:
            print("\n❌ Some servers failed to start. Check the errors above.")
            sys.exit(1)
    
    finally:
        # Cleanup on exit
        manager.cleanup()
        print("👋 MCP Server Manager shutdown complete")


if __name__ == "__main__":
    asyncio.run(main())