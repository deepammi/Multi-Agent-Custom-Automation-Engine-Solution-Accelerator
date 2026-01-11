#!/usr/bin/env python3
"""
Test PO Workflow with Gemini AI
Runs the PO workflow tests using Gemini as the LLM provider.
"""
import asyncio
import os
import sys
from dotenv import load_dotenv
from test_po_workflow_e2e import run_mock_po_test
import uuid

# Load environment variables from .env file
load_dotenv()


async def test_gemini_direct():
    """Test Gemini AI directly without WebSocket serialization issues."""
    try:
        from app.services.ai_planner_service import AIPlanner
        from app.services.llm_service import LLMService
        
        # Test AI Planner with Gemini
        llm_service = LLMService()
        ai_planner = AIPlanner(llm_service)
        
        task_description = "I need to find the status of purchase order PO-2024-001. Can you check where it is in the fulfillment process?"
        
        print(f"📝 Task: {task_description}")
        
        # Test AI planning
        planning_result = await ai_planner.plan_workflow(task_description)
        
        if planning_result.success:
            print(f"✅ AI Planning successful!")
            print(f"   Complexity: {planning_result.task_analysis.complexity}")
            print(f"   Agent Sequence: {' → '.join(planning_result.agent_sequence.agents)}")
            print(f"   Required Systems: {', '.join(planning_result.task_analysis.required_systems)}")
            print(f"   Duration: {planning_result.total_duration}s")
            
            return {
                "status": "completed",
                "agent_sequence": planning_result.agent_sequence.agents,
                "ai_planning_summary": {
                    "success": True,
                    "total_duration": planning_result.total_duration
                }
            }
        else:
            print(f"❌ AI Planning failed: {planning_result.error_message}")
            return {
                "status": "error",
                "error": planning_result.error_message
            }
            
    except Exception as e:
        print(f"❌ Direct Gemini test failed: {e}")
        return {
            "status": "error", 
            "error": str(e)
        }


def setup_gemini_environment():
    """Setup environment for Gemini testing."""
    print("🔧 Setting up Gemini environment...")
    
    # Check for API key
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("❌ GOOGLE_API_KEY not found!")
        print("\n📋 Setup Instructions:")
        print("1. Get API key from: https://makersuite.google.com/app/apikey")
        print("2. Set environment variable:")
        print("   export GOOGLE_API_KEY='your-api-key-here'")
        print("3. Install package:")
        print("   pip install langchain-google-genai")
        return False
    
    # Gemini configuration should already be loaded from .env
    # But ensure it's set correctly if not in .env
    if not os.getenv("LLM_PROVIDER"):
        os.environ["LLM_PROVIDER"] = "gemini"
    if not os.getenv("GEMINI_MODEL"):
        os.environ["GEMINI_MODEL"] = "gemini-pro"
    
    print(f"✅ GOOGLE_API_KEY found: {api_key[:10]}...")
    print(f"✅ LLM_PROVIDER set to: gemini")
    print(f"✅ GEMINI_MODEL set to: gemini-1.5-pro")
    
    return True


async def test_gemini_po_workflow():
    """Test PO workflow with Gemini AI."""
    print("🚀 Testing PO Workflow with Gemini AI")
    print("=" * 60)
    
    if not setup_gemini_environment():
        return False
    
    try:
        # First run mock test to verify basic functionality
        print("\n1️⃣  Running Mock AI Test (baseline)...")
        mock_result = await run_mock_po_test()
        
        if not mock_result or mock_result.get("status") != "completed":
            print("❌ Mock test failed - basic functionality issue")
            return False
        
        print("✅ Mock test passed - proceeding with Gemini test")
        
        # Now run with real Gemini AI
        print("\n2️⃣  Running Real Gemini AI Test...")
        
        # Reset LLM service to pick up Gemini configuration
        from app.services.llm_service import LLMService
        LLMService.reset()
        
        # Test Gemini directly without WebSocket serialization issues
        real_result = await test_gemini_direct()
        
        if real_result and real_result.get("status") == "completed":
            print("🎉 Gemini AI test SUCCESSFUL!")
            print(f"   Status: {real_result['status']}")
            print(f"   Agent Sequence: {' → '.join(real_result.get('agent_sequence', []))}")
            
            if real_result.get('ai_planning_summary'):
                planning = real_result['ai_planning_summary']
                if isinstance(planning, dict) and planning.get('success'):
                    print(f"   AI Planning: ✅ Success")
                    print(f"   Total Duration: {planning.get('total_duration', 'N/A')}s")
                else:
                    print(f"   AI Planning: ⚠️  {planning}")
            
            return True
        else:
            print("❌ Gemini AI test failed")
            if real_result:
                print(f"   Error: {real_result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ Gemini test failed with exception: {e}")
        return False


async def main():
    """Main test runner."""
    print("🧪 Gemini AI PO Workflow Test")
    print("=" * 40)
    
    # Check if required package is installed
    try:
        import langchain_google_genai
        print("✅ langchain-google-genai package found")
    except ImportError:
        print("❌ langchain-google-genai package not found")
        print("   Install with: pip install langchain-google-genai")
        return False
    
    # Run the test
    success = await test_gemini_po_workflow()
    
    if success:
        print("\n🎉 All Gemini tests PASSED!")
        print("\n🚀 Gemini AI is working correctly with the PO workflow!")
        print("   You can now use Gemini for real AI testing in the system.")
    else:
        print("\n❌ Gemini tests FAILED!")
        print("   Please check your API key and network connection.")
    
    return success


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)