#!/usr/bin/env python3
"""
Test comprehensive multi-agent coordination workflow.

This script performs a clean start of the backend and tests the complete
multi-agent workflow with the query:
"check all emails, bills and customer crm accounts with keywords TBI Corp or TBI-001 and analyze them"

Tests all agents:
- Planner Agent: Initial task analysis and routing
- Email Agent: Gmail search for TBI Corp/TBI-001
- AP Agent: Bill.com search for TBI Corp/TBI-001  
- CRM Agent: Salesforce search for TBI Corp/TBI-001
- Analysis Agent: Final analysis and synthesis
"""

import asyncio
import logging
import sys
import os
import json
import time
import subprocess
import signal
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

import requests
import websockets
from app.db.mongodb import MongoDB

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class MultiAgentCoordinationTest:
    """Comprehensive multi-agent coordination test."""
    
    def __init__(self):
        self.backend_process = None
        self.mcp_processes = {}
        self.test_query = "check all emails, bills and customer crm accounts with keywords TBI Corp or TBI-001 and analyze them"
        self.plan_id = None
        self.session_id = None
        self.agent_results = {}
        
    async def clean_start_backend(self):
        """Perform a clean start of the entire backend system."""
        logger.info("🧹 Performing clean start of backend system...")
        
        # Step 1: Stop any existing processes
        logger.info("🛑 Stopping any existing backend processes...")
        try:
            # Kill any existing backend processes
            subprocess.run(["pkill", "-f", "uvicorn.*app.main:app"], check=False)
            subprocess.run(["pkill", "-f", "mcp_server"], check=False)
            await asyncio.sleep(2)
        except Exception as e:
            logger.warning(f"Error stopping existing processes: {e}")
        
        # Step 2: Start MCP servers
        logger.info("🚀 Starting MCP servers...")
        await self.start_mcp_servers()
        
        # Step 3: Start backend
        logger.info("🚀 Starting backend server...")
        await self.start_backend()
        
        # Step 4: Wait for backend to be ready
        logger.info("⏳ Waiting for backend to be ready...")
        await self.wait_for_backend_ready()
        
        logger.info("✅ Backend system started successfully")
    
    async def start_mcp_servers(self):
        """Start all required MCP servers."""
        mcp_servers = {
            "gmail": {
                "script": "../src/mcp_server/gmail_mcp_server.py",
                "port": "9000",
                "name": "Gmail MCP Server"
            },
            "salesforce": {
                "script": "../src/mcp_server/salesforce_mcp_server.py", 
                "port": "9001",
                "name": "Salesforce MCP Server"
            },
            "bill_com": {
                "script": "../src/mcp_server/mcp_server.py",
                "port": "9002", 
                "name": "Bill.com MCP Server"
            }
        }
        
        for service, config in mcp_servers.items():
            try:
                logger.info(f"📡 Starting {config['name']} on port {config['port']}...")
                
                process = subprocess.Popen([
                    "python3", config["script"],
                    "--transport", "http",
                    "--port", config["port"],
                    "--host", "0.0.0.0"
                ], cwd=os.path.dirname(__file__))
                
                self.mcp_processes[service] = process
                logger.info(f"✅ {config['name']} started (PID: {process.pid})")
                
                # Brief wait between server starts
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"❌ Failed to start {config['name']}: {e}")
        
        # Wait for all MCP servers to be ready
        logger.info("⏳ Waiting for MCP servers to be ready...")
        await asyncio.sleep(5)
    
    async def start_backend(self):
        """Start the FastAPI backend server."""
        try:
            # Start backend with uvicorn
            self.backend_process = subprocess.Popen([
                "python3", "-m", "uvicorn", 
                "app.main:app",
                "--host", "0.0.0.0",
                "--port", "8000",
                "--reload"
            ], cwd=os.path.dirname(__file__))
            
            logger.info(f"✅ Backend server started (PID: {self.backend_process.pid})")
            
        except Exception as e:
            logger.error(f"❌ Failed to start backend server: {e}")
            raise
    
    async def wait_for_backend_ready(self):
        """Wait for backend to be ready to accept requests."""
        max_attempts = 30
        for attempt in range(max_attempts):
            try:
                response = requests.get("http://localhost:8000/health", timeout=2)
                if response.status_code == 200:
                    logger.info("✅ Backend is ready")
                    return
            except Exception:
                pass
            
            logger.info(f"⏳ Waiting for backend... (attempt {attempt + 1}/{max_attempts})")
            await asyncio.sleep(2)
        
        raise Exception("Backend failed to start within timeout")
    
    async def submit_task(self):
        """Submit the multi-agent coordination task."""
        logger.info("📤 Submitting multi-agent coordination task...")
        logger.info(f"📝 Query: {self.test_query}")
        
        # Initialize database connection
        MongoDB.connect()
        
        # Submit task to process_request endpoint
        process_request_data = {
            "description": self.test_query,
            "session_id": None,
            "team_id": None
        }
        
        response = requests.post(
            "http://localhost:8000/api/v3/process_request",
            json=process_request_data,
            timeout=30
        )
        
        if response.status_code != 200:
            raise Exception(f"Task submission failed: {response.status_code} - {response.text}")
        
        result = response.json()
        self.plan_id = result.get("plan_id")
        self.session_id = result.get("session_id")
        
        logger.info(f"✅ Task submitted successfully")
        logger.info(f"   Plan ID: {self.plan_id}")
        logger.info(f"   Session ID: {self.session_id}")
        logger.info(f"   Status: {result.get('status')}")
        
        return result
    
    async def monitor_execution(self):
        """Monitor the multi-agent execution via WebSocket."""
        logger.info("🔌 Monitoring multi-agent execution via WebSocket...")
        
        websocket_url = f"ws://localhost:8000/api/v3/socket/{self.plan_id}?user_id=test_user"
        
        try:
            async with websockets.connect(websocket_url) as websocket:
                logger.info("✅ WebSocket connected")
                
                # Listen for messages for up to 120 seconds (longer for multi-agent)
                timeout_seconds = 120
                start_time = asyncio.get_event_loop().time()
                
                messages_received = []
                agents_seen = set()
                
                while (asyncio.get_event_loop().time() - start_time) < timeout_seconds:
                    try:
                        # Wait for message with timeout
                        message = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                        
                        try:
                            parsed_message = json.loads(message)
                            messages_received.append(parsed_message)
                            
                            msg_type = parsed_message.get("type", "unknown")
                            
                            if msg_type == "agent_message":
                                data = parsed_message.get("data", {})
                                agent_name = data.get("agent_name", "Unknown")
                                content = data.get("content", "")
                                status = data.get("status", "unknown")
                                
                                agents_seen.add(agent_name)
                                
                                logger.info(f"🤖 {agent_name} Agent: {status}")
                                if content:
                                    # Truncate long content for readability
                                    display_content = content[:300] + "..." if len(content) > 300 else content
                                    logger.info(f"   Content: {display_content}")
                                
                                # Store agent result
                                if agent_name not in self.agent_results:
                                    self.agent_results[agent_name] = []
                                self.agent_results[agent_name].append({
                                    "status": status,
                                    "content": content,
                                    "timestamp": datetime.now().isoformat()
                                })
                            
                            elif msg_type == "final_result_message":
                                data = parsed_message.get("data", {})
                                logger.info("🎯 Final Result Received!")
                                logger.info(f"   Content: {data.get('content', '')[:500]}...")
                                
                                # Store final result
                                self.agent_results["final_result"] = data.get('content', '')
                                break
                            
                            elif msg_type == "agent_stream_start":
                                data = parsed_message.get("data", {})
                                agent_name = data.get("agent_name", "Unknown")
                                logger.info(f"🌊 {agent_name} Agent: Starting stream...")
                            
                            elif msg_type == "agent_stream_end":
                                data = parsed_message.get("data", {})
                                agent_name = data.get("agent_name", "Unknown")
                                logger.info(f"🏁 {agent_name} Agent: Stream ended")
                            
                            elif msg_type in ["connection_established", "ping"]:
                                # Skip logging these common messages
                                pass
                            else:
                                logger.info(f"📩 Message type: {msg_type}")
                        
                        except json.JSONDecodeError:
                            logger.warning(f"⚠️ Received non-JSON message: {message}")
                    
                    except asyncio.TimeoutError:
                        # No message received in timeout period, continue listening
                        continue
                    except websockets.exceptions.ConnectionClosed:
                        logger.info("🔌 WebSocket connection closed")
                        break
                
                logger.info(f"📊 Execution monitoring completed")
                logger.info(f"   Total messages received: {len(messages_received)}")
                logger.info(f"   Agents seen: {', '.join(sorted(agents_seen))}")
        
        except Exception as e:
            logger.error(f"❌ WebSocket monitoring failed: {e}")
    
    async def analyze_results(self):
        """Analyze the results from all agents."""
        logger.info("📋 Analyzing multi-agent coordination results...")
        
        # Get final plan details
        plan_response = requests.get(
            f"http://localhost:8000/api/v3/plan?plan_id={self.plan_id}",
            timeout=10
        )
        
        if plan_response.status_code == 200:
            plan_data = plan_response.json()
            
            logger.info("✅ Final plan retrieved")
            logger.info(f"   Plan status: {plan_data.get('plan', {}).get('status', 'unknown')}")
            
            messages = plan_data.get('messages', [])
            logger.info(f"   Total messages: {len(messages)}")
            
            # Analyze agent execution sequence
            agents_executed = []
            for msg in messages:
                agent_name = msg.get('agent_name', 'Unknown')
                if agent_name not in agents_executed:
                    agents_executed.append(agent_name)
            
            logger.info(f"   Agent execution sequence: {' → '.join(agents_executed)}")
            
            # Check expected agents
            expected_agents = ["Planner", "Email", "AP", "CRM", "Analysis"]
            
            for expected_agent in expected_agents:
                # Check for variations in agent names
                found = any(expected_agent.lower() in agent.lower() for agent in agents_executed)
                if found:
                    logger.info(f"✅ {expected_agent} Agent executed")
                else:
                    logger.warning(f"⚠️ {expected_agent} Agent not found in execution")
            
            # Show final result if available
            final_result = plan_data.get('streaming_message')
            if final_result:
                logger.info("📄 Final streaming result:")
                logger.info(f"   {final_result[:800]}...")
            
            return plan_data
        
        else:
            logger.error(f"❌ Failed to retrieve plan: {plan_response.status_code}")
            return None
    
    async def detailed_agent_analysis(self):
        """Provide detailed analysis of each agent's performance."""
        logger.info("🔍 Detailed Agent Analysis:")
        logger.info("=" * 80)
        
        for agent_name, results in self.agent_results.items():
            if agent_name == "final_result":
                continue
                
            logger.info(f"\n🤖 {agent_name} Agent Analysis:")
            logger.info(f"   Total interactions: {len(results)}")
            
            for i, result in enumerate(results):
                logger.info(f"   Interaction {i+1}:")
                logger.info(f"     Status: {result['status']}")
                logger.info(f"     Timestamp: {result['timestamp']}")
                
                content = result['content']
                if content:
                    # Look for specific data patterns
                    if "TBI" in content:
                        logger.info(f"     ✅ Found TBI-related content")
                    
                    if any(keyword in content.lower() for keyword in ["email", "message", "gmail"]):
                        logger.info(f"     📧 Email-related content detected")
                    
                    if any(keyword in content.lower() for keyword in ["bill", "invoice", "payment"]):
                        logger.info(f"     💰 Bill/Invoice content detected")
                    
                    if any(keyword in content.lower() for keyword in ["account", "customer", "crm"]):
                        logger.info(f"     👥 CRM/Customer content detected")
                    
                    # Show content preview
                    preview = content[:200] + "..." if len(content) > 200 else content
                    logger.info(f"     Content preview: {preview}")
        
        # Final result analysis
        if "final_result" in self.agent_results:
            logger.info(f"\n🎯 Final Result Analysis:")
            final_content = self.agent_results["final_result"]
            
            # Check for comprehensive analysis
            if "TBI" in final_content:
                logger.info("     ✅ Final result contains TBI analysis")
            if any(keyword in final_content.lower() for keyword in ["email", "bill", "crm", "customer"]):
                logger.info("     ✅ Final result covers multiple data sources")
            if len(final_content) > 500:
                logger.info("     ✅ Final result is comprehensive")
            
            logger.info(f"     Final result length: {len(final_content)} characters")
    
    async def cleanup(self):
        """Clean up all processes."""
        logger.info("🧹 Cleaning up processes...")
        
        # Stop backend
        if self.backend_process:
            try:
                self.backend_process.terminate()
                self.backend_process.wait(timeout=5)
                logger.info("✅ Backend server stopped")
            except Exception as e:
                logger.warning(f"Error stopping backend: {e}")
                try:
                    self.backend_process.kill()
                except:
                    pass
        
        # Stop MCP servers
        for service, process in self.mcp_processes.items():
            try:
                process.terminate()
                process.wait(timeout=5)
                logger.info(f"✅ {service} MCP server stopped")
            except Exception as e:
                logger.warning(f"Error stopping {service} MCP server: {e}")
                try:
                    process.kill()
                except:
                    pass
        
        logger.info("✅ Cleanup completed")
    
    async def run_test(self):
        """Run the complete multi-agent coordination test."""
        try:
            logger.info("🚀 Starting Multi-Agent Coordination Test")
            logger.info("=" * 80)
            
            # Step 1: Clean start of backend
            await self.clean_start_backend()
            
            # Step 2: Submit task
            await self.submit_task()
            
            # Step 3: Monitor execution
            await self.monitor_execution()
            
            # Step 4: Analyze results
            await self.analyze_results()
            
            # Step 5: Detailed agent analysis
            await self.detailed_agent_analysis()
            
            logger.info("=" * 80)
            logger.info("🎉 Multi-Agent Coordination Test Completed Successfully!")
            
        except Exception as e:
            logger.error(f"❌ Multi-Agent Coordination Test Failed: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            await self.cleanup()


async def main():
    """Main test function."""
    test = MultiAgentCoordinationTest()
    await test.run_test()


if __name__ == "__main__":
    asyncio.run(main())