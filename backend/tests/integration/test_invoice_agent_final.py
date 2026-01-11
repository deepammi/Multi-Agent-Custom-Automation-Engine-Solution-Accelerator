#!/usr/bin/env python3
"""
Final Invoice Agent Test

This test verifies that all fixes are working:
1. SSL bypass is working
2. Timezone import is fixed
3. Invoice Agent can process requests
"""

import asyncio
import os
import sys
import subprocess
import signal
import time
from datetime import datetime, timezone
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Force SSL bypass
os.environ["BILL_COM_SSL_VERIFY"] = "false"
os.environ["USE_MOCK_LLM"] = "false"

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

class FinalInvoiceAgentTest:
    """Final test for Invoice Agent with all fixes applied."""
    
    def __init__(self):
        self.mcp_server_process = None
        
    async def start_fresh_mcp_server(self) -> bool:
        """Start a fresh MCP server to pick up SSL configuration."""
        print("🔄 Starting fresh MCP server...")
        
        try:
            from pathlib import Path
            
            # Kill any existing MCP server processes
            try:
                subprocess.run(["pkill", "-f", "mcp_server.py"], check=False)
                await asyncio.sleep(2)  # Wait for cleanup
            except:
                pass
            
            # Resolve script path
            project_root = os.path.dirname(os.getcwd())
            script_path = Path(project_root) / "src/mcp_server/mcp_server.py"
            
            if not script_path.exists():
                print(f"❌ MCP server script not found: {script_path}")
                return False
            
            # Set environment variables
            env = os.environ.copy()
            env["BILL_COM_MCP_ENABLED"] = "true"
            env["BILL_COM_SSL_VERIFY"] = "false"  # Ensure SSL bypass
            
            # Start the server
            cmd = ["python3", str(script_path), "--transport", "http", "--port", "9000"]
            
            self.mcp_server_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=project_root,
                env=env
            )
            
            # Wait for server to initialize
            print("⏳ Waiting for server initialization...")
            for i in range(15):  # Wait up to 15 seconds
                await asyncio.sleep(1)
                
                if self.mcp_server_process.poll() is not None:
                    stdout, stderr = self.mcp_server_process.communicate()
                    print(f"❌ MCP server terminated: {stderr}")
                    return False
                
                print(f"   Startup check {i+1}/15...")
            
            print("✅ MCP server started successfully")
            return True
            
        except Exception as e:
            print(f"❌ Failed to start MCP server: {e}")
            return False
    
    async def stop_mcp_server(self):
        """Stop MCP server."""
        if self.mcp_server_process:
            try:
                self.mcp_server_process.terminate()
                self.mcp_server_process.wait(timeout=5)
            except:
                self.mcp_server_process.kill()
                self.mcp_server_process.wait()
            self.mcp_server_process = None
    
    async def test_invoice_agent(self) -> bool:
        """Test the Invoice Agent with all fixes."""
        print("\n🧪 Testing Invoice Agent...")
        
        try:
            from app.agents.nodes import invoice_agent_node
            
            # Create test state
            plan_id = f"final-test-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}"
            
            class MockWebSocketManager:
                async def send_message(self, plan_id: str, message: dict):
                    print(f"📡 WebSocket: {message.get('data', {}).get('content', 'No content')}")
            
            test_state = {
                "task_description": "Search Bill.com for invoice number INV-1001 and get invoice data",
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
            
            print(f"🎯 Executing Invoice Agent for plan: {plan_id}")
            start_time = time.time()
            
            # Execute Invoice agent
            result = await invoice_agent_node(test_state)
            
            duration = time.time() - start_time
            
            print(f"\n📊 Invoice Agent Results ({duration:.2f}s):")
            print("=" * 60)
            
            invoice_result = result.get('invoice_result', 'No result')
            print(invoice_result)
            
            print("=" * 60)
            
            # Analyze results
            success_indicators = [
                "Bill.com Integration" in invoice_result,
                "timezone" not in invoice_result.lower() or "not defined" not in invoice_result,
                "SSL" not in invoice_result or "certificate" not in invoice_result
            ]
            
            if all(success_indicators):
                print("✅ Invoice Agent test PASSED")
                print("   - No timezone errors")
                print("   - No SSL certificate errors")
                print("   - Bill.com integration working")
                return True
            else:
                print("❌ Invoice Agent test FAILED")
                if "timezone" in invoice_result and "not defined" in invoice_result:
                    print("   - Timezone import issue still exists")
                if "SSL" in invoice_result and "certificate" in invoice_result:
                    print("   - SSL certificate issue still exists")
                return False
                
        except Exception as e:
            print(f"❌ Invoice Agent test failed with exception: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    async def run_final_test(self):
        """Run the final comprehensive test."""
        print("🚀 Final Invoice Agent Test")
        print("=" * 50)
        print(f"🕒 Start Time: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC")
        print(f"🔒 SSL Bypass: {os.getenv('BILL_COM_SSL_VERIFY', 'not set')}")
        print()
        
        try:
            # Start fresh MCP server
            if not await self.start_fresh_mcp_server():
                print("💥 Cannot continue - MCP server failed to start")
                return False
            
            # Wait a bit more for server to fully initialize
            print("⏳ Allowing server to fully initialize...")
            await asyncio.sleep(5)
            
            # Test Invoice Agent
            success = await self.test_invoice_agent()
            
            if success:
                print("\n🎉 ALL TESTS PASSED!")
                print("✅ SSL bypass is working")
                print("✅ Timezone import is fixed")
                print("✅ Invoice Agent is functional")
                print("\n🎯 The Invoice Agent is ready for use!")
            else:
                print("\n💥 TESTS FAILED!")
                print("❌ Some issues still need to be resolved")
            
            return success
            
        finally:
            await self.stop_mcp_server()

async def main():
    """Main entry point."""
    test = FinalInvoiceAgentTest()
    success = await test.run_final_test()
    return 0 if success else 1

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n⚠️ Interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)