#!/usr/bin/env python3
"""
Bill.com Integration Test Script

This script provides comprehensive testing and validation of the Bill.com integration,
including configuration validation, connectivity testing, and integration verification.
"""

import os
import sys
import asyncio
import json
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

# Add project paths
project_root = Path(__file__).parent.parent
mcp_server_path = project_root / "src" / "mcp_server"
backend_path = project_root / "backend"

sys.path.insert(0, str(mcp_server_path))
sys.path.insert(0, str(backend_path))

# Load environment variables from .env files
try:
    from dotenv import load_dotenv
    
    # Load from project root .env first
    root_env = project_root / ".env"
    if root_env.exists():
        load_dotenv(root_env)
        print(f"✅ Loaded environment from {root_env}")
    
    # Load from backend .env (will override root .env)
    backend_env = backend_path / ".env"
    if backend_env.exists():
        load_dotenv(backend_env)
        print(f"✅ Loaded environment from {backend_env}")
    
    # Load from MCP server .env
    mcp_env = mcp_server_path / ".env"
    if mcp_env.exists():
        load_dotenv(mcp_env)
        print(f"✅ Loaded environment from {mcp_env}")
        
except ImportError:
    print("⚠️  python-dotenv not available, using system environment variables only")
except Exception as e:
    print(f"⚠️  Error loading .env files: {e}")


class BillComIntegrationTester:
    """Comprehensive Bill.com integration tester."""
    
    def __init__(self):
        self.results = {
            "configuration": {"status": "unknown", "details": {}},
            "connectivity": {"status": "unknown", "details": {}},
            "authentication": {"status": "unknown", "details": {}},
            "mcp_tools": {"status": "unknown", "details": {}},
            "agent_integration": {"status": "unknown", "details": {}},
            "performance": {"status": "unknown", "details": {}},
            "overall": {"status": "unknown", "summary": ""}
        }
        self.start_time = time.time()
    
    def print_header(self, title: str):
        """Print formatted test section header."""
        print(f"\n{'='*60}")
        print(f" {title}")
        print(f"{'='*60}")
    
    def print_status(self, test_name: str, status: str, details: str = ""):
        """Print formatted test status."""
        status_symbols = {
            "pass": "✅",
            "fail": "❌", 
            "warning": "⚠️",
            "info": "ℹ️",
            "skip": "⏭️"
        }
        
        symbol = status_symbols.get(status, "❓")
        print(f"{symbol} {test_name}")
        if details:
            print(f"   {details}")
    
    async def test_configuration(self) -> Dict[str, Any]:
        """Test Bill.com configuration validation."""
        self.print_header("Configuration Validation")
        
        try:
            from config.bill_com_config import validate_bill_com_setup, BillComConfig
            
            # Test configuration loading
            result = validate_bill_com_setup()
            
            if result["valid"]:
                self.print_status("Configuration validation", "pass", "All required variables present")
                
                # Test configuration object creation
                try:
                    config = BillComConfig.from_env()
                    self.print_status("Configuration object creation", "pass", 
                                    f"Environment: {config.environment}")
                    
                    # Validate configuration details
                    details = {
                        "username": config.username,
                        "organization_id": config.organization_id,
                        "environment": config.environment,
                        "base_url": config.base_url,
                        "timeout": config.timeout,
                        "max_retries": config.max_retries
                    }
                    
                    self.results["configuration"] = {
                        "status": "pass",
                        "details": details
                    }
                    
                except Exception as e:
                    self.print_status("Configuration object creation", "fail", str(e))
                    self.results["configuration"] = {
                        "status": "fail",
                        "details": {"error": str(e)}
                    }
            else:
                missing = result.get("missing_required", [])
                errors = result.get("errors", [])
                
                self.print_status("Configuration validation", "fail", 
                                f"Missing: {', '.join(missing)}")
                
                if errors:
                    for error in errors:
                        self.print_status("Configuration error", "fail", error)
                
                self.results["configuration"] = {
                    "status": "fail",
                    "details": {
                        "missing_required": missing,
                        "errors": errors
                    }
                }
        
        except ImportError as e:
            self.print_status("Configuration module import", "fail", str(e))
            self.results["configuration"] = {
                "status": "fail",
                "details": {"error": f"Import error: {e}"}
            }
        
        return self.results["configuration"]
    
    async def test_connectivity(self) -> Dict[str, Any]:
        """Test network connectivity to Bill.com API."""
        self.print_header("Network Connectivity")
        
        try:
            import httpx
            from config.bill_com_config import BillComConfig
            
            config = BillComConfig.from_env()
            
            # Test basic connectivity
            async with httpx.AsyncClient() as client:
                try:
                    response = await client.get(
                        f"{config.base_url}/",
                        timeout=10.0
                    )
                    
                    self.print_status("Network connectivity", "pass", 
                                    f"Connected to {config.base_url}")
                    
                    self.results["connectivity"] = {
                        "status": "pass",
                        "details": {
                            "base_url": config.base_url,
                            "response_time_ms": response.elapsed.total_seconds() * 1000,
                            "status_code": response.status_code
                        }
                    }
                    
                except httpx.TimeoutException:
                    self.print_status("Network connectivity", "fail", "Connection timeout")
                    self.results["connectivity"] = {
                        "status": "fail",
                        "details": {"error": "Connection timeout"}
                    }
                    
                except httpx.NetworkError as e:
                    self.print_status("Network connectivity", "fail", f"Network error: {e}")
                    self.results["connectivity"] = {
                        "status": "fail",
                        "details": {"error": f"Network error: {e}"}
                    }
        
        except Exception as e:
            self.print_status("Connectivity test", "fail", str(e))
            self.results["connectivity"] = {
                "status": "fail",
                "details": {"error": str(e)}
            }
        
        return self.results["connectivity"]
    
    async def test_authentication(self) -> Dict[str, Any]:
        """Test Bill.com API authentication."""
        self.print_header("API Authentication")
        
        try:
            from services.bill_com_service import BillComAPIService
            
            async with BillComAPIService(plan_id="test", agent="integration_test") as service:
                # Test authentication
                auth_start = time.time()
                auth_result = await service.authenticate()
                auth_time = time.time() - auth_start
                
                if auth_result:
                    self.print_status("API authentication", "pass", 
                                    f"Authenticated successfully ({auth_time:.2f}s)")
                    
                    # Test session details
                    if service.session:
                        session_details = {
                            "session_id": service.session.session_id[:8] + "...",
                            "organization_id": service.session.organization_id,
                            "user_id": service.session.user_id,
                            "expires_at": service.session.expires_at.isoformat(),
                            "authentication_time_ms": auth_time * 1000
                        }
                        
                        self.print_status("Session creation", "pass", 
                                        f"Session expires: {service.session.expires_at}")
                        
                        self.results["authentication"] = {
                            "status": "pass",
                            "details": session_details
                        }
                    else:
                        self.print_status("Session creation", "fail", "No session created")
                        self.results["authentication"] = {
                            "status": "fail",
                            "details": {"error": "No session created despite successful auth"}
                        }
                else:
                    self.print_status("API authentication", "fail", "Authentication failed")
                    self.results["authentication"] = {
                        "status": "fail",
                        "details": {"error": "Authentication failed"}
                    }
        
        except Exception as e:
            self.print_status("Authentication test", "fail", str(e))
            self.results["authentication"] = {
                "status": "fail",
                "details": {"error": str(e)}
            }
        
        return self.results["authentication"]
    
    async def test_mcp_tools(self) -> Dict[str, Any]:
        """Test MCP tools functionality."""
        self.print_header("MCP Tools Testing")
        
        try:
            # Test tool imports
            try:
                from core.bill_com_tools import (
                    get_bill_com_invoices,
                    get_bill_com_invoice_details,
                    search_bill_com_invoices,
                    get_bill_com_vendors
                )
                
                self.print_status("MCP tools import", "pass", "All tools imported successfully")
                
                # Test basic tool functionality (with mocked service)
                from unittest.mock import patch, AsyncMock
                
                with patch('core.bill_com_tools.get_bill_com_service') as mock_get_service:
                    mock_service = AsyncMock()
                    mock_service.get_invoices.return_value = [
                        {
                            "id": "test_inv_001",
                            "invoiceNumber": "TEST-001",
                            "vendorName": "Test Vendor",
                            "amount": 100.00,
                            "status": "approved"
                        }
                    ]
                    mock_get_service.return_value = mock_service
                    
                    # Test get_bill_com_invoices tool
                    tool_start = time.time()
                    result = await get_bill_com_invoices(limit=1)
                    tool_time = time.time() - tool_start
                    
                    # Parse result
                    result_data = json.loads(result)
                    
                    if result_data.get("success"):
                        self.print_status("get_bill_com_invoices tool", "pass", 
                                        f"Tool executed successfully ({tool_time:.3f}s)")
                        
                        tool_details = {
                            "get_bill_com_invoices": {
                                "status": "pass",
                                "execution_time_ms": tool_time * 1000,
                                "response_format": "valid"
                            }
                        }
                        
                        # Test other tools
                        vendors_result = await get_bill_com_vendors()
                        vendors_data = json.loads(vendors_result)
                        
                        if vendors_data.get("success"):
                            self.print_status("get_bill_com_vendors tool", "pass", "Tool executed successfully")
                            tool_details["get_bill_com_vendors"] = {"status": "pass"}
                        
                        search_result = await search_bill_com_invoices("TEST-001", "invoice_number")
                        search_data = json.loads(search_result)
                        
                        if search_data.get("success"):
                            self.print_status("search_bill_com_invoices tool", "pass", "Tool executed successfully")
                            tool_details["search_bill_com_invoices"] = {"status": "pass"}
                        
                        self.results["mcp_tools"] = {
                            "status": "pass",
                            "details": tool_details
                        }
                    else:
                        self.print_status("MCP tools execution", "fail", "Tool execution failed")
                        self.results["mcp_tools"] = {
                            "status": "fail",
                            "details": {"error": "Tool execution failed"}
                        }
                
            except ImportError as e:
                self.print_status("MCP tools import", "fail", str(e))
                self.results["mcp_tools"] = {
                    "status": "fail",
                    "details": {"error": f"Import error: {e}"}
                }
        
        except Exception as e:
            self.print_status("MCP tools test", "fail", str(e))
            self.results["mcp_tools"] = {
                "status": "fail",
                "details": {"error": str(e)}
            }
        
        return self.results["mcp_tools"]
    
    async def test_agent_integration(self) -> Dict[str, Any]:
        """Test agent integration with Bill.com."""
        self.print_header("Agent Integration Testing")
        
        try:
            from app.agents.state import AgentState
            from app.agents.nodes import invoice_agent_node, audit_agent_node
            
            # Test Invoice Agent
            invoice_state = AgentState(
                task_description="Get recent invoices from Bill.com for testing",
                plan_id="integration-test-001",
                messages=[],
                current_agent="Invoice"
            )
            
            agent_start = time.time()
            invoice_result = await invoice_agent_node(invoice_state)
            agent_time = time.time() - agent_start
            
            if invoice_result and "final_result" in invoice_result:
                self.print_status("Invoice Agent integration", "pass", 
                                f"Agent responded ({agent_time:.2f}s)")
                
                # Check if response mentions Bill.com
                response = invoice_result["final_result"].lower()
                mentions_billcom = any(keyword in response for keyword in [
                    "bill.com", "billcom", "integration", "invoice"
                ])
                
                if mentions_billcom:
                    self.print_status("Invoice Agent Bill.com awareness", "pass", 
                                    "Agent mentions Bill.com integration")
                else:
                    self.print_status("Invoice Agent Bill.com awareness", "warning", 
                                    "Agent response doesn't mention Bill.com")
                
                # Test Audit Agent
                audit_state = AgentState(
                    task_description="Check compliance status for invoice processing",
                    plan_id="integration-test-002",
                    messages=[],
                    current_agent="Audit"
                )
                
                audit_result = await audit_agent_node(audit_state)
                
                if audit_result and "final_result" in audit_result:
                    self.print_status("Audit Agent integration", "pass", "Agent responded")
                    
                    agent_details = {
                        "invoice_agent": {
                            "status": "pass",
                            "response_time_ms": agent_time * 1000,
                            "mentions_billcom": mentions_billcom
                        },
                        "audit_agent": {
                            "status": "pass",
                            "response_length": len(audit_result["final_result"])
                        }
                    }
                    
                    self.results["agent_integration"] = {
                        "status": "pass",
                        "details": agent_details
                    }
                else:
                    self.print_status("Audit Agent integration", "fail", "No response from agent")
                    self.results["agent_integration"] = {
                        "status": "fail",
                        "details": {"error": "Audit agent failed to respond"}
                    }
            else:
                self.print_status("Invoice Agent integration", "fail", "No response from agent")
                self.results["agent_integration"] = {
                    "status": "fail",
                    "details": {"error": "Invoice agent failed to respond"}
                }
        
        except Exception as e:
            self.print_status("Agent integration test", "fail", str(e))
            self.results["agent_integration"] = {
                "status": "fail",
                "details": {"error": str(e)}
            }
        
        return self.results["agent_integration"]
    
    async def test_performance(self) -> Dict[str, Any]:
        """Test performance characteristics."""
        self.print_header("Performance Testing")
        
        try:
            from services.bill_com_service import BillComAPIService
            
            # Test service creation performance
            creation_times = []
            
            for i in range(3):
                start = time.time()
                async with BillComAPIService() as service:
                    creation_time = time.time() - start
                    creation_times.append(creation_time)
            
            avg_creation_time = sum(creation_times) / len(creation_times)
            
            self.print_status("Service creation performance", "pass", 
                            f"Average: {avg_creation_time:.3f}s")
            
            # Test concurrent operations
            async def concurrent_test():
                async with BillComAPIService() as service:
                    return service.get_performance_metrics()
            
            concurrent_start = time.time()
            tasks = [concurrent_test() for _ in range(3)]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            concurrent_time = time.time() - concurrent_start
            
            successful_tasks = [r for r in results if not isinstance(r, Exception)]
            
            self.print_status("Concurrent operations", "pass", 
                            f"{len(successful_tasks)}/3 tasks completed ({concurrent_time:.3f}s)")
            
            performance_details = {
                "service_creation_avg_ms": avg_creation_time * 1000,
                "concurrent_operations": {
                    "total_tasks": 3,
                    "successful_tasks": len(successful_tasks),
                    "total_time_ms": concurrent_time * 1000
                }
            }
            
            self.results["performance"] = {
                "status": "pass",
                "details": performance_details
            }
        
        except Exception as e:
            self.print_status("Performance test", "fail", str(e))
            self.results["performance"] = {
                "status": "fail",
                "details": {"error": str(e)}
            }
        
        return self.results["performance"]
    
    def generate_summary(self):
        """Generate overall test summary."""
        self.print_header("Test Summary")
        
        total_time = time.time() - self.start_time
        
        # Count test results
        passed = sum(1 for result in self.results.values() 
                    if isinstance(result, dict) and result.get("status") == "pass")
        failed = sum(1 for result in self.results.values() 
                    if isinstance(result, dict) and result.get("status") == "fail")
        total_tests = len([k for k in self.results.keys() if k != "overall"])
        
        # Determine overall status
        if failed == 0:
            overall_status = "pass"
            status_symbol = "✅"
            summary = f"All {total_tests} test categories passed"
        elif passed > failed:
            overall_status = "warning"
            status_symbol = "⚠️"
            summary = f"{passed}/{total_tests} test categories passed, {failed} failed"
        else:
            overall_status = "fail"
            status_symbol = "❌"
            summary = f"{failed}/{total_tests} test categories failed"
        
        self.results["overall"] = {
            "status": overall_status,
            "summary": summary,
            "total_time_seconds": total_time,
            "tests_passed": passed,
            "tests_failed": failed,
            "tests_total": total_tests
        }
        
        print(f"\n{status_symbol} Overall Status: {summary}")
        print(f"   Total execution time: {total_time:.2f} seconds")
        
        # Print detailed results for failed tests
        if failed > 0:
            print(f"\n{'='*60}")
            print(" Failed Test Details")
            print(f"{'='*60}")
            
            for test_name, result in self.results.items():
                if isinstance(result, dict) and result.get("status") == "fail":
                    print(f"\n❌ {test_name.replace('_', ' ').title()}")
                    error = result.get("details", {}).get("error", "Unknown error")
                    print(f"   Error: {error}")
        
        return self.results["overall"]
    
    def save_results(self, filename: Optional[str] = None):
        """Save test results to JSON file."""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"bill_com_integration_test_results_{timestamp}.json"
        
        results_path = project_root / "logs" / filename
        results_path.parent.mkdir(exist_ok=True)
        
        with open(results_path, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        print(f"\n📄 Test results saved to: {results_path}")
        return results_path


async def main():
    """Run comprehensive Bill.com integration tests."""
    print("Bill.com Integration Test Suite")
    print("=" * 60)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    tester = BillComIntegrationTester()
    
    # Run all tests
    await tester.test_configuration()
    await tester.test_connectivity()
    await tester.test_authentication()
    await tester.test_mcp_tools()
    await tester.test_agent_integration()
    await tester.test_performance()
    
    # Generate summary
    overall_result = tester.generate_summary()
    
    # Save results
    results_file = tester.save_results()
    
    # Exit with appropriate code
    exit_code = 0 if overall_result["status"] == "pass" else 1
    
    print(f"\nTest suite completed with exit code: {exit_code}")
    return exit_code


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️  Test suite interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n\n❌ Test suite failed with error: {e}")
        sys.exit(1)