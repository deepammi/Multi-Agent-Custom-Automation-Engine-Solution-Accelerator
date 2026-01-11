#!/usr/bin/env python3
"""
Standalone Invoice Agent Test

This test isolates the Invoice Agent functionality to debug Bill.com integration
and test various prompts to understand why invoices aren't being found.

Usage:
    python3 test_invoice_agent_standalone.py
    
Features:
- Interactive prompt testing
- Direct Bill.com MCP tool testing
- Verbose logging and debugging
- Multiple search strategies
- Health check diagnostics
"""

import asyncio
import sys
import os
import json
import logging
import subprocess
import time
import signal
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Force disable mock mode to see real responses
os.environ["USE_MOCK_LLM"] = "false"

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MockWebSocketManager:
    """Mock websocket manager for testing."""
    
    def __init__(self, verbose=True):
        self.verbose = verbose
        self.messages = []
    
    async def send_message(self, plan_id: str, message: dict):
        """Mock send message with verbose logging."""
        self.messages.append(message)
        
        if self.verbose:
            msg_type = message.get('type', 'unknown')
            content = message.get('content', '')
            agent = message.get('data', {}).get('agent_name', 'unknown')
            
            if msg_type == "agent_message":
                print(f"📡 Agent Message ({agent}): {content[:100]}...")

class InvoiceAgentTester:
    """Standalone Invoice Agent tester for debugging Bill.com integration."""
    
    def __init__(self):
        """Initialize the tester."""
        self.mcp_server_process = None
        self.websocket_manager = MockWebSocketManager(verbose=True)
        
        # Setup signal handlers for cleanup
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle signals for graceful shutdown."""
        print(f"\n🛑 Received signal {signum}. Cleaning up...")
        asyncio.create_task(self.stop_mcp_server())
        sys.exit(0)
    
    def print_header(self, title: str):
        """Print formatted header."""
        print(f"\n{'=' * 80}")
        print(f"🚀 {title}")
        print(f"{'=' * 80}")
    
    def print_section(self, title: str):
        """Print section header."""
        print(f"\n🔹 {title}")
        print("-" * (len(title) + 4))
    
    async def start_mcp_server(self) -> bool:
        """Start Bill.com MCP server."""
        self.print_section("Starting Bill.com MCP Server")
        
        try:
            from pathlib import Path
            
            # Resolve script path relative to project root
            project_root = os.path.dirname(os.getcwd())
            script_path = Path(project_root) / "src/mcp_server/mcp_server.py"
            
            if not script_path.exists():
                print(f"❌ MCP server script not found: {script_path}")
                return False
            
            print(f"🚀 Starting Bill.com MCP Server on port 9000...")
            
            # Set environment variables
            env = os.environ.copy()
            env["BILL_COM_MCP_ENABLED"] = "true"
            
            # Start the server in HTTP mode
            self.mcp_server_process = subprocess.Popen(
                ["python3", str(script_path), "--transport", "http", "--port", "9000"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=project_root,
                env=env
            )
            
            # Wait for server to initialize
            await asyncio.sleep(3)
            
            # Check if process is still running
            if self.mcp_server_process.poll() is None:
                print(f"✅ Bill.com MCP Server started (PID: {self.mcp_server_process.pid}, Port: 9000)")
                print(f"   Health check: curl http://localhost:9000/health")
                return True
            else:
                stdout, stderr = self.mcp_server_process.communicate()
                print(f"❌ Bill.com MCP Server failed to start (exit code: {self.mcp_server_process.returncode})")
                if stderr:
                    print(f"   Error: {stderr[:300]}...")
                if stdout:
                    print(f"   Output: {stdout[:300]}...")
                return False
                
        except Exception as e:
            print(f"❌ Failed to start Bill.com MCP Server: {e}")
            return False
    
    async def stop_mcp_server(self):
        """Stop MCP server."""
        if not self.mcp_server_process:
            return
        
        self.print_section("Stopping Bill.com MCP Server")
        
        try:
            if self.mcp_server_process.poll() is None:
                print(f"🛑 Stopping Bill.com MCP Server (PID: {self.mcp_server_process.pid})...")
                self.mcp_server_process.terminate()
                
                try:
                    self.mcp_server_process.wait(timeout=5)
                    print(f"✅ Bill.com MCP Server stopped gracefully")
                except subprocess.TimeoutExpired:
                    self.mcp_server_process.kill()
                    self.mcp_server_process.wait()
                    print(f"✅ Bill.com MCP Server force stopped")
            else:
                print(f"📋 Bill.com MCP Server already stopped")
        
        except Exception as e:
            print(f"❌ Error stopping Bill.com MCP Server: {e}")
        
        self.mcp_server_process = None
    
    async def test_bill_com_health(self) -> Dict[str, Any]:
        """Test Bill.com service health."""
        self.print_section("Bill.com Health Check")
        
        try:
            from app.services.mcp_client_service import get_bill_com_service
            
            print("🏥 Checking Bill.com service health...")
            
            bill_com_service = await get_bill_com_service()
            health_result = await bill_com_service.check_bill_com_health()
            
            print(f"📊 Health Check Result:")
            print(f"   Success: {health_result.get('success', False)}")
            print(f"   Error: {health_result.get('error', 'None')}")
            print(f"   Connection Status: {health_result.get('connection_status', 'Unknown')}")
            
            # Show detailed health data if available
            health_data = health_result.get('health_data')
            if health_data:
                if isinstance(health_data, str):
                    try:
                        health_data = json.loads(health_data)
                    except:
                        pass
                
                if isinstance(health_data, dict):
                    print(f"\n📋 Detailed Health Information:")
                    print(f"   Overall Status: {health_data.get('overall_status', 'Unknown')}")
                    
                    checks = health_data.get('checks', {})
                    for check_name, check_data in checks.items():
                        status = check_data.get('status', 'Unknown')
                        message = check_data.get('message', 'No message')
                        emoji = "✅" if status == "healthy" else "⚠️" if status == "warning" else "❌"
                        print(f"   {emoji} {check_name.title()}: {status} - {message}")
            
            return health_result
            
        except Exception as e:
            print(f"❌ Health check failed: {e}")
            import traceback
            traceback.print_exc()
            return {"success": False, "error": str(e)}
    
    async def test_direct_bill_com_tools(self) -> Dict[str, Any]:
        """Test Bill.com tools directly."""
        self.print_section("Direct Bill.com Tool Testing")
        
        try:
            from app.services.mcp_client_service import get_bill_com_service
            
            bill_com_service = await get_bill_com_service()
            
            # Test different search strategies
            test_cases = [
                {
                    "name": "Search by exact invoice number",
                    "method": "search_invoices",
                    "params": {"search_term": "INV-1001", "search_type": "invoice_number"}
                },
                {
                    "name": "Search by partial invoice number",
                    "method": "search_invoices", 
                    "params": {"search_term": "1001", "search_type": "invoice_number"}
                },
                {
                    "name": "Get recent invoices",
                    "method": "get_invoices",
                    "params": {"limit": 10}
                },
                {
                    "name": "Get vendors",
                    "method": "get_vendors",
                    "params": {"limit": 10}
                }
            ]
            
            results = {}
            
            for test_case in test_cases:
                print(f"\n🔍 {test_case['name']}...")
                try:
                    method = getattr(bill_com_service, test_case['method'])
                    result = await method(**test_case['params'])
                    
                    print(f"   ✅ Success: {result.get('success', False)}")
                    
                    if result.get('success'):
                        # Show result data
                        result_data = result.get('result', {})
                        if isinstance(result_data, str):
                            # Parse if it's a formatted string response
                            print(f"   📋 Result: {result_data[:200]}...")
                        elif isinstance(result_data, dict):
                            # Show key information
                            if 'invoices' in result_data:
                                invoices = result_data['invoices']
                                print(f"   📄 Found {len(invoices)} invoices")
                                for i, invoice in enumerate(invoices[:3]):  # Show first 3
                                    print(f"      {i+1}. {invoice.get('invoice_number', 'N/A')} - {invoice.get('vendor_name', 'N/A')}")
                            elif 'vendors' in result_data:
                                vendors = result_data['vendors']
                                print(f"   🏢 Found {len(vendors)} vendors")
                                for i, vendor in enumerate(vendors[:3]):  # Show first 3
                                    print(f"      {i+1}. {vendor.get('name', 'N/A')}")
                            else:
                                print(f"   📋 Result keys: {list(result_data.keys())}")
                    else:
                        print(f"   ❌ Error: {result.get('error', 'Unknown error')}")
                    
                    results[test_case['name']] = result
                    
                except Exception as e:
                    print(f"   ❌ Exception: {e}")
                    results[test_case['name']] = {"success": False, "error": str(e)}
            
            return results
            
        except Exception as e:
            print(f"❌ Direct tool testing failed: {e}")
            import traceback
            traceback.print_exc()
            return {"error": str(e)}
    
    async def test_invoice_agent_with_prompt(self, prompt: str) -> Dict[str, Any]:
        """Test Invoice Agent with a specific prompt."""
        self.print_section(f"Testing Invoice Agent with Prompt")
        
        print(f"📝 Prompt: {prompt}")
        
        try:
            from app.agents.nodes import invoice_agent_node
            
            # Create test state similar to the multi-agent workflow
            plan_id = f"test-plan-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}"
            
            test_state = {
                "task_description": prompt,
                "plan_id": plan_id,
                "websocket_manager": self.websocket_manager,
                "execution_context": {
                    "step_number": 1,
                    "total_steps": 1,
                    "current_agent": "invoice",
                    "previous_results": []
                },
                "collected_data": {},
                "execution_results": []
            }
            
            print(f"🔄 Processing with Invoice Agent...")
            start_time = asyncio.get_event_loop().time()
            
            # Execute Invoice agent
            result = await invoice_agent_node(test_state)
            
            duration = asyncio.get_event_loop().time() - start_time
            print(f"✅ Invoice agent execution completed in {duration:.2f}s")
            
            # Show results
            invoice_result = result.get('invoice_result', 'No result')
            print(f"\n📋 Invoice Agent Response:")
            print(f"   Response Length: {len(invoice_result)} characters")
            
            # Show full response
            if len(invoice_result) > 1000:
                print(f"\n📄 Response (First 1000 chars):")
                print(f"{invoice_result[:1000]}...")
                print(f"\n📄 Response (Last 500 chars):")
                print(f"...{invoice_result[-500:]}")
            else:
                print(f"\n📄 Complete Response:")
                print(f"{invoice_result}")
            
            return result
            
        except Exception as e:
            print(f"❌ Invoice agent test failed: {e}")
            import traceback
            traceback.print_exc()
            return {"error": str(e)}
    
    async def interactive_prompt_testing(self):
        """Interactive prompt testing mode."""
        self.print_section("Interactive Prompt Testing")
        
        print("🎯 Enter prompts to test the Invoice Agent")
        print("   Type 'quit' or 'exit' to stop")
        print("   Type 'help' for suggested prompts")
        print()
        
        suggested_prompts = [
            "Search Bill.com for invoice number INV-1001",
            "Find invoice 1001 in Bill.com",
            "Get invoice details for INV-1001",
            "Search for invoices from Acme Marketing",
            "List recent invoices from Bill.com",
            "Show me all unpaid invoices",
            "Find invoices with amount greater than $1000"
        ]
        
        while True:
            try:
                prompt = input("💬 Enter prompt: ").strip()
                
                if prompt.lower() in ['quit', 'exit']:
                    print("👋 Exiting interactive mode...")
                    break
                
                if prompt.lower() == 'help':
                    print("\n💡 Suggested prompts:")
                    for i, suggestion in enumerate(suggested_prompts, 1):
                        print(f"   {i}. {suggestion}")
                    print()
                    continue
                
                if not prompt:
                    continue
                
                print(f"\n{'='*60}")
                await self.test_invoice_agent_with_prompt(prompt)
                print(f"{'='*60}\n")
                
            except KeyboardInterrupt:
                print("\n👋 Exiting interactive mode...")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
    
    async def run_comprehensive_test(self):
        """Run comprehensive Invoice Agent test."""
        self.print_header("Invoice Agent Standalone Test")
        
        print("🎯 This test isolates Invoice Agent functionality for debugging")
        print("🔧 Testing Bill.com integration and various search strategies")
        print(f"🕒 Start Time: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC")
        
        # Start MCP server
        if not await self.start_mcp_server():
            print("❌ Cannot continue without MCP server")
            return
        
        try:
            # Test Bill.com health
            health_result = await self.test_bill_com_health()
            
            # Test direct Bill.com tools
            tool_results = await self.test_direct_bill_com_tools()
            
            # Test some predefined prompts
            test_prompts = [
                "Search Bill.com for invoice number INV-1001 and get invoice data",
                "Find invoice 1001 in Bill.com system",
                "List recent invoices from Bill.com",
                "Search for invoices from Acme Marketing in Bill.com"
            ]
            
            self.print_section("Predefined Prompt Testing")
            for i, prompt in enumerate(test_prompts, 1):
                print(f"\n📋 Test {i}/{len(test_prompts)}: {prompt}")
                await self.test_invoice_agent_with_prompt(prompt)
            
            # Interactive testing
            print(f"\n{'='*80}")
            print("🎯 Ready for interactive testing!")
            print("   You can now test custom prompts to debug the Invoice Agent")
            print(f"{'='*80}")
            
            await self.interactive_prompt_testing()
            
        finally:
            await self.stop_mcp_server()
        
        print("\n🏁 Invoice Agent standalone test complete!")

async def main():
    """Main entry point."""
    tester = InvoiceAgentTester()
    await tester.run_comprehensive_test()

if __name__ == "__main__":
    asyncio.run(main())