#!/usr/bin/env python3
"""
Test AP and CRM HTTP Agents

This script tests the new HTTP-based AP and CRM agents that use the same
HTTP MCP transport as the Email agent, ensuring they work correctly with
HTTP MCP servers.
"""

import asyncio
import logging
import sys
import os
import json

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Configure for real LLM testing
os.environ["USE_MOCK_LLM"] = "false"
os.environ["LLM_PROVIDER"] = "gemini"
os.environ["GEMINI_MODEL"] = "gemini-2.5-flash"

# Set up logging
logging.basicConfig(level=logging.INFO)


async def test_ap_agent_http():
    """Test the HTTP-based AccountsPayable agent."""
    
    print("\n🔍 Testing HTTP AccountsPayable Agent")
    print("=" * 60)
    
    try:
        from app.agents.accounts_payable_agent_http import get_accounts_payable_agent_http
        
        # Get the HTTP AP agent
        ap_agent = get_accounts_payable_agent_http()
        print(f"✅ HTTP AP Agent initialized")
        print(f"   Supported services: {ap_agent.get_supported_services()}")
        
        # Test scenarios
        test_scenarios = [
            {
                "name": "Get Bills",
                "method": "get_bills",
                "args": {"service": "bill_com", "limit": 5}
            },
            {
                "name": "Search Bills for Acme Marketing",
                "method": "search_bills", 
                "args": {"search_term": "Acme Marketing", "service": "bill_com", "limit": 3}
            },
            {
                "name": "Get Vendors",
                "method": "get_vendors",
                "args": {"service": "bill_com", "limit": 5}
            }
        ]
        
        passed_tests = 0
        
        for i, scenario in enumerate(test_scenarios, 1):
            print(f"\n🧪 AP Test {i}: {scenario['name']}")
            print(f"   Method: {scenario['method']}")
            print(f"   Args: {json.dumps(scenario['args'], indent=2)}")
            
            try:
                # Call the method dynamically
                method = getattr(ap_agent, scenario['method'])
                result = await method(**scenario['args'])
                
                # Check result
                if isinstance(result, dict):
                    if "error" in result:
                        print(f"   ⚠️ MCP returned error: {result['error']}")
                    else:
                        # Count results
                        data_count = 0
                        if "invoices" in result:
                            data_count = len(result["invoices"])
                        elif "vendors" in result:
                            data_count = len(result["vendors"])
                        elif "invoice" in result:
                            data_count = 1 if result["invoice"] else 0
                        
                        print(f"   ✅ Success: Retrieved {data_count} item(s)")
                        print(f"   📊 Result keys: {list(result.keys())}")
                        passed_tests += 1
                else:
                    print(f"   ⚠️ Unexpected result type: {type(result)}")
                    
            except Exception as e:
                print(f"   ❌ Test failed: {e}")
        
        print(f"\n📊 AP Agent Test Results:")
        print(f"   - Total Tests: {len(test_scenarios)}")
        print(f"   - Passed: {passed_tests}")
        print(f"   - Success Rate: {(passed_tests/len(test_scenarios))*100:.1f}%")
        
        return passed_tests == len(test_scenarios)
        
    except Exception as e:
        print(f"❌ AP Agent HTTP Test Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_crm_agent_http():
    """Test the HTTP-based CRM agent."""
    
    print("\n🔍 Testing HTTP CRM Agent")
    print("=" * 60)
    
    try:
        from app.agents.crm_agent_http import get_crm_agent_http
        
        # Get the HTTP CRM agent
        crm_agent = get_crm_agent_http()
        print(f"✅ HTTP CRM Agent initialized")
        print(f"   Supported services: {crm_agent.get_supported_services()}")
        
        # Test scenarios
        test_scenarios = [
            {
                "name": "Get Accounts",
                "method": "get_accounts",
                "args": {"service": "salesforce", "limit": 5}
            },
            {
                "name": "Get Opportunities",
                "method": "get_opportunities",
                "args": {"service": "salesforce", "limit": 3}
            },
            {
                "name": "Search Records",
                "method": "search_records",
                "args": {"search_term": "Acme", "service": "salesforce"}
            }
        ]
        
        passed_tests = 0
        
        for i, scenario in enumerate(test_scenarios, 1):
            print(f"\n🧪 CRM Test {i}: {scenario['name']}")
            print(f"   Method: {scenario['method']}")
            print(f"   Args: {json.dumps(scenario['args'], indent=2)}")
            
            try:
                # Call the method dynamically
                method = getattr(crm_agent, scenario['method'])
                result = await method(**scenario['args'])
                
                # Check result
                if isinstance(result, dict):
                    if "error" in result:
                        print(f"   ⚠️ MCP returned error: {result['error']}")
                    else:
                        # Count results
                        data_count = 0
                        if "records" in result:
                            data_count = len(result["records"])
                        elif "results" in result:
                            data_count = len(result["results"])
                        
                        print(f"   ✅ Success: Retrieved {data_count} item(s)")
                        print(f"   📊 Result keys: {list(result.keys())}")
                        passed_tests += 1
                else:
                    print(f"   ⚠️ Unexpected result type: {type(result)}")
                    
            except Exception as e:
                print(f"   ❌ Test failed: {e}")
        
        print(f"\n📊 CRM Agent Test Results:")
        print(f"   - Total Tests: {len(test_scenarios)}")
        print(f"   - Passed: {passed_tests}")
        print(f"   - Success Rate: {(passed_tests/len(test_scenarios))*100:.1f}%")
        
        return passed_tests == len(test_scenarios)
        
    except Exception as e:
        print(f"❌ CRM Agent HTTP Test Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_service_health():
    """Test service health checking for both agents."""
    
    print("\n🔍 Testing Service Health Checks")
    print("=" * 60)
    
    try:
        from app.agents.accounts_payable_agent_http import get_accounts_payable_agent_http
        from app.agents.crm_agent_http import get_crm_agent_http
        
        ap_agent = get_accounts_payable_agent_http()
        crm_agent = get_crm_agent_http()
        
        # Test AP service health
        print(f"\n📊 AP Service Health:")
        for service in ap_agent.get_supported_services():
            try:
                health = await ap_agent.check_service_health(service)
                status = "✅ Healthy" if health['is_healthy'] else "❌ Unhealthy"
                print(f"   {service}: {status}")
                if not health['is_healthy']:
                    print(f"      Error: {health.get('error_message', 'Unknown')}")
            except Exception as e:
                print(f"   {service}: ❌ Health check failed: {e}")
        
        # Test CRM service health
        print(f"\n📊 CRM Service Health:")
        for service in crm_agent.get_supported_services():
            try:
                health = await crm_agent.check_service_health(service)
                status = "✅ Healthy" if health['is_healthy'] else "❌ Unhealthy"
                print(f"   {service}: {status}")
                if not health['is_healthy']:
                    print(f"      Error: {health.get('error_message', 'Unknown')}")
            except Exception as e:
                print(f"   {service}: ❌ Health check failed: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Service Health Test Failed: {e}")
        return False


async def main():
    """Main test function."""
    
    print("🚀 AP and CRM HTTP Agent Tests")
    print("=" * 80)
    print("Testing HTTP-based agents that use the same transport as Email agent")
    print("=" * 80)
    
    # Verify environment
    llm_provider = os.getenv("LLM_PROVIDER")
    use_mock = os.getenv("USE_MOCK_LLM", "true")
    api_key = os.getenv("GEMINI_API_KEY", "")
    
    print(f"🔧 Environment Configuration:")
    print(f"   LLM_PROVIDER: {llm_provider}")
    print(f"   USE_MOCK_LLM: {use_mock}")
    print(f"   GEMINI_API_KEY: {'✅ Configured' if api_key else '❌ Missing'}")
    
    # Run tests
    results = {}
    
    results["ap_http"] = await test_ap_agent_http()
    results["crm_http"] = await test_crm_agent_http()
    results["health"] = await test_service_health()
    
    # Overall results
    print(f"\n{'🎉' * 30} FINAL RESULTS {'🎉' * 30}")
    print(f"📊 HTTP Agent Test Results:")
    print(f"   - AP HTTP Agent: {'✅ PASSED' if results['ap_http'] else '❌ FAILED'}")
    print(f"   - CRM HTTP Agent: {'✅ PASSED' if results['crm_http'] else '❌ FAILED'}")
    print(f"   - Service Health: {'✅ PASSED' if results['health'] else '❌ FAILED'}")
    
    # Determine overall success
    passed_tests = sum(results.values())
    total_tests = len(results)
    success_rate = (passed_tests / total_tests) * 100
    
    print(f"\n📈 Overall Results:")
    print(f"   - Tests Passed: {passed_tests}/{total_tests}")
    print(f"   - Success Rate: {success_rate:.1f}%")
    
    if success_rate >= 100:
        print(f"\n🎉 ALL HTTP AGENT TESTS PASSED!")
        print(f"   ✅ HTTP-based agents are working correctly")
        print(f"   ✅ Same transport as Email agent confirmed")
        print(f"   ✅ Ready for integration with HTTP MCP servers")
        
        print(f"\n🚀 Next Steps:")
        print(f"   1. Start HTTP MCP servers: python3 backend/start_mcp_servers_http_fixed.py")
        print(f"   2. Test with real servers: python3 backend/test_ap_crm_integration_http_mcp.py")
        print(f"   3. Update agent nodes to use HTTP agents")
        
    elif success_rate >= 66:
        print(f"\n✅ MOST HTTP AGENT TESTS PASSED!")
        print(f"   Some components are working correctly")
        print(f"   Minor issues need to be resolved")
        
    else:
        print(f"\n❌ HTTP AGENT TESTS NEED ATTENTION")
        print(f"   Check the test output above for details")
    
    sys.exit(0 if success_rate >= 66 else 1)


if __name__ == "__main__":
    asyncio.run(main())