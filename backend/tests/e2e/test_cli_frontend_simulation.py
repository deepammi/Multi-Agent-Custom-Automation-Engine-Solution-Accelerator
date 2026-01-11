#!/usr/bin/env python3
"""
Command-line frontend simulation tool for testing MACAE backend
This tool simulates frontend interactions to test the complete backend workflow
"""
import asyncio
import json
import sys
import time
from datetime import datetime
from typing import Dict, Any, Optional
import aiohttp
import websockets
from urllib.parse import urljoin

class Colors:
    """ANSI color codes for terminal output"""
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    PURPLE = '\033[0;35m'
    CYAN = '\033[0;36m'
    WHITE = '\033[1;37m'
    NC = '\033[0m'  # No Color

class MCLITester:
    """MACAE Command Line Interface Tester"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session_id = None
        self.plan_id = None
        self.websocket = None
        
    async def print_colored(self, message: str, color: str = Colors.NC):
        """Print colored message"""
        print(f"{color}{message}{Colors.NC}")
    
    async def test_health_check(self) -> bool:
        """Test if backend is healthy"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/health") as response:
                    if response.status == 200:
                        data = await response.json()
                        await self.print_colored("✅ Backend health check passed", Colors.GREEN)
                        await self.print_colored(f"   Status: {data.get('status', 'unknown')}", Colors.BLUE)
                        return True
                    else:
                        await self.print_colored(f"❌ Backend health check failed: {response.status}", Colors.RED)
                        return False
        except Exception as e:
            await self.print_colored(f"❌ Backend connection failed: {e}", Colors.RED)
            return False
    
    async def submit_task(self, description: str, team_id: Optional[str] = None) -> bool:
        """Submit a task to the backend"""
        try:
            payload = {
                "description": description,
                "session_id": self.session_id,
                "team_id": team_id
            }
            
            await self.print_colored(f"📤 Submitting task: {description}", Colors.CYAN)
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/api/v3/process_request",
                    json=payload
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        self.plan_id = data.get("plan_id")
                        self.session_id = data.get("session_id")
                        
                        await self.print_colored("✅ Task submitted successfully", Colors.GREEN)
                        await self.print_colored(f"   Plan ID: {self.plan_id}", Colors.BLUE)
                        await self.print_colored(f"   Session ID: {self.session_id}", Colors.BLUE)
                        return True
                    else:
                        error_text = await response.text()
                        await self.print_colored(f"❌ Task submission failed: {response.status}", Colors.RED)
                        await self.print_colored(f"   Error: {error_text}", Colors.RED)
                        return False
        except Exception as e:
            await self.print_colored(f"❌ Task submission error: {e}", Colors.RED)
            return False
    
    async def connect_websocket(self) -> bool:
        """Connect to WebSocket for real-time updates"""
        if not self.plan_id:
            await self.print_colored("❌ No plan ID available for WebSocket connection", Colors.RED)
            return False
        
        try:
            ws_url = f"ws://localhost:8000/api/v3/socket/{self.plan_id}?user_id=test-user"
            await self.print_colored(f"🔌 Connecting to WebSocket: {ws_url}", Colors.CYAN)
            
            self.websocket = await websockets.connect(ws_url)
            await self.print_colored("✅ WebSocket connected", Colors.GREEN)
            return True
        except Exception as e:
            await self.print_colored(f"❌ WebSocket connection failed: {e}", Colors.RED)
            return False
    
    async def listen_websocket_messages(self, duration: int = 30):
        """Listen for WebSocket messages for a specified duration"""
        if not self.websocket:
            await self.print_colored("❌ No WebSocket connection available", Colors.RED)
            return
        
        await self.print_colored(f"👂 Listening for WebSocket messages for {duration} seconds...", Colors.YELLOW)
        
        start_time = time.time()
        message_count = 0
        
        try:
            while time.time() - start_time < duration:
                try:
                    # Wait for message with timeout
                    message = await asyncio.wait_for(self.websocket.recv(), timeout=1.0)
                    message_count += 1
                    
                    try:
                        data = json.loads(message)
                        msg_type = data.get("type", "unknown")
                        timestamp = datetime.now().strftime("%H:%M:%S")
                        
                        await self.print_colored(f"📨 [{timestamp}] Message #{message_count}: {msg_type}", Colors.PURPLE)
                        
                        # Show relevant message content
                        if msg_type == "agent_message":
                            agent_data = data.get("data", {})
                            agent_name = agent_data.get("agent_name", "Unknown")
                            content = agent_data.get("content", "")[:100] + "..." if len(agent_data.get("content", "")) > 100 else agent_data.get("content", "")
                            await self.print_colored(f"   🤖 {agent_name}: {content}", Colors.BLUE)
                        
                        elif msg_type == "plan_approval_request":
                            await self.print_colored("   📋 Plan approval requested", Colors.YELLOW)
                        
                        elif msg_type == "final_result_message":
                            result_data = data.get("data", {})
                            result = result_data.get("result", "")[:100] + "..." if len(result_data.get("result", "")) > 100 else result_data.get("result", "")
                            await self.print_colored(f"   🎯 Final result: {result}", Colors.GREEN)
                        
                        elif msg_type == "step_progress":
                            progress_data = data.get("data", {})
                            step = progress_data.get("step", 0)
                            total = progress_data.get("total", 0)
                            agent = progress_data.get("agent", "Unknown")
                            await self.print_colored(f"   📊 Progress: {step}/{total} - {agent}", Colors.CYAN)
                        
                        else:
                            # Show first 50 chars of data for other message types
                            data_str = str(data)[:50] + "..." if len(str(data)) > 50 else str(data)
                            await self.print_colored(f"   📄 Data: {data_str}", Colors.WHITE)
                    
                    except json.JSONDecodeError:
                        await self.print_colored(f"📨 [{timestamp}] Raw message: {message[:100]}...", Colors.PURPLE)
                
                except asyncio.TimeoutError:
                    # No message received in timeout period, continue
                    continue
                except websockets.exceptions.ConnectionClosed:
                    await self.print_colored("🔌 WebSocket connection closed", Colors.YELLOW)
                    break
        
        except Exception as e:
            await self.print_colored(f"❌ WebSocket listening error: {e}", Colors.RED)
        
        await self.print_colored(f"📊 Received {message_count} messages in {duration} seconds", Colors.CYAN)
    
    async def get_plan_status(self) -> Dict[str, Any]:
        """Get current plan status"""
        if not self.plan_id:
            await self.print_colored("❌ No plan ID available", Colors.RED)
            return {}
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/api/v3/plan?plan_id={self.plan_id}") as response:
                    if response.status == 200:
                        data = await response.json()
                        await self.print_colored("✅ Plan status retrieved", Colors.GREEN)
                        
                        plan = data.get("plan", {})
                        messages = data.get("messages", [])
                        
                        await self.print_colored(f"   Status: {plan.get('status', 'unknown')}", Colors.BLUE)
                        await self.print_colored(f"   Messages: {len(messages)}", Colors.BLUE)
                        
                        return data
                    else:
                        error_text = await response.text()
                        await self.print_colored(f"❌ Plan status failed: {response.status}", Colors.RED)
                        await self.print_colored(f"   Error: {error_text}", Colors.RED)
                        return {}
        except Exception as e:
            await self.print_colored(f"❌ Plan status error: {e}", Colors.RED)
            return {}
    
    async def approve_plan(self, approved: bool = True, feedback: str = "") -> bool:
        """Approve or reject a plan"""
        if not self.plan_id:
            await self.print_colored("❌ No plan ID available", Colors.RED)
            return False
        
        try:
            payload = {
                "m_plan_id": self.plan_id,
                "approved": approved,
                "feedback": feedback
            }
            
            action = "approved" if approved else "rejected"
            await self.print_colored(f"📋 Plan {action}", Colors.CYAN)
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/api/v3/plan_approval",
                    json=payload
                ) as response:
                    if response.status == 200:
                        await self.print_colored(f"✅ Plan {action} successfully", Colors.GREEN)
                        return True
                    else:
                        error_text = await response.text()
                        await self.print_colored(f"❌ Plan approval failed: {response.status}", Colors.RED)
                        await self.print_colored(f"   Error: {error_text}", Colors.RED)
                        return False
        except Exception as e:
            await self.print_colored(f"❌ Plan approval error: {e}", Colors.RED)
            return False
    
    async def cleanup(self):
        """Clean up connections"""
        if self.websocket:
            await self.websocket.close()
            await self.print_colored("🔌 WebSocket disconnected", Colors.YELLOW)

async def interactive_mode():
    """Interactive mode for testing"""
    tester = MCLITester()
    
    print(f"{Colors.CYAN}🚀 MACAE CLI Tester - Interactive Mode{Colors.NC}")
    print(f"{Colors.CYAN}===================================={Colors.NC}")
    
    # Test health check
    if not await tester.test_health_check():
        print(f"{Colors.RED}❌ Backend is not healthy. Please start the backend first.{Colors.NC}")
        return
    
    try:
        while True:
            print(f"\n{Colors.WHITE}Available commands:{Colors.NC}")
            print(f"{Colors.YELLOW}1.{Colors.NC} Submit task")
            print(f"{Colors.YELLOW}2.{Colors.NC} Connect WebSocket")
            print(f"{Colors.YELLOW}3.{Colors.NC} Listen for messages")
            print(f"{Colors.YELLOW}4.{Colors.NC} Get plan status")
            print(f"{Colors.YELLOW}5.{Colors.NC} Approve plan")
            print(f"{Colors.YELLOW}6.{Colors.NC} Reject plan")
            print(f"{Colors.YELLOW}7.{Colors.NC} Run full test workflow")
            print(f"{Colors.YELLOW}q.{Colors.NC} Quit")
            
            choice = input(f"\n{Colors.CYAN}Enter your choice: {Colors.NC}").strip().lower()
            
            if choice == '1':
                task = input(f"{Colors.CYAN}Enter task description: {Colors.NC}")
                await tester.submit_task(task)
            
            elif choice == '2':
                await tester.connect_websocket()
            
            elif choice == '3':
                duration = input(f"{Colors.CYAN}Listen duration (seconds, default 30): {Colors.NC}")
                try:
                    duration = int(duration) if duration else 30
                except ValueError:
                    duration = 30
                await tester.listen_websocket_messages(duration)
            
            elif choice == '4':
                await tester.get_plan_status()
            
            elif choice == '5':
                feedback = input(f"{Colors.CYAN}Approval feedback (optional): {Colors.NC}")
                await tester.approve_plan(True, feedback)
            
            elif choice == '6':
                feedback = input(f"{Colors.CYAN}Rejection feedback: {Colors.NC}")
                await tester.approve_plan(False, feedback)
            
            elif choice == '7':
                await run_full_test_workflow(tester)
            
            elif choice == 'q':
                break
            
            else:
                print(f"{Colors.RED}Invalid choice. Please try again.{Colors.NC}")
    
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Interrupted by user{Colors.NC}")
    
    finally:
        await tester.cleanup()

async def run_full_test_workflow(tester: MCLITester):
    """Run a complete test workflow"""
    await tester.print_colored("🧪 Running Full Test Workflow", Colors.WHITE)
    await tester.print_colored("==============================", Colors.WHITE)
    
    # Step 1: Submit task
    test_task = "Analyze invoice INV-12345 for Acme Corp and check payment status"
    if not await tester.submit_task(test_task):
        return
    
    # Step 2: Connect WebSocket
    if not await tester.connect_websocket():
        return
    
    # Step 3: Listen for initial messages
    await tester.print_colored("📡 Phase 1: Listening for initial workflow messages...", Colors.YELLOW)
    await tester.listen_websocket_messages(15)
    
    # Step 4: Check plan status
    await tester.get_plan_status()
    
    # Step 5: Approve plan (simulate user approval)
    await tester.approve_plan(True, "Looks good, proceed with analysis")
    
    # Step 6: Listen for execution messages
    await tester.print_colored("📡 Phase 2: Listening for execution messages...", Colors.YELLOW)
    await tester.listen_websocket_messages(30)
    
    # Step 7: Final status check
    await tester.get_plan_status()
    
    await tester.print_colored("🎉 Full test workflow completed!", Colors.GREEN)

async def automated_test():
    """Run automated test scenarios"""
    tester = MCLITester()
    
    print(f"{Colors.CYAN}🤖 MACAE CLI Tester - Automated Mode{Colors.NC}")
    print(f"{Colors.CYAN}==================================={Colors.NC}")
    
    # Test health check
    if not await tester.test_health_check():
        print(f"{Colors.RED}❌ Backend is not healthy. Exiting.{Colors.NC}")
        return
    
    try:
        await run_full_test_workflow(tester)
    finally:
        await tester.cleanup()

def main():
    """Main entry point"""
    if len(sys.argv) > 1 and sys.argv[1] == "--auto":
        asyncio.run(automated_test())
    else:
        asyncio.run(interactive_mode())

if __name__ == "__main__":
    main()