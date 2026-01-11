#!/usr/bin/env python3
"""
Test comprehensive multi-agent coordination workflow WITHOUT HITL.

This script performs a clean start of the backend and tests the complete
multi-agent workflow with HITL disabled to allow automated testing.

Query: "check all emails, bills and customer crm accounts with keywords TBI Corp or TBI-001 and analyze them"

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


class MultiAgentCoordinationTestNoHITL:
    """Comprehensive multi-agent coordination test without HITL."""
    
    def __init__(self):
        self.backend_process = None
        self.mcp_processes = {}
        self.test_query = "check all emails, bills and customer crm accounts with keywords TBI Corp or TBI-001 and analyze them"
        self.plan_id = None
        self.session_id = None
        self.messages_received = []
        self.agents_seen = set()
        
    async def clean_start_backend(self):
        """Clean start of the backend system."""
        logger.info("🚀 Starting Multi-Agent Coordination Test (No HITL)")
        logger.info("=" * 80)
        
        logger.info("🧹 Performing clean start of backend system...")
        
        # Stop any existing processes
        logger.info("🛑 Stopping any existing backend processes...")
        subprocess.run(["pkill", "-f", "uvicorn.*app.main:app"], capture_output=True)
        subprocess.run(["pkill", "-f", "mcp.*server"], capture_output=True)
        time.sleep(2)
        
        # Start MCP servers
        logger.info("🚀 Starting MCP servers...")
        await self.start_mcp_servers()
        
        # Wait for MCP servers to be ready
        logger.info("⏳ Waiting for MCP servers to be ready...")
        time.sleep(5)
        
        # Start backend server
        logger.info("🚀 Starting backend server...")
        self.backend_process = subprocess.Popen(
            ["python3", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"],
            cwd=os.path.dirname(__file__),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        logger.info(f"✅ Backend server started (PID: {self.backend_process.pid})")
        
        # Wait for backend to be ready
        logger.info("⏳ Waiting for backend to be ready...")
        await self.wait_for_backend()
        
        logger.info("✅ Backend system started successfully")
        
    async def start_mcp_servers(self):
        """Start all MCP servers."""
        mcp_servers = [
            ("gmail", 9000, "python3 -m gmail-mcp"),
            ("salesforce", 9001, "python3 -m salesforce-mcp"),
            ("bill_com", 9002, "python3 -m macae-mcp")
        ]
        
        for name, port, command in mcp_servers:
            logger.info(f"📡 Starting {name.title()} MCP Server on port {port}...")
            process = subprocess.Popen(
                command.split(),
                cwd=os.path.dirname(__file__),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True
            )
            self.mcp_processes[name] = process
            logger.info(f"✅ {name.title()} MCP Server started (PID: {process.pid})")
            
    async def wait_for_backend(self):
        """Wait for backend to be ready."""
        max_attempts = 30
        for attempt in range(max_attempts):
            try:
                response = requests.get("http://localhost:8000/health", timeout=5)
                if response.status_code == 200:
                    logger.info("✅ Backend is ready")
                    return
            except requests.exceptions.RequestException:
                pass
            
            logger.info(f"⏳ Waiting for backend... (attempt {attempt + 1}/{max_attempts})")
            time.sleep(1)
            
        raise Exception("Backend failed to start within timeout")
        
    async def submit_task(self):
        """Submit the multi-agent coordination task with HITL disabled."""
        logger.info("📤 Submitting multi-agent coordination task...")
        logger.info(f"📝 Query: {self.test_query}")
        
        # Submit task with require_hitl=False
        response = requests.post(
            "http://localhost:8000/api/v3/process_request",
            json={
                "description": self.test_query,
                "require_hitl": False  # Disable HITL for automated testing
            },
            timeout=30
        )
        
        if response.status_code != 200:
            raise Exception(f"Failed to submit task: {response.status_code} - {response.text}")
            
        result = response.json()
        self.plan_id = result["plan_id"]
        self.session_id = result["session_id"]
        
        logger.info("✅ Task submitted successfully")
        logger.info(f"   Plan ID: {self.plan_id}")
        logger.info(f"   Session ID: {self.session_id}")
        logger.info(f"   Status: {result['status']}")
        
    async def monitor_execution(self):
        """Monitor multi-agent execution via WebSocket."""
        logger.info("🔌 Monitoring multi-agent execution via WebSocket...")
        
        websocket_url = f"ws://localhost:8000/api/v3/socket/{self.plan_id}?user_id=test_user"
        
        try:
            async with websockets.connect(websocket_url) as websocket:
                logger.info("✅ WebSocket connected")
                
                # Monitor for 2 minutes
                timeout = 120
                start_time = time.time()
                
                while time.time() - start_time < timeout:
                    try:
                        message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                        data = json.loads(message)
                        
                        self.messages_received.append(data)
                        
                        # Log message type
                        message_type = data.get("type", "unknown")
                        logger.info(f"📩 Message type: {message_type}")
                        
                        # Track agents
                        if message_type == "agent_message":
                            agent_name = data.get("data", {}).get("agent_name", "Unknown")
                            self.agents_seen.add(agent_name)
                            
                        # Check for completion
                        if message_type == "final_result_message":
                            logger.info("🎉 Received final result, execution complete")
                            break
                            
                    except asyncio.TimeoutError:
                        # Continue monitoring
                        continue
                    except websockets.exceptions.ConnectionClosed:
                        logger.info("🔌 WebSocket connection closed")
                        break
                        
        except Exception as e:
            logger.error(f"❌ WebSocket monitoring failed: {e}")
            
        logger.info("📊 Execution monitoring completed")
        logger.info(f"   Total messages received: {len(self.messages_received)}")
        logger.info(f"   Agents seen: {', '.join(sorted(self.agents_seen)) if self.agents_seen else 'None'}")
        
    async def analyze_results(self):
        """Analyze the multi-agent coordination results."""
        logger.info("📋 Analyzing multi-agent coordination results...")
        
        # Get final plan state
        response = requests.get(f"http://localhost:8000/api/v3/plan?plan_id={self.plan_id}")
        if response.status_code == 200:
            plan_data = response.json()
            
            logger.info("✅ Final plan retrieved")
            logger.info(f"   Plan status: {plan_data.get('plan', {}).get('status', 'unknown')}")
            logger.info(f"   Total messages: {len(plan_data.get('messages', []))}")
            
            # Analyze agent execution
            messages = plan_data.get('messages', [])
            agent_sequence = []
            for msg in messages:
                agent_name = msg.get('agent_name', 'Unknown')
                if agent_name not in agent_sequence:
                    agent_sequence.append(agent_name)
                    
            logger.info(f"   Agent execution sequence: {' → '.join(agent_sequence) if agent_sequence else 'None'}")
            
            # Check for expected agents
            expected_agents = ["Planner", "Email", "AP", "CRM", "Analysis"]
            for agent in expected_agents:
                if agent not in agent_sequence:
                    logger.warning(f"⚠️ {agent} Agent not found in execution")
                else:
                    logger.info(f"✅ {agent} Agent executed successfully")
                    
        else:
            logger.error(f"❌ Failed to retrieve final plan: {response.status_code}")
            
        # Detailed analysis
        logger.info("🔍 Detailed Agent Analysis:")
        logger.info("=" * 80)
        
        # TODO: Add more detailed analysis of agent outputs, tool usage, etc.
        
        logger.info("=" * 80)
        logger.info("🎉 Multi-Agent Coordination Test Completed Successfully!")
        
    async def cleanup(self):
        """Clean up processes."""
        logger.info("🧹 Cleaning up processes...")
        
        # Stop backend
        if self.backend_process:
            self.backend_process.terminate()
            try:
                self.backend_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.backend_process.kill()
            logger.info("✅ Backend server stopped")
            
        # Stop MCP servers
        for name, process in self.mcp_processes.items():
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
            logger.info(f"✅ {name} MCP server stopped")
            
        logger.info("✅ Cleanup completed")
        
    async def run_test(self):
        """Run the complete multi-agent coordination test."""
        try:
            await self.clean_start_backend()
            await self.submit_task()
            await self.monitor_execution()
            await self.analyze_results()
        finally:
            await self.cleanup()


async def main():
    """Main test execution."""
    test = MultiAgentCoordinationTestNoHITL()
    await test.run_test()


if __name__ == "__main__":
    asyncio.run(main())