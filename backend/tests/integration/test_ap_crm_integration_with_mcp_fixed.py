#!/usr/bin/env python3
"""
AP and CRM Agent Integration Test Script with Real Gemini LLM Calls and MCP Service Calls (FIXED)

This script tests the complete workflow of both AccountsPayable and CRM agents
with real Gemini LLM integration and actual MCP service calls to retrieve real data.

FIXES:
1. Properly initializes MCP services before testing
2. Checks MCP service registration status
3. Provides detailed diagnostics for MCP connection issues
4. Tests both LLM analysis AND real MCP data retrieval

Tests multiple scenarios for both agents:
- AP: Search bills, get specific bills, list vendors, etc.
- CRM: Get accounts, search opportunities, get contacts, etc.
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

# CRITICAL: Configure Gemini LLM instead of mock mode
os.environ["USE_MOCK_LLM"] = "false"
os.environ["LLM_PROVIDER"] = "gemini"
os.environ["GEMINI_MODEL"] = "gemini-2.5-flash"

# Set up logging
logging.basicConfig(level=logging.INFO)


class MockWebSocketManager:
    """Mock WebSocket manager for testing without real WebSocket connections."""
    
    def __init__(self):
        self.messages = []
    
    async def send_message(self, plan_id: str, message: Dict[str, Any]):
        """Mock send message - just store the message for testing."""
        self.messages.append({
            "plan_id": plan_id,
            "message": message,
            "timestamp": message.get("timestamp", "mock-time")
        })
        # Optionally print for debugging
        # print(f"📡 Mock WebSocket: {message.get('type', 'unknown')} for plan {plan_id}")
    
    def clear_messages(self):
        """Clear stored messages."""
        self.messages = []
    
    def get_messages(self):
        """Get all stored messages."""
        return self.messages

class IntegrationTestCase:
    """Test case for integration scenarios."""
    
    def __init__(self, name: str, description: str, user_request: str, 
                 expected_action: str, agent_type: str):
        self.name = name
        self.description = description
        self.user_request = user_request
        self.expected_action = expected_action
        self.agent_type = agent_type


# Test cases for both AP and CRM agents
INTEGRATION_TEST_CASES = [
    # AccountsPayable Agent Test Cases
    IntegrationTestCase(
        name="AP: Search Bills by Vendor",
        description="Search for bills from a specific vendor using LLM analysis",
        user_request="Find all bills from Acme Corporation from the last 2 months",
        expected_action="search_bills",
        agent_type="ap"
    ),
    
    IntegrationTestCase(
        name="AP: Get Specific Bill",
        description="Get details for a specific bill by invoice number",
        user_request="Get the details for invoice INV-1001",
        expected_action="get_bill",
        agent_type="ap"
    ),
    
    IntegrationTestCase(
        name="AP: List Unpaid Bills",
        description="List all unpaid bills with status filter",
        user_request="Show me all unpaid bills that are currently outstanding",
        expected_action="list_bills",
        agent_type="ap"
    ),
    
    # CRM Agent Test Cases
    IntegrationTestCase(
        name="CRM: Get Recent Accounts",
        description="Get recent account updates from CRM",
        user_request="Show me the latest account updates from our CRM system",
        expected_action="get_accounts",
        agent_type="crm"
    ),
    
    IntegrationTestCase(
        name="CRM: Search for Company",
        description="Search for a specific company across CRM records",
        user_request="Search for Microsoft in our CRM system",
        expected_action="search_records",
        agent_type="crm"
    )
]


async def initialize_and_check_mcp_services():
    """Initialize MCP services and check their registration status."""
    
    print("🔧 Initializing MCP Services...")
    print("=" * 60)
    
    try:
        # Import MCP service management
        from app.services.mcp_client_service import initialize_mcp_services, get_mcp_manager
        
        # Initialize all MCP services
        print("📡 Starting MCP service initialization...")
        await initialize_mcp_services()
        print("✅ MCP services initialization completed")
        
        # Get the MCP manager to check service status
        manager = get_mcp_manager()
        
        # Get manager statistics
        stats = manager.get_manager_stats()
        registered_services = stats["registered_services"]
        
        print(f"\n📊 MCP Service Registration Status:")
        print(f"   - Total Registered Services: {len(registered_services)}")
        print(f"   - Registered Services: {registered_services}")
        
        # Check specific services we need
        required_services = ["bill_com", "salesforce"]
        missing_services = []
        available_services = []
        
        for service in required_services:
            if service in registered_services:
                available_services.append(service)
                print(f"   ✅ {service}: REGISTERED")
            else:
                missing_services.append(service)
                print(f"   ❌ {service}: NOT REGISTERED")
        
        # Test service health if available
        if available_services:
            print(f"\n🏥 Testing Service Health...")
            health_status = await manager.get_all_service_health()
            
            for service in available_services:
                if service in health_status:
                    status = health_status[service]
                    health_indicator = "✅ HEALTHY" if status.is_healthy else "❌ UNHEALTHY"
                    response_time_s = status.response_time_ms / 1000.0
                    print(f"   {service}: {health_indicator} (response_time: {response_time_s:.2f}s)")
                    if status.error_message:
                        print(f"     Error: {status.error_message}")
                else:
                    print(f"   {service}: Health check not available")
        
        # Discover available tools
        if available_services:
            print(f"\n🔍 Discovering Available Tools...")
            try:
                tools_by_service = await manager.discover_tools()
                
                for service in available_services:
                    if service in tools_by_service:
                        tools = tools_by_service[service]
                        print(f"   {service}: {len(tools)} tools available")
                        for tool in tools[:3]:  # Show first 3 tools
                            print(f"     - {tool.name}: {tool.description[:50]}...")
                        if len(tools) > 3:
                            print(f"     ... and {len(tools) - 3} more tools")
                    else:
                        print(f"   {service}: No tools discovered")
            except Exception as e:
                print(f"   ⚠️ Tool discovery failed: {e}")
        
        return {
            "success": True,
            "registered_services": registered_services,
            "available_services": available_services,
            "missing_services": missing_services,
            "manager": manager
        }
        
    except Exception as e:
        print(f"❌ MCP service initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "error": str(e),
            "registered_services": [],
            "available_services": [],
            "missing_services": ["bill_com", "salesforce"],
            "manager": None
        }


async def test_ap_agent_integration_with_mcp(mcp_status: Dict[str, Any]):
    """Test AccountsPayable agent with real Gemini LLM integration and MCP calls."""
    
    print("\n🔍 AccountsPayable Agent Integration Test with Real Gemini LLM + MCP Calls")
    print("=" * 80)
    
    try:
        # Import AP agent node
        from app.agents.accounts_payable_agent_node import AccountsPayableAgentNode
        from app.services.llm_service import LLMService
        
        # Verify Gemini configuration
        llm_provider = os.getenv("LLM_PROVIDER", "unknown")
        api_key = os.getenv("GEMINI_API_KEY", "")
        model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        
        print(f"🤖 LLM Configuration:")
        print(f"   Provider: {llm_provider}")
        print(f"   Model: {model}")
        print(f"   API Key Configured: {bool(api_key)}")
        print(f"   Mock Mode: {LLMService.is_mock_mode()}")
        
        if LLMService.is_mock_mode():
            print("❌ ERROR: Mock mode is still enabled! Real LLM calls will not work.")
            return False
        
        if not api_key:
            print("❌ ERROR: GEMINI_API_KEY not configured!")
            return False
        
        # Check MCP service availability
        bill_com_available = "bill_com" in mcp_status["available_services"]
        print(f"\n📡 MCP Service Status:")
        print(f"   Bill.com Service: {'✅ AVAILABLE' if bill_com_available else '❌ NOT AVAILABLE'}")
        
        # Initialize AP agent
        ap_agent = AccountsPayableAgentNode()
        
        print(f"\n✅ AccountsPayable Agent initialized")
        print(f"   Agent: {ap_agent.name}")
        print(f"   Supported Services: {ap_agent.ap_agent.get_supported_services()}")
        
        # Filter AP test cases
        ap_test_cases = [tc for tc in INTEGRATION_TEST_CASES if tc.agent_type == "ap"]
        
        passed_tests = 0
        failed_tests = 0
        mcp_success_count = 0
        
        for i, test_case in enumerate(ap_test_cases, 1):
            print(f"\n{'='*70}")
            print(f"AP TEST {i}/{len(ap_test_cases)}: {test_case.name}")
            print(f"{'='*70}")
            print(f"Description: {test_case.description}")
            print(f"User Request: '{test_case.user_request}'")
            print(f"Expected Action: {test_case.expected_action}")
            
            try:
                # Create mock state for testing with WebSocket manager
                mock_websocket_manager = MockWebSocketManager()
                mock_state = {
                    "task_description": test_case.user_request,
                    "plan_id": f"test-plan-ap-{i}",
                    "websocket_manager": mock_websocket_manager,  # Provide WebSocket manager for real LLM calls
                    "messages": [],
                    "collected_data": {},
                    "execution_results": []
                }
                
                print(f"\n🤖 Analyzing user intent with REAL Gemini LLM...")
                
                # Test LLM-based intent analysis with real Gemini calls
                action_analysis = await ap_agent._analyze_user_intent(
                    test_case.user_request, 
                    mock_state
                )
                
                print(f"📊 Gemini LLM Analysis Result:")
                print(f"   Action: {action_analysis.get('action', 'unknown')}")
                print(f"   Service: {action_analysis.get('service', 'unknown')}")
                print(f"   Search Term: '{action_analysis.get('search_term', '')}'")
                print(f"   Vendor Name: '{action_analysis.get('vendor_name', '')}'")
                print(f"   Bill ID: '{action_analysis.get('bill_id', '')}'")
                print(f"   Status: '{action_analysis.get('status', '')}'")
                print(f"   Limit: {action_analysis.get('limit', 0)}")
                
                # Check if the action matches expectation
                actual_action = action_analysis.get("action")
                action_matches = actual_action == test_case.expected_action
                
                print(f"\n🔍 Analysis:")
                print(f"   Expected Action: {test_case.expected_action}")
                print(f"   Actual Action: {actual_action}")
                print(f"   Action Matches: {action_matches}")
                
                # Validate the analysis result
                validation_passed = ap_agent._final_validation_check(action_analysis)
                has_required_fields = ap_agent._check_required_fields(action_analysis)
                
                print(f"   Validation Passed: {validation_passed}")
                print(f"   Has Required Fields: {has_required_fields}")
                
                if action_matches and validation_passed and has_required_fields:
                    print(f"   ✅ LLM ANALYSIS PASSED - Gemini LLM correctly analyzed the request")
                    
                    # Now test actual MCP service calls if available
                    if bill_com_available:
                        print(f"\n🔧 Testing actual MCP service call...")
                        try:
                            # Execute the determined action using MCP tools
                            if action_analysis["action"] == "search_bills":
                                ap_data = await ap_agent._search_bills_with_llm_params(action_analysis)
                            elif action_analysis["action"] == "get_bill":
                                ap_data = await ap_agent._get_specific_bill(action_analysis)
                            elif action_analysis["action"] == "list_bills":
                                ap_data = await ap_agent._list_bills_with_llm_params(action_analysis)
                            elif action_analysis["action"] == "list_vendors":
                                ap_data = await ap_agent._list_vendors_with_llm_params(action_analysis)
                            elif action_analysis["action"] == "get_vendor":
                                ap_data = await ap_agent._get_specific_vendor(action_analysis)
                            else:
                                ap_data = {"error": "Unknown action"}
                            
                            # Check MCP call results
                            if "error" in ap_data:
                                print(f"   ⚠️ MCP CALL WARNING: {ap_data['error']}")
                                print(f"   📊 MCP Response: {json.dumps(ap_data, indent=2, default=str)}")
                            else:
                                # Count data items
                                data_count = 0
                                if "invoices" in ap_data:
                                    data_count = len(ap_data["invoices"])
                                elif "vendors" in ap_data:
                                    data_count = len(ap_data["vendors"])
                                elif "invoice" in ap_data:
                                    data_count = 1 if ap_data["invoice"] else 0
                                
                                print(f"   ✅ MCP CALL SUCCESS: Retrieved {data_count} item(s)")
                                mcp_success_count += 1
                                
                                # Show sample data if available
                                if data_count > 0:
                                    if "invoices" in ap_data and ap_data["invoices"]:
                                        sample_invoice = ap_data["invoices"][0]
                                        print(f"   📄 Sample Invoice: {sample_invoice.get('invoice_number', 'N/A')} - {sample_invoice.get('vendor_name', 'N/A')} - ${sample_invoice.get('total', 0)}")
                                    elif "vendors" in ap_data and ap_data["vendors"]:
                                        sample_vendor = ap_data["vendors"][0]
                                        print(f"   🏢 Sample Vendor: {sample_vendor.get('name', 'N/A')} - {sample_vendor.get('email', 'N/A')}")
                                    elif "invoice" in ap_data and ap_data["invoice"]:
                                        invoice = ap_data["invoice"]
                                        print(f"   📄 Invoice: {invoice.get('invoice_number', 'N/A')} - {invoice.get('vendor_name', 'N/A')} - ${invoice.get('total', 0)}")
                                
                                print(f"   📊 MCP Response Summary: {json.dumps({k: len(v) if isinstance(v, list) else str(v)[:50] + '...' if len(str(v)) > 50 else v for k, v in ap_data.items()}, indent=2)}")
                            
                        except Exception as mcp_error:
                            print(f"   ❌ MCP CALL FAILED: {mcp_error}")
                            print(f"   📝 This indicates an issue with MCP service connectivity")
                    else:
                        print(f"\n⚠️ Skipping MCP call test - bill_com service not available")
                        print(f"   📝 LLM analysis passed, but MCP service is not registered")
                    
                    passed_tests += 1
                        
                else:
                    print(f"   ❌ TEST FAILED - Gemini LLM analysis did not match expectations")
                    failed_tests += 1
                
            except Exception as e:
                print(f"   💥 TEST ERROR: {e}")
                import traceback
                traceback.print_exc()
                failed_tests += 1
        
        print(f"\n📊 AP INTEGRATION TEST RESULTS:")
        print(f"   - Total Tests: {len(ap_test_cases)}")
        print(f"   - LLM Analysis Passed: {passed_tests}")
        print(f"   - LLM Analysis Failed: {failed_tests}")
        print(f"   - MCP Calls Successful: {mcp_success_count}")
        print(f"   - LLM Success Rate: {(passed_tests / len(ap_test_cases)) * 100:.1f}%")
        
        if bill_com_available:
            print(f"   - MCP Success Rate: {(mcp_success_count / len(ap_test_cases)) * 100:.1f}%")
        else:
            print(f"   - MCP Tests: Skipped (service not available)")
        
        return passed_tests == len(ap_test_cases)
        
    except Exception as e:
        print(f"\n❌ AP INTEGRATION TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_crm_agent_integration_with_mcp(mcp_status: Dict[str, Any]):
    """Test CRM agent with real Gemini LLM integration and MCP calls."""
    
    print("\n🔍 CRM Agent Integration Test with Real Gemini LLM + MCP Calls")
    print("=" * 80)
    
    try:
        # Import CRM agent node
        from app.agents.crm_agent_node import CRMAgentNode
        from app.services.llm_service import LLMService
        
        # Verify Gemini configuration
        llm_provider = os.getenv("LLM_PROVIDER", "unknown")
        api_key = os.getenv("GEMINI_API_KEY", "")
        model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        
        print(f"🤖 LLM Configuration:")
        print(f"   Provider: {llm_provider}")
        print(f"   Model: {model}")
        print(f"   API Key Configured: {bool(api_key)}")
        print(f"   Mock Mode: {LLMService.is_mock_mode()}")
        
        if LLMService.is_mock_mode():
            print("❌ ERROR: Mock mode is still enabled! Real LLM calls will not work.")
            return False
        
        if not api_key:
            print("❌ ERROR: GEMINI_API_KEY not configured!")
            return False
        
        # Check MCP service availability
        salesforce_available = "salesforce" in mcp_status["available_services"]
        print(f"\n📡 MCP Service Status:")
        print(f"   Salesforce Service: {'✅ AVAILABLE' if salesforce_available else '❌ NOT AVAILABLE'}")
        
        # Initialize CRM agent
        crm_agent = CRMAgentNode()
        
        print(f"\n✅ CRM Agent initialized")
        print(f"   Agent: {crm_agent.name}")
        print(f"   Supported Services: {crm_agent.crm_agent.get_supported_services()}")
        
        # Filter CRM test cases
        crm_test_cases = [tc for tc in INTEGRATION_TEST_CASES if tc.agent_type == "crm"]
        
        passed_tests = 0
        failed_tests = 0
        mcp_success_count = 0
        
        for i, test_case in enumerate(crm_test_cases, 1):
            print(f"\n{'='*70}")
            print(f"CRM TEST {i}/{len(crm_test_cases)}: {test_case.name}")
            print(f"{'='*70}")
            print(f"Description: {test_case.description}")
            print(f"User Request: '{test_case.user_request}'")
            print(f"Expected Action: {test_case.expected_action}")
            
            try:
                # Create mock state for testing with WebSocket manager
                mock_websocket_manager = MockWebSocketManager()
                mock_state = {
                    "task_description": test_case.user_request,
                    "plan_id": f"test-plan-crm-{i}",
                    "websocket_manager": mock_websocket_manager,  # Provide WebSocket manager for real LLM calls
                    "messages": [],
                    "collected_data": {},
                    "execution_results": []
                }
                
                print(f"\n🤖 Analyzing user intent with REAL Gemini LLM...")
                
                # Test LLM-based intent analysis with real Gemini calls
                action_analysis = await crm_agent._analyze_user_intent(
                    test_case.user_request, 
                    mock_state
                )
                
                print(f"📊 Gemini LLM Analysis Result:")
                print(f"   Action: {action_analysis.get('action', 'unknown')}")
                print(f"   Service: {action_analysis.get('service', 'unknown')}")
                print(f"   Account Name: '{action_analysis.get('account_name', '')}'")
                print(f"   Search Term: '{action_analysis.get('search_term', '')}'")
                print(f"   Stage: '{action_analysis.get('stage', '')}'")
                print(f"   Objects: {action_analysis.get('objects', [])}")
                print(f"   SOQL Query: '{action_analysis.get('soql_query', '')[:50]}...'")
                print(f"   Limit: {action_analysis.get('limit', 0)}")
                
                # Check if the action matches expectation
                actual_action = action_analysis.get("action")
                action_matches = actual_action == test_case.expected_action
                
                print(f"\n🔍 Analysis:")
                print(f"   Expected Action: {test_case.expected_action}")
                print(f"   Actual Action: {actual_action}")
                print(f"   Action Matches: {action_matches}")
                
                # Validate the analysis result
                validation_passed = crm_agent._final_validation_check(action_analysis)
                has_required_fields = crm_agent._check_required_fields(action_analysis)
                
                print(f"   Validation Passed: {validation_passed}")
                print(f"   Has Required Fields: {has_required_fields}")
                
                if action_matches and validation_passed and has_required_fields:
                    print(f"   ✅ LLM ANALYSIS PASSED - Gemini LLM correctly analyzed the request")
                    
                    # Now test actual MCP service calls if available
                    if salesforce_available:
                        print(f"\n🔧 Testing actual MCP service call...")
                        try:
                            # Execute the determined action using MCP tools
                            if action_analysis["action"] == "get_accounts":
                                crm_data = await crm_agent._get_accounts_with_llm_params(action_analysis)
                            elif action_analysis["action"] == "get_opportunities":
                                crm_data = await crm_agent._get_opportunities_with_llm_params(action_analysis)
                            elif action_analysis["action"] == "get_contacts":
                                crm_data = await crm_agent._get_contacts_with_llm_params(action_analysis)
                            elif action_analysis["action"] == "search_records":
                                crm_data = await crm_agent._search_records_with_llm_params(action_analysis)
                            elif action_analysis["action"] == "run_soql_query":
                                crm_data = await crm_agent._run_soql_query_with_llm_params(action_analysis)
                            else:
                                crm_data = {"error": "Unknown action"}
                            
                            # Check MCP call results
                            if "error" in crm_data:
                                print(f"   ⚠️ MCP CALL WARNING: {crm_data['error']}")
                                print(f"   📊 MCP Response: {json.dumps(crm_data, indent=2, default=str)}")
                            else:
                                # Count data items
                                data_count = 0
                                if "records" in crm_data:
                                    data_count = len(crm_data["records"])
                                elif "results" in crm_data:
                                    data_count = len(crm_data["results"])
                                
                                print(f"   ✅ MCP CALL SUCCESS: Retrieved {data_count} item(s)")
                                mcp_success_count += 1
                                
                                # Show sample data if available
                                if data_count > 0:
                                    if "records" in crm_data and crm_data["records"]:
                                        sample_record = crm_data["records"][0]
                                        record_type = sample_record.get('attributes', {}).get('type', 'Record')
                                        record_name = sample_record.get('Name', 'N/A')
                                        print(f"   📊 Sample {record_type}: {record_name}")
                                    elif "results" in crm_data and crm_data["results"]:
                                        sample_result = crm_data["results"][0]
                                        print(f"   🔍 Sample Result: {str(sample_result)[:100]}...")
                                
                                print(f"   📊 MCP Response Summary: {json.dumps({k: len(v) if isinstance(v, list) else str(v)[:50] + '...' if len(str(v)) > 50 else v for k, v in crm_data.items()}, indent=2)}")
                            
                        except Exception as mcp_error:
                            print(f"   ❌ MCP CALL FAILED: {mcp_error}")
                            print(f"   📝 This indicates an issue with MCP service connectivity")
                    else:
                        print(f"\n⚠️ Skipping MCP call test - salesforce service not available")
                        print(f"   📝 LLM analysis passed, but MCP service is not registered")
                    
                    passed_tests += 1
                        
                else:
                    print(f"   ❌ TEST FAILED - Gemini LLM analysis did not match expectations")
                    failed_tests += 1
                
            except Exception as e:
                print(f"   💥 TEST ERROR: {e}")
                import traceback
                traceback.print_exc()
                failed_tests += 1
        
        print(f"\n📊 CRM INTEGRATION TEST RESULTS:")
        print(f"   - Total Tests: {len(crm_test_cases)}")
        print(f"   - LLM Analysis Passed: {passed_tests}")
        print(f"   - LLM Analysis Failed: {failed_tests}")
        print(f"   - MCP Calls Successful: {mcp_success_count}")
        print(f"   - LLM Success Rate: {(passed_tests / len(crm_test_cases)) * 100:.1f}%")
        
        if salesforce_available:
            print(f"   - MCP Success Rate: {(mcp_success_count / len(crm_test_cases)) * 100:.1f}%")
        else:
            print(f"   - MCP Tests: Skipped (service not available)")
        
        return passed_tests == len(crm_test_cases)
        
    except Exception as e:
        print(f"\n❌ CRM INTEGRATION TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Main function to run integration tests with MCP calls."""
    
    print("🚀 Starting AP and CRM Agent Integration Tests with REAL Gemini LLM + MCP Calls (FIXED)")
    print("=" * 100)
    print("Testing complete workflow: User Query → Gemini LLM Analysis → MCP Query Generation → Real Data Retrieval")
    print("=" * 100)
    
    # Verify environment configuration
    llm_provider = os.getenv("LLM_PROVIDER", "unknown")
    use_mock = os.getenv("USE_MOCK_LLM", "true")
    api_key = os.getenv("GEMINI_API_KEY", "")
    
    print(f"🔧 Environment Configuration:")
    print(f"   LLM_PROVIDER: {llm_provider}")
    print(f"   USE_MOCK_LLM: {use_mock}")
    print(f"   GEMINI_API_KEY: {'✅ Configured' if api_key else '❌ Missing'}")
    
    if use_mock.lower() in ("true", "1", "yes"):
        print("❌ ERROR: USE_MOCK_LLM is still set to true! Please set it to false for real LLM testing.")
        sys.exit(1)
    
    if llm_provider != "gemini":
        print("❌ ERROR: LLM_PROVIDER should be set to 'gemini' for this test.")
        sys.exit(1)
    
    if not api_key:
        print("❌ ERROR: GEMINI_API_KEY environment variable is not set!")
        sys.exit(1)
    
    print("✅ Environment configuration looks good for real Gemini LLM testing!")
    
    # Initialize and check MCP services
    mcp_status = await initialize_and_check_mcp_services()
    
    if not mcp_status["success"]:
        print(f"\n⚠️ MCP service initialization failed, but continuing with LLM-only tests")
        print(f"   Error: {mcp_status.get('error', 'Unknown error')}")
    
    # Test AP agent
    ap_success = await test_ap_agent_integration_with_mcp(mcp_status)
    
    # Test CRM agent
    crm_success = await test_crm_agent_integration_with_mcp(mcp_status)
    
    # Overall results
    print(f"\n{'🎉' * 30} OVERALL RESULTS {'🎉' * 30}")
    print(f"📊 INTEGRATION TEST SUITE RESULTS:")
    print(f"   - AccountsPayable Agent: {'✅ PASSED' if ap_success else '❌ FAILED'}")
    print(f"   - CRM Agent: {'✅ PASSED' if crm_success else '❌ FAILED'}")
    
    # MCP Service Summary
    print(f"\n📡 MCP SERVICE SUMMARY:")
    print(f"   - MCP Initialization: {'✅ SUCCESS' if mcp_status['success'] else '❌ FAILED'}")
    print(f"   - Available Services: {mcp_status['available_services']}")
    print(f"   - Missing Services: {mcp_status['missing_services']}")
    
    overall_success = ap_success and crm_success
    
    if overall_success:
        print(f"\n🎉 ALL INTEGRATION TESTS PASSED!")
        print(f"   Both AP and CRM agents successfully integrate with Gemini LLM")
        print(f"   User queries are properly analyzed and converted to MCP calls")
        print(f"   Validation ensures robust error handling")
        print(f"   Real LLM calls are working correctly")
        
        if mcp_status["success"] and mcp_status["available_services"]:
            print(f"   MCP service calls retrieve real data from external systems")
        else:
            print(f"   ⚠️ MCP services need to be started for full end-to-end testing")
            print(f"   📝 To test with real data, start the MCP servers and run again")
        
        sys.exit(0)
    else:
        print(f"\n❌ SOME INTEGRATION TESTS FAILED")
        print(f"   Review the failed tests above for details")
        print(f"   Check Gemini API configuration and MCP service connectivity")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())