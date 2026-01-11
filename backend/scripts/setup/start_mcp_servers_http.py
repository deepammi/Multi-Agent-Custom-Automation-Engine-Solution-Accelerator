#!/usr/bin/env python3
"""
Start MCP Servers in HTTP Mode

Starts MCP servers in HTTP mode for testing with HTTP transport.
This allows clients to connect to already running servers.
"""

import subprocess
import sys
import os
import time
import signal
from pathlib import Path
from typing import Dict, List, Optional

class HTTPMCPServerManager:
    """Manages MCP servers in HTTP mode."""
    
    def __init__(self):
        """Initialize server manager."""
        self.servers = {}
        self.server_configs = {
            "gmail": {
                "script": "src/mcp_server/gmail_mcp_server.py",
                "name": "Gmail MCP Server",
                "port": 9002
            },
            "salesforce": {
                "script": "src/mcp_server/salesforce_mcp_server.py", 
                "name": "Salesforce MCP Server",
                "port": 9001
            },
            "bill_com": {
                "script": "src/mcp_server/mcp_server.py",
                "name": "Bill.com MCP Server", 
                "port": 9000
            }
        }
        
        # Setup signal handlers for cleanup
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle signals for graceful shutdown."""
        print(f"\n🛑 Received signal {signum}. Stopping all servers...")
        self.stop_all_servers()
        sys.exit(0)
    
    def print_header(self, title: str):
        """Print formatted header."""
        print(f"\n{'=' * 60}")
        print(f"🚀 {title}")
        print(f"{'=' * 60}")
    
    def print_section(self, title: str):
        """Print section header."""
        print(f"\n🔹 {title}")
        print("-" * (len(title) + 4))
    
    def start_server_http(self, server_id: str) -> Optional[subprocess.Popen]:
        """Start a single MCP server in HTTP mode."""
        config = self.server_configs[server_id]
        script_path = Path(config["script"])
        
        if not script_path.exists():
            print(f"❌ {config['name']} script not found: {script_path}")
            return None
        
        try:
            print(f"🚀 Starting {config['name']} on port {config['port']}...")
            
            # Set environment variables
            env = os.environ.copy()
            env.update({
                "SALESFORCE_MCP_ENABLED": "true",
                "GMAIL_MCP_ENABLED": "true", 
                "BILL_COM_MCP_ENABLED": "true"
            })
            
            # Start the server in HTTP mode
            process = subprocess.Popen(
                ["python3", str(script_path), "--transport", "http", "--port", str(config["port"])],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=os.getcwd(),
                env=env
            )
            
            # Wait for server to initialize
            time.sleep(3)
            
            # Check if process is still running
            if process.poll() is None:
                print(f"✅ {config['name']} started (PID: {process.pid}, Port: {config['port']})")
                print(f"   Health check: curl http://localhost:{config['port']}/health")
                self.servers[server_id] = process
                return process
            else:
                # Process exited
                stdout, stderr = process.communicate()
                print(f"❌ {config['name']} failed to start (exit code: {process.returncode})")
                if stderr:
                    print(f"   Error: {stderr[:300]}...")
                if stdout:
                    print(f"   Output: {stdout[:300]}...")
                return None
        
        except Exception as e:
            print(f"❌ Failed to start {config['name']}: {e}")
            return None
    
    def start_all_servers_http(self) -> Dict[str, bool]:
        """Start all MCP servers in HTTP mode."""
        self.print_section("Starting MCP Servers in HTTP Mode")
        
        results = {}
        
        for server_id in self.server_configs.keys():
            process = self.start_server_http(server_id)
            results[server_id] = process is not None
        
        return results
    
    def stop_server(self, server_id: str) -> bool:
        """Stop a single MCP server."""
        if server_id not in self.servers:
            return True
        
        process = self.servers[server_id]
        config = self.server_configs[server_id]
        
        try:
            print(f"🛑 Stopping {config['name']} (PID: {process.pid})...")
            
            # Try graceful termination first
            process.terminate()
            
            # Wait up to 5 seconds for graceful shutdown
            try:
                process.wait(timeout=5)
                print(f"✅ {config['name']} stopped gracefully")
            except subprocess.TimeoutExpired:
                # Force kill if graceful shutdown failed
                print(f"⚠️  Force killing {config['name']}...")
                process.kill()
                process.wait()
                print(f"✅ {config['name']} force stopped")
            
            del self.servers[server_id]
            return True
        
        except Exception as e:
            print(f"❌ Error stopping {config['name']}: {e}")
            return False
    
    def stop_all_servers(self) -> None:
        """Stop all running MCP servers."""
        if not self.servers:
            return
        
        self.print_section("Stopping MCP Servers")
        
        for server_id in list(self.servers.keys()):
            self.stop_server(server_id)
    
    def check_server_status(self) -> Dict[str, Dict[str, any]]:
        """Check status of all servers."""
        self.print_section("MCP Server Status")
        
        status = {}
        
        for server_id, config in self.server_configs.items():
            if server_id in self.servers:
                process = self.servers[server_id]
                if process.poll() is None:
                    print(f"✅ {config['name']}: Running (PID: {process.pid}, Port: {config['port']})")
                    status[server_id] = {"status": "running", "pid": process.pid, "port": config['port']}
                else:
                    print(f"❌ {config['name']}: Stopped (exit code: {process.returncode})")
                    status[server_id] = {"status": "stopped", "exit_code": process.returncode}
                    del self.servers[server_id]
            else:
                print(f"⚪ {config['name']}: Not started")
                status[server_id] = {"status": "not_started"}
        
        return status
    
    def run_servers(self):
        """Start servers and keep them running."""
        self.print_header("HTTP MCP Server Manager")
        
        print("Starting MCP servers in HTTP mode for testing...")
        print("Servers will be accessible via HTTP transport")
        
        # Start all servers
        start_results = self.start_all_servers_http()
        started = sum(start_results.values())
        total = len(start_results)
        
        print(f"\n📊 Started {started}/{total} servers")
        
        if started == 0:
            print(f"❌ No servers started successfully")
            return
        
        # Show connection info
        print(f"\n🌐 Server Connection Information:")
        for server_id, config in self.server_configs.items():
            if server_id in self.servers:
                print(f"   {config['name']}: http://localhost:{config['port']}")
                print(f"     Health check: curl http://localhost:{config['port']}/health")
        
        print(f"\n🧪 Test Commands:")
        print(f"   Gmail Agent Test: python3 backend/test_gmail_agent_http.py")
        print(f"   All Agents Test: python3 backend/test_all_agents_http.py")
        
        print(f"\n✅ Servers are running! Press Ctrl+C to stop all servers")
        
        try:
            # Keep servers running
            while True:
                time.sleep(1)
                
                # Check if any server died
                dead_servers = []
                for server_id, process in list(self.servers.items()):
                    if process.poll() is not None:
                        dead_servers.append(server_id)
                
                if dead_servers:
                    print(f"\n⚠️  Detected dead servers: {', '.join(dead_servers)}")
                    for server_id in dead_servers:
                        config = self.server_configs[server_id]
                        print(f"   {config['name']} exited with code: {self.servers[server_id].returncode}")
                        del self.servers[server_id]
        
        except KeyboardInterrupt:
            print(f"\n🛑 Stopping servers...")
            self.stop_all_servers()


def main():
    """Main entry point."""
    manager = HTTPMCPServerManager()
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "start":
            manager.print_header("Starting HTTP MCP Servers")
            start_results = manager.start_all_servers_http()
            started = sum(start_results.values())
            total = len(start_results)
            print(f"\n📊 Started {started}/{total} servers")
            
            if started > 0:
                print(f"\n✅ Servers started in background")
                print(f"   Use 'python3 {sys.argv[0]} status' to check status")
                print(f"   Use 'python3 {sys.argv[0]} stop' to stop servers")
        
        elif command == "stop":
            manager.print_header("Stopping HTTP MCP Servers")
            manager.stop_all_servers()
        
        elif command == "status":
            manager.print_header("HTTP MCP Server Status")
            manager.check_server_status()
        
        else:
            print(f"❌ Unknown command: {command}")
            print(f"Usage: python3 {sys.argv[0]} [start|stop|status]")
            print(f"   Or run without arguments to start servers interactively")
    
    else:
        # Interactive mode - start and keep running
        manager.run_servers()


if __name__ == "__main__":
    main()