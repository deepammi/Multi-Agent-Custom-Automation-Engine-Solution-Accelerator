#!/usr/bin/env python3
"""
Comprehensive Integration Testing for MCP Client Standardization.

This test suite validates the complete MCP workflow including:
- End-to-end MCP protocol compliance across all services
- Multi-service tool calls within single agent workflows
- Error recovery across service boundaries
- Performance testing with concurrent MCP tool calls

Requirements validated: 5.1, 5.2, 5.3, 5.4
"""

import asyncio
import logging
import sys
import os
import time
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from unittest.mock import AsyncMock, MagicMock, patch
from concurrent.futures import ThreadPoolExecutor
import pytest

# Add the backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.services.mcp_client_service import (
    BaseMCPClient,
    MCPClientManager,
    ToolRegistry,
    ConnectionPool,
    MCPError,
    MCPConnectionError,
    MCPTimeoutError,
    ToolInfo,
    HealthStatus,
    ConnectionStatus,
    get_mcp_manager,
    initialize_mcp_services
)
from app.agents.crm_agent import CRMAgent
from app.agents.email_agent import EmailAgent
from app.agents.accounts_payable_agent import AccountsPayableAgent
from app.agents.state import AgentState
from app.services.error_handler import WorkflowErrorHandler
from app.services.websocket_service import WebSocketManager

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ANSI color codes for better output
BLUE = '\033[94m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
RESET = '\033[0m'
BOLD = '\033[1m'


class MockMCPClient(BaseMCPClient):
    """Enhanced mock MCP client for comprehensive testing."""
    
    def __init__(
        self, 
        service_name: str, 
        tools: List[str] = None,
        simulate_failures: bool = False,
        failure_rate: float = 0.1,
        response_delay: float = 0.1
    ):
        # Initialize without calling parent __init__ to avoid MCP SDK requirement
        self.service_name = service_name
        self.server_command = "mock"
        self.server_args = ["mock"]
        self.timeout = 30
        self.retry_attempts = 3
        self.health_check_interval = 60
        
        # Mock configuration
        self.simulate_failures = simulate_failures
        self.failure_rate = failure_rate
        self.response_delay = response_delay
        self.call_count = 0
        self.failure_count = 0
        
        # Mock connection state
        self._session = "mock_session"
        self._connection_status = ConnectionStatus.CONNECTED
        self._last_health_check = None
        self._health_status = None
        
        # Mock tool registry
        self._available_tools = tools or [
            f"{service_name}_get_data",
            f"{service_name}_process_data",
            f"{service_name}_send_notification"
        ]
        self._tool_metadata = {}
        
        # Create mock tool metadata
        for tool_name in self._available_tools:
            self._tool_metadata[tool_name] = ToolInfo(
                name=tool_name,
                service=service_name,
                description=f"Mock tool: {tool_name}",
                parameters={"param1": {"type": "string"}, "param2": {"type": "integer"}},
                return_type="dict",
                category="mock",
                requires_auth=False
            )
        
        # Performance metrics
        self._connection_time = 0.05
        self._last_tool_call_time = None
        self._tool_call_count = 0
        self._error_count = 0
        self._consecutive_timeouts = 0
        self._consecutive_health_failures = 0
        self._recovery_in_progress = False
        
        # Diagnostic info
        from app.services.mcp_client_service import DiagnosticInfo
        self._diagnostic_info = DiagnosticInfo(service_name=service_name)
    
    async def connect(self):
        """Mock connect method with optional failure simulation."""
        if self.simulate_failures and self.call_count % 10 == 0:
            self.failure_count += 1
            raise MCPConnectionError(f"Mock connection failure for {self.service_name}", self.service_name)
        
        await asyncio.sleep(self.response_delay)
        self._connection_status = ConnectionStatus.CONNECTED
        logger.info(f"Mock connected to {self.service_name}")
    
    async def disconnect(self):
        """Mock disconnect method."""
        self._connection_status = ConnectionStatus.DISCONNECTED
        logger.info(f"Mock disconnected from {self.service_name}")
    
    async def call_tool(self, tool_name: str, arguments: dict) -> dict:
        """Mock tool call with failure simulation and performance tracking."""
        self.call_count += 1
        self._tool_call_count += 1
        start_time = time.time()
        
        # Simulate random failures
        if self.simulate_failures:
            import random
            if random.random() < self.failure_rate:
                self.failure_count += 1
                self._error_count += 1
                if random.random() < 0.5:
                    raise MCPTimeoutError(f"Mock timeout for {tool_name}", self.service_name)
                else:
                    raise MCPError(f"Mock error for {tool_name}", self.service_name)
        
        # Simulate processing time
        await asyncio.sleep(self.response_delay)
        
        execution_time = int((time.time() - start_time) * 1000)
        
        return {
            "success": True,
            "service": self.service_name,
            "tool": tool_name,
            "arguments": arguments,
            "result": f"Mock result from {tool_name}",
            "execution_time_ms": execution_time,
            "call_count": self.call_count,
            "timestamp": datetime.now().isoformat()
        }
    
    async def check_health(self) -> HealthStatus:
        """Mock health check with failure simulation."""
        if self.simulate_failures and self.call_count % 20 == 0:
            self._consecutive_health_failures += 1
            return HealthStatus(
                is_healthy=False,
                last_check=datetime.now(),
                response_time_ms=5000,
                available_tools=0,
                error_message="Mock health check failure",
                connection_status=self._connection_status.value,
                consecutive_failures=self._consecutive_health_failures
            )
        
        return HealthStatus(
            is_healthy=True,
            last_check=datetime.now(),
            response_time_ms=50 + (self.call_count % 100),  # Simulate variable response times
            available_tools=len(self._available_tools),
            connection_status=self._connection_status.value,
            consecutive_failures=0
        )
    
    async def reconnect(self):
        """Mock reconnection with recovery simulation."""
        self._recovery_in_progress = True
        await asyncio.sleep(0.1)  # Simulate recovery time
        await self.connect()
        self._recovery_in_progress = False
        self._consecutive_timeouts = 0
        self._consecutive_health_failures = 0


class ComprehensiveMCPIntegrationTest:
    """Comprehensive integration test suite for MCP client standardization."""
    
    def __init__(self):
        self.test_results = {}
        self.performance_metrics = {}
        self.error_scenarios = {}
        
    async def setup_test_environment(self) -> MCPClientManager:
        """Set up test environment with mock MCP clients."""
        logger.info("Setting up comprehensive test environment")
        
        # Create manager with test configuration
        manager = MCPClientManager(max_connections=5)
        
        # Register mock services with different characteristics
        services = {
            "salesforce": {
                "tools": ["salesforce_get_accounts", "salesforce_get_opportunities", "salesforce_create_lead"],
                "failure_rate": 0.05,
                "response_delay": 0.1
            },
            "gmail": {
                "tools": ["gmail_send_email", "gmail_list_messages", "gmail_search_messages"],
                "failure_rate": 0.03,
                "response_delay": 0.15
            },
            "zoho": {
                "tools": ["zoho_get_invoices", "zoho_get_customers", "zoho_create_invoice"],
                "failure_rate": 0.08,
                "response_delay": 0.2
            },
            "bill_com": {
                "tools": ["bill_com_get_vendors", "bill_com_get_audit_trail", "bill_com_detect_exceptions"],
                "failure_rate": 0.02,
                "response_delay": 0.12
            }
        }
        
        for service_name, config in services.items():
            async def create_client(name=service_name, cfg=config):
                client = MockMCPClient(
                    service_name=name,
                    tools=cfg["tools"],
                    simulate_failures=True,
                    failure_rate=cfg["failure_rate"],
                    response_delay=cfg["response_delay"]
                )
                await client.connect()
                return client
            
            manager.register_service(service_name, create_client)
        
        # Initialize tool discovery
        await manager.discover_tools()
        
        logger.info(f"Test environment setup complete with {len(services)} services")
        return manager
    
    async def test_end_to_end_mcp_workflow(self, manager: MCPClientManager) -> Dict[str, Any]:
        """
        Test complete end-to-end MCP workflow.
        
        Validates Requirements: 5.1, 5.2
        """
        logger.info("=== Testing End-to-End MCP Workflow ===")
        
        test_result = {
            "test_name": "end_to_end_workflow",
            "start_time": datetime.now(),
            "success": False,
            "steps_completed": [],
            "errors": [],
            "performance": {}
        }
        
        try:
            # Step 1: Service Discovery
            start_time = time.time()
            tools_by_service = await manager.discover_tools()
            discovery_time = time.time() - start_time
            
            test_result["steps_completed"].append("service_discovery")
            test_result["performance"]["discovery_time_ms"] = int(discovery_time * 1000)
            
            assert len(tools_by_service) >= 4, f"Expected 4+ services, got {len(tools_by_service)}"
            logger.info(f"✅ Service discovery: {len(tools_by_service)} services found")
            
            # Step 2: Health Check All Services
            start_time = time.time()
            health_status = await manager.get_all_service_health()
            health_check_time = time.time() - start_time
            
            test_result["steps_completed"].append("health_check")
            test_result["performance"]["health_check_time_ms"] = int(health_check_time * 1000)
            
            healthy_services = sum(1 for h in health_status.values() if h.is_healthy)
            assert healthy_services >= 3, f"Expected 3+ healthy services, got {healthy_services}"
            logger.info(f"✅ Health check: {healthy_services}/{len(health_status)} services healthy")
            
            # Step 3: Sequential Tool Calls
            sequential_results = []
            start_time = time.time()
            
            for service_name in ["salesforce", "gmail", "zoho"]:
                if service_name in tools_by_service:
                    tools = tools_by_service[service_name]
                    if tools:
                        tool_name = tools[0].name
                        result = await manager.call_tool(
                            service_name, 
                            tool_name, 
                            {"test_param": f"sequential_test_{service_name}"}
                        )
                        sequential_results.append({
                            "service": service_name,
                            "tool": tool_name,
                            "success": result.get("success", False)
                        })
            
            sequential_time = time.time() - start_time
            test_result["steps_completed"].append("sequential_tool_calls")
            test_result["performance"]["sequential_time_ms"] = int(sequential_time * 1000)
            test_result["performance"]["sequential_results"] = sequential_results
            
            successful_calls = sum(1 for r in sequential_results if r["success"])
            assert successful_calls >= 2, f"Expected 2+ successful calls, got {successful_calls}"
            logger.info(f"✅ Sequential calls: {successful_calls}/{len(sequential_results)} successful")
            
            # Step 4: Manager Statistics
            stats = manager.get_manager_stats()
            test_result["steps_completed"].append("statistics_collection")
            test_result["performance"]["manager_stats"] = stats
            
            logger.info(f"✅ Manager stats: {stats}")
            
            test_result["success"] = True
            logger.info("✅ End-to-end workflow test completed successfully")
            
        except Exception as e:
            test_result["errors"].append(str(e))
            logger.error(f"❌ End-to-end workflow test failed: {e}")
        
        finally:
            test_result["end_time"] = datetime.now()
            test_result["duration_ms"] = int(
                (test_result["end_time"] - test_result["start_time"]).total_seconds() * 1000
            )
        
        return test_result
    
    async def test_multi_service_agent_workflow(self, manager: MCPClientManager) -> Dict[str, Any]:
        """
        Test multi-service tool calls within single agent workflow.
        
        Validates Requirements: 5.1, 5.2
        """
        logger.info("=== Testing Multi-Service Agent Workflow ===")
        
        test_result = {
            "test_name": "multi_service_workflow",
            "start_time": datetime.now(),
            "success": False,
            "agent_results": {},
            "cross_service_calls": [],
            "errors": []
        }
        
        try:
            # Create category-based agents with mock MCP manager
            crm_agent = CRMAgent(manager)
            email_agent = EmailAgent(manager)
            ap_agent = AccountsPayableAgent(manager)
            
            # Simulate complex workflow: CRM -> Email -> AccountsPayable
            workflow_steps = []
            
            # Step 1: CRM Agent - Get account data
            try:
                crm_result = await crm_agent.get_accounts(
                    service="salesforce",
                    limit=5,
                    status="active"
                )
                workflow_steps.append({
                    "agent": "crm",
                    "service": "salesforce",
                    "operation": "get_accounts",
                    "success": crm_result.get("success", False),
                    "result_size": len(str(crm_result))
                })
                test_result["agent_results"]["crm"] = crm_result
                logger.info("✅ CRM agent completed successfully")
            except Exception as e:
                workflow_steps.append({
                    "agent": "crm",
                    "service": "salesforce",
                    "operation": "get_accounts",
                    "success": False,
                    "error": str(e)
                })
                logger.warning(f"⚠️ CRM agent failed: {e}")
            
            # Step 2: Email Agent - Send notification
            try:
                email_result = await email_agent.send_email(
                    service="gmail",
                    to="test@example.com",
                    subject="Account Update",
                    body="Account data has been updated"
                )
                workflow_steps.append({
                    "agent": "email",
                    "service": "gmail",
                    "operation": "send_email",
                    "success": email_result.get("success", False),
                    "result_size": len(str(email_result))
                })
                test_result["agent_results"]["email"] = email_result
                logger.info("✅ Email agent completed successfully")
            except Exception as e:
                workflow_steps.append({
                    "agent": "email",
                    "service": "gmail",
                    "operation": "send_email",
                    "success": False,
                    "error": str(e)
                })
                logger.warning(f"⚠️ Email agent failed: {e}")
            
            # Step 3: AccountsPayable Agent - Get invoice data
            try:
                ap_result = await ap_agent.get_invoices(
                    service="zoho",
                    limit=10,
                    status="pending"
                )
                workflow_steps.append({
                    "agent": "accounts_payable",
                    "service": "zoho",
                    "operation": "get_invoices",
                    "success": ap_result.get("success", False),
                    "result_size": len(str(ap_result))
                })
                test_result["agent_results"]["accounts_payable"] = ap_result
                logger.info("✅ AccountsPayable agent completed successfully")
            except Exception as e:
                workflow_steps.append({
                    "agent": "accounts_payable",
                    "service": "zoho",
                    "operation": "get_invoices",
                    "success": False,
                    "error": str(e)
                })
                logger.warning(f"⚠️ AccountsPayable agent failed: {e}")
            
            # Step 4: Cross-service data correlation
            try:
                # Simulate cross-service call: Use CRM data to update AP records
                if test_result["agent_results"].get("crm") and test_result["agent_results"].get("accounts_payable"):
                    correlation_result = await ap_agent.update_customer_info(
                        service="zoho",
                        customer_data=test_result["agent_results"]["crm"]
                    )
                    test_result["cross_service_calls"].append({
                        "from_service": "salesforce",
                        "to_service": "zoho",
                        "operation": "update_customer_info",
                        "success": correlation_result.get("success", False)
                    })
                    logger.info("✅ Cross-service correlation completed")
            except Exception as e:
                test_result["cross_service_calls"].append({
                    "from_service": "salesforce",
                    "to_service": "zoho",
                    "operation": "update_customer_info",
                    "success": False,
                    "error": str(e)
                })
                logger.warning(f"⚠️ Cross-service correlation failed: {e}")
            
            test_result["workflow_steps"] = workflow_steps
            
            # Validate workflow success
            successful_steps = sum(1 for step in workflow_steps if step["success"])
            total_steps = len(workflow_steps)
            
            if successful_steps >= total_steps * 0.7:  # 70% success rate
                test_result["success"] = True
                logger.info(f"✅ Multi-service workflow: {successful_steps}/{total_steps} steps successful")
            else:
                logger.warning(f"⚠️ Multi-service workflow: Only {successful_steps}/{total_steps} steps successful")
            
        except Exception as e:
            test_result["errors"].append(str(e))
            logger.error(f"❌ Multi-service workflow test failed: {e}")
        
        finally:
            test_result["end_time"] = datetime.now()
            test_result["duration_ms"] = int(
                (test_result["end_time"] - test_result["start_time"]).total_seconds() * 1000
            )
        
        return test_result
    
    async def test_error_recovery_across_services(self, manager: MCPClientManager) -> Dict[str, Any]:
        """
        Test error recovery across service boundaries.
        
        Validates Requirements: 5.3
        """
        logger.info("=== Testing Error Recovery Across Services ===")
        
        test_result = {
            "test_name": "error_recovery",
            "start_time": datetime.now(),
            "success": False,
            "recovery_scenarios": [],
            "errors": []
        }
        
        try:
            # Scenario 1: Service timeout recovery
            logger.info("Testing timeout recovery...")
            timeout_scenario = await self._test_timeout_recovery(manager)
            test_result["recovery_scenarios"].append(timeout_scenario)
            
            # Scenario 2: Connection failure recovery
            logger.info("Testing connection failure recovery...")
            connection_scenario = await self._test_connection_failure_recovery(manager)
            test_result["recovery_scenarios"].append(connection_scenario)
            
            # Scenario 3: Service degradation handling
            logger.info("Testing service degradation handling...")
            degradation_scenario = await self._test_service_degradation(manager)
            test_result["recovery_scenarios"].append(degradation_scenario)
            
            # Scenario 4: Cross-service error propagation
            logger.info("Testing cross-service error propagation...")
            propagation_scenario = await self._test_error_propagation(manager)
            test_result["recovery_scenarios"].append(propagation_scenario)
            
            # Evaluate overall recovery success
            successful_recoveries = sum(1 for s in test_result["recovery_scenarios"] if s["recovered"])
            total_scenarios = len(test_result["recovery_scenarios"])
            
            if successful_recoveries >= total_scenarios * 0.75:  # 75% recovery rate
                test_result["success"] = True
                logger.info(f"✅ Error recovery: {successful_recoveries}/{total_scenarios} scenarios recovered")
            else:
                logger.warning(f"⚠️ Error recovery: Only {successful_recoveries}/{total_scenarios} scenarios recovered")
            
        except Exception as e:
            test_result["errors"].append(str(e))
            logger.error(f"❌ Error recovery test failed: {e}")
        
        finally:
            test_result["end_time"] = datetime.now()
            test_result["duration_ms"] = int(
                (test_result["end_time"] - test_result["start_time"]).total_seconds() * 1000
            )
        
        return test_result
    
    async def _test_timeout_recovery(self, manager: MCPClientManager) -> Dict[str, Any]:
        """Test timeout recovery scenario."""
        scenario = {
            "name": "timeout_recovery",
            "recovered": False,
            "attempts": 0,
            "recovery_time_ms": 0
        }
        
        start_time = time.time()
        
        try:
            # Force timeout by calling non-existent tool
            for attempt in range(3):
                scenario["attempts"] += 1
                try:
                    await manager.call_tool("salesforce", "non_existent_tool", {})
                    break
                except (MCPTimeoutError, MCPError) as e:
                    if attempt == 2:  # Last attempt
                        # Try recovery with valid tool
                        result = await manager.call_tool("salesforce", "salesforce_get_accounts", {})
                        if result.get("success"):
                            scenario["recovered"] = True
                    await asyncio.sleep(0.1)  # Brief pause between attempts
        
        except Exception:
            pass  # Expected for this test
        
        scenario["recovery_time_ms"] = int((time.time() - start_time) * 1000)
        return scenario
    
    async def _test_connection_failure_recovery(self, manager: MCPClientManager) -> Dict[str, Any]:
        """Test connection failure recovery scenario."""
        scenario = {
            "name": "connection_failure_recovery",
            "recovered": False,
            "reconnection_attempts": 0,
            "recovery_time_ms": 0
        }
        
        start_time = time.time()
        
        try:
            # Simulate connection failure by forcing reconnection
            client = await manager.get_client("gmail")
            if hasattr(client, 'reconnect'):
                scenario["reconnection_attempts"] += 1
                await client.reconnect()
                
                # Test if service is working after reconnection
                result = await manager.call_tool("gmail", "gmail_send_email", {"test": "recovery"})
                if result.get("success"):
                    scenario["recovered"] = True
        
        except Exception:
            pass  # Expected for this test
        
        scenario["recovery_time_ms"] = int((time.time() - start_time) * 1000)
        return scenario
    
    async def _test_service_degradation(self, manager: MCPClientManager) -> Dict[str, Any]:
        """Test service degradation handling."""
        scenario = {
            "name": "service_degradation",
            "recovered": False,
            "fallback_used": False,
            "recovery_time_ms": 0
        }
        
        start_time = time.time()
        
        try:
            # Test health monitoring during degradation
            health_before = await manager.get_all_service_health()
            healthy_before = sum(1 for h in health_before.values() if h.is_healthy)
            
            # Simulate some service calls that might fail
            results = []
            for i in range(5):
                try:
                    result = await manager.call_tool("zoho", "zoho_get_invoices", {"test": f"degradation_{i}"})
                    results.append(result.get("success", False))
                except Exception:
                    results.append(False)
            
            # Check if system handled degradation gracefully
            success_rate = sum(results) / len(results)
            if success_rate >= 0.6:  # 60% success during degradation
                scenario["recovered"] = True
            
            # Check if fallback mechanisms were used
            health_after = await manager.get_all_service_health()
            healthy_after = sum(1 for h in health_after.values() if h.is_healthy)
            
            if healthy_after >= healthy_before:
                scenario["fallback_used"] = True
        
        except Exception:
            pass  # Expected for this test
        
        scenario["recovery_time_ms"] = int((time.time() - start_time) * 1000)
        return scenario
    
    async def _test_error_propagation(self, manager: MCPClientManager) -> Dict[str, Any]:
        """Test cross-service error propagation."""
        scenario = {
            "name": "error_propagation",
            "recovered": False,
            "isolation_maintained": False,
            "recovery_time_ms": 0
        }
        
        start_time = time.time()
        
        try:
            # Test that errors in one service don't affect others
            services = ["salesforce", "gmail", "zoho"]
            service_results = {}
            
            for service in services:
                try:
                    # Make a call that might fail
                    tools = await manager.discover_tools()
                    if service in tools and tools[service]:
                        tool_name = tools[service][0].name
                        result = await manager.call_tool(service, tool_name, {"test": "isolation"})
                        service_results[service] = result.get("success", False)
                    else:
                        service_results[service] = False
                except Exception:
                    service_results[service] = False
            
            # Check if at least some services remained operational
            working_services = sum(1 for success in service_results.values() if success)
            if working_services >= len(services) * 0.5:  # 50% services still working
                scenario["isolation_maintained"] = True
                scenario["recovered"] = True
        
        except Exception:
            pass  # Expected for this test
        
        scenario["recovery_time_ms"] = int((time.time() - start_time) * 1000)
        return scenario
    
    async def test_concurrent_performance(self, manager: MCPClientManager) -> Dict[str, Any]:
        """
        Test performance with concurrent MCP tool calls.
        
        Validates Requirements: 5.4
        """
        logger.info("=== Testing Concurrent Performance ===")
        
        test_result = {
            "test_name": "concurrent_performance",
            "start_time": datetime.now(),
            "success": False,
            "performance_metrics": {},
            "concurrency_tests": [],
            "errors": []
        }
        
        try:
            # Test different concurrency levels
            concurrency_levels = [1, 5, 10, 20]
            
            for concurrency in concurrency_levels:
                logger.info(f"Testing concurrency level: {concurrency}")
                
                concurrency_result = await self._test_concurrency_level(manager, concurrency)
                test_result["concurrency_tests"].append(concurrency_result)
                
                # Brief pause between tests
                await asyncio.sleep(0.5)
            
            # Analyze performance trends
            performance_analysis = self._analyze_performance_trends(test_result["concurrency_tests"])
            test_result["performance_metrics"] = performance_analysis
            
            # Determine success based on performance criteria
            if (performance_analysis.get("max_throughput", 0) >= 10 and  # 10 calls/second
                performance_analysis.get("error_rate", 1.0) <= 0.1):    # 10% error rate
                test_result["success"] = True
                logger.info("✅ Concurrent performance test passed")
            else:
                logger.warning("⚠️ Concurrent performance test did not meet criteria")
            
        except Exception as e:
            test_result["errors"].append(str(e))
            logger.error(f"❌ Concurrent performance test failed: {e}")
        
        finally:
            test_result["end_time"] = datetime.now()
            test_result["duration_ms"] = int(
                (test_result["end_time"] - test_result["start_time"]).total_seconds() * 1000
            )
        
        return test_result
    
    async def _test_concurrency_level(self, manager: MCPClientManager, concurrency: int) -> Dict[str, Any]:
        """Test specific concurrency level."""
        result = {
            "concurrency_level": concurrency,
            "total_calls": concurrency * 3,  # 3 calls per concurrent task
            "successful_calls": 0,
            "failed_calls": 0,
            "total_time_ms": 0,
            "average_response_time_ms": 0,
            "throughput_per_second": 0,
            "error_rate": 0
        }
        
        start_time = time.time()
        
        async def make_concurrent_calls():
            """Make multiple calls concurrently."""
            tasks = []
            services = ["salesforce", "gmail", "zoho"]
            
            for i in range(concurrency):
                service = services[i % len(services)]
                
                # Create tasks for different operations
                for j in range(3):  # 3 calls per task
                    task = asyncio.create_task(
                        self._make_test_call(manager, service, f"concurrent_{i}_{j}")
                    )
                    tasks.append(task)
            
            # Wait for all tasks to complete
            results = await asyncio.gather(*tasks, return_exceptions=True)
            return results
        
        # Execute concurrent calls
        call_results = await make_concurrent_calls()
        
        # Analyze results
        for call_result in call_results:
            if isinstance(call_result, Exception):
                result["failed_calls"] += 1
            elif isinstance(call_result, dict) and call_result.get("success"):
                result["successful_calls"] += 1
            else:
                result["failed_calls"] += 1
        
        # Calculate metrics
        total_time = time.time() - start_time
        result["total_time_ms"] = int(total_time * 1000)
        
        if result["total_calls"] > 0:
            result["error_rate"] = result["failed_calls"] / result["total_calls"]
            result["throughput_per_second"] = result["total_calls"] / total_time
            result["average_response_time_ms"] = int(
                (total_time * 1000) / result["total_calls"]
            )
        
        logger.info(
            f"Concurrency {concurrency}: {result['successful_calls']}/{result['total_calls']} "
            f"successful, {result['throughput_per_second']:.2f} calls/sec"
        )
        
        return result
    
    async def _make_test_call(self, manager: MCPClientManager, service: str, test_id: str) -> Dict[str, Any]:
        """Make a single test call."""
        try:
            tools = await manager.discover_tools()
            if service in tools and tools[service]:
                tool_name = tools[service][0].name
                return await manager.call_tool(service, tool_name, {"test_id": test_id})
            else:
                return {"success": False, "error": "No tools available"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _analyze_performance_trends(self, concurrency_tests: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze performance trends across concurrency levels."""
        if not concurrency_tests:
            return {}
        
        throughputs = [test["throughput_per_second"] for test in concurrency_tests]
        error_rates = [test["error_rate"] for test in concurrency_tests]
        response_times = [test["average_response_time_ms"] for test in concurrency_tests]
        
        return {
            "max_throughput": max(throughputs) if throughputs else 0,
            "min_throughput": min(throughputs) if throughputs else 0,
            "avg_throughput": sum(throughputs) / len(throughputs) if throughputs else 0,
            "max_error_rate": max(error_rates) if error_rates else 0,
            "avg_error_rate": sum(error_rates) / len(error_rates) if error_rates else 0,
            "max_response_time": max(response_times) if response_times else 0,
            "avg_response_time": sum(response_times) / len(response_times) if response_times else 0,
            "scalability_factor": (
                (max(throughputs) / min(throughputs)) if throughputs and min(throughputs) > 0 else 1
            )
        }
    
    async def run_comprehensive_test_suite(self) -> Dict[str, Any]:
        """Run the complete comprehensive integration test suite."""
        logger.info(f"{BOLD}🚀 Starting Comprehensive MCP Integration Test Suite{RESET}")
        
        suite_result = {
            "suite_name": "comprehensive_mcp_integration",
            "start_time": datetime.now(),
            "tests": {},
            "summary": {},
            "success": False
        }
        
        try:
            # Setup test environment
            manager = await self.setup_test_environment()
            
            # Run all test categories
            tests = [
                ("end_to_end_workflow", self.test_end_to_end_mcp_workflow),
                ("multi_service_workflow", self.test_multi_service_agent_workflow),
                ("error_recovery", self.test_error_recovery_across_services),
                ("concurrent_performance", self.test_concurrent_performance)
            ]
            
            for test_name, test_method in tests:
                logger.info(f"\n{BLUE}{'='*60}{RESET}")
                logger.info(f"{BOLD}Running {test_name.replace('_', ' ').title()} Test{RESET}")
                logger.info(f"{BLUE}{'='*60}{RESET}")
                
                try:
                    test_result = await test_method(manager)
                    suite_result["tests"][test_name] = test_result
                    
                    if test_result["success"]:
                        logger.info(f"{GREEN}✅ {test_name} test PASSED{RESET}")
                    else:
                        logger.warning(f"{YELLOW}⚠️ {test_name} test FAILED{RESET}")
                
                except Exception as e:
                    logger.error(f"{RED}❌ {test_name} test ERROR: {e}{RESET}")
                    suite_result["tests"][test_name] = {
                        "test_name": test_name,
                        "success": False,
                        "error": str(e)
                    }
            
            # Cleanup
            await manager.shutdown()
            
            # Generate summary
            suite_result["summary"] = self._generate_test_summary(suite_result["tests"])
            suite_result["success"] = suite_result["summary"]["overall_success"]
            
        except Exception as e:
            logger.error(f"{RED}❌ Test suite setup failed: {e}{RESET}")
            suite_result["setup_error"] = str(e)
        
        finally:
            suite_result["end_time"] = datetime.now()
            suite_result["total_duration_ms"] = int(
                (suite_result["end_time"] - suite_result["start_time"]).total_seconds() * 1000
            )
        
        return suite_result
    
    def _generate_test_summary(self, tests: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive test summary."""
        total_tests = len(tests)
        passed_tests = sum(1 for test in tests.values() if test.get("success", False))
        
        summary = {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": total_tests - passed_tests,
            "success_rate": (passed_tests / total_tests * 100) if total_tests > 0 else 0,
            "overall_success": passed_tests >= total_tests * 0.75,  # 75% pass rate
            "test_details": {}
        }
        
        for test_name, test_result in tests.items():
            summary["test_details"][test_name] = {
                "success": test_result.get("success", False),
                "duration_ms": test_result.get("duration_ms", 0),
                "error_count": len(test_result.get("errors", []))
            }
        
        return summary
    
    def print_final_report(self, suite_result: Dict[str, Any]) -> None:
        """Print comprehensive final report."""
        logger.info(f"\n{BOLD}{'='*80}{RESET}")
        logger.info(f"{BOLD}📊 COMPREHENSIVE MCP INTEGRATION TEST REPORT{RESET}")
        logger.info(f"{BOLD}{'='*80}{RESET}")
        
        summary = suite_result.get("summary", {})
        
        # Overall results
        if suite_result["success"]:
            logger.info(f"{GREEN}🎉 OVERALL RESULT: PASSED{RESET}")
        else:
            logger.info(f"{RED}❌ OVERALL RESULT: FAILED{RESET}")
        
        logger.info(f"\n{BOLD}Summary:{RESET}")
        logger.info(f"  Total Tests: {summary.get('total_tests', 0)}")
        logger.info(f"  Passed: {GREEN}{summary.get('passed_tests', 0)}{RESET}")
        logger.info(f"  Failed: {RED}{summary.get('failed_tests', 0)}{RESET}")
        logger.info(f"  Success Rate: {summary.get('success_rate', 0):.1f}%")
        logger.info(f"  Total Duration: {suite_result.get('total_duration_ms', 0):,}ms")
        
        # Individual test results
        logger.info(f"\n{BOLD}Individual Test Results:{RESET}")
        for test_name, details in summary.get("test_details", {}).items():
            status = f"{GREEN}PASS{RESET}" if details["success"] else f"{RED}FAIL{RESET}"
            logger.info(f"  {test_name.replace('_', ' ').title()}: {status} ({details['duration_ms']:,}ms)")
        
        # Requirements validation
        logger.info(f"\n{BOLD}Requirements Validation:{RESET}")
        requirements = {
            "5.1": "End-to-end MCP workflow testing",
            "5.2": "Multi-service tool calls validation", 
            "5.3": "Error recovery across service boundaries",
            "5.4": "Performance testing with concurrent calls"
        }
        
        for req_id, req_desc in requirements.items():
            # Map requirements to tests
            test_mapping = {
                "5.1": ["end_to_end_workflow", "multi_service_workflow"],
                "5.2": ["end_to_end_workflow", "multi_service_workflow"],
                "5.3": ["error_recovery"],
                "5.4": ["concurrent_performance"]
            }
            
            req_tests = test_mapping.get(req_id, [])
            req_passed = all(
                summary.get("test_details", {}).get(test, {}).get("success", False)
                for test in req_tests
            )
            
            status = f"{GREEN}✅ VALIDATED{RESET}" if req_passed else f"{RED}❌ NOT VALIDATED{RESET}"
            logger.info(f"  Requirement {req_id}: {status}")
            logger.info(f"    {req_desc}")
        
        logger.info(f"\n{BOLD}{'='*80}{RESET}")


async def main():
    """Main test execution function."""
    test_suite = ComprehensiveMCPIntegrationTest()
    
    try:
        # Run comprehensive test suite
        results = await test_suite.run_comprehensive_test_suite()
        
        # Print final report
        test_suite.print_final_report(results)
        
        # Return appropriate exit code
        return 0 if results["success"] else 1
        
    except KeyboardInterrupt:
        logger.info(f"\n{YELLOW}⚠️ Tests interrupted by user{RESET}")
        return 130
    except Exception as e:
        logger.error(f"\n{RED}❌ Test suite failed with unexpected error: {e}{RESET}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)