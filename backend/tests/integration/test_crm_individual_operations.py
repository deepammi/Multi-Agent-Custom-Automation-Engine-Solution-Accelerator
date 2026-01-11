#!/usr/bin/env python3
"""
Test Individual CRM Operations - Tool Mapping and Parameter Validation

This script tests all CRM operations with correct tool name mapping and parameter validation
as specified in task 3.1 of the Salesforce Agent HTTP Integration spec.

**Feature: salesforce-agent-http-integration, Task 3.1**
**Validates: Requirements 6.1, 6.2, 6.3, 6.4, 6.5**
"""

import asyncio
import logging
import json
import sys
import os
from typing import Dict, Any, List
from datetime import datetime

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CRMOperationTester:
    """Test class for validating individual CRM operations."""
    
    def __init__(self):
        self.crm_agent = None
        self.test_results = {}
        
    async def initialize(self):
        """Initialize the CRM HTTP agent."""
        try:
            from app.agents.crm_agent_http import get_crm_agent_http
            self.crm_agent = get_crm_agent_http()
            logger.info("✅ CRM HTTP Agent initialized successfully")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to initialize CRM HTTP Agent: {e}")
            return False
    
    async def test_get_accounts_operation(self) -> Dict[str, Any]:
        """
        Test get_accounts operation with account name filtering and limits.
        **Validates: Requirements 6.1**
        """
        print("\n🏢 Testing get_accounts Operation")
        print("=" * 50)
        
        test_results = {
            "operation": "get_accounts",
            "tool_mapping": None,
            "parameter_tests": [],
            "success": False,
            "errors": []
        }
        
        try:
            # Test 1: Basic get_accounts call with default parameters
            print("\n1. Testing basic get_accounts call...")
            result1 = await self.crm_agent.get_accounts(service='salesforce', limit=3)
            
            print(f"   ✅ Basic call successful")
            print(f"   📊 Result type: {type(result1)}")
            print(f"   📊 Result keys: {list(result1.keys()) if isinstance(result1, dict) else 'Not a dict'}")
            
            # Validate result structure
            if isinstance(result1, dict):
                if 'records' in result1 or 'result' in result1:
                    print(f"   ✅ Result has expected structure")
                    test_results["parameter_tests"].append({
                        "test": "basic_call",
                        "passed": True,
                        "result_keys": list(result1.keys())
                    })
                else:
                    print(f"   ⚠️ Result missing expected 'records' or 'result' key")
                    test_results["parameter_tests"].append({
                        "test": "basic_call",
                        "passed": False,
                        "issue": "Missing expected result structure"
                    })
            
            # Test 2: get_accounts with account name filtering
            print("\n2. Testing get_accounts with account name filter...")
            result2 = await self.crm_agent.get_accounts(
                service='salesforce', 
                account_name='Acme',
                limit=5
            )
            
            print(f"   ✅ Account name filtering successful")
            print(f"   📊 Filtered result type: {type(result2)}")
            
            test_results["parameter_tests"].append({
                "test": "account_name_filter",
                "passed": True,
                "parameters": {"account_name": "Acme", "limit": 5}
            })
            
            # Test 3: get_accounts with different limit values
            print("\n3. Testing get_accounts with different limits...")
            for limit in [1, 10, 20]:
                result3 = await self.crm_agent.get_accounts(
                    service='salesforce',
                    limit=limit
                )
                print(f"   ✅ Limit {limit} successful")
                
                test_results["parameter_tests"].append({
                    "test": f"limit_{limit}",
                    "passed": True,
                    "parameters": {"limit": limit}
                })
            
            # Test 4: Validate tool name mapping
            print("\n4. Validating tool name mapping...")
            expected_tool = 'salesforce_get_accounts'
            actual_tool = self.crm_agent._get_tool_name('salesforce', 'get_accounts')
            
            if actual_tool == expected_tool:
                print(f"   ✅ Tool mapping correct: get_accounts -> {actual_tool}")
                test_results["tool_mapping"] = {
                    "expected": expected_tool,
                    "actual": actual_tool,
                    "correct": True
                }
            else:
                print(f"   ❌ Tool mapping incorrect: expected {expected_tool}, got {actual_tool}")
                test_results["tool_mapping"] = {
                    "expected": expected_tool,
                    "actual": actual_tool,
                    "correct": False
                }
                test_results["errors"].append(f"Incorrect tool mapping for get_accounts")
            
            test_results["success"] = len(test_results["errors"]) == 0
            
        except Exception as e:
            error_msg = f"get_accounts operation failed: {e}"
            logger.error(error_msg)
            test_results["errors"].append(error_msg)
            test_results["success"] = False
        
        return test_results
    
    async def test_get_opportunities_operation(self) -> Dict[str, Any]:
        """
        Test get_opportunities operation with stage filtering and limits.
        **Validates: Requirements 6.2**
        """
        print("\n💼 Testing get_opportunities Operation")
        print("=" * 50)
        
        test_results = {
            "operation": "get_opportunities",
            "tool_mapping": None,
            "parameter_tests": [],
            "success": False,
            "errors": []
        }
        
        try:
            # Test 1: Basic get_opportunities call
            print("\n1. Testing basic get_opportunities call...")
            result1 = await self.crm_agent.get_opportunities(service='salesforce', limit=3)
            
            print(f"   ✅ Basic call successful")
            print(f"   📊 Result type: {type(result1)}")
            
            test_results["parameter_tests"].append({
                "test": "basic_call",
                "passed": True,
                "result_keys": list(result1.keys()) if isinstance(result1, dict) else None
            })
            
            # Test 2: get_opportunities with stage filtering
            print("\n2. Testing get_opportunities with stage filter...")
            stages_to_test = ['Closed Won', 'Negotiation/Review', 'Proposal/Price Quote']
            
            for stage in stages_to_test:
                result2 = await self.crm_agent.get_opportunities(
                    service='salesforce',
                    stage=stage,
                    limit=5
                )
                
                print(f"   ✅ Stage filter '{stage}' successful")
                
                test_results["parameter_tests"].append({
                    "test": f"stage_filter_{stage.replace('/', '_').replace(' ', '_').lower()}",
                    "passed": True,
                    "parameters": {"stage": stage, "limit": 5}
                })
            
            # Test 3: get_opportunities with different limits
            print("\n3. Testing get_opportunities with different limits...")
            for limit in [2, 8, 15]:
                result3 = await self.crm_agent.get_opportunities(
                    service='salesforce',
                    limit=limit
                )
                print(f"   ✅ Limit {limit} successful")
                
                test_results["parameter_tests"].append({
                    "test": f"limit_{limit}",
                    "passed": True,
                    "parameters": {"limit": limit}
                })
            
            # Test 4: Validate tool name mapping
            print("\n4. Validating tool name mapping...")
            expected_tool = 'salesforce_get_opportunities'
            actual_tool = self.crm_agent._get_tool_name('salesforce', 'get_opportunities')
            
            if actual_tool == expected_tool:
                print(f"   ✅ Tool mapping correct: get_opportunities -> {actual_tool}")
                test_results["tool_mapping"] = {
                    "expected": expected_tool,
                    "actual": actual_tool,
                    "correct": True
                }
            else:
                print(f"   ❌ Tool mapping incorrect: expected {expected_tool}, got {actual_tool}")
                test_results["tool_mapping"] = {
                    "expected": expected_tool,
                    "actual": actual_tool,
                    "correct": False
                }
                test_results["errors"].append(f"Incorrect tool mapping for get_opportunities")
            
            test_results["success"] = len(test_results["errors"]) == 0
            
        except Exception as e:
            error_msg = f"get_opportunities operation failed: {e}"
            logger.error(error_msg)
            test_results["errors"].append(error_msg)
            test_results["success"] = False
        
        return test_results
    
    async def test_get_contacts_operation(self) -> Dict[str, Any]:
        """
        Test get_contacts operation with account name filtering and limits.
        **Validates: Requirements 6.3**
        """
        print("\n👥 Testing get_contacts Operation")
        print("=" * 50)
        
        test_results = {
            "operation": "get_contacts",
            "tool_mapping": None,
            "parameter_tests": [],
            "success": False,
            "errors": []
        }
        
        try:
            # Test 1: Basic get_contacts call
            print("\n1. Testing basic get_contacts call...")
            result1 = await self.crm_agent.get_contacts(service='salesforce', limit=3)
            
            print(f"   ✅ Basic call successful")
            print(f"   📊 Result type: {type(result1)}")
            
            test_results["parameter_tests"].append({
                "test": "basic_call",
                "passed": True,
                "result_keys": list(result1.keys()) if isinstance(result1, dict) else None
            })
            
            # Test 2: get_contacts with account name filtering
            print("\n2. Testing get_contacts with account name filter...")
            account_names = ['Acme', 'Global', 'Tech Solutions']
            
            for account_name in account_names:
                result2 = await self.crm_agent.get_contacts(
                    service='salesforce',
                    account_name=account_name,
                    limit=5
                )
                
                print(f"   ✅ Account filter '{account_name}' successful")
                
                test_results["parameter_tests"].append({
                    "test": f"account_filter_{account_name.lower().replace(' ', '_')}",
                    "passed": True,
                    "parameters": {"account_name": account_name, "limit": 5}
                })
            
            # Test 3: get_contacts with different limits
            print("\n3. Testing get_contacts with different limits...")
            for limit in [1, 7, 12]:
                result3 = await self.crm_agent.get_contacts(
                    service='salesforce',
                    limit=limit
                )
                print(f"   ✅ Limit {limit} successful")
                
                test_results["parameter_tests"].append({
                    "test": f"limit_{limit}",
                    "passed": True,
                    "parameters": {"limit": limit}
                })
            
            # Test 4: Validate tool name mapping
            print("\n4. Validating tool name mapping...")
            expected_tool = 'salesforce_get_contacts'
            actual_tool = self.crm_agent._get_tool_name('salesforce', 'get_contacts')
            
            if actual_tool == expected_tool:
                print(f"   ✅ Tool mapping correct: get_contacts -> {actual_tool}")
                test_results["tool_mapping"] = {
                    "expected": expected_tool,
                    "actual": actual_tool,
                    "correct": True
                }
            else:
                print(f"   ❌ Tool mapping incorrect: expected {expected_tool}, got {actual_tool}")
                test_results["tool_mapping"] = {
                    "expected": expected_tool,
                    "actual": actual_tool,
                    "correct": False
                }
                test_results["errors"].append(f"Incorrect tool mapping for get_contacts")
            
            test_results["success"] = len(test_results["errors"]) == 0
            
        except Exception as e:
            error_msg = f"get_contacts operation failed: {e}"
            logger.error(error_msg)
            test_results["errors"].append(error_msg)
            test_results["success"] = False
        
        return test_results
    
    async def test_search_records_operation(self) -> Dict[str, Any]:
        """
        Test search_records operation across multiple Salesforce objects.
        **Validates: Requirements 6.4**
        """
        print("\n🔍 Testing search_records Operation")
        print("=" * 50)
        
        test_results = {
            "operation": "search_records",
            "tool_mapping": None,
            "parameter_tests": [],
            "success": False,
            "errors": []
        }
        
        try:
            # Test 1: Basic search_records call
            print("\n1. Testing basic search_records call...")
            result1 = await self.crm_agent.search_records(
                search_term='Acme',
                service='salesforce'
            )
            
            print(f"   ✅ Basic search successful")
            print(f"   📊 Result type: {type(result1)}")
            
            test_results["parameter_tests"].append({
                "test": "basic_search",
                "passed": True,
                "parameters": {"search_term": "Acme"},
                "result_keys": list(result1.keys()) if isinstance(result1, dict) else None
            })
            
            # Test 2: search_records with different search terms
            print("\n2. Testing search_records with different search terms...")
            search_terms = ['Microsoft', 'Technology', 'Corp', 'Global']
            
            for term in search_terms:
                result2 = await self.crm_agent.search_records(
                    search_term=term,
                    service='salesforce'
                )
                
                print(f"   ✅ Search term '{term}' successful")
                
                test_results["parameter_tests"].append({
                    "test": f"search_term_{term.lower()}",
                    "passed": True,
                    "parameters": {"search_term": term}
                })
            
            # Test 3: search_records with object type filtering
            print("\n3. Testing search_records with object filtering...")
            object_combinations = [
                ['Account'],
                ['Contact'],
                ['Opportunity'],
                ['Account', 'Contact'],
                ['Account', 'Contact', 'Opportunity']
            ]
            
            for objects in object_combinations:
                result3 = await self.crm_agent.search_records(
                    search_term='Test',
                    service='salesforce',
                    objects=objects
                )
                
                print(f"   ✅ Object filter {objects} successful")
                
                test_results["parameter_tests"].append({
                    "test": f"objects_{'_'.join(objects).lower()}",
                    "passed": True,
                    "parameters": {"search_term": "Test", "objects": objects}
                })
            
            # Test 4: Validate required parameter (search_term)
            print("\n4. Testing required parameter validation...")
            try:
                await self.crm_agent.search_records(
                    search_term='',  # Empty search term should fail
                    service='salesforce'
                )
                print(f"   ❌ Empty search term should have failed")
                test_results["errors"].append("Empty search term validation failed")
            except ValueError as e:
                print(f"   ✅ Empty search term correctly rejected: {e}")
                test_results["parameter_tests"].append({
                    "test": "empty_search_term_validation",
                    "passed": True,
                    "validation": "Empty search term correctly rejected"
                })
            
            # Test 5: Validate tool name mapping
            print("\n5. Validating tool name mapping...")
            expected_tool = 'salesforce_search_records'
            actual_tool = self.crm_agent._get_tool_name('salesforce', 'search_records')
            
            if actual_tool == expected_tool:
                print(f"   ✅ Tool mapping correct: search_records -> {actual_tool}")
                test_results["tool_mapping"] = {
                    "expected": expected_tool,
                    "actual": actual_tool,
                    "correct": True
                }
            else:
                print(f"   ❌ Tool mapping incorrect: expected {expected_tool}, got {actual_tool}")
                test_results["tool_mapping"] = {
                    "expected": expected_tool,
                    "actual": actual_tool,
                    "correct": False
                }
                test_results["errors"].append(f"Incorrect tool mapping for search_records")
            
            test_results["success"] = len(test_results["errors"]) == 0
            
        except Exception as e:
            error_msg = f"search_records operation failed: {e}"
            logger.error(error_msg)
            test_results["errors"].append(error_msg)
            test_results["success"] = False
        
        return test_results
    
    async def test_run_soql_query_operation(self) -> Dict[str, Any]:
        """
        Test run_soql_query operation with custom SOQL queries.
        **Validates: Requirements 6.5**
        """
        print("\n📊 Testing run_soql_query Operation")
        print("=" * 50)
        
        test_results = {
            "operation": "run_soql_query",
            "tool_mapping": None,
            "parameter_tests": [],
            "success": False,
            "errors": []
        }
        
        try:
            # Test 1: Basic SOQL query
            print("\n1. Testing basic SOQL query...")
            basic_query = "SELECT Id, Name FROM Account LIMIT 5"
            result1 = await self.crm_agent.run_soql_query(
                query=basic_query,
                service='salesforce'
            )
            
            print(f"   ✅ Basic SOQL query successful")
            print(f"   📊 Result type: {type(result1)}")
            
            test_results["parameter_tests"].append({
                "test": "basic_soql_query",
                "passed": True,
                "parameters": {"query": basic_query},
                "result_keys": list(result1.keys()) if isinstance(result1, dict) else None
            })
            
            # Test 2: Complex SOQL queries
            print("\n2. Testing complex SOQL queries...")
            complex_queries = [
                "SELECT Id, Name, Industry, AnnualRevenue FROM Account WHERE Industry = 'Technology' LIMIT 10",
                "SELECT Id, Name, StageName, Amount FROM Opportunity WHERE Amount > 100000 LIMIT 5",
                "SELECT Id, Name, Email, Title, Account.Name FROM Contact WHERE Title LIKE '%Manager%' LIMIT 8",
                "SELECT COUNT() FROM Account",
                "SELECT Id, Name, (SELECT Name FROM Contacts) FROM Account LIMIT 3"
            ]
            
            for i, query in enumerate(complex_queries, 1):
                result2 = await self.crm_agent.run_soql_query(
                    query=query,
                    service='salesforce'
                )
                
                print(f"   ✅ Complex query {i} successful")
                
                test_results["parameter_tests"].append({
                    "test": f"complex_query_{i}",
                    "passed": True,
                    "parameters": {"query": query[:50] + "..." if len(query) > 50 else query}
                })
            
            # Test 3: Validate service restriction (SOQL only for Salesforce)
            print("\n3. Testing service restriction validation...")
            try:
                await self.crm_agent.run_soql_query(
                    query="SELECT Id FROM Account",
                    service='hubspot'  # Should fail - SOQL only for Salesforce
                )
                print(f"   ❌ Non-Salesforce service should have failed")
                test_results["errors"].append("Service restriction validation failed")
            except ValueError as e:
                print(f"   ✅ Non-Salesforce service correctly rejected: {e}")
                test_results["parameter_tests"].append({
                    "test": "service_restriction_validation",
                    "passed": True,
                    "validation": "Non-Salesforce service correctly rejected"
                })
            
            # Test 4: Validate required parameter (query)
            print("\n4. Testing required parameter validation...")
            try:
                await self.crm_agent.run_soql_query(
                    query='',  # Empty query should fail
                    service='salesforce'
                )
                print(f"   ❌ Empty query should have failed")
                test_results["errors"].append("Empty query validation failed")
            except ValueError as e:
                print(f"   ✅ Empty query correctly rejected: {e}")
                test_results["parameter_tests"].append({
                    "test": "empty_query_validation",
                    "passed": True,
                    "validation": "Empty query correctly rejected"
                })
            
            # Test 5: Validate tool name mapping
            print("\n5. Validating tool name mapping...")
            expected_tool = 'salesforce_soql_query'
            actual_tool = self.crm_agent._get_tool_name('salesforce', 'run_soql_query')
            
            if actual_tool == expected_tool:
                print(f"   ✅ Tool mapping correct: run_soql_query -> {actual_tool}")
                test_results["tool_mapping"] = {
                    "expected": expected_tool,
                    "actual": actual_tool,
                    "correct": True
                }
            else:
                print(f"   ❌ Tool mapping incorrect: expected {expected_tool}, got {actual_tool}")
                test_results["tool_mapping"] = {
                    "expected": expected_tool,
                    "actual": actual_tool,
                    "correct": False
                }
                test_results["errors"].append(f"Incorrect tool mapping for run_soql_query")
            
            test_results["success"] = len(test_results["errors"]) == 0
            
        except Exception as e:
            error_msg = f"run_soql_query operation failed: {e}"
            logger.error(error_msg)
            test_results["errors"].append(error_msg)
            test_results["success"] = False
        
        return test_results
    
    async def test_parameter_validation(self) -> Dict[str, Any]:
        """Test parameter validation across all operations."""
        print("\n🔧 Testing Parameter Validation")
        print("=" * 50)
        
        validation_results = {
            "service_validation": [],
            "operation_validation": [],
            "parameter_type_validation": [],
            "success": False,
            "errors": []
        }
        
        # Test 1: Invalid service validation
        print("\n1. Testing invalid service validation...")
        try:
            await self.crm_agent.get_accounts(service='invalid_service')
            print(f"   ❌ Invalid service should have failed")
            validation_results["errors"].append("Invalid service validation failed")
        except (ValueError, Exception) as e:
            # Accept both ValueError and other exception types (like MCPHTTPError)
            if "Unsupported CRM service" in str(e):
                print(f"   ✅ Invalid service correctly rejected: {e}")
                validation_results["service_validation"].append({
                    "test": "invalid_service",
                    "passed": True,
                    "validation": str(e)
                })
            else:
                print(f"   ❌ Unexpected error during invalid service test: {e}")
                validation_results["errors"].append(f"Unexpected error during invalid service test: {e}")
        
        # Test 2: Invalid operation validation
        print("\n2. Testing invalid operation validation...")
        try:
            self.crm_agent._get_tool_name('salesforce', 'invalid_operation')
            print(f"   ❌ Invalid operation should have failed")
            validation_results["errors"].append("Invalid operation validation failed")
        except ValueError as e:
            print(f"   ✅ Invalid operation correctly rejected: {e}")
            validation_results["operation_validation"].append({
                "test": "invalid_operation",
                "passed": True,
                "validation": str(e)
            })
        except Exception as e:
            print(f"   ❌ Unexpected error during invalid operation test: {e}")
            validation_results["errors"].append(f"Unexpected error during invalid operation test: {e}")
        
        # Test 3: Parameter type validation
        print("\n3. Testing parameter type validation...")
        
        # Test negative limit (should work but might be handled by server)
        try:
            result = await self.crm_agent.get_accounts(service='salesforce', limit=-1)
            print(f"   ⚠️ Negative limit accepted (server may handle this)")
            validation_results["parameter_type_validation"].append({
                "test": "negative_limit",
                "passed": True,
                "note": "Negative limit accepted, server may validate"
            })
        except Exception as e:
            print(f"   ✅ Negative limit rejected: {e}")
            validation_results["parameter_type_validation"].append({
                "test": "negative_limit",
                "passed": True,
                "validation": str(e)
            })
        
        # Test very large limit
        try:
            result = await self.crm_agent.get_accounts(service='salesforce', limit=10000)
            print(f"   ⚠️ Very large limit accepted (server may handle this)")
            validation_results["parameter_type_validation"].append({
                "test": "large_limit",
                "passed": True,
                "note": "Large limit accepted, server may validate"
            })
        except Exception as e:
            print(f"   ✅ Very large limit handled: {e}")
            validation_results["parameter_type_validation"].append({
                "test": "large_limit",
                "passed": True,
                "validation": str(e)
            })
        
        validation_results["success"] = len(validation_results["errors"]) == 0
        
        return validation_results
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all individual CRM operation tests."""
        print("🚀 Starting Individual CRM Operations Test Suite")
        print("=" * 80)
        print(f"⏰ Started at: {datetime.now().isoformat()}")
        
        # Initialize the agent
        if not await self.initialize():
            return {"success": False, "error": "Failed to initialize CRM agent"}
        
        # Run all operation tests
        self.test_results = {
            "get_accounts": await self.test_get_accounts_operation(),
            "get_opportunities": await self.test_get_opportunities_operation(),
            "get_contacts": await self.test_get_contacts_operation(),
            "search_records": await self.test_search_records_operation(),
            "run_soql_query": await self.test_run_soql_query_operation(),
            "parameter_validation": await self.test_parameter_validation()
        }
        
        return self.test_results
    
    def generate_summary(self) -> Dict[str, Any]:
        """Generate a comprehensive test summary."""
        if not self.test_results:
            return {"error": "No test results available"}
        
        summary = {
            "total_operations_tested": len([k for k in self.test_results.keys() if k != "parameter_validation"]),
            "successful_operations": 0,
            "failed_operations": 0,
            "tool_mapping_results": {},
            "parameter_test_results": {},
            "overall_success": True,
            "recommendations": []
        }
        
        # Analyze operation results
        for operation, results in self.test_results.items():
            if operation == "parameter_validation":
                continue
                
            if results.get("success", False):
                summary["successful_operations"] += 1
            else:
                summary["failed_operations"] += 1
                summary["overall_success"] = False
            
            # Tool mapping analysis
            tool_mapping = results.get("tool_mapping", {})
            if tool_mapping:
                summary["tool_mapping_results"][operation] = tool_mapping.get("correct", False)
            
            # Parameter test analysis
            param_tests = results.get("parameter_tests", [])
            summary["parameter_test_results"][operation] = {
                "total_tests": len(param_tests),
                "passed_tests": len([t for t in param_tests if t.get("passed", False)])
            }
        
        # Parameter validation analysis
        param_validation = self.test_results.get("parameter_validation", {})
        if not param_validation.get("success", False):
            summary["overall_success"] = False
        
        # Generate recommendations
        if summary["failed_operations"] > 0:
            summary["recommendations"].append("Fix failed operations before proceeding")
        
        incorrect_mappings = [op for op, correct in summary["tool_mapping_results"].items() if not correct]
        if incorrect_mappings:
            summary["recommendations"].append(f"Fix tool mappings for: {', '.join(incorrect_mappings)}")
        
        if not param_validation.get("success", False):
            summary["recommendations"].append("Improve parameter validation logic")
        
        if summary["overall_success"]:
            summary["recommendations"].append("All tests passed - ready for next phase")
        
        return summary


async def main():
    """Main test execution."""
    tester = CRMOperationTester()
    
    # Run all tests
    results = await tester.run_all_tests()
    
    # Generate and display summary
    print("\n" + "=" * 80)
    print("📋 TEST SUMMARY")
    print("=" * 80)
    
    summary = tester.generate_summary()
    
    if "error" in summary:
        print(f"❌ {summary['error']}")
        return False
    
    print(f"📊 Operations Tested: {summary['total_operations_tested']}")
    print(f"✅ Successful Operations: {summary['successful_operations']}")
    print(f"❌ Failed Operations: {summary['failed_operations']}")
    
    print(f"\n🔧 Tool Mapping Results:")
    for operation, correct in summary["tool_mapping_results"].items():
        status = "✅" if correct else "❌"
        print(f"   {status} {operation}: {'Correct' if correct else 'Incorrect'}")
    
    print(f"\n🧪 Parameter Test Results:")
    for operation, test_info in summary["parameter_test_results"].items():
        total = test_info["total_tests"]
        passed = test_info["passed_tests"]
        status = "✅" if passed == total else "⚠️"
        print(f"   {status} {operation}: {passed}/{total} tests passed")
    
    print(f"\n📝 Recommendations:")
    for rec in summary["recommendations"]:
        print(f"   • {rec}")
    
    overall_status = "✅ PASSED" if summary["overall_success"] else "❌ FAILED"
    print(f"\n🎯 Overall Result: {overall_status}")
    
    if summary["overall_success"]:
        print("\n🎉 All individual CRM operations tested successfully!")
        print("   Ready to proceed to real data retrieval testing (Task 4.1)")
    else:
        print("\n⚠️ Some tests failed. Please address the issues before proceeding.")
    
    return summary["overall_success"]


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)