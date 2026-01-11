#!/usr/bin/env python3
"""
Real Data Response Test for MACAE Backend
Tests the specific query: "analyze all bills and communications with keyword TBI-001 or TBI Corp"
Shows actual agent responses and data processing
"""
import asyncio
import json
import sys
import time
from datetime import datetime
from typing import Dict, Any, List
import aiohttp
import websockets

class Colors:
    """ANSI color codes for terminal output"""
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    PURPLE = '\033[0;35m'
    CYAN = '\033[0;36m'
    WHITE = '\033[1;37m'
    BOLD = '\033[1m'
    NC = '\033[0m'  # No Color

class RealDataTester:
    """Real Data Response Tester for MACAE"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session_id = None
        self.plan_id = None
        self.websocket = None
        self.agent_responses = []
        self.streaming_content = ""
        
    def print_header(self, title: str):
        """Print a formatted header"""
        print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.NC}")
        print(f"{Colors.BOLD}{Colors.CYAN}{title.center(60)}{Colors.NC}")
        print(f"{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.NC}\n")
    
    def print_colored(self, message: str, color: str = Colors.NC):
        """Print colored message"""
        print(f"{color}{message}{Colors.NC}")
    
    async def test_health_check(self) -> bool:
        """Test if backend is healthy"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/health") as response:
                    if response.status == 200:
                        data = await response.json()
                        self.print_colored("✅ Backend health check passed", Colors.GREEN)
                        return True
                    else:
                        self.print_colored(f"❌ Backend health check failed: {response.status}", Colors.RED)
                        return False
        except Exception as e:
            self.print_colored(f"❌ Backend connection failed: {e}", Colors.RED)
            return False
    
    async def submit_tbi_query(self) -> bool:
        """Submit the specific TBI query"""
        query = "analyze all bills and communications with keyword TBI-001 or TBI Corp"
        
        try:
            payload = {
                "description": query,
                "session_id": self.session_id
            }
            
            self.print_colored(f"📤 Submitting TBI Analysis Query:", Colors.CYAN)
            self.print_colored(f"   Query: {query}", Colors.WHITE)
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/api/v3/process_request",
                    json=payload
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        self.plan_id = data.get("plan_id")
                        self.session_id = data.get("session_id")
                        
                        self.print_colored("✅ Query submitted successfully", Colors.GREEN)
                        self.print_colored(f"   Plan ID: {self.plan_id}", Colors.BLUE)
                        self.print_colored(f"   Session ID: {self.session_id}", Colors.BLUE)
                        return True
                    else:
                        error_text = await response.text()
                        self.print_colored(f"❌ Query submission failed: {response.status}", Colors.RED)
                        self.print_colored(f"   Error: {error_text}", Colors.RED)
                        return False
        except Exception as e:
            self.print_colored(f"❌ Query submission error: {e}", Colors.RED)
            return False
    
    async def connect_websocket(self) -> bool:
        """Connect to WebSocket for real-time updates"""
        if not self.plan_id:
            self.print_colored("❌ No plan ID available for WebSocket connection", Colors.RED)
            return False
        
        try:
            ws_url = f"ws://localhost:8000/api/v3/socket/{self.plan_id}?user_id=tbi-test-user"
            self.print_colored(f"🔌 Connecting to WebSocket for real-time agent responses...", Colors.CYAN)
            
            self.websocket = await websockets.connect(ws_url)
            self.print_colored("✅ WebSocket connected - listening for agent responses", Colors.GREEN)
            return True
        except Exception as e:
            self.print_colored(f"❌ WebSocket connection failed: {e}", Colors.RED)
            return False
    
    async def capture_agent_responses(self, duration: int = 45):
        """Capture and display real agent responses"""
        if not self.websocket:
            self.print_colored("❌ No WebSocket connection available", Colors.RED)
            return
        
        self.print_header("REAL-TIME AGENT RESPONSES")
        self.print_colored(f"👂 Capturing agent responses for {duration} seconds...", Colors.YELLOW)
        
        start_time = time.time()
        message_count = 0
        current_agent = None
        
        try:
            while time.time() - start_time < duration:
                try:
                    # Wait for message with timeout
                    message = await asyncio.wait_for(self.websocket.recv(), timeout=2.0)
                    message_count += 1
                    
                    try:
                        data = json.loads(message)
                        msg_type = data.get("type", "unknown")
                        timestamp = datetime.now().strftime("%H:%M:%S")
                        
                        if msg_type == "connection_established":
                            self.print_colored(f"🔗 [{timestamp}] Connection established", Colors.BLUE)
                        
                        elif msg_type == "system_message":
                            system_data = data.get("data", {})
                            system_msg = system_data.get("message", "")
                            self.print_colored(f"🔧 [{timestamp}] System: {system_msg}", Colors.CYAN)
                        
                        elif msg_type == "agent_stream_start":
                            agent_data = data.get("data", {})
                            current_agent = agent_data.get("agent_name", "Unknown")
                            self.print_colored(f"\n🚀 [{timestamp}] {current_agent} Agent Starting Analysis...", Colors.BOLD + Colors.GREEN)
                            self.streaming_content = ""
                        
                        elif msg_type == "agent_message_streaming":
                            stream_data = data.get("data", {})
                            content = stream_data.get("content", "")
                            if content:
                                self.streaming_content += content
                                # Print streaming content in real-time (every few tokens)
                                if len(self.streaming_content) % 50 == 0:  # Print every 50 characters
                                    print(f"{Colors.WHITE}{content}{Colors.NC}", end="", flush=True)
                        
                        elif msg_type == "agent_stream_end":
                            agent_data = data.get("data", {})
                            agent_name = agent_data.get("agent_name", current_agent or "Unknown")
                            
                            # Print final streaming content
                            if self.streaming_content:
                                print()  # New line after streaming
                                self.print_colored(f"\n📋 [{timestamp}] {agent_name} Agent Complete Response:", Colors.BOLD + Colors.PURPLE)
                                self.print_colored("─" * 80, Colors.PURPLE)
                                
                                # Format and display the complete response
                                formatted_response = self.format_agent_response(self.streaming_content)
                                print(formatted_response)
                                
                                self.print_colored("─" * 80, Colors.PURPLE)
                                
                                # Store the response
                                self.agent_responses.append({
                                    "agent": agent_name,
                                    "timestamp": timestamp,
                                    "content": self.streaming_content,
                                    "formatted": formatted_response
                                })
                                
                                self.streaming_content = ""
                        
                        elif msg_type == "step_progress":
                            progress_data = data.get("data", {})
                            step = progress_data.get("step", 0)
                            total = progress_data.get("total", 0)
                            agent = progress_data.get("agent", "Unknown")
                            self.print_colored(f"📊 [{timestamp}] Progress: {step}/{total} - {agent}", Colors.CYAN)
                        
                        elif msg_type == "final_result_message":
                            result_data = data.get("data", {})
                            result = result_data.get("result", "")
                            self.print_colored(f"\n🎯 [{timestamp}] FINAL RESULT:", Colors.BOLD + Colors.GREEN)
                            self.print_colored("=" * 80, Colors.GREEN)
                            print(f"{Colors.WHITE}{result}{Colors.NC}")
                            self.print_colored("=" * 80, Colors.GREEN)
                        
                        elif msg_type == "ping":
                            # Don't print ping messages, just continue
                            continue
                        
                        else:
                            # Print other message types for debugging
                            self.print_colored(f"📨 [{timestamp}] {msg_type}: {str(data)[:100]}...", Colors.WHITE)
                    
                    except json.JSONDecodeError:
                        self.print_colored(f"📨 [{timestamp}] Raw message: {message[:100]}...", Colors.PURPLE)
                
                except asyncio.TimeoutError:
                    # Check if we have any responses yet
                    if message_count == 0:
                        print(".", end="", flush=True)
                    continue
                except websockets.exceptions.ConnectionClosed:
                    self.print_colored("\n🔌 WebSocket connection closed", Colors.YELLOW)
                    break
        
        except Exception as e:
            self.print_colored(f"\n❌ WebSocket listening error: {e}", Colors.RED)
        
        self.print_colored(f"\n📊 Captured {message_count} messages in {duration} seconds", Colors.CYAN)
        return len(self.agent_responses) > 0
    
    def format_agent_response(self, content: str) -> str:
        """Format agent response for better readability"""
        if not content:
            return "No content received"
        
        # Clean up the content
        lines = content.strip().split('\n')
        formatted_lines = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Highlight key information
            if any(keyword in line.lower() for keyword in ['tbi-001', 'tbi corp', 'invoice', 'bill', 'payment', 'status']):
                formatted_lines.append(f"{Colors.YELLOW}🔍 {line}{Colors.NC}")
            elif line.startswith('##') or line.startswith('**'):
                formatted_lines.append(f"{Colors.BOLD}{Colors.BLUE}{line}{Colors.NC}")
            elif line.startswith('-') or line.startswith('*'):
                formatted_lines.append(f"{Colors.GREEN}  {line}{Colors.NC}")
            else:
                formatted_lines.append(f"{Colors.WHITE}{line}{Colors.NC}")
        
        return '\n'.join(formatted_lines)
    
    async def get_final_plan_status(self) -> Dict[str, Any]:
        """Get final plan status and results"""
        if not self.plan_id:
            return {}
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/api/v3/plan?plan_id={self.plan_id}") as response:
                    if response.status == 200:
                        data = await response.json()
                        return data
                    else:
                        self.print_colored(f"❌ Failed to get plan status: {response.status}", Colors.RED)
                        return {}
        except Exception as e:
            self.print_colored(f"❌ Plan status error: {e}", Colors.RED)
            return {}
    
    def display_summary(self, plan_data: Dict[str, Any]):
        """Display summary of the analysis"""
        self.print_header("TBI ANALYSIS SUMMARY")
        
        plan = plan_data.get("plan", {})
        messages = plan_data.get("messages", [])
        
        self.print_colored(f"📋 Plan Status: {plan.get('status', 'unknown')}", Colors.BLUE)
        self.print_colored(f"📨 Total Messages: {len(messages)}", Colors.BLUE)
        self.print_colored(f"🤖 Agent Responses Captured: {len(self.agent_responses)}", Colors.BLUE)
        
        if self.agent_responses:
            self.print_colored("\n📊 Agent Analysis Results:", Colors.BOLD + Colors.CYAN)
            for i, response in enumerate(self.agent_responses, 1):
                self.print_colored(f"\n{i}. {response['agent']} Agent ({response['timestamp']}):", Colors.PURPLE)
                self.print_colored(f"   Response Length: {len(response['content'])} characters", Colors.WHITE)
                
                # Extract key findings
                content_lower = response['content'].lower()
                if 'tbi-001' in content_lower or 'tbi corp' in content_lower:
                    self.print_colored("   ✅ Found TBI-related content", Colors.GREEN)
                else:
                    self.print_colored("   ⚠️  No specific TBI matches found", Colors.YELLOW)
        
        # Display final result if available
        final_result = plan.get("final_result", "")
        if final_result:
            self.print_colored(f"\n🎯 Final Analysis Result:", Colors.BOLD + Colors.GREEN)
            self.print_colored("=" * 60, Colors.GREEN)
            print(f"{Colors.WHITE}{final_result}{Colors.NC}")
            self.print_colored("=" * 60, Colors.GREEN)
    
    async def cleanup(self):
        """Clean up connections"""
        if self.websocket:
            await self.websocket.close()
            self.print_colored("🔌 WebSocket disconnected", Colors.YELLOW)

async def main():
    """Main test execution"""
    tester = RealDataTester()
    
    tester.print_header("MACAE TBI ANALYSIS - REAL DATA TEST")
    print(f"{Colors.CYAN}Testing Query: 'analyze all bills and communications with keyword TBI-001 or TBI Corp'{Colors.NC}")
    
    try:
        # Step 1: Health check
        if not await tester.test_health_check():
            print(f"{Colors.RED}❌ Backend is not healthy. Please start the backend first.{Colors.NC}")
            return
        
        # Step 2: Submit TBI query
        if not await tester.submit_tbi_query():
            return
        
        # Step 3: Connect WebSocket
        if not await tester.connect_websocket():
            return
        
        # Step 4: Capture real agent responses
        has_responses = await tester.capture_agent_responses(45)  # 45 seconds to capture full workflow
        
        # Step 5: Get final plan status
        plan_data = await tester.get_final_plan_status()
        
        # Step 6: Display summary
        tester.display_summary(plan_data)
        
        if has_responses:
            tester.print_colored(f"\n🎉 TBI Analysis completed successfully!", Colors.BOLD + Colors.GREEN)
            tester.print_colored(f"   Real agent responses captured and displayed above.", Colors.GREEN)
        else:
            tester.print_colored(f"\n⚠️  No agent responses captured. Check backend logs for issues.", Colors.YELLOW)
    
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Test interrupted by user{Colors.NC}")
    
    finally:
        await tester.cleanup()

if __name__ == "__main__":
    asyncio.run(main())