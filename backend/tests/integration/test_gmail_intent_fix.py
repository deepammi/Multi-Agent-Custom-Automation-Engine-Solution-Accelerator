#!/usr/bin/env python3
"""
Simple test to verify the Gmail intent analysis fix.
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    # Load from the root directory (one level up from backend)
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
    load_dotenv(env_path)
    print(f"✅ Loaded environment variables from: {env_path}")
except ImportError:
    print("⚠️ python-dotenv not available, environment variables may not be loaded")

from app.agents.gmail_agent_node import EmailAgentNode

async def test_gmail_intent_fix():
    """Test if the Gmail agent now correctly chooses search over list."""
    print("🔍 Testing Gmail Intent Analysis Fix")
    print("=" * 60)
    
    # Create Gmail agent
    gmail_agent = EmailAgentNode(service='gmail')
    
    # Test cases that should trigger "search" action
    test_cases = [
        "check all emails with keywords TBI Corp or TBI-001",
        "find emails from John",
        "show me emails about invoices",
        "unread messages from my boss",
        "emails containing project update",
        "messages from last week about budget"
    ]
    
    # Test cases that should trigger "list" action (rare)
    list_test_cases = [
        "show my recent emails",
        "what are my latest messages",
        "list inbox"
    ]
    
    print("Testing SEARCH cases (should choose 'search' action):")
    print("-" * 50)
    
    for i, user_request in enumerate(test_cases, 1):
        print(f"\n{i}. Testing: '{user_request}'")
        
        try:
            # Test the intent analysis directly
            action_analysis = await gmail_agent._analyze_user_intent(user_request, {})
            
            action = action_analysis.get('action', 'MISSING')
            query = action_analysis.get('query', 'MISSING')
            
            print(f"   Action: {action}")
            print(f"   Query: '{query}'")
            
            if action == 'search':
                print("   ✅ CORRECT: Chose 'search' action")
                if query and query != 'MISSING' and len(query.strip()) > 0:
                    print("   ✅ GOOD: Has non-empty query")
                else:
                    print("   ⚠️  WARNING: Query is empty or missing")
            elif action == 'list':
                print("   ❌ ISSUE: Chose 'list' instead of 'search'")
            else:
                print(f"   ⚠️  UNEXPECTED: Action '{action}'")
                
        except Exception as e:
            print(f"   ❌ ERROR: {e}")
    
    print(f"\n\nTesting LIST cases (should choose 'list' action):")
    print("-" * 50)
    
    for i, user_request in enumerate(list_test_cases, 1):
        print(f"\n{i}. Testing: '{user_request}'")
        
        try:
            action_analysis = await gmail_agent._analyze_user_intent(user_request, {})
            
            action = action_analysis.get('action', 'MISSING')
            
            print(f"   Action: {action}")
            
            if action == 'list':
                print("   ✅ CORRECT: Chose 'list' action for generic request")
            elif action == 'search':
                print("   ⚠️  ACCEPTABLE: Chose 'search' (also works for generic requests)")
            else:
                print(f"   ⚠️  UNEXPECTED: Action '{action}'")
                
        except Exception as e:
            print(f"   ❌ ERROR: {e}")

if __name__ == "__main__":
    asyncio.run(test_gmail_intent_fix())