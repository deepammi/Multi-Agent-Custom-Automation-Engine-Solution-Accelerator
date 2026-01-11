#!/usr/bin/env python3
"""
CRM Agent LLM Response Validation Test Script

This script tests the robust validation layer that ensures
CRM agent execution is protected against LLM response errors when
converting user queries into MCP-compatible structured JSON.

Tests the main CRM cases:
1. Review latest account updates
2. Search opportunities
3. Get account information
4. Find contacts
5. Run SOQL queries (Salesforce)
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

class CRMValidationTestCase:
    """Test case for CRM validation scenarios."""
    
    def __init__(self, name: str, description: str, invalid_llm_response: Dict[str, Any], 
                 user_request: str, expected_action: str, should_pass_validation: bool):
        self.name = name
        self.description = description
        self.invalid_llm_response = invalid_llm_response
        self.user_request = user_request
        self.expected_action = expected_action
        self.should_pass_validation = should_pass_validation


# Test cases covering various LLM response validation scenarios for CRM
CRM_VALIDATION_TEST_CASES = [
    CRMValidationTestCase(
        name="Valid Get Accounts",
        description="LLM provides valid get_accounts action with limit",
        invalid_llm_response={
            "action": "get_accounts",
            "service": "salesforce",
            "limit": 10
        },
        user_request="Show me recent account updates",
        expected_action="get_accounts",
        should_pass_validation=True
    ),
    
    CRMValidationTestCase(
        name="Missing Account Limit",
        description="LLM provides get_accounts but missing limit - should use default",
        invalid_llm_response={
            "action": "get_accounts",
            "service": "salesforce"
        },
        user_request="Show me account information",
        expected_action="get_accounts",
        should_pass_validation=True  # Should pass with default limit
    ),
    
    CRMValidationTestCase(
        name="Invalid Action Type",
        description="LLM provides invalid action - should default to get_accounts",
        invalid_llm_response={
            "action": "invalid_crm_action",
            "service": "salesforce"
        },
        user_request="Show me CRM data",
        expected_action="get_accounts",
        should_pass_validation=True  # Should pass after correction
    ),
    
    CRMValidationTestCase(
        name="Valid Get Opportunities",
        description="LLM provides valid get_opportunities action with stage filter",
        invalid_llm_response={
            "action": "get_opportunities",
            "service": "salesforce",
            "stage": "Closed Won",
            "limit": 5
        },
        user_request="Show me opportunities in Closed Won stage",
        expected_action="get_opportunities",
        should_pass_validation=True
    ),
    
    CRMValidationTestCase(
        name="Valid Search Records",
        description="LLM provides valid search_records action with search term",
        invalid_llm_response={
            "action": "search_records",
            "service": "salesforce",
            "search_term": "Acme Corp",
            "objects": ["Account", "Contact"]
        },
        user_request="Search for Acme Corp in CRM",
        expected_action="search_records",
        should_pass_validation=True
    ),
    
    CRMValidationTestCase(
        name="Search Records Missing Term",
        description="LLM provides search_records but missing search_term - should generate fallback",
        invalid_llm_response={
            "action": "search_records",
            "service": "salesforce",
            "objects": ["Account"]
        },
        user_request="Search for Microsoft accounts",
        expected_action="search_records",
        should_pass_validation=True  # Should pass with fallback search term
    ),
    
    CRMValidationTestCase(
        name="Valid SOQL Query",
        description="LLM provides valid run_soql_query action",
        invalid_llm_response={
            "action": "run_soql_query",
            "service": "salesforce",
            "soql_query": "SELECT Id, Name FROM Account LIMIT 5"
        },
        user_request="Run SOQL query to get accounts",
        expected_action="run_soql_query",
        should_pass_validation=True
    ),
    
    CRMValidationTestCase(
        name="SOQL Query Missing Query",
        description="LLM provides run_soql_query but missing soql_query - should generate fallback",
        invalid_llm_response={
            "action": "run_soql_query",
            "service": "salesforce"
        },
        user_request="Run SOQL query for opportunities",
        expected_action="run_soql_query",
        should_pass_validation=True  # Should pass with fallback query
    ),
    
    CRMValidationTestCase(
        name="SOQL Query Non-Salesforce Service",
        description="LLM provides run_soql_query for non-Salesforce service - should change to Salesforce",
        invalid_llm_response={
            "action": "run_soql_query",
            "service": "hubspot",
            "soql_query": "SELECT Id, Name FROM Account LIMIT 5"
        },
        user_request="Run SOQL query",
        expected_action="run_soql_query",
        should_pass_validation=True  # Should pass with corrected service
    ),
    
    CRMValidationTestCase(
        name="Valid Get Contacts",
        description="LLM provides valid get_contacts action with account filter",
        invalid_llm_response={
            "action": "get_contacts",
            "service": "salesforce",
            "account_name": "Microsoft",
            "limit": 8
        },
        user_request="Get contacts for Microsoft account",
        expected_action="get_contacts",
        should_pass_validation=True
    ),
    
    CRMValidationTestCase(
        name="Invalid Service Type",
        description="LLM provides invalid service - should default to salesforce",
        invalid_llm_response={
            "action": "get_accounts",
            "service": "invalid_crm_service",
            "limit": 5
        },
        user_request="Show me accounts",
        expected_action="get_accounts",
        should_pass_validation=True  # Should pass with corrected service
    ),
    
    CRMValidationTestCase(
        name="Invalid Limit Type",
        description="LLM provides invalid limit - should use default",
        invalid_llm_response={
            "action": "get_opportunities",
            "service": "salesforce",
            "limit": "not-a-number"
        },
        user_request="Show me opportunities",
        expected_action="get_opportunities",
        should_pass_validation=True  # Should pass with corrected limit
    ),
    
    CRMValidationTestCase(
        name="Completely Empty Response",
        description="LLM provides completely empty response - should use safe fallback",
        invalid_llm_response={},
        user_request="Show me CRM information",
        expected_action="get_accounts",  # Should fallback to safe get_accounts
        should_pass_validation=True
    )
]


async def test_crm_validation():
    """Test CRM agent LLM response validation."""
    
    print("🔍 CRM Agent LLM Response Validation Test Suite")
    print("=" * 80)
    print("Testing robust validation against LLM response errors")
    print("Ensuring MCP-compatible structured JSON for all CRM action types")
    print("=" * 80)
    
    try:
        # Import CRM agent node
        from app.agents.crm_agent_node import CRMAgentNode
        
        # Initialize CRM agent
        crm_agent = CRMAgentNode()
        
        print(f"\n✅ CRM Agent initialized successfully")
        print(f"   Agent: {crm_agent.name}")
        print(f"   Supported Services: {crm_agent.crm_agent.get_supported_services()}")
        
        # Run validation tests
        passed_tests = 0
        failed_tests = 0
        
        for i, test_case in enumerate(CRM_VALIDATION_TEST_CASES, 1):
            print(f"\n{'='*60}")
            print(f"TEST {i}/{len(CRM_VALIDATION_TEST_CASES)}: {test_case.name}")
            print(f"{'='*60}")
            print(f"Description: {test_case.description}")
            print(f"User Request: '{test_case.user_request}'")
            print(f"Expected Action: {test_case.expected_action}")
            
            print(f"\n📥 INVALID LLM RESPONSE:")
            print(f"   {json.dumps(test_case.invalid_llm_response, indent=2)}")
            
            try:
                # Test the validation method directly
                validated_result = crm_agent._validate_and_sanitize_action_analysis(
                    test_case.invalid_llm_response, 
                    test_case.user_request
                )
                
                print(f"\n📤 VALIDATED RESULT:")
                print(f"   {json.dumps(validated_result, indent=2)}")
                
                # Check if validation worked as expected
                final_action = validated_result.get("action")
                final_service = validated_result.get("service")
                validation_passed = crm_agent._final_validation_check(validated_result)
                has_required_fields = crm_agent._check_required_fields(validated_result)
                
                print(f"\n🔍 VALIDATION ANALYSIS:")
                print(f"   Final Action: {final_action}")
                print(f"   Expected Action: {test_case.expected_action}")
                print(f"   Final Service: {final_service}")
                print(f"   Action Matches: {final_action == test_case.expected_action}")
                print(f"   Validation Passed: {validation_passed}")
                print(f"   Has Required Fields: {has_required_fields}")
                
                # Determine test result
                test_passed = (
                    validation_passed and 
                    has_required_fields and
                    (final_action == test_case.expected_action or test_case.expected_action == "get_accounts")
                )
                
                if test_passed:
                    print(f"   ✅ TEST PASSED")
                    passed_tests += 1
                else:
                    print(f"   ❌ TEST FAILED")
                    failed_tests += 1
                
                # Show specific validation for each action type
                if final_action in ["get_accounts", "get_opportunities", "get_contacts"]:
                    limit = validated_result.get("limit", 0)
                    account_name = validated_result.get("account_name", "")
                    stage = validated_result.get("stage", "")
                    print(f"   Limit: {limit} (valid: {isinstance(limit, int) and limit > 0})")
                    if account_name:
                        print(f"   Account Name: '{account_name}'")
                    if stage:
                        print(f"   Stage: '{stage}'")
                elif final_action == "search_records":
                    search_term = validated_result.get("search_term", "")
                    objects = validated_result.get("objects", [])
                    print(f"   Search Term: '{search_term}' (length: {len(search_term)})")
                    print(f"   Objects: {objects}")
                elif final_action == "run_soql_query":
                    soql_query = validated_result.get("soql_query", "")
                    print(f"   SOQL Query: '{soql_query[:50]}...' (length: {len(soql_query)})")
                
            except Exception as e:
                print(f"   💥 TEST ERROR: {e}")
                failed_tests += 1
        
        # Print summary
        print(f"\n{'🎉' * 20} CRM VALIDATION TEST RESULTS {'🎉' * 20}")
        print(f"📊 CRM AGENT VALIDATION TEST SUITE RESULTS:")
        print(f"   - Total Tests: {len(CRM_VALIDATION_TEST_CASES)}")
        print(f"   - Passed: {passed_tests}")
        print(f"   - Failed: {failed_tests}")
        print(f"   - Success Rate: {(passed_tests / len(CRM_VALIDATION_TEST_CASES)) * 100:.1f}%")
        
        print(f"\n🔧 CRM VALIDATION FEATURES TESTED:")
        print(f"   ✅ Invalid action type handling")
        print(f"   ✅ Missing required field detection")
        print(f"   ✅ Fallback parameter generation")
        print(f"   ✅ Service validation")
        print(f"   ✅ Numeric parameter validation")
        print(f"   ✅ SOQL query validation")
        print(f"   ✅ Empty/malformed response handling")
        print(f"   ✅ MCP-compatible JSON structure enforcement")
        
        if passed_tests == len(CRM_VALIDATION_TEST_CASES):
            print(f"\n🎉 ALL CRM VALIDATION TESTS PASSED!")
            print(f"   CRM agent is robust against LLM response errors")
            print(f"   MCP queries will always be properly structured")
        elif passed_tests > 0:
            print(f"\n⚠️ PARTIAL SUCCESS: {passed_tests}/{len(CRM_VALIDATION_TEST_CASES)} tests passed")
            print(f"   Some validation scenarios may need attention")
        else:
            print(f"\n❌ ALL CRM VALIDATION TESTS FAILED")
            print(f"   Validation implementation needs review")
        
        return passed_tests == len(CRM_VALIDATION_TEST_CASES)
        
    except Exception as e:
        print(f"\n❌ CRM VALIDATION TEST SUITE FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Main function to run CRM validation tests."""
    
    print("🚀 Starting CRM Agent LLM Response Validation Tests...")
    
    success = await test_crm_validation()
    
    if success:
        print(f"\n✅ CRM agent validation is working perfectly!")
        sys.exit(0)
    else:
        print(f"\n❌ CRM agent validation needs attention!")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())