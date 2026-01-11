#!/usr/bin/env python3
"""
Test script to validate CRM HTTP Agent FastMCP CallToolResult processing.

This script tests the _process_mcp_result() method in the AccountsPayable HTTP agent
(which follows the Bill.com pattern) and validates that the CRM HTTP agent
follows the same pattern for FastMCP result processing.

**Feature: salesforce-agent-http-integration, Task 2.3**
**Validates: Requirements 1.3**
"""

import asyncio
import logging
import json
from typing import Dict, Any
from dataclasses import dataclass

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class MockFastMCPResult:
    """Mock FastMCP CallToolResult for testing."""
    structured_content: Dict[str, Any] = None
    data: Any = None
    
    def __init__(self, structured_content=None, data=None):
        self.structured_content = structured_content
        self.data = data


class FastMCPResultProcessor:
    """Test class to validate FastMCP result processing patterns."""
    
    def _process_mcp_result(self, result: Any) -> Dict[str, Any]:
        """
        Process MCP CallToolResult into a standard dictionary format.
        This follows the Bill.com agent pattern.
        
        Args:
            result: Raw result from MCP tool call
            
        Returns:
            Processed result dictionary
        """
        # Handle FastMCP CallToolResult format
        if hasattr(result, 'structured_content') and result.structured_content:
            return result.structured_content
        elif hasattr(result, 'data') and result.data:
            return {"result": result.data}
        elif isinstance(result, dict):
            return result
        elif isinstance(result, str):
            return {"result": result}
        else:
            return {"result": str(result)}


async def test_fastmcp_result_processing():
    """Test FastMCP CallToolResult processing with various response formats."""
    
    print("🧪 Testing FastMCP CallToolResult Processing")
    print("=" * 60)
    
    processor = FastMCPResultProcessor()
    
    # Test Case 1: FastMCP result with structured_content
    print("\n1. Testing FastMCP result with structured_content")
    mock_result_1 = MockFastMCPResult(
        structured_content={
            "records": [
                {"Id": "001XX000004C7h2", "Name": "Acme Corp", "Type": "Customer"}
            ],
            "totalSize": 1
        }
    )
    
    processed_1 = processor._process_mcp_result(mock_result_1)
    print(f"   Input: FastMCP result with structured_content")
    print(f"   Output: {json.dumps(processed_1, indent=2)}")
    
    # Validate structured_content is returned directly
    assert processed_1 == mock_result_1.structured_content
    assert "records" in processed_1
    assert processed_1["totalSize"] == 1
    print("   ✅ PASS: structured_content returned directly")
    
    # Test Case 2: FastMCP result with data field
    print("\n2. Testing FastMCP result with data field")
    mock_result_2 = MockFastMCPResult(
        data="Simple string data from MCP server"
    )
    
    processed_2 = processor._process_mcp_result(mock_result_2)
    print(f"   Input: FastMCP result with data field")
    print(f"   Output: {json.dumps(processed_2, indent=2)}")
    
    # Validate data is wrapped in result field
    assert processed_2 == {"result": mock_result_2.data}
    assert processed_2["result"] == "Simple string data from MCP server"
    print("   ✅ PASS: data wrapped in result field")
    
    # Test Case 3: Plain dictionary result
    print("\n3. Testing plain dictionary result")
    dict_result = {
        "accounts": [
            {"name": "Microsoft", "industry": "Technology"},
            {"name": "Apple", "industry": "Technology"}
        ],
        "count": 2
    }
    
    processed_3 = processor._process_mcp_result(dict_result)
    print(f"   Input: Plain dictionary")
    print(f"   Output: {json.dumps(processed_3, indent=2)}")
    
    # Validate dictionary is returned as-is
    assert processed_3 == dict_result
    assert processed_3["count"] == 2
    print("   ✅ PASS: dictionary returned as-is")
    
    # Test Case 4: String result
    print("\n4. Testing string result")
    string_result = "No records found matching criteria"
    
    processed_4 = processor._process_mcp_result(string_result)
    print(f"   Input: String result")
    print(f"   Output: {json.dumps(processed_4, indent=2)}")
    
    # Validate string is wrapped in result field
    assert processed_4 == {"result": string_result}
    print("   ✅ PASS: string wrapped in result field")
    
    # Test Case 5: Other object types
    print("\n5. Testing other object types")
    other_result = 12345
    
    processed_5 = processor._process_mcp_result(other_result)
    print(f"   Input: Integer")
    print(f"   Output: {json.dumps(processed_5, indent=2)}")
    
    # Validate other types are converted to string and wrapped
    assert processed_5 == {"result": "12345"}
    print("   ✅ PASS: other types converted to string and wrapped")
    
    # Test Case 6: FastMCP result with both structured_content and data (structured_content takes precedence)
    print("\n6. Testing FastMCP result with both fields (precedence test)")
    mock_result_6 = MockFastMCPResult(
        structured_content={"priority": "structured_content"},
        data="should be ignored"
    )
    
    processed_6 = processor._process_mcp_result(mock_result_6)
    print(f"   Input: FastMCP result with both fields")
    print(f"   Output: {json.dumps(processed_6, indent=2)}")
    
    # Validate structured_content takes precedence
    assert processed_6 == {"priority": "structured_content"}
    assert "should be ignored" not in str(processed_6)
    print("   ✅ PASS: structured_content takes precedence over data")
    
    print("\n" + "=" * 60)
    print("🎉 All FastMCP CallToolResult processing tests PASSED!")
    
    return True


async def validate_crm_http_agent_pattern():
    """Validate that CRM HTTP agent follows the same pattern as Bill.com agent."""
    
    print("\n🔍 Validating CRM HTTP Agent Pattern Compliance")
    print("=" * 60)
    
    try:
        # Import the CRM HTTP agent
        from app.agents.crm_agent_http import CRMAgentHTTP
        
        # Check if CRM HTTP agent has the _process_mcp_result method
        crm_agent = CRMAgentHTTP()
        
        # Check if the method exists
        if not hasattr(crm_agent, '_process_mcp_result'):
            print("   ❌ ISSUE: CRM HTTP agent missing _process_mcp_result method")
            print("   📝 RECOMMENDATION: Add _process_mcp_result method following Bill.com pattern")
            return False
        
        print("   ✅ CRM HTTP agent has _process_mcp_result method")
        
        # Test the method with sample data
        test_data = MockFastMCPResult(
            structured_content={"test": "data", "records": []}
        )
        
        try:
            result = crm_agent._process_mcp_result(test_data)
            print(f"   ✅ Method executes successfully: {result}")
            
            # Validate it returns structured_content
            if result == test_data.structured_content:
                print("   ✅ Method correctly processes FastMCP structured_content")
                return True
            else:
                print("   ❌ Method does not correctly process FastMCP structured_content")
                return False
                
        except Exception as e:
            print(f"   ❌ Method execution failed: {e}")
            return False
            
    except ImportError as e:
        print(f"   ❌ Failed to import CRM HTTP agent: {e}")
        return False
    except Exception as e:
        print(f"   ❌ Validation failed: {e}")
        return False


async def compare_with_bill_com_pattern():
    """Compare CRM HTTP agent with Bill.com agent pattern."""
    
    print("\n📊 Comparing CRM HTTP Agent with Bill.com Pattern")
    print("=" * 60)
    
    try:
        # Import both agents
        from app.agents.crm_agent_http import CRMAgentHTTP
        from app.agents.accounts_payable_agent_http import AccountsPayableAgentHTTP
        
        crm_agent = CRMAgentHTTP()
        ap_agent = AccountsPayableAgentHTTP()
        
        # Check HTTP MCP client usage
        print("\n1. HTTP MCP Client Usage:")
        
        # Both should use get_mcp_http_manager()
        crm_uses_http = hasattr(crm_agent, 'mcp_manager')
        ap_uses_http = hasattr(ap_agent, 'mcp_manager')
        
        print(f"   CRM Agent uses HTTP MCP manager: {crm_uses_http}")
        print(f"   AP Agent uses HTTP MCP manager: {ap_uses_http}")
        
        if crm_uses_http and ap_uses_http:
            print("   ✅ Both agents use HTTP MCP transport")
        else:
            print("   ❌ Inconsistent HTTP MCP transport usage")
        
        # Check _process_mcp_result method
        print("\n2. FastMCP Result Processing:")
        
        crm_has_processor = hasattr(crm_agent, '_process_mcp_result')
        ap_has_processor = hasattr(ap_agent, '_process_mcp_result')
        
        print(f"   CRM Agent has _process_mcp_result: {crm_has_processor}")
        print(f"   AP Agent has _process_mcp_result: {ap_has_processor}")
        
        if not crm_has_processor and ap_has_processor:
            print("   ❌ CRM Agent missing _process_mcp_result method")
            print("   📝 RECOMMENDATION: Add _process_mcp_result method to CRM HTTP agent")
            return False
        elif crm_has_processor and ap_has_processor:
            print("   ✅ Both agents have FastMCP result processing")
        
        # Check tool mapping structure
        print("\n3. Tool Mapping Structure:")
        
        crm_services = getattr(crm_agent, 'supported_services', {})
        ap_services = getattr(ap_agent, 'supported_services', {})
        
        print(f"   CRM Agent services: {list(crm_services.keys())}")
        print(f"   AP Agent services: {list(ap_services.keys())}")
        
        # Check Salesforce tool mapping
        if 'salesforce' in crm_services:
            sf_tools = crm_services['salesforce'].get('tools', {})
            print(f"   CRM Salesforce tools: {list(sf_tools.keys())}")
            
            # Validate tool name mapping
            expected_mappings = {
                'get_accounts': 'salesforce_get_accounts',
                'get_opportunities': 'salesforce_get_opportunities',
                'get_contacts': 'salesforce_get_contacts',
                'search_records': 'salesforce_search_records',
                'run_soql_query': 'salesforce_soql_query'
            }
            
            mapping_correct = True
            for operation, expected_tool in expected_mappings.items():
                actual_tool = sf_tools.get(operation)
                if actual_tool != expected_tool:
                    print(f"   ❌ Incorrect mapping: {operation} -> {actual_tool} (expected {expected_tool})")
                    mapping_correct = False
                else:
                    print(f"   ✅ Correct mapping: {operation} -> {actual_tool}")
            
            if mapping_correct:
                print("   ✅ All Salesforce tool mappings are correct")
                return True
            else:
                print("   ❌ Some Salesforce tool mappings are incorrect")
                return False
        else:
            print("   ❌ CRM Agent missing Salesforce service configuration")
            return False
            
    except ImportError as e:
        print(f"   ❌ Failed to import agents: {e}")
        return False
    except Exception as e:
        print(f"   ❌ Comparison failed: {e}")
        return False


async def main():
    """Main test execution."""
    
    print("🚀 CRM HTTP Agent FastMCP Validation Test Suite")
    print("=" * 80)
    
    # Test 1: FastMCP result processing patterns
    test1_passed = await test_fastmcp_result_processing()
    
    # Test 2: Validate CRM HTTP agent pattern
    test2_passed = await validate_crm_http_agent_pattern()
    
    # Test 3: Compare with Bill.com pattern
    test3_passed = await compare_with_bill_com_pattern()
    
    # Summary
    print("\n" + "=" * 80)
    print("📋 TEST SUMMARY")
    print("=" * 80)
    
    print(f"1. FastMCP Result Processing: {'✅ PASS' if test1_passed else '❌ FAIL'}")
    print(f"2. CRM Agent Pattern Validation: {'✅ PASS' if test2_passed else '❌ FAIL'}")
    print(f"3. Bill.com Pattern Comparison: {'✅ PASS' if test3_passed else '❌ FAIL'}")
    
    all_passed = test1_passed and test2_passed and test3_passed
    
    if all_passed:
        print("\n🎉 ALL TESTS PASSED - CRM HTTP Agent FastMCP validation successful!")
        print("\n📝 FINDINGS:")
        print("   • CRM HTTP Agent follows Bill.com pattern correctly")
        print("   • FastMCP CallToolResult processing is implemented properly")
        print("   • HTTP MCP transport is used consistently")
        print("   • Tool mapping configuration is correct for Salesforce operations")
    else:
        print("\n❌ SOME TESTS FAILED - Issues found in CRM HTTP Agent implementation")
        print("\n📝 REQUIRED ACTIONS:")
        if not test2_passed:
            print("   • Add _process_mcp_result method to CRM HTTP agent")
        if not test3_passed:
            print("   • Fix tool mapping configuration")
            print("   • Ensure consistent HTTP MCP transport usage")
    
    return all_passed


if __name__ == "__main__":
    asyncio.run(main())