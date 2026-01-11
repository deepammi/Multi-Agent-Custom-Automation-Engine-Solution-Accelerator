#!/usr/bin/env python3
"""
Simple test for AccountsPayable Agent without MCP server dependencies.

This test verifies the basic structure and functionality of the AccountsPayable Agent
without requiring the full MCP server infrastructure.
"""

import asyncio
import sys
import os
import logging

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.agents.accounts_payable_agent import AccountsPayableAgent, get_accounts_payable_agent
from app.agents.accounts_payable_agent import ZohoAgentLegacy, get_zoho_agent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ANSI color codes for better output
BLUE = '\033[94m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
RESET = '\033[0m'
BOLD = '\033[1m'


async def test_agent_structure():
    """Test the basic structure and configuration of the AccountsPayable Agent."""
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BOLD}Testing AccountsPayable Agent Structure{RESET}")
    print(f"{BLUE}{'='*60}{RESET}")
    
    try:
        # Test agent creation
        ap_agent = AccountsPayableAgent()
        
        # Test service information
        print(f"\n{GREEN}1. Testing service configuration{RESET}")
        services = ap_agent.get_supported_services()
        print(f"Supported services: {services}")
        
        expected_services = ['zoho', 'bill_com', 'quickbooks', 'xero']
        for service in expected_services:
            if service in services:
                print(f"  ✅ {service} service configured")
                info = ap_agent.get_service_info(service)
                print(f"     Name: {info['name']}")
                print(f"     Operations: {len(info['operations'])}")
                print(f"     Available operations: {', '.join(info['operations'][:3])}...")
            else:
                print(f"  ❌ {service} service missing")
        
        # Test tool name resolution
        print(f"\n{GREEN}2. Testing tool name resolution{RESET}")
        test_cases = [
            ('zoho', 'list_invoices', 'zoho_list_invoices'),
            ('bill_com', 'get_audit_trail', 'get_audit_trail'),
            ('quickbooks', 'list_invoices', 'quickbooks_list_invoices'),
        ]
        
        for service, operation, expected_tool in test_cases:
            try:
                tool_name = ap_agent._get_tool_name(service, operation)
                if tool_name == expected_tool:
                    print(f"  ✅ {service}.{operation} -> {tool_name}")
                else:
                    print(f"  ❌ {service}.{operation} -> {tool_name} (expected {expected_tool})")
            except Exception as e:
                print(f"  ❌ {service}.{operation} -> Error: {e}")
        
        # Test service validation
        print(f"\n{GREEN}3. Testing service validation{RESET}")
        valid_services = ['zoho', 'bill_com']
        invalid_services = ['invalid_service', 'nonexistent']
        
        for service in valid_services:
            try:
                ap_agent._validate_service(service)
                print(f"  ✅ {service} validation passed")
            except Exception as e:
                print(f"  ❌ {service} validation failed: {e}")
        
        for service in invalid_services:
            try:
                ap_agent._validate_service(service)
                print(f"  ❌ {service} validation should have failed")
            except ValueError:
                print(f"  ✅ {service} validation correctly failed")
            except Exception as e:
                print(f"  ❌ {service} validation failed with unexpected error: {e}")
        
        print(f"\n{GREEN}✅ Agent structure test completed{RESET}")
        
    except Exception as e:
        print(f"\n{RED}❌ Agent structure test failed: {e}{RESET}")
        import traceback
        traceback.print_exc()


async def test_backward_compatibility_structure():
    """Test backward compatibility wrappers without MCP calls."""
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BOLD}Testing Backward Compatibility Structure{RESET}")
    print(f"{BLUE}{'='*60}{RESET}")
    
    try:
        # Test ZohoAgentLegacy creation
        print(f"\n{GREEN}1. Testing ZohoAgentLegacy wrapper{RESET}")
        zoho_agent = ZohoAgentLegacy()
        
        print(f"  Service: {zoho_agent.service}")
        print(f"  Has AP agent: {zoho_agent._ap_agent is not None}")
        
        # Test get_zoho_agent function
        zoho_agent2 = get_zoho_agent()
        print(f"  Factory function works: {zoho_agent2 is not None}")
        
        # Test global AccountsPayable agent
        print(f"\n{GREEN}2. Testing global agent functions{RESET}")
        ap_agent1 = get_accounts_payable_agent()
        ap_agent2 = get_accounts_payable_agent()
        
        print(f"  Singleton pattern: {ap_agent1 is ap_agent2}")
        print(f"  Agent type: {type(ap_agent1).__name__}")
        
        print(f"\n{GREEN}✅ Backward compatibility structure test completed{RESET}")
        
    except Exception as e:
        print(f"\n{RED}❌ Backward compatibility structure test failed: {e}{RESET}")
        import traceback
        traceback.print_exc()


async def test_legacy_zoho_service():
    """Test the legacy Zoho service with standardized client fallback."""
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BOLD}Testing Legacy Zoho Service{RESET}")
    print(f"{BLUE}{'='*60}{RESET}")
    
    try:
        # Test ZohoMCPService creation and initialization
        print(f"\n{GREEN}1. Testing ZohoMCPService initialization{RESET}")
        from app.services.zoho_mcp_service import ZohoMCPService, get_zoho_service
        
        # Test direct creation
        zoho_service = ZohoMCPService()
        print(f"  Service created: {zoho_service is not None}")
        print(f"  Use standardized: {zoho_service._use_standardized}")
        print(f"  Use mock: {zoho_service.use_mock}")
        print(f"  Enabled: {zoho_service.enabled}")
        
        # Test factory function
        zoho_service2 = get_zoho_service()
        print(f"  Factory function works: {zoho_service2 is not None}")
        
        # Test initialization (disable standardized client to avoid MCP server dependency)
        zoho_service._use_standardized = False
        await zoho_service.initialize()
        print(f"  Initialization completed: {zoho_service._initialized}")
        
        # Test mock data methods (should work without MCP)
        print(f"\n{GREEN}2. Testing mock data generation{RESET}")
        mock_invoices = zoho_service._get_mock_invoices()
        print(f"  Mock invoices count: {len(mock_invoices)}")
        
        mock_customers = zoho_service._get_mock_customers()
        print(f"  Mock customers count: {len(mock_customers)}")
        
        # Test mock operations (should work without MCP server)
        if zoho_service.use_mock:
            print(f"\n{GREEN}3. Testing mock operations{RESET}")
            
            # Force use of legacy implementation for testing
            zoho_service._use_standardized = False
            
            result = await zoho_service.list_invoices(limit=3)
            print(f"  Mock list_invoices success: {result.get('success', False)}")
            print(f"  Mock invoices returned: {len(result.get('invoices', []))}")
            
            result = await zoho_service.list_customers(limit=3)
            print(f"  Mock list_customers success: {result.get('success', False)}")
            print(f"  Mock customers returned: {len(result.get('contacts', []))}")
            
            result = await zoho_service.get_invoice_summary()
            print(f"  Mock get_invoice_summary success: {result.get('success', False)}")
        
        print(f"\n{GREEN}✅ Legacy Zoho service test completed{RESET}")
        
    except Exception as e:
        print(f"\n{RED}❌ Legacy Zoho service test failed: {e}{RESET}")
        import traceback
        traceback.print_exc()


async def main():
    """Run all tests."""
    print(f"{BOLD}AccountsPayable Agent Simple Test Suite{RESET}")
    print(f"Testing basic structure and compatibility without MCP server")
    
    # Run tests
    await test_agent_structure()
    await test_backward_compatibility_structure()
    await test_legacy_zoho_service()
    
    print(f"\n{BOLD}{'='*60}{RESET}")
    print(f"{BOLD}All simple tests completed{RESET}")
    print(f"{BOLD}{'='*60}{RESET}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n{YELLOW}⚠️  Tests interrupted by user{RESET}")
    except Exception as e:
        print(f"\n{RED}❌ Test suite failed: {e}{RESET}")
        sys.exit(1)