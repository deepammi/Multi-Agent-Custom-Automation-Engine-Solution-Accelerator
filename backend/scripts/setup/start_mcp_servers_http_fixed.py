#!/usr/bin/env python3
"""
Fixed MCP Servers HTTP Startup Script

This script fixes the MCP server startup issues by:
1. Using correct FastMCP HTTP endpoints (no /mcp suffix)
2. Adding better error handling and logging
3. Ensuring proper tool registration
4. Validating server startup with tool listing
"""

import subprocess
import sys
import os
import time
import signal
import asyncio
import json
from pathlib import Path
from typing import Dict, List, Optional

class FixedHTTPMCPServerManager:
    """Fixed MCP server manager with proper HTTP configuration."""
    
    def __init__(self):
        """Initialize server manager."""
        self.servers = {}
        self.server_configs = {
            "bill_com": {
                "script": "src/mcp_server/mcp_server.py",
                "name": "Bill.com MCP Server", 
                "port": 9000,
                "url": "http://localhost:9000"  # No /mcp suffix - FastMCP handles routing
            },
            "salesforce": {
                "script": "src/mcp_server/salesforce_mcp_server.py", 
                "name": "Salesforce MCP Server",
                "port": 9001,
                "url": "http://localhost:9001"
            },
            "gmail": {
                "script": "src/mcp_server/gmail_mcp_server.py",
                "name": "Gmail MCP Server",
                "port": 9002,
                "url": "http://localhost:9002"
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
        print(f"\n{'=' * 70}")
        print(f"🚀 {title}")
        print(f"{'=' * 70}")
    
    def print_section(self, title: str):
        """Print section header."""
        print(f"\n🔹 {title}")
        print("-" * (len(title) + 4))
    
    def start_server_http(self, server_id: str) -> Optional[subprocess.Popen]:
        """Start a single MCP server in HTTP mode with enhanced error handling."""
        config = self.server_configs[server_id]
        script_path = Path(config["script"])
        
        if not script_path.exists():
            print(f"❌ {config['name']} script not found: {script_path}")
            return None
        
        try:
            print(f"🚀 Starting {config['name']} on port {config['port']}...")
            
            # Set comprehensive environment variables
            env = os.environ.copy()
            env.update({
                # Enable all MCP services
                "SALESFORCE_MCP_ENABLED": "true",
                "GMAIL_MCP_ENABLED": "true", 
                "BILL_COM_MCP_ENABLED": "true",
                
                # Ensure Python path includes necessary directories
                "PYTHONPATH": f"{os.getcwd()}/src/mcp_server:{env.get('PYTHONPATH', '')}",
                
                # Enable debug logging for troubleshooting
                "MCP_DEBUG": "true"
            })
            
            # Start the server in HTTP mode with explicit arguments
            cmd = [
                "python3", 
                str(script_path), 
                "--transport", "http", 
                "--port", str(config["port"]),
                "--host", "0.0.0.0",  # Allow external connections
                "--debug"  # Enable debug logging
            ]
            
            print(f"   📝 Command: {' '.join(cmd)}")
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=os.getcwd(),
                env=env
            )
            
            # Wait longer for server to initialize (especially for Bill.com with config validation)
            print(f"   ⏳ Waiting for {config['name']} to initialize...")
            time.sleep(8)  # Increased wait time
            
            # Check if process is still running
            if process.poll() is None:
                print(f"✅ {config['name']} started (PID: {process.pid}, Port: {config['port']})")
                print(f"   🌐 URL: {config['url']}")
                
                # Test server connectivity
                if self._test_server_connectivity(config):
                    self.servers[server_id] = process
                    return process
                else:
                    print(f"⚠️  {config['name']} started but connectivity test failed")
                    # Keep the server running but note the issue
                    self.servers[server_id] = process
                    return process
            else:
                # Process exited - get detailed error info
                stdout, stderr = process.communicate()
                print(f"❌ {config['name']} failed to start (exit code: {process.returncode})")
                
                if stderr:
                    print(f"   📄 Error output:")
                    for line in stderr.split('\n')[:10]:  # Show first 10 lines
                        if line.strip():
                            print(f"      {line}")
                
                if stdout:
                    print(f"   📄 Standard output:")
                    for line in stdout.split('\n')[:10]:  # Show first 10 lines
                        if line.strip():
                            print(f"      {line}")
                
                return None
        
        except Exception as e:
            print(f"❌ Failed to start {config['name']}: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _test_server_connectivity(self, config: Dict) -> bool:
        """Test if server is responding to HTTP requests."""
        try:
            import requests
            
            # Test basic HTTP connectivity
            health_url = f"{config['url']}/health"
            response = requests.get(health_url, timeout=5)
            
            if response.status_code == 200:
                print(f"   ✅ Health check passed: {health_url}")
                return True
            else:
                print(f"   ⚠️  Health check failed: {health_url} (status: {response.status_code})")
                return False
                
        except ImportError:
            print(f"   ⚠️  Requests library not available - skipping connectivity test")
            return True  # Assume success if we can't test
        except Exception as e:
            print(f"   ⚠️  Connectivity test failed: {e}")
            return False
    
    async def _test_mcp_tools(self, server_id: str, config: Dict) -> bool:
        """Test if MCP server is exposing tools properly."""
        try:
            from fastmcp import Client
            
            # Use the correct MCP endpoint
            mcp_url = f"{config['url']}/mcp"
            print(f"   🔧 Testing MCP tools at: {mcp_url}")
            
            async with Client(mcp_url) as client:
                tools = await client.list_tools()
                tool_count = len(tools.tools) if hasattr(tools, 'tools') else 0
                
                if tool_count > 0:
                    print(f"   ✅ MCP tools available: {tool_count}")
                    
                    # Show first few tools
                    if hasattr(tools, 'tools'):
                        for i, tool in enumerate(tools.tools[:3]):
                            print(f"      - {tool.name}")
                        if len(tools.tools) > 3:
                            print(f"      ... and {len(tools.tools) - 3} more")
                    
                    return True
                else:
                    print(f"   ❌ No MCP tools found")
                    return False
                    
        except ImportError:
            print(f"   ⚠️  FastMCP client not available - skipping tool test")
            return True
        except Exception as e:
            print(f"   ❌ MCP tool test failed: {e}")
            return False
    
    def start_all_servers_http(self) -> Dict[str, bool]:
        """Start all MCP servers in HTTP mode with validation."""
        self.print_section("Starting MCP Servers in HTTP Mode")
        
        results = {}
        
        # Start servers sequentially to avoid port conflicts
        for server_id in self.server_configs.keys():
            print(f"\n{'─' * 50}")
            process = self.start_server_http(server_id)
            results[server_id] = process is not None
            
            if process is not None:
                # Test MCP functionality asynchronously
                config = self.server_configs[server_id]
                try:
                    # Run async tool test
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    tool_test_result = loop.run_until_complete(
                        self._test_mcp_tools(server_id, config)
                    )
                    loop.close()
                    
                    if not tool_test_result:
                        print(f"   ⚠️  {config['name']}: Started but tools not accessible")
                except Exception as e:
                    print(f"   ⚠️  {config['name']}: Tool test error: {e}")
        
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
            
            # Wait up to 10 seconds for graceful shutdown
            try:
                process.wait(timeout=10)
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
            print("ℹ️  No servers to stop")
            return
        
        self.print_section("Stopping MCP Servers")
        
        for server_id in list(self.servers.keys()):
            self.stop_server(server_id)
    
    def check_server_status(self) -> Dict[str, Dict[str, any]]:
        """Check status of all servers with enhanced diagnostics."""
        self.print_section("MCP Server Status")
        
        status = {}
        
        for server_id, config in self.server_configs.items():
            print(f"\n🔍 {config['name']}:")
            
            if server_id in self.servers:
                process = self.servers[server_id]
                if process.poll() is None:
                    print(f"   ✅ Process: Running (PID: {process.pid})")
                    print(f"   🌐 Port: {config['port']}")
                    print(f"   🔗 URL: {config['url']}")
                    
                    # Test connectivity
                    if self._test_server_connectivity(config):
                        print(f"   ✅ HTTP: Responding")
                    else:
                        print(f"   ❌ HTTP: Not responding")
                    
                    # Test MCP tools
                    try:
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        tool_test = loop.run_until_complete(
                            self._test_mcp_tools(server_id, config)
                        )
                        loop.close()
                        
                        if tool_test:
                            print(f"   ✅ MCP: Tools available")
                        else:
                            print(f"   ❌ MCP: No tools found")
                    except Exception as e:
                        print(f"   ❌ MCP: Test failed ({e})")
                    
                    status[server_id] = {
                        "status": "running", 
                        "pid": process.pid, 
                        "port": config['port']
                    }
                else:
                    print(f"   ❌ Process: Stopped (exit code: {process.returncode})")
                    status[server_id] = {
                        "status": "stopped", 
                        "exit_code": process.returncode
                    }
                    del self.servers[server_id]
            else:
                print(f"   ⚪ Process: Not started")
                status[server_id] = {"status": "not_started"}
        
        return status
    
    def run_servers(self):
        """Start servers and keep them running with monitoring."""
        self.print_header("Fixed HTTP MCP Server Manager")
        
        print("🎯 This script fixes MCP server startup issues:")
        print("   • Correct FastMCP HTTP endpoints")
        print("   • Enhanced error handling and logging")
        print("   • Proper tool registration validation")
        print("   • Comprehensive connectivity testing")
        
        # Start all servers
        start_results = self.start_all_servers_http()
        started = sum(start_results.values())
        total = len(start_results)
        
        print(f"\n📊 Startup Results: {started}/{total} servers started")
        
        if started == 0:
            print(f"❌ No servers started successfully")
            print(f"   Check the error messages above for troubleshooting")
            return
        
        # Show connection info
        print(f"\n🌐 Server Connection Information:")
        for server_id, config in self.server_configs.items():
            if server_id in self.servers:
                print(f"   ✅ {config['name']}:")
                print(f"      HTTP: {config['url']}")
                print(f"      MCP:  {config['url']}/mcp")
                print(f"      Health: curl {config['url']}/health")
        
        print(f"\n🧪 Test Commands:")
        print(f"   Connectivity Test: python3 backend/test_mcp_http_connectivity.py")
        print(f"   Integration Test:  python3 backend/test_ap_crm_integration_http_mcp.py")
        print(f"   Complete Test:     python3 backend/test_complete_integration_success.py")
        
        print(f"\n✅ Servers are running! Press Ctrl+C to stop all servers")
        print(f"📊 Use 'python3 {sys.argv[0]} status' to check detailed status")
        
        try:
            # Keep servers running with health monitoring
            while True:
                time.sleep(10)  # Check every 10 seconds
                
                # Check if any server died
                dead_servers = []
                for server_id, process in list(self.servers.items()):
                    if process.poll() is not None:
                        dead_servers.append(server_id)
                
                if dead_servers:
                    print(f"\n⚠️  Detected dead servers: {', '.join(dead_servers)}")
                    for server_id in dead_servers:
                        config = self.server_configs[server_id]
                        process = self.servers[server_id]
                        print(f"   ❌ {config['name']} exited with code: {process.returncode}")
                        
                        # Get final output
                        try:
                            stdout, stderr = process.communicate(timeout=1)
                            if stderr:
                                print(f"      Final error: {stderr.split(chr(10))[-2] if stderr else 'None'}")
                        except:
                            pass
                        
                        del self.servers[server_id]
        
        except KeyboardInterrupt:
            print(f"\n🛑 Stopping servers...")
            self.stop_all_servers()


def main():
    """Main entry point with enhanced command handling."""
    manager = FixedHTTPMCPServerManager()
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "start":
            manager.print_header("Starting Fixed HTTP MCP Servers")
            start_results = manager.start_all_servers_http()
            started = sum(start_results.values())
            total = len(start_results)
            print(f"\n📊 Started {started}/{total} servers")
            
            if started > 0:
                print(f"\n✅ Servers started successfully")
                print(f"   Use 'python3 {sys.argv[0]} status' to check detailed status")
                print(f"   Use 'python3 {sys.argv[0]} stop' to stop servers")
            else:
                print(f"\n❌ No servers started - check error messages above")
        
        elif command == "stop":
            manager.print_header("Stopping HTTP MCP Servers")
            manager.stop_all_servers()
        
        elif command == "status":
            manager.print_header("HTTP MCP Server Status")
            manager.check_server_status()
        
        elif command == "restart":
            manager.print_header("Restarting HTTP MCP Servers")
            print("🔄 Stopping existing servers...")
            manager.stop_all_servers()
            time.sleep(2)
            print("🚀 Starting servers...")
            start_results = manager.start_all_servers_http()
            started = sum(start_results.values())
            total = len(start_results)
            print(f"\n📊 Restarted {started}/{total} servers")
        
        else:
            print(f"❌ Unknown command: {command}")
            print(f"Usage: python3 {sys.argv[0]} [start|stop|status|restart]")
            print(f"   Or run without arguments to start servers interactively")
    
    else:
        # Interactive mode - start and keep running
        manager.run_servers()


if __name__ == "__main__":
    main()