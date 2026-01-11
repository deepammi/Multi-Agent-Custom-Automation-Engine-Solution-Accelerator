#!/usr/bin/env python3
"""
Complete Frontend Workflow Simulation

Simulates the complete frontend workflow:
1. Start MCP servers automatically
2. Send query to AI Planner
3. Get human approval for plan
4. Execute specific agents (Gmail, Salesforce, Bill.com)
5. Show verbose data from each agent
6. Stop MCP servers when done

Test Query: "What is the status of Payment Invoice number Acme Marketing Invoice number Inv-1001"
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

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Test query for PO investigation
TEST_QUERY = "What is the status of Payment Invoice number Acme Marketing Invoice number Inv-1001"

class FrontendWorkflowSimulator:
    """Simulates the complete frontend workflow with MCP server management."""
    
    def __init__(self):
        """Initialize the workflow simulator."""
        self.test_query = TEST_QUERY
        self.mcp_servers = {}
        self.verbose = True
        
        # Setup signal handlers for cleanup
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle signals for graceful shutdown."""
        print(f"\n🛑 Received signal {signum}. Cleaning up...")
        asyncio.create_task(self.stop_mcp_servers())
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
    
    def print_step(self, step_num: int, title: str):
        """Print step header."""
        print(f"\n📋 Step {step_num}: {title}")
        print("=" * (len(title) + 15))
    
    async def start_mcp_servers(self) -> bool:
        """Start all required MCP servers in HTTP mode."""
        self.print_section("Starting MCP Servers in HTTP Mode")
        
        from pathlib import Path
        
        servers = {
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
        
        all_started = True
        
        for server_id, config in servers.items():
            try:
                # Resolve script path relative to project root
                project_root = os.path.dirname(os.getcwd())  # Parent of backend directory
                script_path = Path(project_root) / config["script"]
                
                if not script_path.exists():
                    print(f"❌ {config['name']} script not found: {script_path}")
                    all_started = False
                    continue
                
                print(f"🚀 Starting {config['name']} on port {config['port']}...")
                
                # Set environment variables for the server
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
                    cwd=os.path.dirname(os.getcwd()),  # Use parent directory (project root)
                    env=env
                )
                
                # Wait for server to initialize
                await asyncio.sleep(3)
                
                # Check if process is still running
                if process.poll() is None:
                    print(f"✅ {config['name']} started (PID: {process.pid}, Port: {config['port']})")
                    print(f"   Health check: curl http://localhost:{config['port']}/health")
                    self.mcp_servers[server_id] = {
                        "process": process,
                        "name": config["name"],
                        "port": config["port"]
                    }
                else:
                    # Process exited
                    stdout, stderr = process.communicate()
                    print(f"❌ {config['name']} failed to start (exit code: {process.returncode})")
                    if stderr:
                        print(f"   Error: {stderr[:300]}...")
                    if stdout:
                        print(f"   Output: {stdout[:300]}...")
                    all_started = False
                
            except Exception as e:
                print(f"❌ Failed to start {config['name']}: {e}")
                all_started = False
        
        if all_started:
            print(f"\n✅ All MCP servers started successfully in HTTP mode!")
            print(f"\n🌐 Server Connection Information:")
            for server_id, server_info in self.mcp_servers.items():
                print(f"   {server_info['name']}: http://localhost:{server_info['port']}")
        else:
            print(f"\n⚠️  Some MCP servers failed to start")
        
        return all_started
    
    async def stop_mcp_servers(self):
        """Stop all MCP servers."""
        if not self.mcp_servers:
            return
        
        self.print_section("Stopping MCP Servers")
        
        for server_id, server_info in self.mcp_servers.items():
            try:
                process = server_info["process"]
                name = server_info["name"]
                port = server_info.get("port", "unknown")
                
                if process.poll() is None:
                    print(f"🛑 Stopping {name} (PID: {process.pid}, Port: {port})...")
                    
                    # Try graceful termination first
                    process.terminate()
                    
                    try:
                        # Wait up to 5 seconds for graceful shutdown
                        process.wait(timeout=5)
                        print(f"✅ {name} stopped gracefully")
                    except subprocess.TimeoutExpired:
                        # Force kill if graceful shutdown failed
                        print(f"⚠️  Force killing {name}...")
                        process.kill()
                        process.wait()
                        print(f"✅ {name} force stopped")
                else:
                    print(f"📋 {name} already stopped")
            
            except Exception as e:
                print(f"❌ Error stopping {server_info['name']}: {e}")
        
        self.mcp_servers.clear()
        print(f"✅ All MCP servers stopped")
    
    async def call_ai_planner(self, query: str) -> Dict[str, Any]:
        """Call the AI Planner service to create a plan."""
        self.print_section("AI Planner - Creating Execution Plan")
        
        try:
            from app.services.ai_planner_service import AIPlanner
            from app.services.llm_service import LLMService
            
            print(f"🧠 Initializing AI Planner...")
            llm_service = LLMService()
            planner = AIPlanner(llm_service)
            
            print(f"📝 Query: {query}")
            print(f"🔄 Generating execution plan...")
            
            # Create plan using plan_workflow method
            plan_result = await planner.plan_workflow(query)
            
            print(f"\n📊 Plan Generation Result:")
            print(f"   Status: {'success' if plan_result.success else 'failed'}")
            print(f"   Total Duration: {plan_result.total_duration:.2f}s")
            
            if self.verbose and plan_result.success:
                print(f"\n📋 Generated Plan Details:")
                print(f"   Task: {plan_result.task_description}")
                print(f"   Complexity: {plan_result.task_analysis.complexity}")
                print(f"   Agents: {' → '.join(plan_result.agent_sequence.agents)}")
                print(f"   Estimated Duration: {plan_result.agent_sequence.estimated_duration}s")
                
                for i, agent in enumerate(plan_result.agent_sequence.agents, 1):
                    reasoning = plan_result.agent_sequence.reasoning.get(agent, 'No reasoning provided')
                    print(f"   Step {i}: {agent} - {reasoning}")
            
            # Convert to expected format for compatibility
            if plan_result.success:
                return {
                    "status": "success",
                    "plan_id": f"plan-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}",
                    "plan": {
                        "description": plan_result.task_description,
                        "steps": [
                            {
                                "id": f"step-{i}",
                                "description": plan_result.agent_sequence.reasoning.get(agent, f"Execute {agent} agent"),
                                "agent": agent,
                                "status": "pending"
                            }
                            for i, agent in enumerate(plan_result.agent_sequence.agents, 1)
                        ]
                    },
                    "ai_planning_summary": plan_result
                }
            else:
                return {
                    "status": "error", 
                    "error": plan_result.error_message or "Planning failed",
                    "ai_planning_summary": plan_result
                }
        
        except Exception as e:
            print(f"❌ AI Planner error: {e}")
            import traceback
            traceback.print_exc()
            return {"status": "error", "error": str(e)}
    
    def simulate_human_approval(self, plan_result: Dict[str, Any]) -> bool:
        """Simulate human approval of the plan."""
        self.print_section("Human Approval Simulation")
        
        if plan_result.get('status') != 'success':
            print(f"❌ Cannot approve plan - planner failed")
            return False
        
        plan = plan_result.get('plan', {})
        print(f"👤 Human reviewing plan...")
        print(f"   Plan Description: {plan.get('description', 'N/A')}")
        print(f"   Number of Steps: {len(plan.get('steps', []))}")
        
        # Auto-approve for simulation
        print(f"✅ Plan approved by human (simulated)")
        return True
    
    async def call_agent(self, agent_name: str, query: str) -> Dict[str, Any]:
        """Call a specific agent with the query."""
        print(f"\n🤖 Executing {agent_name.title()} Agent")
        print("-" * 40)
        
        try:
            if agent_name.lower() == "gmail":
                from app.agents.gmail_agent_node import GmailAgentNode
                agent = GmailAgentNode()
            elif agent_name.lower() == "salesforce":
                from app.agents.salesforce_agent_node import SalesforceAgentNode
                agent = SalesforceAgentNode()
            elif agent_name.lower() == "invoice" or agent_name.lower() == "bill_com":
                from app.agents.invoice_agent_node import InvoiceAgentNode
                agent = InvoiceAgentNode()
            else:
                return {"status": "error", "error": f"Unknown agent: {agent_name}"}
            
            print(f"📧 Agent initialized: {type(agent).__name__}")
            
            # Create test state
            test_state = {
                "task": query,
                "user_request": query,
                "messages": [],
                "plan_id": f"test-{agent_name}-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}",
                "session_id": f"test-session-{agent_name}"
            }
            
            print(f"🔄 Processing query with {agent_name} agent...")
            result = await agent.process(test_state)
            
            print(f"\n📊 {agent_name.title()} Agent Results:")
            print(f"   Result Type: {type(result)}")
            print(f"   Result Keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
            
            if self.verbose and isinstance(result, dict):
                print(f"\n📋 Detailed {agent_name.title()} Agent Response:")
                
                # Show key fields
                for key in ['status', 'message', 'data', 'result', 'content']:
                    if key in result:
                        value = result[key]
                        if isinstance(value, str) and len(value) > 200:
                            print(f"   {key}: {value[:200]}...")
                        else:
                            print(f"   {key}: {value}")
                
                # Show full JSON for debugging
                print(f"\n🔍 Full {agent_name.title()} Agent JSON Response:")
                print(json.dumps(result, indent=2, default=str))
            
            return result
        
        except Exception as e:
            print(f"❌ {agent_name.title()} agent error: {e}")
            import traceback
            traceback.print_exc()
            return {"status": "error", "error": str(e)}
    
    async def execute_agents(self, plan_result: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the agents based on the plan."""
        self.print_section("Agent Execution Phase")
        
        # For PO investigation, we'll call Gmail, Salesforce, and Invoice agents
        agents_to_call = ["gmail", "salesforce", "invoice"]
        
        print(f"🎯 Executing agents for PO investigation: {', '.join(agents_to_call)}")
        
        agent_results = {}
        
        for agent_name in agents_to_call:
            try:
                result = await self.call_agent(agent_name, self.test_query)
                agent_results[agent_name] = result
                
                # Brief summary
                status = result.get('status', 'unknown') if isinstance(result, dict) else 'completed'
                status_icon = "✅" if status == 'success' or status == 'completed' else "❌"
                print(f"{status_icon} {agent_name.title()} Agent: {status}")
                
            except Exception as e:
                print(f"❌ {agent_name.title()} Agent failed: {e}")
                agent_results[agent_name] = {"status": "error", "error": str(e)}
        
        return agent_results
    
    def analyze_results(self, agent_results: Dict[str, Any]):
        """Analyze the results from all agents."""
        self.print_section("Results Analysis")
        
        print(f"🔍 Analyzing results from {len(agent_results)} agents...")
        
        # Check for hallucination indicators
        hallucination_indicators = [
            "I don't have access",
            "I cannot access",
            "mock data",
            "sample data",
            "placeholder",
            "example data",
            "I'm ready to help",
            "generic response"
        ]
        
        for agent_name, result in agent_results.items():
            print(f"\n📊 {agent_name.title()} Agent Analysis:")
            
            if isinstance(result, dict):
                # Check status
                status = result.get('status', 'unknown')
                print(f"   Status: {status}")
                
                # Check for actual data vs hallucination
                content_fields = ['message', 'content', 'data', 'result']
                has_real_data = False
                has_hallucination_indicators = False
                
                for field in content_fields:
                    if field in result:
                        content = str(result[field]).lower()
                        
                        # Check for hallucination indicators
                        for indicator in hallucination_indicators:
                            if indicator in content:
                                has_hallucination_indicators = True
                                print(f"   ⚠️  Possible hallucination detected: '{indicator}' found in {field}")
                        
                        # Check for specific data (invoice numbers, amounts, etc.)
                        if any(term in content for term in ['inv-1001', 'acme marketing', '$', 'amount', 'status']):
                            has_real_data = True
                            print(f"   ✅ Specific data found in {field}")
                
                if has_real_data and not has_hallucination_indicators:
                    print(f"   🎉 {agent_name.title()} appears to have real data!")
                elif has_hallucination_indicators:
                    print(f"   ⚠️  {agent_name.title()} may be hallucinating or using mock data")
                else:
                    print(f"   ❓ {agent_name.title()} data quality unclear")
            
            else:
                print(f"   ❓ Unexpected result type: {type(result)}")
    
    def generate_summary(self, plan_result: Dict[str, Any], agent_results: Dict[str, Any]):
        """Generate a summary of the entire workflow."""
        self.print_section("Workflow Summary")
        
        print(f"🎯 Query: {self.test_query}")
        print(f"🕒 Execution Time: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
        
        # Plan summary
        plan_status = plan_result.get('status', 'unknown')
        plan_icon = "✅" if plan_status == 'success' else "❌"
        print(f"{plan_icon} AI Planner: {plan_status}")
        
        # Agent summary
        print(f"\n🤖 Agent Execution Results:")
        for agent_name, result in agent_results.items():
            status = result.get('status', 'unknown') if isinstance(result, dict) else 'completed'
            status_icon = "✅" if status == 'success' or status == 'completed' else "❌"
            print(f"   {status_icon} {agent_name.title()}: {status}")
        
        # Overall assessment
        successful_agents = sum(1 for result in agent_results.values() 
                              if isinstance(result, dict) and result.get('status') in ['success', 'completed'])
        
        print(f"\n📊 Overall Results:")
        print(f"   Successful Agents: {successful_agents}/{len(agent_results)}")
        print(f"   Plan Generation: {'Success' if plan_status == 'success' else 'Failed'}")
        
        if successful_agents == len(agent_results) and plan_status == 'success':
            print(f"🎉 Workflow completed successfully!")
        else:
            print(f"⚠️  Workflow completed with some issues")
        
        print(f"\n💡 Next Steps:")
        print(f"   1. Review agent responses for data quality")
        print(f"   2. Check for hallucination vs real data")
        print(f"   3. Verify MCP server connections are working")
        print(f"   4. Configure credentials if needed")
    
    async def run_complete_workflow(self):
        """Run the complete frontend workflow simulation."""
        self.print_header("Frontend Workflow Simulation")
        
        print(f"🎯 Test Query: {self.test_query}")
        print(f"🔧 Verbose Mode: {self.verbose}")
        print(f"🕒 Start Time: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
        
        try:
            # Step 1: Start MCP Servers
            self.print_step(1, "Start MCP Servers")
            servers_started = await self.start_mcp_servers()
            
            if not servers_started:
                print(f"❌ Cannot continue - MCP servers failed to start")
                return
            
            # Wait a moment for servers to fully initialize
            await asyncio.sleep(2)
            
            # Step 2: AI Planner
            self.print_step(2, "AI Planner - Generate Execution Plan")
            plan_result = await self.call_ai_planner(self.test_query)
            
            # Step 3: Human Approval (Simulated)
            self.print_step(3, "Human Approval")
            approved = self.simulate_human_approval(plan_result)
            
            if not approved:
                print(f"❌ Plan not approved - stopping workflow")
                return
            
            # Step 4: Execute Agents
            self.print_step(4, "Execute Agents")
            agent_results = await self.execute_agents(plan_result)
            
            # Step 5: Analyze Results
            self.print_step(5, "Analyze Results for Hallucination")
            self.analyze_results(agent_results)
            
            # Step 6: Generate Summary
            self.print_step(6, "Workflow Summary")
            self.generate_summary(plan_result, agent_results)
            
        except Exception as e:
            print(f"❌ Workflow error: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            # Always stop MCP servers
            await self.stop_mcp_servers()

async def main():
    """Main entry point."""
    print("🚀 Complete Frontend Workflow Simulation")
    print("=" * 50)
    print("This script simulates the complete frontend workflow:")
    print("1. Start MCP servers automatically")
    print("2. Send query to AI Planner")
    print("3. Get human approval for plan")
    print("4. Execute specific agents (Gmail, Salesforce, Bill.com)")
    print("5. Show verbose data from each agent")
    print("6. Analyze results for hallucination")
    print("7. Stop MCP servers when done")
    
    simulator = FrontendWorkflowSimulator()
    await simulator.run_complete_workflow()
    
    print(f"\n🏁 Workflow simulation complete!")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⚠️ Workflow interrupted by user.")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()