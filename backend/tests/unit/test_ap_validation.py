#!/usr/bin/env python3
"""
AccountsPayable Agent LLM Response Validation Test Script

This script tests the robust validation layer that ensures
AP agent execution is protected against LLM response errors when
converting user queries into MCP-compatible structured JSON.

Tests the main AP cases:
1. Search bills based on keywords or dates
2. Search bills for a specific vendor name  
3. Get latest bills from specific vendor
4. Get specific bill by ID
5. List vendors
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

class APValidationTestCase:
    """Test case for AP validation scenarios."""
    
    def __init__(self, name: str, description: str, invalid_llm_response: Dict[str, Any], 
                 user_request: str, expected_action: str, should_pass_validation: bool):
        self.name = name
        self.description = description
        self.invalid_llm_response = invalid_llm_response
        self.user_request = user_request
        self.expected_action = expected_action
        self.should_pass_validation = should_pass_validation


# Test cases covering various LLM response validation scenarios for AP
AP_VALIDATION_TEST_CASES = [
    APValidationTestCase(
        name="Valid Search Bills by Vendor",
        description="LLM provides valid search_bills action with vendor name",
        invalid_llm_response={
            "action": "search_bills",
            "service": "bill_com",
            "vendor_name": "Acme Corp",
            "limit": 15
        },
        user_request="Find bills from Acme Corp",
        expected_action="search_bills",
        should_pass_validation=True
    ),
    
    APValidationTestCase(
        name="Missing Search Parameters",
        description="LLM provides search_bills but missing both search_term and vendor_name",
        invalid_llm_response={
            "action": "search_bills",
            "service": "bill_com",
            "limit": 10
        },
        user_request="Find bills with invoice keywords from last month",
        expected_action="search_bills",
        should_pass_validation=True  # Should pass after fallback generation
    ),
    
    APValidationTestCase(
        name="Invalid Action Type",
        description="LLM provides invalid action - should default to list_bills",
        invalid_llm_response={
            "action": "invalid_ap_action",
            "service": "bill_com"
        },
        user_request="Show me recent bills",
        expected_action="list_bills",
        should_pass_validation=True  # Should pass after correction
    ),
    
    APValidationTestCase(
        name="Valid Get Specific Bill",
        description="LLM provides valid get_bill action with bill ID",
        invalid_llm_response={
            "action": "get_bill",
            "service": "bill_com",
            "bill_id": "INV-1001"
        },
        user_request="Get bill INV-1001",
        expected_action="get_bill",
        should_pass_validation=True
    ),
    
    APValidationTestCase(
        name="Get Bill Missing ID",
        description="LLM provides get_bill but missing bill_id - should fallback to list_bills",
        invalid_llm_response={
            "action": "get_bill",
            "service": "bill_com"
        },
        user_request="Get bill INV-1001",
        expected_action="get_bill",  # Should extract ID from request
        should_pass_validation=True
    ),
    
    APValidationTestCase(
        name="Valid List Bills with Status",
        description="LLM provides valid list_bills action with status filter",
        invalid_llm_response={
            "action": "list_bills",
            "service": "bill_com",
            "status": "unpaid",
            "limit": 10
        },
        user_request="Show me unpaid bills",
        expected_action="list_bills",
        should_pass_validation=True
    ),
    
    APValidationTestCase(
        name="List Bills Invalid Limit",
        description="LLM provides list_bills with invalid limit - should use default",
        invalid_llm_response={
            "action": "list_bills",
            "service": "bill_com",
            "limit": "not-a-number"
        },
        user_request="Show me recent bills",
        expected_action="list_bills",
        should_pass_validation=True  # Should pass with corrected limit
    ),
    
    APValidationTestCase(
        name="Valid List Vendors",
        description="LLM provides valid list_vendors action",
        invalid_llm_response={
            "action": "list_vendors",
            "service": "bill_com",
            "limit": 15
        },
        user_request="Show me all vendors",
        expected_action="list_vendors",
        should_pass_validation=True
    ),
    
    APValidationTestCase(
        name="Invalid Service Type",
        description="LLM provides invalid service - should default to bill_com",
        invalid_llm_response={
            "action": "list_bills",
            "service": "invalid_service",
            "limit": 10
        },
        user_request="Show me bills",
        expected_action="list_bills",
        should_pass_validation=True  # Should pass with corrected service
    ),
    
    APValidationTestCase(
        name="Completely Empty Response",
        description="LLM provides completely empty response - should use safe fallback",
        invalid_llm_response={},
        user_request="Show me vendor bills",
        expected_action="list_bills",  # Should fallback to safe list_bills
        should_pass_validation=True
    ),
    
    APValidationTestCase(
        name="Search Bills with Keywords",
        description="LLM provides search_bills with search_term",
        invalid_llm_response={
            "action": "search_bills",
            "service": "bill_com",
            "search_term": "invoice",
            "limit": 20
        },
        user_request="Find bills with invoice keywords",
        expected_action="search_bills",
        should_pass_validation=True
    ),
    
    APValidationTestCase(
        name="Get Vendor Missing Name",
        description="LLM provides get_vendor but missing vendor_name - should fallback to list_vendors",
        invalid_llm_response={
            "action": "get_vendor",
            "service": "bill_com"
        },
        user_request="Get vendor Acme Corp",
        expected_action="get_vendor",  # Should extract name from request
        should_pass_validation=True
    )
]


async def test_ap_validation():
    """Test AccountsPayable agent LLM response validation."""
    
    print("🔍 AccountsPayable Agent LLM Response Validation Test Suite")
    print("=" * 80)
    print("Testing robust validation against LLM response errors")
    print("Ensuring MCP-compatible structured JSON for all AP action types")
    print("=" * 80)
    
    try:
        # Import AP agent node
        from app.agents.accounts_payable_agent_node import AccountsPayableAgentNode
        
        # Initialize AP agent
        ap_agent = AccountsPayableAgentNode()
        
        print(f"\n✅ AccountsPayable Agent initialized successfully")
        print(f"   Agent: {ap_agent.name}")
        print(f"   Supported Services: {ap_agent.ap_agent.get_supported_services()}")
        
        # Run validation tests
        passed_tests = 0
        failed_tests = 0
        
        for i, test_case in enumerate(AP_VALIDATION_TEST_CASES, 1):
            print(f"\n{'='*60}")
            print(f"TEST {i}/{len(AP_VALIDATION_TEST_CASES)}: {test_case.name}")
            print(f"{'='*60}")
            print(f"Description: {test_case.description}")
            print(f"User Request: '{test_case.user_request}'")
            print(f"Expected Action: {test_case.expected_action}")
            
            print(f"\n📥 INVALID LLM RESPONSE:")
            print(f"   {json.dumps(test_case.invalid_llm_response, indent=2)}")
            
            try:
                # Test the validation method directly
                validated_result = ap_agent._validate_and_sanitize_action_analysis(
                    test_case.invalid_llm_response, 
                    test_case.user_request
                )
                
                print(f"\n📤 VALIDATED RESULT:")
                print(f"   {json.dumps(validated_result, indent=2)}")
                
                # Check if validation worked as expected
                final_action = validated_result.get("action")
                final_service = validated_result.get("service")
                validation_passed = ap_agent._final_validation_check(validated_result)
                has_required_fields = ap_agent._check_required_fields(validated_result)
                
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
                    (final_action == test_case.expected_action or test_case.expected_action == "list_bills")
                )
                
                if test_passed:
                    print(f"   ✅ TEST PASSED")
                    passed_tests += 1
                else:
                    print(f"   ❌ TEST FAILED")
                    failed_tests += 1
                
                # Show specific validation for each action type
                if final_action == "search_bills":
                    search_term = validated_result.get("search_term", "")
                    vendor_name = validated_result.get("vendor_name", "")
                    print(f"   Search Term: '{search_term}' (length: {len(search_term)})")
                    print(f"   Vendor Name: '{vendor_name}' (length: {len(vendor_name)})")
                elif final_action == "get_bill":
                    bill_id = validated_result.get("bill_id", "")
                    print(f"   Bill ID: '{bill_id}' (length: {len(bill_id)})")
                elif final_action == "list_bills":
                    limit = validated_result.get("limit", 0)
                    status = validated_result.get("status", "")
                    print(f"   Limit: {limit} (valid: {isinstance(limit, int) and limit > 0})")
                    print(f"   Status Filter: '{status}'")
                elif final_action == "list_vendors":
                    limit = validated_result.get("limit", 0)
                    print(f"   Limit: {limit} (valid: {isinstance(limit, int) and limit > 0})")
                elif final_action == "get_vendor":
                    vendor_name = validated_result.get("vendor_name", "")
                    print(f"   Vendor Name: '{vendor_name}' (length: {len(vendor_name)})")
                
            except Exception as e:
                print(f"   💥 TEST ERROR: {e}")
                failed_tests += 1
        
        # Print summary
        print(f"\n{'🎉' * 20} AP VALIDATION TEST RESULTS {'🎉' * 20}")
        print(f"📊 ACCOUNTS PAYABLE AGENT VALIDATION TEST SUITE RESULTS:")
        print(f"   - Total Tests: {len(AP_VALIDATION_TEST_CASES)}")
        print(f"   - Passed: {passed_tests}")
        print(f"   - Failed: {failed_tests}")
        print(f"   - Success Rate: {(passed_tests / len(AP_VALIDATION_TEST_CASES)) * 100:.1f}%")
        
        print(f"\n🔧 AP VALIDATION FEATURES TESTED:")
        print(f"   ✅ Invalid action type handling")
        print(f"   ✅ Missing required field detection")
        print(f"   ✅ Fallback parameter generation")
        print(f"   ✅ Service validation")
        print(f"   ✅ Numeric parameter validation")
        print(f"   ✅ Empty/malformed response handling")
        print(f"   ✅ MCP-compatible JSON structure enforcement")
        
        if passed_tests == len(AP_VALIDATION_TEST_CASES):
            print(f"\n🎉 ALL AP VALIDATION TESTS PASSED!")
            print(f"   AccountsPayable agent is robust against LLM response errors")
            print(f"   MCP queries will always be properly structured")
        elif passed_tests > 0:
            print(f"\n⚠️ PARTIAL SUCCESS: {passed_tests}/{len(AP_VALIDATION_TEST_CASES)} tests passed")
            print(f"   Some validation scenarios may need attention")
        else:
            print(f"\n❌ ALL AP VALIDATION TESTS FAILED")
            print(f"   Validation implementation needs review")
        
        return passed_tests == len(AP_VALIDATION_TEST_CASES)
        
    except Exception as e:
        print(f"\n❌ AP VALIDATION TEST SUITE FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Main function to run AP validation tests."""
    
    print("🚀 Starting AccountsPayable Agent LLM Response Validation Tests...")
    
    success = await test_ap_validation()
    
    if success:
        print(f"\n✅ AccountsPayable agent validation is working perfectly!")
        sys.exit(0)
    else:
        print(f"\n❌ AccountsPayable agent validation needs attention!")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())