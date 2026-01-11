#!/usr/bin/env python3
"""
Start All MCP Servers Script

This script starts all 3 required MCP servers for the comprehensive agent integration tests:
- Bill.com MCP Server (port 9000)
- Salesforce MCP Server (port 9001) 
- Email MCP Server (port 9002)

Usage:
    python3 start_all_mcp_servers.py

The servers will run in the background. Use Ctrl+C to stop all servers.
"""

import asyncio
import subprocess
import signal
import sys
import os
import time
from pathlib import Path
from typing import Dict, List

class MCPServerManager:
    """Manages multiple MCP servers."""
    
    def __init__(self):
        self.servers: Dict[str, subprocess.Popen] = {}
        self.server_configs = [
            {
                "name": "Bill.com MCP Server",
                "port": 9000,
                "id": "bill_com"
            },
            {
                "name": "Salesforce MCP Server", 
                "port": 9001,
                "id": "salesforce"
            },
            {
                "name": "Email MCP Server",
                "port": 9002,
                "id": "email"
            }
        ]
    
    def start_server(self, config: Dict) -> bool:
        """Start a single MCP server."""
        try:
            # Use current working directory as project root
            script_path = Path("../src/mcp_server/mcp_server.py")
            
            if not script_path.exists():
                print(f"❌ MCP server script not found: {script_path}")
                return False
            
            print(f"🚀 Starting {config['name']} on port {config['port']}...")
            
            # Start the server in HTTP mode
            process = subprocess.Popen(
                ["python3", str(script_path), "--transport", "http", "--port", str(config['port'])],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=os.getcwd()
            )
            
            # Store the process
            self.servers[config['id']] = process
            
            # Give server time to start
            time.sleep(2)
            
            # Check if process is still running
            if process.poll() is None:
                print(f"✅ {config['name']} started (PID: {process.pid}, Port: {config['port']})")
                return True
            else:
                stdout, stderr = process.communicate()
                print(f"❌ {config['name']} failed to start (exit code: {process.returncode})")
                if stderr:
                    print(f"   Error: {stderr[:200]}...")
                return False
                        
        except Exception as e:
            print(f"❌ Failed to start {config['name']}: {e}")
            return False
    
    def start_all_servers(self) -> bool:
        """Start all MCP servers."""
        print("🚀 Starting All MCP Servers for Comprehensive Agent Integration Tests")
        print("=" * 80)
        
        success_count = 0
        
        for config in self.server_configs:
            if self.start_server(config):
                success_count += 1
            else:
                print(f"⚠️  Failed to start {config['name']}")
        
        print(f"\n📊 Server Startup Summary:")
        print(f"   Started: {success_count}/{len(self.server_configs)} servers")
        
        if success_count == len(self.server_configs):
            print(f"✅ All MCP servers started successfully!")
            print(f"\n🔗 Server URLs:")
            for config in self.server_configs:
                print(f"   {config['name']}: http://localhost:{config['port']}")
            
            print(f"\n🧪 Ready to run comprehensive tests:")
            print(f"   cd backend")
            print(f"   python3 test_agent_integration_comprehensive.py")
            
            return True
        else:
            print(f"❌ Some servers failed to start")
            return False
    
    def stop_all_servers(self):
        """Stop all MCP servers."""
        if not self.servers:
            return
        
        print(f"\n🛑 Stopping All MCP Servers...")
        
        for server_id, process in self.servers.items():
            try:
                config = next(c for c in self.server_configs if c['id'] == server_id)
                name = config['name']
                port = config['port']
                
                if process.poll() is None:
                    print(f"🛑 Stopping {name} (PID: {process.pid}, Port: {port})...")
                    process.terminate()
                    
                    try:
                        process.wait(timeout=5)
                        print(f"✅ {name} stopped gracefully")
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait()
                        print(f"✅ {name} force stopped")
                else:
                    print(f"📋 {name} already stopped")
            
            except Exception as e:
                print(f"❌ Error stopping server: {e}")
        
        self.servers.clear()
        print(f"✅ All MCP servers stopped")
    
    def check_server_status(self):
        """Check status of all servers."""
        print(f"\n📊 MCP Server Status:")
        
        for config in self.server_configs:
            server_id = config['id']
            if server_id in self.servers:
                process = self.servers[server_id]
                if process.poll() is None:
                    print(f"   ✅ {config['name']}: Running (PID: {process.pid}, Port: {config['port']})")
                else:
                    print(f"   ❌ {config['name']}: Stopped (Port: {config['port']})")
            else:
                print(f"   ❌ {config['name']}: Not started (Port: {config['port']})")


def main():
    """Main function."""
    manager = MCPServerManager()
    
    # Setup signal handlers for cleanup
    def signal_handler(signum, frame):
        print(f"\n🛑 Received signal {signum}. Cleaning up...")
        manager.stop_all_servers()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Start all servers
        success = manager.start_all_servers()
        
        if success:
            print(f"\n⏳ Servers are running. Press Ctrl+C to stop all servers.")
            print(f"💡 You can now run the comprehensive test in another terminal:")
            print(f"   cd backend && python3 test_agent_integration_comprehensive.py")
            
            # Keep the script running
            while True:
                time.sleep(10)
                # Optionally check server status periodically
                # manager.check_server_status()
        else:
            print(f"\n❌ Failed to start all servers. Exiting.")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print(f"\n🛑 Interrupted by user")
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
    finally:
        manager.stop_all_servers()


if __name__ == "__main__":
    main()