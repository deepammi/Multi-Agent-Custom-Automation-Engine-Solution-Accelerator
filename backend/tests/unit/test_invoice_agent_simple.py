#!/usr/bin/env python3
"""
Simple Invoice Agent Test

A minimal, focused test for the Invoice Agent that allows easy manual prompt testing.
This test isolates just the Invoice Agent functionality for debugging Bill.com integration.

Usage:
    python3 test_invoice_agent_simple.py

Features:
- Simple prompt testing (edit the PROMPT variable below)
- Direct Invoice Agent execution
- Clear output formatting
- Minimal setup required
"""

import asyncio
import sys
import os
import subprocess
import signal
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Force disable mock mode to see real responses
os.environ["USE_MOCK_LLM"] = "false"

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Setup verbose logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# =============================================================================
# EDIT THIS PROMPT TO TEST DIFFERENT QUERIES
# =============================================================================
PROMPT = "Search Bill.com for invoice number INV-1001 and get invoice data"
# 
# Try these other prompts:
# PROMPT = "Find invoice 1001 in Bill.com"
# PROMPT = "List recent invoices from Bill.com"
# PROMPT = "Search for invoices from Acme Marketing in Bill.com"
# PROMPT = "Get invoice details for INV-1001"
# PROMPT = "Show me all unpaid invoices"
# =============================================================================

class SimpleInvoiceAgentTester:
    """Simple Invoice Agent tester for manual prompt testing."""
    
    def __init__(self):
        """Initialize the tester."""
        self.mcp_server_process = None
        
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
                print(f"✅ Bill.com MCP Server started (PID: {self.mcp_server_process.pid})")
                return True
            else:
                stdout, stderr = self.mcp_server_process.communicate()
                print(f"❌ Bill.com MCP Server failed to start (exit code: {self.mcp_server_process.returncode})")
                if stderr:
                    print(f"   Error: {stderr[:500]}...")
                if stdout:
                    print(f"   Output: {stdout[:500]}...")
                return False
                
        except Exception as e:
            print(f"❌ Failed to start Bill.com MCP Server: {e}")
            return False
    
    async def stop_mcp_server(self):
        """Stop MCP server."""
        if not self.mcp_server_process:
            return
        
        try:
            if self.mcp_server_process.poll() is None:
                print(f"🛑 Stopping Bill.com MCP Server...")
                self.mcp_server_process.terminate()
                
                try:
                    self.mcp_server_process.wait(timeout=5)
                    print(f"✅ Bill.com MCP Server stopped")
                except subprocess.TimeoutExpired:
                    self.mcp_server_process.kill()
                    self.mcp_server_process.wait()
                    print(f"✅ Bill.com MCP Server force stopped")
        
        except Exception as e:
            print(f"❌ Error stopping Bill.com MCP Server: {e}")
        
        self.mcp_server_process = None
    
    async def test_invoice_agent(self, prompt: str) -> Dict[str, Any]:
        """Test Invoice Agent with the given prompt."""
        self.print_section(f"Testing Invoice Agent")
        
        print(f"📝 Prompt: {prompt}")
        
        try:
            from app.agents.nodes import invoice_agent_node
            
            # Create minimal test state
            plan_id = f"test-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}"
            
            # Mock websocket manager with debugging
            class MockWebSocketManager:
                async def send_message(self, plan_id: str, message: dict):
                    print(f"🔍 DEBUG: WebSocket message - Type: {message.get('type', 'unknown')}")
                    if message.get('type') == 'agent_message':
                        content = message.get('content', '')
                        print(f"🔍 DEBUG: Message content preview: {content[:200]}...")
            
            test_state = {
                "task_description": prompt,
                "plan_id": plan_id,
                "websocket_manager": MockWebSocketManager(),
                "execution_context": {
                    "step_number": 1,
                    "total_steps": 1,
                    "current_agent": "invoice",
                    "previous_results": []
                },
                "collected_data": {},
                "execution_results": []
            }
            
            print(f"🔍 DEBUG: Test state created with plan_id: {plan_id}")
            print(f"🔍 DEBUG: Task description: {prompt}")
            
            print(f"🔄 Processing with Invoice Agent...")
            start_time = asyncio.get_event_loop().time()
            
            # Execute Invoice agent
            result = await invoice_agent_node(test_state)
            
            duration = asyncio.get_event_loop().time() - start_time
            print(f"✅ Invoice agent execution completed in {duration:.2f}s")
            
            print(f"🔍 DEBUG: Result type: {type(result)}")
            print(f"🔍 DEBUG: Result keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
            
            # Show results
            invoice_result = result.get('invoice_result', 'No result')
            print(f"\n📊 Result Summary:")
            print(f"   Response Length: {len(invoice_result)} characters")
            print(f"   Execution Time: {duration:.2f}s")
            
            # Show the response
            print(f"\n📋 Invoice Agent Response:")
            print("=" * 80)
            print(invoice_result)
            print("=" * 80)
            
            # Analysis
            print(f"\n🔍 Response Analysis:")
            if "Bill.com Service Unavailable" in invoice_result:
                print(f"   ⚠️  Bill.com service is unavailable")
            elif "INV-1001" in invoice_result:
                print(f"   ✅ Response mentions INV-1001")
            elif "invoice" in invoice_result.lower():
                print(f"   ✅ Response contains invoice-related content")
            else:
                print(f"   ❓ Response content unclear")
            
            if "error" in invoice_result.lower():
                print(f"   ⚠️  Response contains error information")
            
            # Show any MCP-related debug info
            if hasattr(result, 'debug_info'):
                print(f"🔍 DEBUG: Additional debug info available")
                print(f"   Debug info: {result.debug_info}")
            
            return result
            
        except Exception as e:
            print(f"❌ Invoice agent test failed: {e}")
            print(f"🔍 DEBUG: Exception type: {type(e).__name__}")
            import traceback
            print(f"🔍 DEBUG: Full traceback:")
            traceback.print_exc()
            return {"error": str(e)}
    
    async def run_test(self):
        """Run the simple Invoice Agent test."""
        self.print_header("Simple Invoice Agent Test")
        
        print(f"🎯 Testing Invoice Agent with manual prompt")
        print(f"📝 Current Prompt: {PROMPT}")
        print(f"🔧 To test different prompts, edit the PROMPT variable at the top of this file")
        print(f"🕒 Start Time: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC")
        
        # Start MCP server
        if not await self.start_mcp_server():
            print("❌ Cannot continue without MCP server")
            return
        
        try:
            # Test the Invoice Agent with the current prompt
            result = await self.test_invoice_agent(PROMPT)
            
            # Final summary
            print(f"\n🏁 Test Complete!")
            print(f"   Prompt: {PROMPT}")
            print(f"   Status: {'✅ Success' if 'error' not in result else '❌ Error'}")
            
            if 'error' in result:
                print(f"   Error: {result['error']}")
            
        finally:
            await self.stop_mcp_server()

async def main():
    """Main entry point."""
    print("🚀 Simple Invoice Agent Test")
    print("=" * 50)
    print("This test allows you to easily test different prompts with the Invoice Agent.")
    print("Edit the PROMPT variable at the top of this file to test different queries.")
    print()
    
    tester = SimpleInvoiceAgentTester()
    await tester.run_test()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⚠️ Test interrupted by user.")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()