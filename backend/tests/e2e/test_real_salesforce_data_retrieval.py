#!/usr/bin/env python3
"""
Test Real Salesforce Data Retrieval - Task 4.1

This script tests all CRM operations with real Salesforce org data and validates
data format and content accuracy as specified in task 4.1 of the Salesforce Agent
HTTP Integration spec.

**Feature: salesforce-agent-http-integration, Task 4.1**
**Validates: Requirements 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7**
"""

import asyncio
import logging
import json
import sys
import os
from typing import Dict, Any, List, Optional
from datetime import datetime
import re

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RealSalesforceDataTester:
    """Test class for validating real Salesforce data retrieval and formatting."""
    
    def __init__(self):
        self.crm_agent = None
        self.test_results = {}
        self.data_validation_results = {}
        
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
    
    def _validate_account_data(self, records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Validate account data structure and content.
        **Validates: Requirements 4.1, 4.6, 4.7**
        """
        validation = {
            "total_records": len(records),
            "required_fields_present": 0,
            "data_format_issues": [],
            "monetary_format_issues": [],
            "field_analysis": {},
            "success": True
        }
        
        required_fields = ['Id', 'Name']
        optional_fields = ['Phone', 'Industry', 'AnnualRevenue']
        
        for i, record in enumerate(records):
            record_issues = []
            
            # Check required fields
            for field in required_fields:
                if field in record and record[field]:
                    validation["required_fields_present"] += 1
                else:
                    record_issues.append(f"Missing or empty required field: {field}")
            
            # Validate data formats
            if 'Id' in record:
                # Salesforce ID should be 15 or 18 characters
                sf_id = record['Id']
                if not (len(sf_id) == 15 or len(sf_id) == 18):
                    record_issues.append(f"Invalid Salesforce ID format: {sf_id}")
            
            if 'Name' in record:
                # Name should be a non-empty string
                name = record['Name']
                if not isinstance(name, str) or len(name.strip()) == 0:
                    record_issues.append(f"Invalid account name: {name}")
            
            if 'Phone' in record and record['Phone']:
                # Phone should be a string (format can vary)
                phone = record['Phone']
                if not isinstance(phone, str):
                    record_issues.append(f"Invalid phone format: {phone}")
            
            if 'AnnualRevenue' in record and record['AnnualRevenue'] is not None:
                # Revenue should be numeric
                revenue = record['AnnualRevenue']
                if not isinstance(revenue, (int, float)):
                    validation["monetary_format_issues"].append(
                        f"Record {i}: AnnualRevenue not numeric: {revenue} ({type(revenue)})"
                    )
                elif revenue < 0:
                    validation["monetary_format_issues"].append(
                        f"Record {i}: Negative revenue: {revenue}"
                    )
            
            if record_issues:
                validation["data_format_issues"].extend([f"Record {i}: {issue}" for issue in record_issues])
        
        # Field presence analysis
        for field in required_fields + optional_fields:
            present_count = sum(1 for record in records if field in record and record[field] is not None)
            validation["field_analysis"][field] = {
                "present_in_records": present_count,
                "percentage": (present_count / len(records) * 100) if records else 0
            }
        
        validation["success"] = len(validation["data_format_issues"]) == 0
        
        return validation
    
    def _validate_opportunity_data(self, records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Validate opportunity data structure and content.
        **Validates: Requirements 4.2, 4.6, 4.7**
        """
        validation = {
            "total_records": len(records),
            "required_fields_present": 0,
            "data_format_issues": [],
            "monetary_format_issues": [],
            "date_format_issues": [],
            "field_analysis": {},
            "success": True
        }
        
        required_fields = ['Id', 'Name']
        optional_fields = ['StageName', 'Amount', 'CloseDate', 'Account']
        
        for i, record in enumerate(records):
            record_issues = []
            
            # Check required fields
            for field in required_fields:
                if field in record and record[field]:
                    validation["required_fields_present"] += 1
                else:
                    record_issues.append(f"Missing or empty required field: {field}")
            
            # Validate Amount (monetary field)
            if 'Amount' in record and record['Amount'] is not None:
                amount = record['Amount']
                if not isinstance(amount, (int, float)):
                    validation["monetary_format_issues"].append(
                        f"Record {i}: Amount not numeric: {amount} ({type(amount)})"
                    )
                elif amount < 0:
                    validation["monetary_format_issues"].append(
                        f"Record {i}: Negative amount: {amount}"
                    )
            
            # Validate CloseDate (date field)
            if 'CloseDate' in record and record['CloseDate']:
                close_date = record['CloseDate']
                if isinstance(close_date, str):
                    # Check if it's a valid date format (YYYY-MM-DD or similar)
                    date_pattern = r'^\d{4}-\d{2}-\d{2}$'
                    if not re.match(date_pattern, close_date):
                        validation["date_format_issues"].append(
                            f"Record {i}: Invalid date format: {close_date}"
                        )
                else:
                    validation["date_format_issues"].append(
                        f"Record {i}: CloseDate not a string: {close_date} ({type(close_date)})"
                    )
            
            # Validate StageName
            if 'StageName' in record and record['StageName']:
                stage = record['StageName']
                if not isinstance(stage, str):
                    record_issues.append(f"Invalid stage name type: {stage} ({type(stage)})")
            
            # Validate Account relationship
            if 'Account' in record and record['Account']:
                account = record['Account']
                if isinstance(account, dict):
                    if 'Name' not in account:
                        record_issues.append("Account relationship missing Name field")
                else:
                    record_issues.append(f"Account should be a dict, got: {type(account)}")
            
            if record_issues:
                validation["data_format_issues"].extend([f"Record {i}: {issue}" for issue in record_issues])
        
        # Field presence analysis
        for field in required_fields + optional_fields:
            if field == 'Account':
                # Special handling for Account relationship
                present_count = sum(1 for record in records 
                                  if field in record and record[field] is not None 
                                  and isinstance(record[field], dict) 
                                  and 'Name' in record[field])
            else:
                present_count = sum(1 for record in records if field in record and record[field] is not None)
            
            validation["field_analysis"][field] = {
                "present_in_records": present_count,
                "percentage": (present_count / len(records) * 100) if records else 0
            }
        
        validation["success"] = (len(validation["data_format_issues"]) == 0 and 
                               len(validation["monetary_format_issues"]) == 0 and
                               len(validation["date_format_issues"]) == 0)
        
        return validation
    
    def _validate_contact_data(self, records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Validate contact data structure and content.
        **Validates: Requirements 4.3, 4.6, 4.7**
        """
        validation = {
            "total_records": len(records),
            "required_fields_present": 0,
            "data_format_issues": [],
            "email_format_issues": [],
            "field_analysis": {},
            "success": True
        }
        
        required_fields = ['Id', 'Name']
        optional_fields = ['Email', 'Phone', 'Title', 'Account']
        
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
        for i, record in enumerate(records):
            record_issues = []
            
            # Check required fields
            for field in required_fields:
                if field in record and record[field]:
                    validation["required_fields_present"] += 1
                else:
                    record_issues.append(f"Missing or empty required field: {field}")
            
            # Validate Email format
            if 'Email' in record and record['Email']:
                email = record['Email']
                if isinstance(email, str):
                    if not re.match(email_pattern, email):
                        validation["email_format_issues"].append(
                            f"Record {i}: Invalid email format: {email}"
                        )
                else:
                    validation["email_format_issues"].append(
                        f"Record {i}: Email not a string: {email} ({type(email)})"
                    )
            
            # Validate Title
            if 'Title' in record and record['Title']:
                title = record['Title']
                if not isinstance(title, str):
                    record_issues.append(f"Invalid title type: {title} ({type(title)})")
            
            # Validate Account relationship
            if 'Account' in record and record['Account']:
                account = record['Account']
                if isinstance(account, dict):
                    if 'Name' not in account:
                        record_issues.append("Account relationship missing Name field")
                else:
                    record_issues.append(f"Account should be a dict, got: {type(account)}")
            
            if record_issues:
                validation["data_format_issues"].extend([f"Record {i}: {issue}" for issue in record_issues])
        
        # Field presence analysis
        for field in required_fields + optional_fields:
            if field == 'Account':
                # Special handling for Account relationship
                present_count = sum(1 for record in records 
                                  if field in record and record[field] is not None 
                                  and isinstance(record[field], dict) 
                                  and 'Name' in record[field])
            else:
                present_count = sum(1 for record in records if field in record and record[field] is not None)
            
            validation["field_analysis"][field] = {
                "present_in_records": present_count,
                "percentage": (present_count / len(records) * 100) if records else 0
            }
        
        validation["success"] = (len(validation["data_format_issues"]) == 0 and 
                               len(validation["email_format_issues"]) == 0)
        
        return validation
    
    def _validate_soql_query_result(self, result: Dict[str, Any], query: str) -> Dict[str, Any]:
        """
        Validate SOQL query result structure and content.
        **Validates: Requirements 4.4**
        """
        validation = {
            "query": query[:100] + "..." if len(query) > 100 else query,
            "result_structure_valid": False,
            "has_records": False,
            "record_count": 0,
            "structure_issues": [],
            "success": False
        }
        
        # Check basic result structure
        if not isinstance(result, dict):
            validation["structure_issues"].append(f"Result is not a dict: {type(result)}")
            return validation
        
        # Check for expected keys
        expected_keys = ['success', 'totalSize', 'records']
        missing_keys = [key for key in expected_keys if key not in result]
        
        if missing_keys:
            validation["structure_issues"].append(f"Missing keys: {missing_keys}")
        else:
            validation["result_structure_valid"] = True
        
        # Check success status
        if 'success' in result:
            if not result['success']:
                validation["structure_issues"].append(f"Query failed: {result.get('error', 'Unknown error')}")
                return validation
        
        # Check records
        if 'records' in result:
            records = result['records']
            if isinstance(records, list):
                validation["record_count"] = len(records)
                validation["has_records"] = len(records) > 0
            else:
                validation["structure_issues"].append(f"Records is not a list: {type(records)}")
        
        # Check totalSize
        if 'totalSize' in result:
            total_size = result['totalSize']
            if not isinstance(total_size, int):
                validation["structure_issues"].append(f"totalSize is not an integer: {type(total_size)}")
            elif total_size < 0:
                validation["structure_issues"].append(f"totalSize is negative: {total_size}")
        
        validation["success"] = (validation["result_structure_valid"] and 
                               len(validation["structure_issues"]) == 0)
        
        return validation
    
    def _validate_search_result(self, result: Dict[str, Any], search_term: str) -> Dict[str, Any]:
        """
        Validate search result structure and content.
        **Validates: Requirements 4.5**
        """
        validation = {
            "search_term": search_term,
            "result_structure_valid": False,
            "has_results": False,
            "result_count": 0,
            "structure_issues": [],
            "success": False
        }
        
        # Check basic result structure
        if not isinstance(result, dict):
            validation["structure_issues"].append(f"Result is not a dict: {type(result)}")
            return validation
        
        # Search results can have different structures, check for common patterns
        if 'records' in result:
            records = result['records']
            if isinstance(records, list):
                validation["result_count"] = len(records)
                validation["has_results"] = len(records) > 0
                validation["result_structure_valid"] = True
            else:
                validation["structure_issues"].append(f"Records is not a list: {type(records)}")
        elif 'results' in result:
            results = result['results']
            if isinstance(results, list):
                validation["result_count"] = len(results)
                validation["has_results"] = len(results) > 0
                validation["result_structure_valid"] = True
            else:
                validation["structure_issues"].append(f"Results is not a list: {type(results)}")
        else:
            validation["structure_issues"].append("No 'records' or 'results' key found")
        
        validation["success"] = (validation["result_structure_valid"] and 
                               len(validation["structure_issues"]) == 0)
        
        return validation
    
    async def test_real_account_data_retrieval(self) -> Dict[str, Any]:
        """
        Test real account data retrieval and validation.
        **Validates: Requirements 4.1, 4.6, 4.7**
        """
        print("\n🏢 Testing Real Account Data Retrieval")
        print("=" * 60)
        
        test_results = {
            "operation": "get_accounts",
            "tests": [],
            "data_validation": {},
            "success": False,
            "errors": []
        }
        
        try:
            # Test 1: Basic account retrieval
            print("\n1. Testing basic account retrieval...")
            result1 = await self.crm_agent.get_accounts(service='salesforce', limit=10)
            
            print(f"   ✅ Basic account retrieval successful")
            print(f"   📊 Result type: {type(result1)}")
            print(f"   📊 Result keys: {list(result1.keys()) if isinstance(result1, dict) else 'Not a dict'}")
            
            # Extract records for validation
            records = []
            if isinstance(result1, dict):
                if 'records' in result1:
                    records = result1['records']
                elif 'result' in result1 and isinstance(result1['result'], list):
                    records = result1['result']
            
            print(f"   📊 Records found: {len(records)}")
            
            # Validate account data
            if records:
                validation = self._validate_account_data(records)
                test_results["data_validation"]["basic_accounts"] = validation
                
                print(f"   📋 Data validation:")
                print(f"      • Total records: {validation['total_records']}")
                print(f"      • Required fields present: {validation['required_fields_present']}")
                print(f"      • Data format issues: {len(validation['data_format_issues'])}")
                print(f"      • Monetary format issues: {len(validation['monetary_format_issues'])}")
                
                # Show field analysis
                print(f"   📊 Field presence analysis:")
                for field, analysis in validation["field_analysis"].items():
                    print(f"      • {field}: {analysis['present_in_records']}/{validation['total_records']} ({analysis['percentage']:.1f}%)")
                
                # Show sample data
                if records:
                    print(f"   📄 Sample account data:")
                    sample_record = records[0]
                    for key, value in sample_record.items():
                        if key == 'AnnualRevenue' and value is not None:
                            print(f"      • {key}: ${value:,}" if isinstance(value, (int, float)) else f"      • {key}: {value}")
                        else:
                            print(f"      • {key}: {value}")
            
            test_results["tests"].append({
                "test": "basic_account_retrieval",
                "passed": True,
                "record_count": len(records)
            })
            
            # Test 2: Account retrieval with filtering
            print("\n2. Testing account retrieval with name filtering...")
            
            # Try different account name filters
            filter_terms = ['Corp', 'Inc', 'LLC', 'Company', 'Global']
            
            for term in filter_terms:
                try:
                    result2 = await self.crm_agent.get_accounts(
                        service='salesforce',
                        account_name=term,
                        limit=5
                    )
                    
                    filtered_records = []
                    if isinstance(result2, dict):
                        if 'records' in result2:
                            filtered_records = result2['records']
                        elif 'result' in result2 and isinstance(result2['result'], list):
                            filtered_records = result2['result']
                    
                    print(f"   ✅ Filter '{term}' successful: {len(filtered_records)} records")
                    
                    test_results["tests"].append({
                        "test": f"account_filter_{term}",
                        "passed": True,
                        "record_count": len(filtered_records)
                    })
                    
                    # If we found records, validate one set
                    if filtered_records and "filtered_accounts" not in test_results["data_validation"]:
                        validation = self._validate_account_data(filtered_records)
                        test_results["data_validation"]["filtered_accounts"] = validation
                    
                except Exception as e:
                    print(f"   ⚠️ Filter '{term}' failed: {e}")
                    test_results["tests"].append({
                        "test": f"account_filter_{term}",
                        "passed": False,
                        "error": str(e)
                    })
            
            # Test 3: Different limit values
            print("\n3. Testing different limit values...")
            for limit in [1, 5, 15, 25]:
                try:
                    result3 = await self.crm_agent.get_accounts(
                        service='salesforce',
                        limit=limit
                    )
                    
                    limit_records = []
                    if isinstance(result3, dict):
                        if 'records' in result3:
                            limit_records = result3['records']
                        elif 'result' in result3 and isinstance(result3['result'], list):
                            limit_records = result3['result']
                    
                    print(f"   ✅ Limit {limit} successful: {len(limit_records)} records")
                    
                    test_results["tests"].append({
                        "test": f"account_limit_{limit}",
                        "passed": True,
                        "record_count": len(limit_records),
                        "requested_limit": limit
                    })
                    
                except Exception as e:
                    print(f"   ❌ Limit {limit} failed: {e}")
                    test_results["tests"].append({
                        "test": f"account_limit_{limit}",
                        "passed": False,
                        "error": str(e)
                    })
            
            # Determine overall success
            failed_tests = [t for t in test_results["tests"] if not t.get("passed", False)]
            validation_failures = [v for v in test_results["data_validation"].values() if not v.get("success", False)]
            
            test_results["success"] = len(failed_tests) == 0 and len(validation_failures) == 0
            
            if failed_tests:
                test_results["errors"].extend([f"Test failed: {t['test']}" for t in failed_tests])
            
            if validation_failures:
                test_results["errors"].append("Data validation failures detected")
            
        except Exception as e:
            error_msg = f"Account data retrieval test failed: {e}"
            logger.error(error_msg)
            test_results["errors"].append(error_msg)
            test_results["success"] = False
        
        return test_results
    
    async def test_real_opportunity_data_retrieval(self) -> Dict[str, Any]:
        """
        Test real opportunity data retrieval and validation.
        **Validates: Requirements 4.2, 4.6, 4.7**
        """
        print("\n💼 Testing Real Opportunity Data Retrieval")
        print("=" * 60)
        
        test_results = {
            "operation": "get_opportunities",
            "tests": [],
            "data_validation": {},
            "success": False,
            "errors": []
        }
        
        try:
            # Test 1: Basic opportunity retrieval
            print("\n1. Testing basic opportunity retrieval...")
            result1 = await self.crm_agent.get_opportunities(service='salesforce', limit=10)
            
            print(f"   ✅ Basic opportunity retrieval successful")
            print(f"   📊 Result type: {type(result1)}")
            
            # Extract records for validation
            records = []
            if isinstance(result1, dict):
                if 'records' in result1:
                    records = result1['records']
                elif 'result' in result1 and isinstance(result1['result'], list):
                    records = result1['result']
            
            print(f"   📊 Records found: {len(records)}")
            
            # Validate opportunity data
            if records:
                validation = self._validate_opportunity_data(records)
                test_results["data_validation"]["basic_opportunities"] = validation
                
                print(f"   📋 Data validation:")
                print(f"      • Total records: {validation['total_records']}")
                print(f"      • Data format issues: {len(validation['data_format_issues'])}")
                print(f"      • Monetary format issues: {len(validation['monetary_format_issues'])}")
                print(f"      • Date format issues: {len(validation['date_format_issues'])}")
                
                # Show sample data with formatting
                if records:
                    print(f"   📄 Sample opportunity data:")
                    sample_record = records[0]
                    for key, value in sample_record.items():
                        if key == 'Amount' and value is not None:
                            print(f"      • {key}: ${value:,}" if isinstance(value, (int, float)) else f"      • {key}: {value}")
                        elif key == 'CloseDate' and value:
                            print(f"      • {key}: {value} (Date format)")
                        elif key == 'Account' and isinstance(value, dict):
                            print(f"      • {key}: {value.get('Name', 'N/A')} (Related Account)")
                        else:
                            print(f"      • {key}: {value}")
            
            test_results["tests"].append({
                "test": "basic_opportunity_retrieval",
                "passed": True,
                "record_count": len(records)
            })
            
            # Test 2: Opportunity retrieval with stage filtering
            print("\n2. Testing opportunity retrieval with stage filtering...")
            
            # Common Salesforce opportunity stages
            stages = ['Prospecting', 'Qualification', 'Needs Analysis', 'Value Proposition', 
                     'Id. Decision Makers', 'Perception Analysis', 'Proposal/Price Quote', 
                     'Negotiation/Review', 'Closed Won', 'Closed Lost']
            
            for stage in stages[:5]:  # Test first 5 stages
                try:
                    result2 = await self.crm_agent.get_opportunities(
                        service='salesforce',
                        stage=stage,
                        limit=5
                    )
                    
                    stage_records = []
                    if isinstance(result2, dict):
                        if 'records' in result2:
                            stage_records = result2['records']
                        elif 'result' in result2 and isinstance(result2['result'], list):
                            stage_records = result2['result']
                    
                    print(f"   ✅ Stage '{stage}' successful: {len(stage_records)} records")
                    
                    test_results["tests"].append({
                        "test": f"opportunity_stage_{stage.replace('/', '_').replace(' ', '_').lower()}",
                        "passed": True,
                        "record_count": len(stage_records)
                    })
                    
                    # Validate stage filtering worked
                    if stage_records:
                        for record in stage_records:
                            if 'StageName' in record and record['StageName'] != stage:
                                print(f"   ⚠️ Stage filter may not be working: expected '{stage}', got '{record['StageName']}'")
                    
                except Exception as e:
                    print(f"   ⚠️ Stage '{stage}' failed: {e}")
                    test_results["tests"].append({
                        "test": f"opportunity_stage_{stage.replace('/', '_').replace(' ', '_').lower()}",
                        "passed": False,
                        "error": str(e)
                    })
            
            # Determine overall success
            failed_tests = [t for t in test_results["tests"] if not t.get("passed", False)]
            validation_failures = [v for v in test_results["data_validation"].values() if not v.get("success", False)]
            
            test_results["success"] = len(failed_tests) == 0 and len(validation_failures) == 0
            
        except Exception as e:
            error_msg = f"Opportunity data retrieval test failed: {e}"
            logger.error(error_msg)
            test_results["errors"].append(error_msg)
            test_results["success"] = False
        
        return test_results
    
    async def test_real_contact_data_retrieval(self) -> Dict[str, Any]:
        """
        Test real contact data retrieval and validation.
        **Validates: Requirements 4.3, 4.6, 4.7**
        """
        print("\n👥 Testing Real Contact Data Retrieval")
        print("=" * 60)
        
        test_results = {
            "operation": "get_contacts",
            "tests": [],
            "data_validation": {},
            "success": False,
            "errors": []
        }
        
        try:
            # Test 1: Basic contact retrieval
            print("\n1. Testing basic contact retrieval...")
            result1 = await self.crm_agent.get_contacts(service='salesforce', limit=10)
            
            print(f"   ✅ Basic contact retrieval successful")
            
            # Extract records for validation
            records = []
            if isinstance(result1, dict):
                if 'records' in result1:
                    records = result1['records']
                elif 'result' in result1 and isinstance(result1['result'], list):
                    records = result1['result']
            
            print(f"   📊 Records found: {len(records)}")
            
            # Validate contact data
            if records:
                validation = self._validate_contact_data(records)
                test_results["data_validation"]["basic_contacts"] = validation
                
                print(f"   📋 Data validation:")
                print(f"      • Total records: {validation['total_records']}")
                print(f"      • Data format issues: {len(validation['data_format_issues'])}")
                print(f"      • Email format issues: {len(validation['email_format_issues'])}")
                
                # Show sample data
                if records:
                    print(f"   📄 Sample contact data:")
                    sample_record = records[0]
                    for key, value in sample_record.items():
                        if key == 'Email' and value:
                            print(f"      • {key}: {value} (Email format)")
                        elif key == 'Account' and isinstance(value, dict):
                            print(f"      • {key}: {value.get('Name', 'N/A')} (Related Account)")
                        else:
                            print(f"      • {key}: {value}")
            
            test_results["tests"].append({
                "test": "basic_contact_retrieval",
                "passed": True,
                "record_count": len(records)
            })
            
            # Test 2: Contact retrieval with account filtering
            print("\n2. Testing contact retrieval with account filtering...")
            
            # Get some account names from previous account test if available
            account_filters = ['Corp', 'Inc', 'Global', 'Tech', 'Solutions']
            
            for account_name in account_filters[:3]:  # Test first 3
                try:
                    result2 = await self.crm_agent.get_contacts(
                        service='salesforce',
                        account_name=account_name,
                        limit=5
                    )
                    
                    filtered_records = []
                    if isinstance(result2, dict):
                        if 'records' in result2:
                            filtered_records = result2['records']
                        elif 'result' in result2 and isinstance(result2['result'], list):
                            filtered_records = result2['result']
                    
                    print(f"   ✅ Account filter '{account_name}' successful: {len(filtered_records)} records")
                    
                    test_results["tests"].append({
                        "test": f"contact_account_filter_{account_name.lower()}",
                        "passed": True,
                        "record_count": len(filtered_records)
                    })
                    
                except Exception as e:
                    print(f"   ⚠️ Account filter '{account_name}' failed: {e}")
                    test_results["tests"].append({
                        "test": f"contact_account_filter_{account_name.lower()}",
                        "passed": False,
                        "error": str(e)
                    })
            
            # Determine overall success
            failed_tests = [t for t in test_results["tests"] if not t.get("passed", False)]
            validation_failures = [v for v in test_results["data_validation"].values() if not v.get("success", False)]
            
            test_results["success"] = len(failed_tests) == 0 and len(validation_failures) == 0
            
        except Exception as e:
            error_msg = f"Contact data retrieval test failed: {e}"
            logger.error(error_msg)
            test_results["errors"].append(error_msg)
            test_results["success"] = False
        
        return test_results
    
    async def test_real_soql_query_execution(self) -> Dict[str, Any]:
        """
        Test real SOQL query execution and validation.
        **Validates: Requirements 4.4**
        """
        print("\n📊 Testing Real SOQL Query Execution")
        print("=" * 60)
        
        test_results = {
            "operation": "run_soql_query",
            "tests": [],
            "query_validations": {},
            "success": False,
            "errors": []
        }
        
        try:
            # Test queries with increasing complexity
            test_queries = [
                {
                    "name": "simple_account_query",
                    "query": "SELECT Id, Name FROM Account LIMIT 5",
                    "description": "Simple account query"
                },
                {
                    "name": "account_with_revenue",
                    "query": "SELECT Id, Name, Industry, AnnualRevenue FROM Account WHERE AnnualRevenue > 0 LIMIT 10",
                    "description": "Account query with revenue filter"
                },
                {
                    "name": "opportunity_with_amount",
                    "query": "SELECT Id, Name, StageName, Amount, CloseDate FROM Opportunity WHERE Amount > 10000 LIMIT 8",
                    "description": "Opportunity query with amount filter"
                },
                {
                    "name": "contact_with_account",
                    "query": "SELECT Id, Name, Email, Title, Account.Name FROM Contact WHERE Email != null LIMIT 7",
                    "description": "Contact query with account relationship"
                },
                {
                    "name": "aggregate_query",
                    "query": "SELECT COUNT(Id) RecordCount FROM Account",
                    "description": "Aggregate count query"
                }
            ]
            
            for query_test in test_queries:
                print(f"\n   Testing {query_test['description']}...")
                
                try:
                    result = await self.crm_agent.run_soql_query(
                        query=query_test['query'],
                        service='salesforce'
                    )
                    
                    print(f"   ✅ Query successful")
                    print(f"   📊 Result type: {type(result)}")
                    
                    # Validate query result
                    validation = self._validate_soql_query_result(result, query_test['query'])
                    test_results["query_validations"][query_test['name']] = validation
                    
                    print(f"   📋 Query validation:")
                    print(f"      • Structure valid: {validation['result_structure_valid']}")
                    print(f"      • Has records: {validation['has_records']}")
                    print(f"      • Record count: {validation['record_count']}")
                    
                    if validation['structure_issues']:
                        print(f"      • Issues: {validation['structure_issues']}")
                    
                    # Show sample data for non-aggregate queries
                    if (validation['has_records'] and 
                        isinstance(result, dict) and 
                        'records' in result and 
                        result['records'] and
                        'COUNT' not in query_test['query'].upper()):
                        
                        print(f"   📄 Sample record:")
                        sample_record = result['records'][0]
                        for key, value in sample_record.items():
                            if key in ['Amount', 'AnnualRevenue'] and value is not None:
                                print(f"      • {key}: ${value:,}" if isinstance(value, (int, float)) else f"      • {key}: {value}")
                            else:
                                print(f"      • {key}: {value}")
                    
                    test_results["tests"].append({
                        "test": query_test['name'],
                        "passed": True,
                        "query": query_test['query'],
                        "record_count": validation['record_count']
                    })
                    
                except Exception as e:
                    print(f"   ❌ Query failed: {e}")
                    test_results["tests"].append({
                        "test": query_test['name'],
                        "passed": False,
                        "query": query_test['query'],
                        "error": str(e)
                    })
            
            # Determine overall success
            failed_tests = [t for t in test_results["tests"] if not t.get("passed", False)]
            validation_failures = [v for v in test_results["query_validations"].values() if not v.get("success", False)]
            
            test_results["success"] = len(failed_tests) == 0 and len(validation_failures) == 0
            
        except Exception as e:
            error_msg = f"SOQL query execution test failed: {e}"
            logger.error(error_msg)
            test_results["errors"].append(error_msg)
            test_results["success"] = False
        
        return test_results
    
    async def test_real_search_operations(self) -> Dict[str, Any]:
        """
        Test real search operations and validation.
        **Validates: Requirements 4.5**
        """
        print("\n🔍 Testing Real Search Operations")
        print("=" * 60)
        
        test_results = {
            "operation": "search_records",
            "tests": [],
            "search_validations": {},
            "success": False,
            "errors": []
        }
        
        try:
            # Test different search terms
            search_tests = [
                {
                    "name": "company_search",
                    "search_term": "Corp",
                    "description": "Search for companies with 'Corp'"
                },
                {
                    "name": "technology_search",
                    "search_term": "Technology",
                    "description": "Search for technology-related records"
                },
                {
                    "name": "global_search",
                    "search_term": "Global",
                    "description": "Search for global companies"
                },
                {
                    "name": "inc_search",
                    "search_term": "Inc",
                    "description": "Search for incorporated companies"
                }
            ]
            
            for search_test in search_tests:
                print(f"\n   Testing {search_test['description']}...")
                
                try:
                    result = await self.crm_agent.search_records(
                        search_term=search_test['search_term'],
                        service='salesforce'
                    )
                    
                    print(f"   ✅ Search successful")
                    print(f"   📊 Result type: {type(result)}")
                    
                    # Validate search result
                    validation = self._validate_search_result(result, search_test['search_term'])
                    test_results["search_validations"][search_test['name']] = validation
                    
                    print(f"   📋 Search validation:")
                    print(f"      • Structure valid: {validation['result_structure_valid']}")
                    print(f"      • Has results: {validation['has_results']}")
                    print(f"      • Result count: {validation['result_count']}")
                    
                    if validation['structure_issues']:
                        print(f"      • Issues: {validation['structure_issues']}")
                    
                    test_results["tests"].append({
                        "test": search_test['name'],
                        "passed": True,
                        "search_term": search_test['search_term'],
                        "result_count": validation['result_count']
                    })
                    
                except Exception as e:
                    print(f"   ❌ Search failed: {e}")
                    test_results["tests"].append({
                        "test": search_test['name'],
                        "passed": False,
                        "search_term": search_test['search_term'],
                        "error": str(e)
                    })
            
            # Test search with object filtering (if supported)
            print(f"\n   Testing search with object filtering...")
            try:
                result = await self.crm_agent.search_records(
                    search_term="Test",
                    service='salesforce',
                    objects=['Account', 'Contact']
                )
                
                print(f"   ✅ Object filtering search successful")
                
                validation = self._validate_search_result(result, "Test")
                test_results["search_validations"]["object_filtering"] = validation
                
                test_results["tests"].append({
                    "test": "object_filtering_search",
                    "passed": True,
                    "search_term": "Test",
                    "objects": ['Account', 'Contact'],
                    "result_count": validation['result_count']
                })
                
            except Exception as e:
                print(f"   ⚠️ Object filtering search failed: {e}")
                test_results["tests"].append({
                    "test": "object_filtering_search",
                    "passed": False,
                    "error": str(e)
                })
            
            # Determine overall success
            failed_tests = [t for t in test_results["tests"] if not t.get("passed", False)]
            validation_failures = [v for v in test_results["search_validations"].values() if not v.get("success", False)]
            
            test_results["success"] = len(failed_tests) == 0 and len(validation_failures) == 0
            
        except Exception as e:
            error_msg = f"Search operations test failed: {e}"
            logger.error(error_msg)
            test_results["errors"].append(error_msg)
            test_results["success"] = False
        
        return test_results
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all real data retrieval tests."""
        print("🚀 Starting Real Salesforce Data Retrieval Test Suite")
        print("=" * 80)
        print(f"⏰ Started at: {datetime.now().isoformat()}")
        
        # Initialize the agent
        if not await self.initialize():
            return {"success": False, "error": "Failed to initialize CRM agent"}
        
        # Run all data retrieval tests
        self.test_results = {
            "accounts": await self.test_real_account_data_retrieval(),
            "opportunities": await self.test_real_opportunity_data_retrieval(),
            "contacts": await self.test_real_contact_data_retrieval(),
            "soql_queries": await self.test_real_soql_query_execution(),
            "search_operations": await self.test_real_search_operations()
        }
        
        return self.test_results
    
    def generate_summary(self) -> Dict[str, Any]:
        """Generate a comprehensive test summary."""
        if not self.test_results:
            return {"error": "No test results available"}
        
        summary = {
            "total_operations_tested": len(self.test_results),
            "successful_operations": 0,
            "failed_operations": 0,
            "data_validation_summary": {},
            "total_records_retrieved": 0,
            "data_quality_issues": [],
            "overall_success": True,
            "recommendations": []
        }
        
        # Analyze operation results
        for operation, results in self.test_results.items():
            if results.get("success", False):
                summary["successful_operations"] += 1
            else:
                summary["failed_operations"] += 1
                summary["overall_success"] = False
            
            # Count total records retrieved
            for test in results.get("tests", []):
                if "record_count" in test:
                    summary["total_records_retrieved"] += test["record_count"]
            
            # Analyze data validation results
            data_validations = results.get("data_validation", {})
            query_validations = results.get("query_validations", {})
            search_validations = results.get("search_validations", {})
            
            all_validations = {**data_validations, **query_validations, **search_validations}
            
            if all_validations:
                validation_summary = {
                    "total_validations": len(all_validations),
                    "successful_validations": len([v for v in all_validations.values() if v.get("success", False)]),
                    "issues_found": []
                }
                
                for validation_name, validation in all_validations.items():
                    if not validation.get("success", False):
                        issues = []
                        issues.extend(validation.get("data_format_issues", []))
                        issues.extend(validation.get("monetary_format_issues", []))
                        issues.extend(validation.get("date_format_issues", []))
                        issues.extend(validation.get("email_format_issues", []))
                        issues.extend(validation.get("structure_issues", []))
                        
                        if issues:
                            validation_summary["issues_found"].extend(issues)
                            summary["data_quality_issues"].extend(issues)
                
                summary["data_validation_summary"][operation] = validation_summary
        
        # Generate recommendations
        if summary["failed_operations"] > 0:
            summary["recommendations"].append("Fix failed operations before proceeding")
        
        if summary["data_quality_issues"]:
            summary["recommendations"].append("Address data quality issues found during validation")
        
        if summary["total_records_retrieved"] == 0:
            summary["recommendations"].append("No records retrieved - check Salesforce org connectivity and data")
        
        if summary["overall_success"]:
            summary["recommendations"].append("All real data retrieval tests passed - ready for next phase")
        
        return summary


async def main():
    """Main test execution."""
    tester = RealSalesforceDataTester()
    
    # Run all tests
    results = await tester.run_all_tests()
    
    # Generate and display summary
    print("\n" + "=" * 80)
    print("📋 REAL DATA RETRIEVAL TEST SUMMARY")
    print("=" * 80)
    
    summary = tester.generate_summary()
    
    if "error" in summary:
        print(f"❌ {summary['error']}")
        return False
    
    print(f"📊 Operations Tested: {summary['total_operations_tested']}")
    print(f"✅ Successful Operations: {summary['successful_operations']}")
    print(f"❌ Failed Operations: {summary['failed_operations']}")
    print(f"📈 Total Records Retrieved: {summary['total_records_retrieved']}")
    
    print(f"\n🔍 Data Validation Summary:")
    for operation, validation_info in summary["data_validation_summary"].items():
        total_val = validation_info["total_validations"]
        success_val = validation_info["successful_validations"]
        status = "✅" if success_val == total_val else "⚠️"
        print(f"   {status} {operation}: {success_val}/{total_val} validations passed")
        
        if validation_info["issues_found"]:
            print(f"      Issues: {len(validation_info['issues_found'])} data quality issues")
    
    if summary["data_quality_issues"]:
        print(f"\n⚠️ Data Quality Issues Found:")
        for issue in summary["data_quality_issues"][:10]:  # Show first 10 issues
            print(f"   • {issue}")
        if len(summary["data_quality_issues"]) > 10:
            print(f"   ... and {len(summary['data_quality_issues']) - 10} more issues")
    
    print(f"\n📝 Recommendations:")
    for rec in summary["recommendations"]:
        print(f"   • {rec}")
    
    overall_status = "✅ PASSED" if summary["overall_success"] else "❌ FAILED"
    print(f"\n🎯 Overall Result: {overall_status}")
    
    if summary["overall_success"]:
        print("\n🎉 All real Salesforce data retrieval tests passed!")
        print("   ✓ Account data retrieval and validation successful")
        print("   ✓ Opportunity data retrieval and validation successful")
        print("   ✓ Contact data retrieval and validation successful")
        print("   ✓ SOQL query execution and validation successful")
        print("   ✓ Search operations and validation successful")
        print("   ✓ Data formatting for monetary amounts and dates validated")
        print("\n   Ready to proceed to AI Planner integration testing (Task 6)")
    else:
        print("\n⚠️ Some real data retrieval tests failed.")
        print("   Please address the issues before proceeding to the next phase.")
    
    return summary["overall_success"]


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)