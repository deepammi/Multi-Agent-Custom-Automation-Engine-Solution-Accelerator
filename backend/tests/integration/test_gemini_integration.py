#!/usr/bin/env python3
"""
Test Gemini AI Integration
Tests the PO workflow with Gemini AI as the LLM provider.
"""
import asyncio
import uuid
import os
import json
from datetime import datetime, timezone
from typing import Dict, Any, List
from dotenv import load_dotenv

from app.services.langgraph_service import LangGraphService
from app.services.ai_planner_service import AIPlanner
from app.services.llm_service import LLMService

# Load environment variables from .env file
load_dotenv()


class SimpleWebSocketManager:
    """Simple WebSocket manager for testing."""
    
    def __init__(self):
        self.messages = []
    
    async def send_message(self, plan_id: str, message: Dict[str, Any]):
        """Capture WebSocket messages."""
        self.messages.append({
            "plan_id": plan_id,
            "message": message,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        print(f"📡 {message['type']}: {message.get('data', {}).get('content', '')[:100]}")
    
    def __getstate__(self):
        return {"messages": self.messages}
    
    def __setstate__(self, state):
        self.messages = state.get("messages", [])


async def test_gemini_llm_service():
    """Test Gemini LLM service directly."""
    print("🧪 Testing Gemini LLM Service")
    print("=" * 50)
    
    # Check if Gemini is configured
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("❌ GOOGLE_API_KEY not found in environment variables")
        print("   Please set GOOGLE_API_KEY to test Gemini integration")
        return False
    
    # Set Gemini as provider
    os.environ["LLM_PROVIDER"] = "gemini"
    
    # Reset LLM service to pick up new provider
    LLMService.reset()
    
    try:
        # Test LLM initialization
        llm = LLMService.get_llm_instance()
        print(f"✅ Gemini LLM initialized successfully")
        
        # Test simple call
        websocket_manager = SimpleWebSocketManager()
        
        response = await LLMService.call_llm_streaming(
            prompt="Analyze this task: Where is my PO-2024-001? Provide a brief analysis.",
            plan_id="test-plan-123",
            websocket_manager=websocket_manager,
            agent_name="TestAgent"
        )
        
        print(f"✅ Gemini response received ({len(response)} chars)")
        print(f"   Response preview: {response[:200]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Gemini LLM test failed: {e}")
        return False


async def test_gemini_ai_planner():
    """Test AI Planner with Gemini."""
    print("\n🧪 Testing AI Planner with Gemini")
    print("=" * 50)
    
    # Ensure Gemini is configured
    os.environ["LLM_PROVIDER"] = "gemini"
    LLMService.reset()
    
    try:
        llm_service = LLMService()
        ai_planner = AIPlanner(llm_service)
        
        # Test AI planning
        task_description = "Where is my PO-2024-001? I need to check the status and delivery date."
        
        print(f"📝 Task: {task_description}")
        
        planning_result = await ai_planner.plan_workflow(task_description)
        
        if planning_result.success:
            print(f"✅ AI Planning successful!")
            print(f"   Complexity: {planning_result.task_analysis.complexity}")
            print(f"   Agent Sequence: {' → '.join(planning_result.agent_sequence.agents)}")
            print(f"   Required Systems: {', '.join(planning_result.task_analysis.required_systems)}")
            print(f"   Duration: {planning_result.total_duration}s")
            return planning_result
        else:
            print(f"❌ AI Planning failed: {planning_result.error_message}")
            return None
            
    except Exception as e:
        print(f"❌ AI Planner test failed: {e}")
        return None


async def test_gemini_full_workflow():
    """Test full PO workflow with Gemini."""
    print("\n🧪 Testing Full PO Workflow with Gemini")
    print("=" * 50)
    
    # Ensure Gemini is configured
    os.environ["LLM_PROVIDER"] = "gemini"
    LLMService.reset()
    
    try:
        # Test data
        task_description = "Where is my PO-2024-001? I need to check the status and delivery date."
        plan_id = str(uuid.uuid4())
        session_id = str(uuid.uuid4())
        
        print(f"📝 Task: {task_description}")
        print(f"🆔 Plan ID: {plan_id[:8]}...")
        
        # Execute workflow with Gemini
        result = await LangGraphService.execute_task_with_ai_planner(
            plan_id=plan_id,
            session_id=session_id,
            task_description=task_description,
            websocket_manager=None  # Avoid serialization issues
        )
        
        if result["status"] == "completed":
            print(f"✅ Full workflow completed successfully!")
            print(f"   Status: {result['status']}")
            print(f"   Agent Sequence: {' → '.join(result.get('agent_sequence', []))}")
            print(f"   Final Result: {result.get('final_result', 'N/A')[:200]}...")
            return result
        else:
            print(f"❌ Workflow failed: {result.get('error', 'Unknown error')}")
            return None
            
    except Exception as e:
        print(f"❌ Full workflow test failed: {e}")
        return None


async def run_gemini_tests():
    """Run all Gemini integration tests."""
    print("🚀 Gemini AI Integration Tests")
    print("=" * 60)
    
    # Check prerequisites
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("❌ GOOGLE_API_KEY environment variable is required")
        print("\n📋 Setup Instructions:")
        print("1. Get a Google AI API key from: https://makersuite.google.com/app/apikey")
        print("2. Set environment variable: export GOOGLE_API_KEY='your-api-key'")
        print("3. Install required package: pip install langchain-google-genai")
        return False
    
    print(f"✅ GOOGLE_API_KEY found: {api_key[:10]}...")
    
    results = {}
    
    # Test 1: LLM Service
    results["llm_service"] = await test_gemini_llm_service()
    
    # Test 2: AI Planner
    if results["llm_service"]:
        results["ai_planner"] = await test_gemini_ai_planner()
    else:
        results["ai_planner"] = False
    
    # Test 3: Full Workflow
    if results["ai_planner"]:
        results["full_workflow"] = await test_gemini_full_workflow()
    else:
        results["full_workflow"] = False
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 GEMINI INTEGRATION TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name.replace('_', ' ').title()}: {status}")
    
    print(f"\n🎯 Overall Result: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All Gemini integration tests PASSED!")
        print("\n🚀 You can now use Gemini for real AI testing:")
        print("   export LLM_PROVIDER=gemini")
        print("   python3 test_po_workflow_e2e.py")
        return True
    else:
        print("❌ Some Gemini integration tests FAILED!")
        return False


if __name__ == "__main__":
    success = asyncio.run(run_gemini_tests())
    exit(0 if success else 1)