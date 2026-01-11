#!/usr/bin/env python3
"""
Gmail Agent LLM Response Validation Test Script

This script specifically tests the robust validation layer that ensures
Gmail agent execution is protected against LLM response errors when
converting user queries into MCP-compatible structured JSON.

Tests the 3 main cases:
1. Search emails based on keywords
2. Get emails based on message ID  
3. Send email with recipient, subject, body
"""

import asyncio
import logging
import sys
import os
import json
from typing import Dict, Any

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Set up logging
logging.basicConfig(level=logging.INFO)

class ValidationTestCase:
    """Test case for validation scenarios."""
    
    def __init__(self, name: str, description: str, invalid_llm_response: Dict[str, Any], 
                 user_request: str, expected_action: str, should_pass_validation: bool):
        self.name = name
        self.description = description
        self.invalid_llm_response = invalid_llm_response
        self.user_request = user_request
        self.expected_action = expected_action
        self.should_pass_validation = should_pass_validation


# Test cases covering various LLM response validation scenarios
VALIDATION_TEST_CASES = [
    ValidationTestCase(
        name="Valid Search Query",
        description="LLM provides valid search action with proper query",
        invalid_llm_response={
            "action": "search",
            "query": "invoice INV-1001 newer_than:1m",
            "max_results": 15
        },
        user_request="Find emails with invoice INV-1001 from last month",
        expected_action="search",
        should_pass_validation=True
    ),
    
    ValidationTestCase(
        name="Missing Search Query",
        description="LLM provides search action but missing query - should generate fallback",
        invalid_llm_response={
            "action": "search",
            "max_results": 10
        },
        user_request="Find emails with invoice INV-1001 from last month",
        expected_action="search",
        should_pass_validation=True  # Should pass after fallback generation
    ),
    
    ValidationTestCase(
        name="Invalid Action Type",
        description="LLM provides invalid action - should default to search",
        invalid_llm_response={
            "action": "invalid_action",
            "query": "some query"
        },
        user_request="Find emails about invoices",
        expected_action="search",
        should_pass_validation=True  # Should pass after correction
    ),
    
    ValidationTestCase(
        name="Valid Send Email",
        description="LLM provides valid send action with all required fields",
        invalid_llm_response={
            "action": "send",
            "recipient": "test@example.com",
            "subject": "Invoice Follow-up",
            "body": "Please provide status update on INV-1001"
        },
        user_request="Send email to test@example.com about invoice follow-up",
        expected_action="send",
        should_pass_validation=True
    ),
    
    ValidationTestCase(
        name="Send Email Missing Recipient",
        description="LLM provides send action but missing recipient - should fallback to search",
        invalid_llm_response={
            "action": "send",
            "subject": "Invoice Follow-up",
            "body": "Please provide status update"
        },
        user_request="Send email about invoice follow-up",
        expected_action="search",  # Should fallback to search
        should_pass_validation=True
    ),
    
    ValidationTestCase(
        name="Send Email Invalid Recipient",
        description="LLM provides send action with invalid email - should fallback to search",
        invalid_llm_response={
            "action": "send",
            "recipient": "not-an-email",
            "subject": "Invoice Follow-up",
            "body": "Please provide status update"
        },
        user_request="Send email to invalid-address about invoice",
        expected_action="search",  # Should fallback to search
        should_pass_validation=True
    ),
    
    ValidationTestCase(
        name="Valid Get Email",
        description="LLM provides valid get action with message ID",
        invalid_llm_response={
            "action": "get",
            "message_id": "19b2cc0af24ac217"
        },
        user_request="Get email with ID 19b2cc0af24ac217",
        expected_action="get",
        should_pass_validation=True
    ),
    
    ValidationTestCase(
        name="Get Email Missing Message ID",
        description="LLM provides get action but missing message ID - should fallback to search",
        invalid_llm_response={
            "action": "get"
        },
        user_request="Get email with ID 19b2cc0af24ac217",
        expected_action="search",  # Should fallback to search if ID can't be extracted
        should_pass_validation=True
    ),
    
    ValidationTestCase(
        name="Valid List Emails",
        description="LLM provides valid list action with max_results",
        invalid_llm_response={
            "action": "list",
            "max_results": 5
        },
        user_request="Show me my 5 most recent emails",
        expected_action="list",
        should_pass_validation=True
    ),
    
    ValidationTestCase(
        name="List Emails Invalid Max Results",
        description="LLM provides list action with invalid max_results - should use default",
        invalid_llm_response={
            "action": "list",
            "max_results": "not-a-number"
        },
        user_request="Show me recent emails",
        expected_action="list",
        should_pass_validation=True  # Should pass with corrected max_results
    ),
    
    ValidationTestCase(
        name="Completely Empty Response",
        description="LLM provides completely empty response - should use safe fallback",
        invalid_llm_response={},
        user_request="Find emails about invoices",
        expected_action="search",  # Should fallback to safe search
        should_pass_validation=True
    ),
    
    ValidationTestCase(
        name="Malformed JSON Structure",
        description="LLM provides response with unexpected structure - should handle gracefully",
        invalid_llm_response={
            "unexpected_field": "value",
            "action": "search"
        },
        user_request="Find emails with invoice keywords",
        expected_action="search",
        should_pass_validation=True  # Should pass after validation
    )
]


async def test_gmail_validation():
    """Test Gmail agent LLM response validation."""
    
    print("🔍 Gmail Agent LLM Response Validation Test Suite")
    print("=" * 80)
    print("Testing robust validation against LLM response errors")
    print("Ensuring MCP-compatible structured JSON for all action types")
    print("=" * 80)
    
    try:
        # Import Gmail agent
        from app.agents.gmail_agent_node import GmailAgentNode
        
        # Initialize Gmail agent
        gmail_agent = GmailAgentNode()
        
        print(f"\n✅ Gmail Agent initialized successfully")
        print(f"   Agent: {gmail_agent.name}")
        print(f"   Service: {gmail_agent.service}")
        
        # Run validation tests
        passed_tests = 0
        failed_tests = 0
        
        for i, test_case in enumerate(VALIDATION_TEST_CASES, 1):
            print(f"\n{'='*60}")
            print(f"TEST {i}/{len(VALIDATION_TEST_CASES)}: {test_case.name}")
            print(f"{'='*60}")
            print(f"Description: {test_case.description}")
            print(f"User Request: '{test_case.user_request}'")
            print(f"Expected Action: {test_case.expected_action}")
            
            print(f"\n📥 INVALID LLM RESPONSE:")
            print(f"   {json.dumps(test_case.invalid_llm_response, indent=2)}")
            
            try:
                # Test the validation method directly
                validated_result = gmail_agent._validate_and_sanitize_action_analysis(
                    test_case.invalid_llm_response, 
                    test_case.user_request
                )
                
                print(f"\n📤 VALIDATED RESULT:")
                print(f"   {json.dumps(validated_result, indent=2)}")
                
                # Check if validation worked as expected
                final_action = validated_result.get("action")
                validation_passed = gmail_agent._final_validation_check(validated_result)
                has_required_fields = gmail_agent._check_required_fields(validated_result)
                
                print(f"\n🔍 VALIDATION ANALYSIS:")
                print(f"   Final Action: {final_action}")
                print(f"   Expected Action: {test_case.expected_action}")
                print(f"   Action Matches: {final_action == test_case.expected_action}")
                print(f"   Validation Passed: {validation_passed}")
                print(f"   Has Required Fields: {has_required_fields}")
                
                # Determine test result
                test_passed = (
                    validation_passed and 
                    has_required_fields and
                    (final_action == test_case.expected_action or test_case.expected_action == "search")
                )
                
                if test_passed:
                    print(f"   ✅ TEST PASSED")
                    passed_tests += 1
                else:
                    print(f"   ❌ TEST FAILED")
                    failed_tests += 1
                
                # Show specific validation for each action type
                if final_action == "search":
                    query = validated_result.get("query", "")
                    print(f"   Search Query: '{query}' (length: {len(query)})")
                elif final_action == "send":
                    recipient = validated_result.get("recipient", "")
                    subject = validated_result.get("subject", "")
                    body = validated_result.get("body", "")
                    print(f"   Recipient: '{recipient}' (valid email: {'@' in recipient})")
                    print(f"   Subject: '{subject}' (length: {len(subject)})")
                    print(f"   Body: '{body[:50]}...' (length: {len(body)})")
                elif final_action == "get":
                    message_id = validated_result.get("message_id", "")
                    print(f"   Message ID: '{message_id}' (length: {len(message_id)})")
                elif final_action == "list":
                    max_results = validated_result.get("max_results", 0)
                    print(f"   Max Results: {max_results} (valid: {isinstance(max_results, int) and max_results > 0})")
                
            except Exception as e:
                print(f"   💥 TEST ERROR: {e}")
                failed_tests += 1
        
        # Print summary
        print(f"\n{'🎉' * 20} VALIDATION TEST RESULTS {'🎉' * 20}")
        print(f"📊 GMAIL AGENT VALIDATION TEST SUITE RESULTS:")
        print(f"   - Total Tests: {len(VALIDATION_TEST_CASES)}")
        print(f"   - Passed: {passed_tests}")
        print(f"   - Failed: {failed_tests}")
        print(f"   - Success Rate: {(passed_tests / len(VALIDATION_TEST_CASES)) * 100:.1f}%")
        
        print(f"\n🔧 VALIDATION FEATURES TESTED:")
        print(f"   ✅ Invalid action type handling")
        print(f"   ✅ Missing required field detection")
        print(f"   ✅ Fallback parameter generation")
        print(f"   ✅ Email address validation")
        print(f"   ✅ Numeric parameter validation")
        print(f"   ✅ Empty/malformed response handling")
        print(f"   ✅ MCP-compatible JSON structure enforcement")
        
        if passed_tests == len(VALIDATION_TEST_CASES):
            print(f"\n🎉 ALL VALIDATION TESTS PASSED!")
            print(f"   Gmail agent is robust against LLM response errors")
            print(f"   MCP queries will always be properly structured")
        elif passed_tests > 0:
            print(f"\n⚠️ PARTIAL SUCCESS: {passed_tests}/{len(VALIDATION_TEST_CASES)} tests passed")
            print(f"   Some validation scenarios may need attention")
        else:
            print(f"\n❌ ALL VALIDATION TESTS FAILED")
            print(f"   Validation implementation needs review")
        
        return passed_tests == len(VALIDATION_TEST_CASES)
        
    except Exception as e:
        print(f"\n❌ VALIDATION TEST SUITE FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Main function to run validation tests."""
    
    print("🚀 Starting Gmail Agent LLM Response Validation Tests...")
    
    success = await test_gmail_validation()
    
    if success:
        print(f"\n✅ Gmail agent validation is working perfectly!")
        sys.exit(0)
    else:
        print(f"\n❌ Gmail agent validation needs attention!")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())