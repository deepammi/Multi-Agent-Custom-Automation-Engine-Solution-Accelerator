#!/usr/bin/env python
"""Quick test with OpenAI API."""
import asyncio
import os
import sys

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))

from app.services.llm_service import LLMService
from app.agents.prompts import build_invoice_prompt


class MockWebSocketManager:
    """Mock WebSocket manager for testing."""
    def __init__(self):
        self.messages = []
        self.streaming_content = []
    
    async def send_message(self, plan_id, message):
        self.messages.append(message)
        msg_type = message.get("type", "unknown")
        
        if msg_type == "agent_stream_start":
            print("\n🚀 Streaming started...")
        elif msg_type == "agent_message_streaming":
            content = message.get("content", "")
            self.streaming_content.append(content)
            print(content, end="", flush=True)
        elif msg_type == "agent_stream_end":
            print("\n\n✅ Streaming completed!")


async def test_openai():
    """Test with OpenAI API."""
    print("\n" + "="*60)
    print("OpenAI API Test")
    print("="*60)
    
    # Check for API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or api_key.startswith("sk-your"):
        print("\n❌ ERROR: OPENAI_API_KEY not set or invalid")
        print("\nPlease set your OpenAI API key:")
        print("  export OPENAI_API_KEY=sk-your-actual-key")
        print("\nOr add it to backend/.env:")
        print("  OPENAI_API_KEY=sk-your-actual-key")
        return False
    
    print(f"✓ API Key found: {api_key[:10]}...{api_key[-4:]}")
    
    # Configure for real API
    os.environ["USE_MOCK_LLM"] = "false"
    os.environ["LLM_PROVIDER"] = "openai"
    os.environ["OPENAI_MODEL"] = "gpt-4o-mini"  # Use mini for faster/cheaper testing
    
    # Reset service
    LLMService.reset()
    
    print(f"✓ Mock mode: {LLMService.is_mock_mode()}")
    print(f"✓ Provider: openai")
    print(f"✓ Model: gpt-4o-mini")
    
    # Build prompt
    task = "What are the top 3 things to verify when checking an invoice for accuracy?"
    print(f"\n📝 Task: {task}")
    
    prompt = build_invoice_prompt(task)
    print(f"✓ Prompt built ({len(prompt)} chars)")
    
    # Create mock websocket manager
    ws_manager = MockWebSocketManager()
    
    try:
        print("\n🤖 Calling OpenAI API...")
        print("-" * 60)
        
        response = await LLMService.call_llm_streaming(
            prompt=prompt,
            plan_id="test-123",
            websocket_manager=ws_manager,
            agent_name="Invoice"
        )
        
        print("-" * 60)
        print(f"\n✅ SUCCESS!")
        print(f"✓ Response length: {len(response)} chars")
        print(f"✓ Tokens streamed: {len(ws_manager.streaming_content)}")
        print(f"✓ WebSocket messages: {len(ws_manager.messages)}")
        
        # Verify message sequence
        msg_types = [m.get("type") for m in ws_manager.messages]
        print(f"✓ Message sequence: {' → '.join(msg_types)}")
        
        expected_sequence = ["agent_stream_start", "agent_message_streaming", "agent_stream_end"]
        has_start = "agent_stream_start" in msg_types
        has_streaming = "agent_message_streaming" in msg_types
        has_end = "agent_stream_end" in msg_types
        
        if has_start and has_streaming and has_end:
            print("✓ Streaming sequence correct!")
        else:
            print(f"⚠️  Streaming sequence incomplete: start={has_start}, streaming={has_streaming}, end={has_end}")
        
        print("\n" + "="*60)
        print("✅ OpenAI API Test PASSED!")
        print("="*60)
        return True
        
    except Exception as e:
        print(f"\n❌ API call failed: {e}")
        print("\nPossible issues:")
        print("  - Invalid API key")
        print("  - Network connectivity")
        print("  - Rate limiting")
        print("  - Insufficient credits")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run the test."""
    success = await test_openai()
    
    if success:
        print("\n✨ The Invoice Agent is working with real AI!")
        print("\nNext steps:")
        print("1. Update backend/.env with USE_MOCK_LLM=false")
        print("2. Start the backend server")
        print("3. Test via the frontend")
    else:
        print("\n⚠️  Test failed. Please check the error messages above.")
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
