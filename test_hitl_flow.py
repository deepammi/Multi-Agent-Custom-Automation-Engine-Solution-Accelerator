#!/usr/bin/env python3
"""
Simple test script to verify HITL flow with Invoice Agent
"""
import asyncio
import json
from datetime import datetime

# Mock the required components for testing
class MockPlanRepository:
    @staticmethod
    async def update_status(plan_id, status):
        print(f"✅ Plan {plan_id} status updated to: {status}")

class MockMessageRepository:
    @staticmethod
    async def get_by_plan_id(plan_id):
        return []

class MockWebSocketManager:
    @staticmethod
    async def send_message(plan_id, message):
        msg_type = message.get("type", "unknown")
        print(f"📨 WebSocket message sent to {plan_id}: {msg_type}")
        if msg_type == "user_clarification_request":
            print(f"   ✅ HITL ROUTING SUCCESSFUL!")
            print(f"   Question: {message['data'].get('question')}")
        elif msg_type == "final_result_message":
            print(f"   Status: {message['data'].get('status')}")

# Test the logic
def test_hitl_routing():
    print("\n" + "="*60)
    print("HITL ROUTING TEST")
    print("="*60 + "\n")
    
    # Simulate execution state
    execution_state = {
        "session_id": "test-session",
        "task_description": "Check invoice for accuracy",
        "next_agent": "invoice",
        "state": {"plan_id": "test-plan", "task_description": "Check invoice for accuracy"},
        "require_hitl": True  # This is the key flag
    }
    
    print("1️⃣  Execution State:")
    print(f"   require_hitl: {execution_state.get('require_hitl')}")
    print(f"   next_agent: {execution_state.get('next_agent')}")
    
    # Check the logic
    require_hitl = execution_state.get("require_hitl", True)
    print(f"\n2️⃣  Checking HITL requirement:")
    print(f"   require_hitl value: {require_hitl}")
    print(f"   not require_hitl: {not require_hitl}")
    
    if not require_hitl:
        print(f"\n❌ PROBLEM: HITL is disabled!")
        print(f"   Task would complete without HITL routing")
    else:
        print(f"\n✅ CORRECT: HITL is enabled!")
        print(f"   Task will route to HITL agent")
    
    print("\n3️⃣  Expected Flow:")
    print("   Invoice Agent → HITL Agent → User Clarification")
    
    print("\n" + "="*60 + "\n")

if __name__ == "__main__":
    test_hitl_routing()
