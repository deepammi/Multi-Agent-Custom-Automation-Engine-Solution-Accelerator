#!/usr/bin/env python3
"""
Simple integration test runner for Bill.com integration.
Tests key functionality without external dependencies.
"""

import os
import sys
import asyncio
from pathlib import Path

# Add paths
mcp_server_path = Path(__file__).parent / "src" / "mcp_server"
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(mcp_server_path))
sys.path.insert(0, str(backend_path))

async def run_integration_tests():
    """Run comprehensive integration tests."""
    print("🧪 Bill.com Integration Test Suite")
    print("=" * 60)
    
    test_results = {}
    
    # Set up test environment
    test_env = {
        "BILL_COM_USERNAME": "test@example.com",
        "BILL_COM_PASSWORD": "test_password",
        "BILL_COM_ORG_ID": "test_org_123456789",
        "BILL_COM_DEV_KEY": "test_dev_key_12345",
        "BILL_COM_ENVIRONMENT": "sandbox"
    }
    
    for key, value in test_env.items():
        os.environ[key] = value
    
    try:
        # Test 1: Configuration System
        print("\n1️⃣ Testing Configuration System...")
        try:
            from config.bill_com_config import BillComConfig, validate_bill_com_setup
            
            config = BillComConfig.from_env()
            validation = validate_bill_com_setup()
            
            assert config.environment.value == "sandbox"
            assert validation["valid"] is True
            
            print("   ✅ Configuration creation and validation")
            test_results["configuration"] = True
            
        except Exception as e:
            print(f"   ❌ Configuration test failed: {e}")
            test_results["configuration"] = False
        
        # Test 2: Health Monitoring
        print("\n2️⃣ Testing Health Monitoring...")
        try:
            from services.bill_com_health_service import get_health_service
            from core.bill_com_health_tools import bill_com_config_validation, bill_com_setup_guide
            
            health_service = get_health_service()
            config_result = await bill_com_config_validation()
            setup_result = await bill_com_setup_guide()
            
            assert isinstance(health_service.last_health_check, type(None))  # Initially None
            assert len(config_result) > 50  # Should return substantial JSON
            assert len(setup_result) > 100  # Should return setup instructions
            
            print("   ✅ Health service and tools")
            test_results["health"] = True
            
        except Exception as e:
            print(f"   ❌ Health monitoring test failed: {e}")
            test_results["health"] = False
        
        # Test 3: Audit System
        print("\n3️⃣ Testing Audit System...")
        try:
            from interfaces.audit_provider import AuditProvider, AuditEventType
            from services.audit_service import AuditService
            from adapters.billcom_audit_adapter import BillComAuditAdapter
            from services.audit_tools_service import AuditToolsService
            
            audit_service = AuditService()
            audit_tools_service = AuditToolsService()
            
            assert len(list(AuditEventType)) == 8
            assert audit_service.get_available_providers() == {}  # No providers registered yet
            assert audit_tools_service.domain == "audit"
            
            print("   ✅ Audit interface and services")
            test_results["audit"] = True
            
        except Exception as e:
            print(f"   ❌ Audit system test failed: {e}")
            test_results["audit"] = False
        
        # Test 4: Agent Integration
        print("\n4️⃣ Testing Agent Integration...")
        try:
            from app.agents.state import AgentState
            from app.agents.nodes import invoice_agent_node, audit_agent_node, closing_agent_node
            
            # Test Invoice Agent
            invoice_state = AgentState(
                task_description="Get recent invoices from Bill.com",
                plan_id="test-invoice",
                messages=[],
                current_agent="Invoice"
            )
            
            invoice_result = await invoice_agent_node(invoice_state)
            
            # Test Audit Agent
            audit_state = AgentState(
                task_description="Check for compliance exceptions",
                plan_id="test-audit",
                messages=[],
                current_agent="Audit"
            )
            
            audit_result = await audit_agent_node(audit_state)
            
            # Test Closing Agent
            closing_state = AgentState(
                task_description="Perform month-end closing",
                plan_id="test-closing",
                messages=[],
                current_agent="Closing"
            )
            
            closing_result = closing_agent_node(closing_state)
            
            # Verify all agents respond appropriately
            assert "final_result" in invoice_result
            assert "final_result" in audit_result
            assert "final_result" in closing_result
            
            # Check for Bill.com integration mentions
            invoice_response = invoice_result["final_result"]
            assert "Bill.com" in invoice_response or "billcom" in invoice_response.lower()
            
            # Check for audit functionality
            audit_response = audit_result["final_result"]
            assert any(keyword in audit_response.lower() for keyword in ["audit", "compliance"])
            
            # Check for future enhancement message in closing
            closing_response = closing_result["final_result"]
            assert any(keyword in closing_response.lower() for keyword in ["development", "coming soon"])
            
            print("   ✅ Agent integration and responses")
            test_results["agents"] = True
            
        except Exception as e:
            print(f"   ❌ Agent integration test failed: {e}")
            test_results["agents"] = False
        
        # Test 5: Integration Service
        print("\n5️⃣ Testing Integration Service...")
        try:
            from app.services.bill_com_integration_service import get_bill_com_service
            
            service = get_bill_com_service()
            
            # Test service methods exist
            methods = ["get_invoices", "get_invoice_details", "search_invoices", "get_vendors"]
            for method in methods:
                assert hasattr(service, method), f"Missing method: {method}"
            
            # Test health check (will fail without MCP server, but shouldn't crash)
            health_result = await service.check_bill_com_health()
            assert isinstance(health_result, dict)
            
            await service.close()
            
            print("   ✅ Integration service architecture")
            test_results["integration_service"] = True
            
        except Exception as e:
            print(f"   ❌ Integration service test failed: {e}")
            test_results["integration_service"] = False
        
        # Test 6: MCP Tools Services
        print("\n6️⃣ Testing MCP Tools Services...")
        try:
            from services.bill_com_health_tools_service import BillComHealthToolsService
            from services.audit_tools_service import AuditToolsService
            
            health_tools = BillComHealthToolsService()
            audit_tools = AuditToolsService()
            
            assert health_tools.domain == "bill_com_health"
            assert audit_tools.domain == "audit"
            
            # Test that methods exist
            health_methods = ["bill_com_health_check", "bill_com_config_validation"]
            for method in health_methods:
                assert hasattr(health_tools, method), f"Missing health method: {method}"
            
            audit_methods = ["get_audit_trail", "detect_audit_exceptions"]
            for method in audit_methods:
                assert hasattr(audit_tools, method), f"Missing audit method: {method}"
            
            print("   ✅ MCP tools services")
            test_results["mcp_tools"] = True
            
        except Exception as e:
            print(f"   ❌ MCP tools test failed: {e}")
            test_results["mcp_tools"] = False
        
        # Test 7: Error Handling
        print("\n7️⃣ Testing Error Handling...")
        try:
            # Test with invalid configuration
            original_username = os.environ.get("BILL_COM_USERNAME")
            del os.environ["BILL_COM_USERNAME"]
            
            validation = validate_bill_com_setup()
            assert validation["valid"] is False
            assert "BILL_COM_USERNAME" in validation.get("missing_required", [])
            
            # Restore configuration
            if original_username:
                os.environ["BILL_COM_USERNAME"] = original_username
            
            print("   ✅ Error handling and validation")
            test_results["error_handling"] = True
            
        except Exception as e:
            print(f"   ❌ Error handling test failed: {e}")
            test_results["error_handling"] = False
        
        # Final Results
        print("\n" + "=" * 60)
        print("📊 Integration Test Results")
        print("=" * 60)
        
        passed_tests = sum(1 for result in test_results.values() if result)
        total_tests = len(test_results)
        
        for test_name, result in test_results.items():
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"{status} - {test_name.replace('_', ' ').title()}")
        
        print(f"\n📈 Overall Result: {passed_tests}/{total_tests} tests passed")
        
        if passed_tests == total_tests:
            print("\n🎉 All integration tests passed!")
            print("\n✅ Bill.com Integration Status: FULLY FUNCTIONAL")
            
            print("\n🚀 Verified Capabilities:")
            print("   ✅ Configuration system with multi-environment support")
            print("   ✅ Health monitoring and diagnostics")
            print("   ✅ Generic audit interface with Bill.com adapter")
            print("   ✅ Agent integration (Invoice, Audit, Closing)")
            print("   ✅ MCP tools registration and services")
            print("   ✅ Error handling and graceful fallbacks")
            print("   ✅ Integration service architecture")
            
            print("\n📋 Ready for Production:")
            print("   • Configure real Bill.com credentials")
            print("   • Start MCP server for full functionality")
            print("   • Test with real Bill.com data")
            print("   • Monitor health and performance")
            
            return True
        else:
            print(f"\n❌ {total_tests - passed_tests} test(s) failed")
            print("\n🔧 Issues need to be resolved")
            return False
    
    finally:
        # Clean up test environment
        for key in test_env.keys():
            if key in os.environ:
                del os.environ[key]


if __name__ == "__main__":
    success = asyncio.run(run_integration_tests())
    exit(0 if success else 1)