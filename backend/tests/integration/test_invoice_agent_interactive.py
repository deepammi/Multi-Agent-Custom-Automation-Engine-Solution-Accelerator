#!/usr/bin/env python3
"""
Interactive Invoice Agent Test

A simple interactive test for the Invoice Agent that allows you to test multiple prompts
without restarting the script. Just type prompts and see results immediately.

Usage:
    python3 test_invoice_agent_interactive.py

Features:
- Interactive prompt testing
- No need to restart between tests
- Clear, focused output
- Easy to use
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

# Setup verbose logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Force disable mock mode to see real responses
os.environ["USE_MOCK_LLM"] = "false"

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

class InteractiveInvoiceAgentTester:
    """Interactive Invoice Agent tester."""
    
    def __init__(self):
        """Initialize the tester."""
        self.mcp_server_process = None
        self.server_started = False
        
        # Setup signal handlers for cleanup
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle signals for graceful shutdown."""
        print(f"\n🛑 Shutting down...")
        asyncio.create_task(self.stop_mcp_server())
        sys.exit(0)
    
    async def start_mcp_server(self) -> bool:
        """Start Bill.com MCP server."""
        if self.server_started:
            return True
            
        print("🚀 Starting Bill.com MCP Server...")
        
        try:
            from pathlib import Path
            
            # Resolve script path relative to project root
            project_root = os.path.dirname(os.getcwd())
            script_path = Path(project_root) / "src/mcp_server/mcp_server.py"
            
            if not script_path.exists():
                print(f"❌ MCP server script not found: {script_path}")
                return False
            
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
                print(f"✅ Bill.com MCP Server started successfully")
                self.server_started = True
                return True
            else:
                stdout, stderr = self.mcp_server_process.communicate()
                print(f"❌ Bill.com MCP Server failed to start")
                if stderr:
                    print(f"Error: {stderr[:300]}...")
                return False
                
        except Exception as e:
            print(f"❌ Failed to start Bill.com MCP Server: {e}")
            return False
    
    async def stop_mcp_server(self):
        """Stop MCP server."""
        if not self.mcp_server_process or not self.server_started:
            return
        
        try:
            if self.mcp_server_process.poll() is None:
                print(f"🛑 Stopping Bill.com MCP Server...")
                self.mcp_server_process.terminate()
                
                try:
                    self.mcp_server_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.mcp_server_process.kill()
                    self.mcp_server_process.wait()
                
                print(f"✅ Server stopped")
        
        except Exception as e:
            print(f"❌ Error stopping server: {e}")
        
        self.mcp_server_process = None
        self.server_started = False
    
    async def test_invoice_agent(self, prompt: str) -> Dict[str, Any]:
        """Test Invoice Agent with the given prompt."""
        try:
            from app.agents.nodes import invoice_agent_node
            
            # Create minimal test state
            plan_id = f"test-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}"
            
            # Mock websocket manager with verbose logging
            class MockWebSocketManager:
                async def send_message(self, plan_id: str, message: dict):
                    print(f"🔍 DEBUG: WebSocket message sent - Type: {message.get('type', 'unknown')}")
                    print(f"🔍 DEBUG: WebSocket message content: {str(message)[:200]}...")
            
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
            
            print(f"🔍 DEBUG: Test state created:")
            print(f"  Plan ID: {plan_id}")
            print(f"  Task: {prompt}")
            print(f"  State keys: {list(test_state.keys())}")
            
            print(f"🔄 Processing...")
            start_time = asyncio.get_event_loop().time()
            
            # Execute Invoice agent
            result = await invoice_agent_node(test_state)
            
            duration = asyncio.get_event_loop().time() - start_time
            
            print(f"🔍 DEBUG: Invoice agent returned:")
            print(f"  Result type: {type(result)}")
            print(f"  Result keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
            
            # Show results
            invoice_result = result.get('invoice_result', 'No result')
            
            print(f"\n📊 Result ({duration:.1f}s, {len(invoice_result)} chars):")
            print("-" * 60)
            print(invoice_result)
            print("-" * 60)
            
            # Quick analysis
            if "Bill.com Service Unavailable" in invoice_result:
                print("⚠️  Bill.com service unavailable")
            elif "INV-1001" in invoice_result:
                print("✅ Found INV-1001 reference")
            elif "invoice" in invoice_result.lower():
                print("✅ Invoice-related response")
            elif "error" in invoice_result.lower():
                print("❌ Error in response")
            else:
                print("❓ Check response content")
            
            return result
            
        except Exception as e:
            print(f"❌ Error: {e}")
            print(f"🔍 DEBUG: Exception type: {type(e).__name__}")
            import traceback
            print(f"🔍 DEBUG: Full traceback:")
            traceback.print_exc()
            return {"error": str(e)}
    
    async def run_interactive_test(self):
        """Run interactive testing."""
        print("🚀 Interactive Invoice Agent Test")
        print("=" * 50)
        print("Type prompts to test the Invoice Agent.")
        print("Commands: 'quit' or 'exit' to stop, 'help' for examples")
        print()
        
        # Start MCP server
        if not await self.start_mcp_server():
            print("❌ Cannot start without MCP server")
            return
        
        # Example prompts
        examples = [
            "Search Bill.com for invoice number INV-1001",
            "Find invoice 1001 in Bill.com",
            "List recent invoices from Bill.com",
            "Get invoice details for INV-1001",
            "Search for invoices from Acme Marketing",
            "Show me all unpaid invoices"
        ]
        
        try:
            while True:
                try:
                    prompt = input("\n💬 Enter prompt (or 'help'): ").strip()
                    
                    if prompt.lower() in ['quit', 'exit', 'q']:
                        print("👋 Goodbye!")
                        break
                    
                    if prompt.lower() in ['help', 'h']:
                        print("\n💡 Example prompts:")
                        for i, example in enumerate(examples, 1):
                            print(f"   {i}. {example}")
                        continue
                    
                    if not prompt:
                        continue
                    
                    print(f"\n📝 Testing: {prompt}")
                    await self.test_invoice_agent(prompt)
                    
                except KeyboardInterrupt:
                    print("\n👋 Goodbye!")
                    break
                except Exception as e:
                    print(f"❌ Error: {e}")
        
        finally:
            await self.stop_mcp_server()

async def main():
    """Main entry point."""
    tester = InteractiveInvoiceAgentTester()
    await tester.run_interactive_test()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⚠️ Interrupted by user.")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")