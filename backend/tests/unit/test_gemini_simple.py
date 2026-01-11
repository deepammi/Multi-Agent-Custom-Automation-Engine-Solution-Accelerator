#!/usr/bin/env python3
"""
Simple Gemini AI test to verify the integration works.
"""
import os
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from app.services.llm_service import LLMService


class SimpleWebSocketManager:
    """Simple WebSocket manager for testing."""
    
    def __init__(self):
        self.messages = []
    
    async def send_message(self, plan_id: str, message: dict):
        """Capture WebSocket messages."""
        self.messages.append({
            "plan_id": plan_id,
            "message": message
        })
        print(f"📡 {message.get('type', 'message')}: {message.get('content', '')[:50]}")


async def test_gemini_simple():
    """Simple test of Gemini integration."""
    print("🧪 Simple Gemini AI Test")
    print("=" * 40)
    
    # Check API key
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("❌ GOOGLE_API_KEY not set!")
        print("   Get one from: https://makersuite.google.com/app/apikey")
        print("   Then run: export GOOGLE_API_KEY='your-key'")
        return False
    
    print(f"✅ API Key found: {api_key[:10]}...")
    
    # Set Gemini as provider
    os.environ["LLM_PROVIDER"] = "gemini"
    os.environ["GEMINI_MODEL"] = "gemini-2.5-flash"
    
    # Reset LLM service
    LLMService.reset()
    
    try:
        # Test LLM initialization
        llm = LLMService.get_llm_instance()
        print("✅ Gemini LLM initialized")
        
        # Create a simple mock websocket manager
        websocket = SimpleWebSocketManager()
        
        # Test simple call
        print("🤖 Testing Gemini API call...")
        response = await LLMService.call_llm_streaming(
            prompt="Analyze this task: 'Where is my PO-2024-001?' Provide a brief analysis in JSON format with fields: task_type, complexity, required_systems.",
            plan_id="test-123",
            websocket_manager=websocket,
            agent_name="TestAgent"
        )
        
        print(f"✅ Gemini response received!")
        print(f"   Length: {len(response)} characters")
        print(f"   Preview: {response[:200]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Gemini test failed: {e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_gemini_simple())
    if success:
        print("\n🎉 Gemini integration is working!")
        print("   You can now run: python3 test_po_workflow_gemini.py")
    else:
        print("\n❌ Gemini integration failed!")
        print("   Please check your API key and try again.")