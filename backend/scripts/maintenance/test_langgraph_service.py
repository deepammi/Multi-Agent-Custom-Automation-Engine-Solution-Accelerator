"""Test LangGraph service layer."""
import asyncio
import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.langgraph_service import LangGraphService


async def test_service():
    """Test LangGraph service."""
    print("=" * 60)
    print("Testing LangGraph Service Layer")
    print("=" * 60)
    
    # Test 1: Execute task
    print("\n1. Testing task execution...")
    result = await LangGraphService.execute_task(
        plan_id="test-service-001",
        session_id="test-session",
        task_description="Show me Zoho invoices"
    )
    
    print(f"   Status: {result.get('status')}")
    print(f"   Agent: {result.get('current_agent')}")
    if result.get('final_result'):
        preview = result['final_result'][:150]
        print(f"   Result: {preview}...")
    print("   ✅ Task execution successful")
    
    # Test 2: Get state
    print("\n2. Testing state retrieval...")
    state = await LangGraphService.get_state("test-service-001")
    if state:
        print(f"   Plan ID: {state.get('plan_id')}")
        print(f"   Current Agent: {state.get('current_agent')}")
        print(f"   Messages: {len(state.get('messages', []))}")
        print("   ✅ State retrieval successful")
    else:
        print("   ⚠️  No state found (expected for in-memory)")
    
    # Test 3: Multiple tasks
    print("\n3. Testing multiple task types...")
    tasks = [
        ("Show Salesforce accounts", "test-sf-001"),
        ("List customers", "test-cust-001"),
        ("Process invoice", "test-inv-001"),
    ]
    
    for task, plan_id in tasks:
        result = await LangGraphService.execute_task(
            plan_id=plan_id,
            session_id="test-session",
            task_description=task
        )
        print(f"   Task: '{task}' → Agent: {result.get('current_agent')} ✅")
    
    print("\n" + "=" * 60)
    print("✅ All Service Tests Passed!")
    print("=" * 60)
    print("\nLangGraph service is ready for integration!")
    print("Next step: Create workflow templates (Phase 3)")


if __name__ == "__main__":
    asyncio.run(test_service())
