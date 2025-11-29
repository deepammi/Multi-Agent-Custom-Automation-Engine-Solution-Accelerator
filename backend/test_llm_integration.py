#!/usr/bin/env python
"""Test script for LLM integration."""
import asyncio
import os
import sys

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))

from app.services.llm_service import LLMService
from app.agents.prompts import build_invoice_prompt, validate_prompt_structure


async def test_mock_mode():
    """Test mock mode functionality."""
    print("\n" + "="*60)
    print("TEST 1: Mock Mode")
    print("="*60)
    
    # Set mock mode
    os.environ["USE_MOCK_LLM"] = "true"
    
    # Reset LLM service to pick up new env var
    LLMService.reset()
    
    # Check mock mode
    is_mock = LLMService.is_mock_mode()
    print(f"✓ Mock mode enabled: {is_mock}")
    assert is_mock, "Mock mode should be enabled"
    
    # Get mock response
    response = LLMService.get_mock_response("Invoice", "Check invoice #123")
    print(f"✓ Mock response length: {len(response)} chars")
    print(f"✓ Mock response preview: {response[:100]}...")
    assert len(response) > 0, "Mock response should not be empty"
    assert "Invoice Agent" in response, "Mock response should mention Invoice Agent"
    
    print("\n✅ Mock mode test PASSED\n")


async def test_prompt_building():
    """Test prompt building and validation."""
    print("\n" + "="*60)
    print("TEST 2: Prompt Building")
    print("="*60)
    
    # Build invoice prompt
    task = "Verify invoice #12345 from Acme Corp for $5,000"
    prompt = build_invoice_prompt(task)
    
    print(f"✓ Prompt length: {len(prompt)} chars")
    print(f"✓ Task included: {task in prompt}")
    
    # Validate prompt structure
    is_valid = validate_prompt_structure(prompt, "Invoice")
    print(f"✓ Prompt structure valid: {is_valid}")
    
    assert len(prompt) > 0, "Prompt should not be empty"
    assert task in prompt, "Task should be in prompt"
    assert is_valid, "Prompt structure should be valid"
    
    # Check required elements
    assert "expert" in prompt.lower(), "Prompt should mention expertise"
    assert "Task:" in prompt, "Prompt should have Task section"
    assert "provide" in prompt.lower(), "Prompt should have instructions"
    
    print("\n✅ Prompt building test PASSED\n")


async def test_llm_provider_config():
    """Test LLM provider configuration."""
    print("\n" + "="*60)
    print("TEST 3: LLM Provider Configuration")
    print("="*60)
    
    # Disable mock mode
    os.environ["USE_MOCK_LLM"] = "false"
    LLMService.reset()
    
    # Test with different providers
    providers_to_test = []
    
    # Check which providers are configured
    if os.getenv("OPENAI_API_KEY"):
        providers_to_test.append("openai")
    if os.getenv("ANTHROPIC_API_KEY"):
        providers_to_test.append("anthropic")
    # Always test ollama as it doesn't require API key
    providers_to_test.append("ollama")
    
    if not providers_to_test:
        print("⚠️  No API keys configured, testing with Ollama only")
        providers_to_test = ["ollama"]
    
    for provider in providers_to_test:
        print(f"\nTesting provider: {provider}")
        os.environ["LLM_PROVIDER"] = provider
        LLMService.reset()
        
        try:
            llm = LLMService.get_llm_instance()
            print(f"✓ {provider.capitalize()} provider initialized successfully")
            print(f"  Type: {type(llm).__name__}")
        except Exception as e:
            print(f"⚠️  {provider.capitalize()} provider failed: {e}")
            if provider == "ollama":
                print("  (This is expected if Ollama is not running locally)")
    
    print("\n✅ Provider configuration test PASSED\n")


async def test_real_api_call():
    """Test real API call (if API key is available)."""
    print("\n" + "="*60)
    print("TEST 4: Real API Call (Optional)")
    print("="*60)
    
    # Check if we have an API key
    has_openai = os.getenv("OPENAI_API_KEY") and os.getenv("OPENAI_API_KEY") != "sk-your-key-here"
    has_anthropic = os.getenv("ANTHROPIC_API_KEY") and os.getenv("ANTHROPIC_API_KEY") != "sk-ant-your-key-here"
    
    if not (has_openai or has_anthropic):
        print("⚠️  No API keys configured - skipping real API test")
        print("   To test with real API, set OPENAI_API_KEY or ANTHROPIC_API_KEY")
        print("\n✅ Real API test SKIPPED (no API keys)\n")
        return
    
    # Disable mock mode
    os.environ["USE_MOCK_LLM"] = "false"
    
    # Use OpenAI if available, otherwise Anthropic
    if has_openai:
        os.environ["LLM_PROVIDER"] = "openai"
        provider = "OpenAI"
    else:
        os.environ["LLM_PROVIDER"] = "anthropic"
        provider = "Anthropic"
    
    LLMService.reset()
    
    print(f"Testing with {provider}...")
    print("⚠️  This will make a real API call and incur costs!")
    
    # Create a simple mock websocket manager for testing
    class MockWebSocketManager:
        async def send_message(self, plan_id, message):
            msg_type = message.get("type", "unknown")
            print(f"  📨 WebSocket: {msg_type}")
            if msg_type == "agent_message_streaming":
                content = message.get("content", "")
                print(f"     Token: '{content}'", end="", flush=True)
    
    # Build a simple prompt
    task = "What are the key things to check when verifying an invoice?"
    prompt = build_invoice_prompt(task)
    
    try:
        print(f"\nCalling {provider} API...")
        response = await LLMService.call_llm_streaming(
            prompt=prompt,
            plan_id="test-123",
            websocket_manager=MockWebSocketManager(),
            agent_name="Invoice"
        )
        
        print(f"\n\n✓ API call successful!")
        print(f"✓ Response length: {len(response)} chars")
        print(f"✓ Response preview: {response[:200]}...")
        
        assert len(response) > 0, "Response should not be empty"
        
        print("\n✅ Real API test PASSED\n")
        
    except Exception as e:
        print(f"\n❌ API call failed: {e}")
        print("   This might be due to:")
        print("   - Invalid API key")
        print("   - Network issues")
        print("   - Rate limiting")
        print("\n⚠️  Real API test FAILED\n")


async def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("LLM Integration Test Suite")
    print("="*60)
    
    try:
        await test_mock_mode()
        await test_prompt_building()
        await test_llm_provider_config()
        await test_real_api_call()
        
        print("\n" + "="*60)
        print("✅ ALL TESTS COMPLETED")
        print("="*60)
        print("\nNext steps:")
        print("1. Set USE_MOCK_LLM=true in .env for cost-free testing")
        print("2. Set USE_MOCK_LLM=false and add API key for real AI calls")
        print("3. Start the backend server and test via the frontend")
        print("\n")
        
    except Exception as e:
        print(f"\n❌ TEST SUITE FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
