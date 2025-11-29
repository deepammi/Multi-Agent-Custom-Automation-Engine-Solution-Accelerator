#!/usr/bin/env python
"""Debug script to trace LLM flow and WebSocket messages."""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from app.agents.nodes import invoice_agent_node
from app.agents.state import AgentState
from app.services.llm_service import LLMService


class DebugWebSocketManager:
    """Debug WebSocket manager that prints all messages."""
    
    def __init__(self):
        self.messages = []
    
    async def send_message(self, plan_id, message):
        msg_type = message.get("type", "unknown")
        print(f"\n📨 WebSocket Message #{len(self.messages) + 1}:")
        print(f"   Type: {msg_type}")
        print(f"   Plan ID: {plan_id}")
        
        if msg_type == "agent_message":
            data = message.get("data", {})
            content = data.get("content", "")
            print(f"   Agent: {data.get('agent_name', 'Unknown')}")
            print(f"   Content: {content[:100]}..." if len(content) > 100 else f"   Content: {content}")
        
        elif msg_type == "agent_message_streaming":
            content = message.get("content", "")
            print(f"   Token: '{content}'")
        
        elif msg_type == "agent_stream_start":
            print(f"   Agent: {message.get('agent', 'Unknown')}")
            print(f"   🚀 Streaming started")
        
        elif msg_type == "agent_stream_end":
            print(f"   Agent: {message.get('agent', 'Unknown')}")
            error = message.get("error", False)
            if error:
                print(f"   ❌ Streaming ended with error")
            else:
                print(f"   ✅ Streaming completed")
        
        self.messages.append(message)


async def test_invoice_agent():
    """Test the invoice agent with debug output."""
    print("="*60)
    print("Invoice Agent LLM Flow Debug")
    print("="*60)
    
    # Check configuration
    print("\n1. Configuration Check:")
    print(f"   USE_MOCK_LLM: {os.getenv('USE_MOCK_LLM', 'not set')}")
    print(f"   LLM_PROVIDER: {os.getenv('LLM_PROVIDER', 'not set')}")
    print(f"   Mock mode active: {LLMService.is_mock_mode()}")
    
    # Create debug WebSocket manager
    ws_manager = DebugWebSocketManager()
    
    # Create agent state
    state: AgentState = {
        "messages": [],
        "plan_id": "debug-test-123",
        "session_id": "debug-session",
        "task_description": "Check invoice #12345 from Acme Corp for $5,000",
        "current_agent": "",
        "next_agent": None,
        "final_result": "",
        "approval_required": False,
        "approved": None,
        "websocket_manager": ws_manager,
        "llm_provider": None,
        "llm_temperature": None
    }
    
    print("\n2. Calling Invoice Agent:")
    print(f"   Task: {state['task_description']}")
    print(f"   Plan ID: {state['plan_id']}")
    
    try:
        print("\n3. Executing agent node...")
        result = await invoice_agent_node(state)
        
        print("\n4. Agent Result:")
        print(f"   Current Agent: {result.get('current_agent', 'Unknown')}")
        print(f"   Messages: {len(result.get('messages', []))} message(s)")
        print(f"   Final Result Length: {len(result.get('final_result', ''))} chars")
        
        final_result = result.get('final_result', '')
        if final_result:
            print(f"\n5. Final Result Preview:")
            print(f"   {final_result[:200]}...")
        
        print(f"\n6. WebSocket Messages Sent: {len(ws_manager.messages)}")
        
        # Analyze message types
        msg_types = [m.get("type") for m in ws_manager.messages]
        print(f"   Message sequence: {' → '.join(msg_types)}")
        
        # Check for expected sequence
        has_start = "agent_stream_start" in msg_types
        has_streaming = "agent_message_streaming" in msg_types
        has_end = "agent_stream_end" in msg_types
        
        print(f"\n7. Streaming Validation:")
        print(f"   ✓ Stream start: {has_start}")
        print(f"   ✓ Streaming tokens: {has_streaming} ({msg_types.count('agent_message_streaming')} tokens)")
        print(f"   ✓ Stream end: {has_end}")
        
        if has_start and has_streaming and has_end:
            print(f"\n✅ SUCCESS: Invoice Agent is working correctly!")
            print(f"\nThe agent sent {len(ws_manager.messages)} WebSocket messages.")
            print(f"If the frontend isn't showing them, the issue is likely:")
            print(f"  1. WebSocket connection not established")
            print(f"  2. Frontend not listening for these message types")
            print(f"  3. Frontend message handler not processing correctly")
        else:
            print(f"\n⚠️  WARNING: Streaming sequence incomplete")
            print(f"   This suggests an issue with the LLM service")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Run the debug test."""
    await test_invoice_agent()
    
    print("\n" + "="*60)
    print("Debug Complete")
    print("="*60)
    print("\nNext steps:")
    print("1. If backend is working, check frontend WebSocket connection")
    print("2. Open browser DevTools → Network → WS tab")
    print("3. Look for WebSocket connection to /api/v3/socket/")
    print("4. Check if messages are being received")
    print("5. Check browser console for JavaScript errors")


if __name__ == "__main__":
    asyncio.run(main())
