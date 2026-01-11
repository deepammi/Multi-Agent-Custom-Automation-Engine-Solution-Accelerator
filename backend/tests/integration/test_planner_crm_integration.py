#!/usr/bin/env python3
"""
Planner + HTTP CRM Agent Integration Test Script

This script tests the complete workflow from user query → AI Planner → HTTP CRM Agent
using the working Salesforce MCP server. It demonstrates:

1. AI Planner analyzing CRM-related queries and selecting appropriate agents
2. HTTP CRM Agent executing Salesforce operations via HTTP MCP transport
3. Real LLM calls and real MCP responses with actual Salesforce data
4. Complete workflow integration with WebSocket streaming

**Feature: salesforce-agent-http-integration, Task 6.1**
**Validates: Requirements 5.1, 5.2, 5.3, 5.4, 5.5**
"""

import asyncio
import logging
import os
import sys
import signal
import json
import subprocess
import time
from datetime import datetime
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

# Load environment variables FIRST
load_dotenv()

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('planner_crm_integration_test.log')
    ]
)

# Create a custom logger for our tracing
trace_logger = logging.getLogger("PLANNER_CRM_TRACE")
trace_logger.setLevel(logging.INFO)

# Test scenarios for CRM operations
TEST_SCENARIOS = [
    {
        "name": "Account Retrieval Query",
        "description": "Test AI Planner recognition of account-related queries",
        "user_query": "Show me recent account updates from Salesforce",
        "expected_action": "get_accounts",
        "expected_agents": ["crm", "analysis"],
        "crm_operation": "get_accounts",
        "parameters": {"limit": 5}
    },
    {
        "name": "Opportunity Search Query", 
        "description": "Test AI Planner recognition of opportunity-related queries",
        "user_query": "Find opportunities in closing stage",
        "expected_action": "get_opportunities",
        "expected_agents": ["crm", "analysis"],
        "crm_operation": "get_opportunities",
        "parameters": {"stage": "Closed Won", "limit": 5}
    },
    {
        "name": "Contact Lookup Query",
        "description": "Test AI Planner recognition of contact-related queries", 
        "user_query": "Get contacts for Acme Corporation",
        "expected_action": "get_contacts",
        "expected_agents": ["crm", "analysis"],
        "crm_operation": "get_contacts",
        "parameters": {"account_name": "Acme Corporation", "limit": 5}
    },
    {
        "name": "SOQL Query Request",
        "description": "Test AI Planner recognition of custom query requests",
        "user_query": "Run SOQL query to get top accounts by revenue",
        "expected_action": "run_soql_query",
        "expected_agents": ["crm", "analysis"],
        "crm_operation": "run_soql_query",
        "parameters": {"soql_query": "SELECT Name, AnnualRevenue FROM Account WHERE AnnualRevenue > 0 ORDER BY AnnualRevenue DESC LIMIT 5"}
    },
    {
        "name": "General CRM Search Query",
        "description": "Test AI Planner recognition of general search queries",
        "user_query": "Search for Microsoft in our CRM",
        "expected_action": "search_records",
        "expected_agents": ["crm", "analysis"],
        "crm_operation": "search_records",
        "parameters": {"search_term": "Microsoft", "limit": 5}
    }
]


class PlannerCRMIntegrationTracer:
    """Traces the complete Planner → HTTP CRM Agent workflow with real calls."""
    
    def __init__(self):
        self.trace_steps = []
        self.mcp_server_process = None
        self.start_time = datetime.now()
        
    def log_step(self, step_name: str, inputs: Dict[str, Any], outputs: Dict[str, Any], description: str):
        """Log a step in the integration trace."""
        step = {
            "step_name": step_name,
            "timestamp": datetime.now().isoformat(),
            "inputs": inputs,
            "outputs": outputs,
            "description": description
        }
        self.trace_steps.append(step)
        
        # Also log to our trace logger
        trace_logger.info(
            f"STEP: {step_name}",
            extra={
                "step": step_name,
                "inputs": inputs,
                "outputs": outputs,
                "description": description
            }
        )
    
    async def start_salesforce_mcp_server(self) -> bool:
        """Start the Salesforce MCP server in HTTP mode."""
        try:
            print("🚀 Starting Salesforce MCP server in HTTP mode...")
            
            # Check if server is already running
            try:
                import requests
                # Try different endpoints to check if server is running
                for endpoint in ["/health", "/", "/docs"]:
                    try:
                        response = requests.get(f"http://localhost:9001{endpoint}", timeout=2)
                        if response.status_code in [200, 404]:  # 404 is also valid, means server is running
                            print("✅ Salesforce MCP server already running on port 9001")
                            return True
                    except:
                        continue
            except:
                pass
            
            # Start the server
            server_script = os.path.join(os.path.dirname(__file__), "..", "src", "mcp_server", "mcp_server.py")
            if not os.path.exists(server_script):
                print(f"❌ MCP server script not found at: {server_script}")
                return False
            
            # Start server process
            env = os.environ.copy()
            env["MCP_SERVER_PORT"] = "9001"
            env["MCP_SERVER_HOST"] = "localhost"
            
            self.mcp_server_process = subprocess.Popen(
                [sys.executable, server_script],
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=os.path.dirname(server_script)
            )
            
            # Wait for server to start
            max_attempts = 30
            for attempt in range(max_attempts):
                try:
                    import requests
                    # Try different endpoints to check if server is running
                    for endpoint in ["/health", "/", "/docs"]:
                        try:
                            response = requests.get(f"http://localhost:9001{endpoint}", timeout=2)
                            if response.status_code in [200, 404]:  # 404 is also valid, means server is running
                                print(f"✅ Salesforce MCP server started successfully on port 9001")
                                return True
                        except:
                            continue
                except:
                    pass
                
                await asyncio.sleep(1)
                print(f"⏳ Waiting for server to start... ({attempt + 1}/{max_attempts})")
            
            print("❌ Salesforce MCP server failed to start within timeout")
            return False
            
        except Exception as e:
            print(f"❌ Error starting Salesforce MCP server: {e}")
            return False
    
    async def stop_mcp_servers(self):
        """Stop MCP servers."""
        if self.mcp_server_process:
            print("🛑 Stopping Salesforce MCP server...")
            self.mcp_server_process.terminate()
            try:
                self.mcp_server_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.mcp_server_process.kill()
            self.mcp_server_process = None
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary of the trace."""
        return {
            "total_steps": len(self.trace_steps),
            "start_time": self.start_time.isoformat(),
            "end_time": datetime.now().isoformat(),
            "steps": [step["step_name"] for step in self.trace_steps]
        }


async def trace_planner_crm_integration(test_scenario: Dict[str, Any], tracer: PlannerCRMIntegrationTracer):
    """
    Trace the complete Planner → HTTP CRM Agent integration using REAL LLM and MCP calls.
    
    Args:
        test_scenario: Test scenario configuration
        tracer: Integration tracer instance
        
    Returns:
        Dict containing trace results and success metrics
    """
    user_query = test_scenario["user_query"]
    scenario_name = test_scenario["name"]
    
    print(f"\n🚀 STARTING PLANNER → HTTP CRM AGENT INTEGRATION TRACE")
    print(f"📝 Scenario: {scenario_name}")
    print(f"📝 User Query: '{user_query}'")
    print(f"📝 Expected Action: {test_scenario['expected_action']}")
    print(f"📝 Expected Agents: {test_scenario['expected_agents']}")
    
    try:
        # Import required modules
        from app.services.ai_planner_service import AIPlanner
        from app.services.llm_service import LLMService
        from app.agents.crm_agent_http import CRMAgentHTTP
        
        # Step 1: Environment Validation
        print(f"\n🔧 VALIDATING ENVIRONMENT...")
        
        # Check LLM provider configuration
        llm_provider = os.getenv("LLM_PROVIDER", "gemini")
        print(f"LLM Provider: {llm_provider}")
        
        api_key_env = {
            "openai": "OPENAI_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY",
            "google": "GOOGLE_API_KEY", 
            "gemini": "GOOGLE_API_KEY"
        }.get(llm_provider.lower())
        
        api_key = os.getenv(api_key_env) if api_key_env else None
        if not api_key:
            raise ValueError(f"API key not configured for {llm_provider}. Set {api_key_env} environment variable.")
        
        # Step 2: AI Planner Initialization and Analysis
        print(f"\n🧠 INITIALIZING AI PLANNER...")
        
        llm_service = LLMService()
        planner = AIPlanner(llm_service)
        
        planner_info = {
            "planner_class": "AIPlanner",
            "llm_provider": llm_provider,
            "llm_service_type": type(llm_service).__name__,
            "available_agents": planner.available_agents,
            "agent_capabilities": planner.agent_capabilities
        }
        
        tracer.log_step(
            "AI Planner Initialization",
            {"query": user_query},
            planner_info,
            "Initialize AI Planner with LLM service and agent capabilities"
        )
        
        # Step 3: REAL AI Planner Task Analysis
        print(f"\n🤖 CALLING REAL AI PLANNER FOR TASK ANALYSIS...")
        print(f"Provider: {llm_provider}")
        print(f"Mock Mode: {LLMService.is_mock_mode()}")
        
        # Call the real AI planner for task analysis
        task_analysis = await planner.analyze_task(user_query)
        
        tracer.log_step(
            "REAL AI Planner Task Analysis",
            {
                "user_query": user_query,
                "llm_provider": llm_provider,
                "mock_mode": LLMService.is_mock_mode()
            },
            {
                "complexity": task_analysis.complexity,
                "required_systems": task_analysis.required_systems,
                "business_context": task_analysis.business_context,
                "data_sources_needed": task_analysis.data_sources_needed,
                "estimated_agents": task_analysis.estimated_agents,
                "confidence_score": task_analysis.confidence_score,
                "reasoning": task_analysis.reasoning,
                "is_real_llm": True
            },
            "Real AI Planner analyzes task and determines agent requirements"
        )
        
        # Step 4: REAL AI Planner Agent Sequence Generation
        print(f"\n🎯 CALLING REAL AI PLANNER FOR AGENT SEQUENCE...")
        
        # Generate agent sequence
        agent_sequence = await planner.generate_sequence(task_analysis, user_query)
        
        tracer.log_step(
            "REAL AI Planner Agent Sequence",
            {
                "task_analysis": task_analysis.complexity,
                "user_query": user_query
            },
            {
                "agents": agent_sequence.agents,
                "reasoning": agent_sequence.reasoning,
                "estimated_duration": agent_sequence.estimated_duration,
                "complexity_score": agent_sequence.complexity_score,
                "is_real_llm": True
            },
            "Real AI Planner generates optimal agent execution sequence"
        )
        
        # Step 5: Validate Planner Output for CRM Operations
        crm_agent_selected = any(agent in ["crm", "salesforce", "customer"] for agent in agent_sequence.agents)
        
        validation_result = {
            "agent_sequence": agent_sequence.agents,
            "expected_action": test_scenario["expected_action"],
            "planner_reasoning": agent_sequence.reasoning,
            "crm_agent_selected": crm_agent_selected,
            "validation_passed": crm_agent_selected
        }
        
        tracer.log_step(
            "Planner Output Validation",
            {"expected_agents": ["crm", "salesforce"], "scenario_type": test_scenario["expected_action"]},
            validation_result,
            "Validate that planner selected appropriate agents for CRM operations"
        )
        
        if not crm_agent_selected:
            print(f"⚠️ WARNING: Planner did not select CRM agent for CRM query!")
            print(f"   Selected agents: {agent_sequence.agents}")
            print(f"   Expected: crm or related agent")
        
        # Step 6: HTTP CRM Agent Initialization
        print(f"\n🏢 INITIALIZING HTTP CRM AGENT...")
        
        crm_agent = CRMAgentHTTP()
        
        crm_agent_info = {
            "agent_class": "CRMAgentHTTP",
            "transport": "http",
            "supported_services": list(crm_agent.supported_services.keys()),
            "default_service": "salesforce"
        }
        
        tracer.log_step(
            "HTTP CRM Agent Initialization",
            {"service": "salesforce"},
            crm_agent_info,
            "Initialize HTTP CRM Agent with Salesforce service configuration"
        )
        
        # Step 7: Execute CRM Operation via HTTP MCP
        print(f"\n🔄 EXECUTING CRM OPERATION VIA HTTP MCP...")
        
        crm_operation = test_scenario["crm_operation"]
        parameters = test_scenario["parameters"]
        
        print(f"Operation: {crm_operation}")
        print(f"Parameters: {parameters}")
        
        # Execute the CRM operation
        operation_start_time = time.time()
        
        try:
            if crm_operation == "get_accounts":
                result = await crm_agent.get_accounts(
                    service="salesforce",
                    limit=parameters.get("limit", 5),
                    account_name=parameters.get("account_name")
                )
            elif crm_operation == "get_opportunities":
                result = await crm_agent.get_opportunities(
                    service="salesforce",
                    limit=parameters.get("limit", 5),
                    stage=parameters.get("stage")
                )
            elif crm_operation == "get_contacts":
                result = await crm_agent.get_contacts(
                    service="salesforce",
                    limit=parameters.get("limit", 5),
                    account_name=parameters.get("account_name")
                )
            elif crm_operation == "search_records":
                result = await crm_agent.search_records(
                    service="salesforce",
                    search_term=parameters.get("search_term"),
                    limit=parameters.get("limit", 5)
                )
            elif crm_operation == "run_soql_query":
                result = await crm_agent.run_soql_query(
                    service="salesforce",
                    soql_query=parameters.get("soql_query")
                )
            else:
                raise ValueError(f"Unknown CRM operation: {crm_operation}")
            
            operation_duration = time.time() - operation_start_time
            operation_success = True
            
            print(f"✅ CRM operation completed in {operation_duration:.2f}s")
            
        except Exception as e:
            operation_duration = time.time() - operation_start_time
            operation_success = False
            result = {"error": str(e)}
            print(f"❌ CRM operation failed after {operation_duration:.2f}s: {e}")
        
        # Analyze result structure and content
        result_analysis = {
            "operation_success": operation_success,
            "operation_duration": operation_duration,
            "result_type": type(result).__name__,
            "has_data": bool(result and not result.get("error")),
            "record_count": 0,
            "data_fields": []
        }
        
        if operation_success and isinstance(result, dict):
            if "records" in result:
                result_analysis["record_count"] = len(result["records"])
                if result["records"]:
                    result_analysis["data_fields"] = list(result["records"][0].keys())
            elif "totalSize" in result:
                result_analysis["record_count"] = result["totalSize"]
        
        tracer.log_step(
            "HTTP CRM Operation Execution",
            {
                "operation": crm_operation,
                "parameters": parameters,
                "service": "salesforce"
            },
            result_analysis,
            f"Execute {crm_operation} operation via HTTP MCP transport"
        )
        
        # Step 8: Validate Real Data Content
        print(f"\n🔍 VALIDATING REAL DATA CONTENT...")
        
        data_validation = {
            "has_real_data": False,
            "data_quality": "unknown",
            "sample_records": [],
            "validation_details": {}
        }
        
        if operation_success and isinstance(result, dict) and "records" in result:
            records = result["records"]
            if records:
                data_validation["has_real_data"] = True
                data_validation["sample_records"] = records[:2]  # First 2 records
                
                # Validate data quality based on operation type
                if crm_operation == "get_accounts":
                    has_names = all("Name" in record for record in records)
                    data_validation["validation_details"]["has_account_names"] = has_names
                    data_validation["data_quality"] = "good" if has_names else "poor"
                    
                elif crm_operation == "get_opportunities":
                    has_amounts = any("Amount" in record for record in records)
                    has_stages = all("StageName" in record for record in records)
                    data_validation["validation_details"]["has_amounts"] = has_amounts
                    data_validation["validation_details"]["has_stages"] = has_stages
                    data_validation["data_quality"] = "good" if has_stages else "poor"
                    
                elif crm_operation == "get_contacts":
                    has_emails = any("Email" in record for record in records)
                    has_names = all("Name" in record for record in records)
                    data_validation["validation_details"]["has_emails"] = has_emails
                    data_validation["validation_details"]["has_names"] = has_names
                    data_validation["data_quality"] = "good" if has_names else "poor"
        
        tracer.log_step(
            "Real Data Content Validation",
            {"operation": crm_operation, "expected_fields": test_scenario.get("expected_fields", [])},
            data_validation,
            "Validate that CRM operation returned real Salesforce data with expected structure"
        )
        
        # Step 9: Overall Integration Analysis
        print(f"\n📊 ANALYZING OVERALL INTEGRATION SUCCESS...")
        
        # Calculate success metrics
        planner_accuracy = 1.0 if crm_agent_selected else 0.0
        operation_success_rate = 1.0 if operation_success else 0.0
        data_quality_score = 1.0 if data_validation["has_real_data"] else 0.0
        
        overall_success = (
            planner_accuracy >= 0.9 and  # >90% planner accuracy
            operation_success_rate == 1.0 and  # 100% operation success
            data_quality_score >= 0.8  # Good data quality
        )
        
        scenario_results = {
            "scenario_name": scenario_name,
            "user_query": user_query,
            "planner_success": crm_agent_selected,
            "planner_accuracy": planner_accuracy,
            "operation_success": operation_success,
            "operation_duration": operation_duration,
            "data_quality_score": data_quality_score,
            "overall_success": overall_success,
            "expected_operation": test_scenario.get("expected_action"),
            "actual_agents": agent_sequence.agents,
            "expected_agents": test_scenario["expected_agents"]
        }
        
        tracer.log_step(
            "Overall Integration Analysis",
            {"scenario": test_scenario},
            scenario_results,
            "Analyze overall success of Planner → HTTP CRM Agent integration"
        )
        
        # Return summary
        summary = tracer.get_summary()
        summary["test_scenarios"] = [scenario_results]
        
        # Print Pipeline Summary
        print(f"\n🎯 PLANNER → HTTP CRM AGENT INTEGRATION SUMMARY")
        print(f"{'='*80}")
        print(f"Scenario: {scenario_name}")
        print(f"Total Steps: {summary['total_steps']}")
        print(f"Planner Success: {'✅' if crm_agent_selected else '❌'}")
        print(f"MCP Call Success: {'✅' if operation_success else '❌'}")
        print(f"Data Quality: {'✅' if data_validation['has_real_data'] else '❌'}")
        print(f"Overall Success: {'✅' if overall_success else '❌'}")
        
        print(f"\nExecution Steps:")
        for i, step_name in enumerate(summary["steps"], 1):
            print(f"  {i}. {step_name}")
        
        print(f"\n✅ PLANNER → HTTP CRM AGENT INTEGRATION TRACE COMPLETED")
        print(f"⏰ Completed at: {datetime.now().isoformat()}")
        
        return summary
        
    except Exception as e:
        print(f"\n❌ PLANNER → HTTP CRM AGENT INTEGRATION TRACE FAILED: {e}")
        import traceback
        traceback.print_exc()
        return None


async def run_all_test_scenarios():
    """Run all test scenarios and provide comprehensive analysis."""
    
    print("🔍 Planner + HTTP CRM Agent Integration Test Suite")
    print("=" * 80)
    print("This tool tests the complete workflow from user query → AI Planner → HTTP CRM Agent")
    print("using the working Salesforce MCP server with REAL LLM calls and REAL MCP responses.")
    print("=" * 80)
    
    # Initialize tracer
    tracer = PlannerCRMIntegrationTracer()
    
    # Setup signal handlers for cleanup
    def signal_handler(signum, frame):
        print(f"\n🛑 Received signal {signum}. Cleaning up...")
        asyncio.create_task(tracer.stop_mcp_servers())
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Step 1: Start Salesforce MCP Server
        print(f"\n🚀 STARTING SALESFORCE MCP SERVER...")
        server_started = await tracer.start_salesforce_mcp_server()
        
        if not server_started:
            print(f"❌ Cannot continue - Salesforce MCP server failed to start")
            return
        
        # Wait for server to fully initialize
        print(f"⏳ Waiting for server to fully initialize...")
        await asyncio.sleep(5)
        
        # Check environment setup
        print(f"\n🔧 ENVIRONMENT CHECK:")
        os.environ["LLM_PROVIDER"] = "gemini"  # Force Gemini
        os.environ["USE_MOCK_LLM"] = "false"  # Use REAL LLM calls
        llm_provider = os.getenv("LLM_PROVIDER", "gemini")
        print(f"   LLM Provider: {llm_provider}")
        
        api_key_env = {
            "openai": "OPENAI_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY", 
            "google": "GOOGLE_API_KEY",
            "gemini": "GOOGLE_API_KEY"
        }.get(llm_provider.lower())
        
        api_key = os.getenv(api_key_env) if api_key_env else None
        print(f"   API Key: {'✅ Configured' if api_key else '❌ Missing'}")
        
        # Check for real API key
        use_mock = os.getenv("USE_MOCK_LLM", "false").lower() == "true"
        if not use_mock and not api_key:
            print(f"\n❌ ERROR: {api_key_env} environment variable not set!")
            print(f"   Please set your API key: export {api_key_env}=your_key_here")
            return
        
        print(f"   MCP Server: http://localhost:9001")
        print(f"   Mock Mode: {'❌ DISABLED' if not use_mock else '✅ ENABLED'} (using {'real' if not use_mock else 'mock'} LLM responses)")
        print(f"   Salesforce Org: {os.getenv('SALESFORCE_ORG_ALIAS', 'default')}")
        
        # Run all test scenarios
        results = []
        successful_scenarios = 0
        
        for i, scenario in enumerate(TEST_SCENARIOS, 1):
            print(f"\n{'🔥' * 20} SCENARIO {i}/{len(TEST_SCENARIOS)} {'🔥' * 20}")
            print(f"Testing: {scenario['name']}")
            print(f"Description: {scenario['description']}")
            
            try:
                result = await trace_planner_crm_integration(scenario, tracer)
                if result:
                    results.append(result)
                    # Check if scenario was successful
                    scenario_success = False
                    if result.get('test_scenarios'):
                        scenario_success = result['test_scenarios'][-1].get('overall_success', False)
                    
                    if scenario_success:
                        successful_scenarios += 1
                        print(f"✅ Scenario {i} PASSED: {scenario['name']}")
                    else:
                        print(f"❌ Scenario {i} FAILED: {scenario['name']}")
                else:
                    print(f"💥 Scenario {i} CRASHED: {scenario['name']}")
                    
            except Exception as e:
                print(f"💥 Scenario {i} ERROR: {scenario['name']} - {e}")
            
            # Brief pause between scenarios
            await asyncio.sleep(2)
        
        # Final Summary
        print(f"\n{'🎉' * 20} FINAL RESULTS {'🎉' * 20}")
        print(f"Total Scenarios: {len(TEST_SCENARIOS)}")
        print(f"Successful: {successful_scenarios}")
        print(f"Failed: {len(TEST_SCENARIOS) - successful_scenarios}")
        print(f"Success Rate: {(successful_scenarios / len(TEST_SCENARIOS)) * 100:.1f}%")
        
        # Target: >90% accuracy for CRM query recognition
        target_accuracy = 0.9
        actual_accuracy = successful_scenarios / len(TEST_SCENARIOS)
        
        if actual_accuracy >= target_accuracy:
            print(f"🎯 TARGET ACHIEVED: {actual_accuracy:.1%} >= {target_accuracy:.1%}")
            print(f"✅ AI Planner CRM query recognition meets requirements!")
        else:
            print(f"⚠️ TARGET MISSED: {actual_accuracy:.1%} < {target_accuracy:.1%}")
            print(f"❌ AI Planner CRM query recognition needs improvement")
        
        # Save detailed results
        results_file = f"planner_crm_integration_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_file, 'w') as f:
            json.dump({
                "test_summary": {
                    "total_scenarios": len(TEST_SCENARIOS),
                    "successful_scenarios": successful_scenarios,
                    "success_rate": actual_accuracy,
                    "target_accuracy": target_accuracy,
                    "target_achieved": actual_accuracy >= target_accuracy,
                    "timestamp": datetime.now().isoformat()
                },
                "detailed_results": results
            }, f, indent=2)
        
        print(f"\n📄 Detailed results saved to: {results_file}")
        
    finally:
        # Cleanup
        await tracer.stop_mcp_servers()
        print(f"\n🧹 Cleanup completed")


if __name__ == "__main__":
    print("🚀 Starting Planner + HTTP CRM Agent Integration Test")
    print("=" * 80)
    
    try:
        asyncio.run(run_all_test_scenarios())
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")
    except Exception as e:
        print(f"\n💥 Test failed with error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n✅ Test execution completed")