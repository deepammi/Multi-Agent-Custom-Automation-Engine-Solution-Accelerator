#!/usr/bin/env python3
"""
Real PO Workflow Test
Tests the actual LangGraph orchestrator with real AI API calls.
"""
import asyncio
import uuid
import sys
import os
from datetime import datetime

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.langgraph_service import LangGraphService


class RealPOWorkflowTester:
    """Tests PO workflow with real AI API."""
    
    def __init__(self):
        self.messages = []
        self.step_counter = 0
    
    def log_step(self, step: str, details: str = ""):
        """Log test steps."""
        self.step_counter += 1
        timestamp = datetime.utcnow().strftime("%H:%M:%S")
        print(f"{self.step_counter:2d}. [{timestamp}] {step}")
        if details:
            print(f"    {details}")
    
    async def send_message(self, plan_id: str, message: dict):
        """Mock WebSocket manager for capturing messages."""
        self.messages.append(message)
        msg_type = message.get('type', 'unknown')
        content = message.get('data', {}).get('content', '')[:100]
        print(f"    📡 {msg_type}: {content}...")
    
    async def test_real_po_workflow(self, task_description: str):
        """Test PO workflow with real AI."""
        print("🌐 REAL AI PO WORKFLOW TEST")
        print("="*60)
        print(f"Task: {task_description}")
        print()
        
        # Generate test IDs
        plan_id = str(uuid.uuid4())
        session_id = str(uuid.uuid4())
        
        self.log_step("SETUP", f"Plan: {plan_id[:8]}..., Session: {session_id[:8]}...")
        
        try:
            # Execute with real LangGraph service
            self.log_step("EXECUTION_START", "Starting real AI workflow execution")
            
            result = await LangGraphService.execute_task_with_ai_planner(
                plan_id=plan_id,
                session_id=session_id,
                task_description=task_description,
                websocket_manager=self
            )
            
            self.log_step("EXECUTION_COMPLETE", f"Status: {result['status']}")
            
            # Display results
            if result["status"] == "completed":
                self.log_step("SUCCESS", "Workflow completed successfully")
                
                if result.get('agent_sequence'):
                    sequence = " → ".join(result['agent_sequence'])
                    self.log_step("AGENT_SEQUENCE", f"AI generated: {sequence}")
                
                if result.get('final_result'):
                    final_result = result['final_result'][:200]
                    self.log_step("FINAL_RESULT", f"{final_result}...")
                
                if result.get('ai_planning_summary'):
                    planning = result['ai_planning_summary']
                    if isinstance(planning, dict) and planning.get('success'):
                        self.log_step("AI_PLANNING", "AI planning was successful")
                    else:
                        self.log_step("AI_PLANNING", "AI planning used fallback")
                
            elif result["status"] == "error":
                error_msg = result.get('error', 'Unknown error')
                self.log_step("ERROR", f"Workflow failed: {error_msg}")
            
            # Summary
            print(f"\n📊 Test Summary:")
            print(f"   Status: {result['status']}")
            print(f"   Steps Logged: {self.step_counter}")
            print(f"   Messages: {len(self.messages)}")
            
            if result.get('agent_sequence'):
                print(f"   Agent Sequence: {' → '.join(result['agent_sequence'])}")
            
            return result
            
        except Exception as e:
            self.log_step("EXCEPTION", f"Test failed with exception: {str(e)}")
            print(f"\n⚠️  This is expected if:")
            print(f"   • LLM service is not configured")
            print(f"   • API keys are not set")
            print(f"   • Network connectivity issues")
            return {"status": "error", "error": str(e)}


async def main():
    """Main test function."""
    print("🚀 REAL PO WORKFLOW TESTER")
    print("="*50)
    print("This tests the actual LangGraph orchestrator with real AI API calls.")
    print("Requires proper LLM service configuration (OpenAI, Anthropic, etc.)")
    print()
    
    tester = RealPOWorkflowTester()
    
    # Test scenarios
    test_scenarios = [
        "Where is my PO-2024-001? I need to check the status and delivery date.",
        "I placed purchase order PO-2024-002 last week for office supplies. Can you track it?",
        "Check the status of PO-2024-003 - it was supposed to arrive yesterday.",
        "Help me find information about PO-2024-004 including vendor and delivery timeline."
    ]
    
    print("Available test scenarios:")
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"{i}. {scenario}")
    
    print("\nSelect a scenario (1-4) or press Enter for scenario 1:")
    try:
        choice = input().strip()
        if choice and choice.isdigit() and 1 <= int(choice) <= 4:
            selected_scenario = test_scenarios[int(choice) - 1]
        else:
            selected_scenario = test_scenarios[0]
    except (ValueError, KeyboardInterrupt):
        selected_scenario = test_scenarios[0]
    
    print(f"\nSelected: {selected_scenario}")
    print()
    
    # Run the test
    result = await tester.test_real_po_workflow(selected_scenario)
    
    if result["status"] == "completed":
        print("\n✅ Real AI test completed successfully!")
        print("   The LangGraph orchestrator is working with real AI.")
    elif result["status"] == "error":
        print("\n⚠️  Real AI test encountered an error.")
        print("   This may be due to configuration or connectivity issues.")
    
    print("\n📋 Next Steps:")
    print("   • Configure LLM service if not already done")
    print("   • Set up API keys in environment variables")
    print("   • Run the mock demo: python3 demo_po_workflow.py")
    print("   • Check the detailed analysis: python3 -m pytest test_po_workflow_e2e.py -v -s")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Test interrupted. Goodbye!")
    except Exception as e:
        print(f"\n❌ Test error: {e}")
        sys.exit(1)