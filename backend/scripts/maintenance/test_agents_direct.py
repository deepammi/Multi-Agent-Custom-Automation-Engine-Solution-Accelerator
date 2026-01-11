#!/usr/bin/env python3
"""
Direct Agent Test Script

Tests agents directly without MCP server dependency to isolate issues.
This bypasses the MCP connection layer to test agent logic directly.
"""

import asyncio
import sys
import os
import json
import logging
from datetime import datetime, timezone
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Test query
TEST_QUERY = "What is the status of Payment Invoice number Acme Marketing Invoice number Inv-1001"

class DirectAgentTester:
    """Test agents directly without MCP server dependency."""
    
    def __init__(self):
        """Initialize the tester."""
        self.test_query = TEST_QUERY
    
    def print_header(self, title: str):
        """Print formatted header."""
        print(f"\n{'=' * 80}")
        print(f"🧪 {title}")
        print(f"{'=' * 80}")
    
    def print_section(self, title: str):
        """Print section header."""
        print(f"\n🔹 {title}")
        print("-" * (len(title) + 4))
    
    async def test_gmail_agent_direct(self):
        """Test Gmail agent directly."""
        self.print_section("Testing Gmail Agent Direct")
        
        try:
            from app.agents.gmail_agent_node import GmailAgentNode
            
            print(f"📧 Initializing Gmail agent...")
            agent = GmailAgentNode()
            
            print(f"✅ Gmail agent initialized: {type(agent).__name__}")
            
            # Create minimal test state
            test_state = {
                "task_description": self.test_query,
                "plan_id": f"test-direct-gmail-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}",
                "session_id": "test-session-direct",
                "messages": [],
                "collected_data": {},
                "execution_results": [],
                "final_result": "",
                "agent_sequence": ["gmail"],
                "current_step": 0,
                "total_steps": 1,
                "current_agent": "gmail",
                "approval_required": False,
                "awaiting_user_input": False
            }
            
            print(f"🔄 Processing query directly...")
            print(f"   Query: {self.test_query}")
            
            # Call agent directly
            result = await agent.process(test_state)
            
            print(f"\n📊 Gmail Agent Direct Result:")
            print(f"   Result Type: {type(result)}")
            print(f"   Result Keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
            
            if isinstance(result, dict):
                # Show key information
                for key in ['task_description', 'messages', 'final_result', 'execution_results']:
                    if key in result:
                        value = result[key]
                        if isinstance(value, str) and len(value) > 200:
                            print(f"   {key}: {value[:200]}...")
                        elif isinstance(value, list):
                            print(f"   {key}: {len(value)} items")
                        else:
                            print(f"   {key}: {value}")
            
            print(f"\n📋 Full Gmail Agent Result:")
            print(json.dumps(result, indent=2, default=str))
            
            return result
        
        except Exception as e:
            print(f"❌ Gmail agent direct test error: {e}")
            import traceback
            traceback.print_exc()
            return {"status": "error", "error": str(e)}
    
    async def test_salesforce_agent_direct(self):
        """Test Salesforce agent directly."""
        self.print_section("Testing Salesforce Agent Direct")
        
        try:
            from app.agents.salesforce_node import salesforce_agent_node
            from app.agents.state import AgentState
            
            print(f"🏢 Testing Salesforce agent function...")
            
            # Create proper AgentState
            agent_state = AgentState(
                task_description=self.test_query,
                plan_id=f"test-direct-sf-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}",
                session_id="test-session-direct",
                messages=[],
                collected_data={},
                execution_results=[],
                final_result="",
                agent_sequence=["salesforce"],
                current_step=0,
                total_steps=1,
                current_agent="salesforce",
                approval_required=False,
                awaiting_user_input=False
            )
            
            print(f"✅ AgentState created for Salesforce")
            
            print(f"🔄 Processing query directly...")
            print(f"   Query: {self.test_query}")
            
            # Call agent function directly
            result = await salesforce_agent_node(agent_state)
            
            print(f"\n📊 Salesforce Agent Direct Result:")
            print(f"   Result Type: {type(result)}")
            print(f"   Result Keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
            
            if isinstance(result, dict):
                # Show key information
                for key in ['task_description', 'messages', 'final_result', 'execution_results']:
                    if key in result:
                        value = result[key]
                        if isinstance(value, str) and len(value) > 200:
                            print(f"   {key}: {value[:200]}...")
                        elif isinstance(value, list):
                            print(f"   {key}: {len(value)} items")
                        else:
                            print(f"   {key}: {value}")
            
            print(f"\n📋 Full Salesforce Agent Result:")
            print(json.dumps(result, indent=2, default=str))
            
            return result
        
        except Exception as e:
            print(f"❌ Salesforce agent direct test error: {e}")
            import traceback
            traceback.print_exc()
            return {"status": "error", "error": str(e)}
    
    async def test_invoice_agent_direct(self):
        """Test Invoice agent directly."""
        self.print_section("Testing Invoice Agent Direct")
        
        try:
            from app.agents.accounts_payable_agent_node import accounts_payable_agent_node
            from app.agents.state import AgentState
            
            print(f"💰 Testing Accounts Payable/Invoice agent function...")
            
            # Create proper AgentState
            agent_state = AgentState(
                task_description=self.test_query,
                plan_id=f"test-direct-inv-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}",
                session_id="test-session-direct",
                messages=[],
                collected_data={},
                execution_results=[],
                final_result="",
                agent_sequence=["invoice"],
                current_step=0,
                total_steps=1,
                current_agent="invoice",
                approval_required=False,
                awaiting_user_input=False
            )
            
            print(f"✅ AgentState created for Invoice/AP")
            
            print(f"🔄 Processing query directly...")
            print(f"   Query: {self.test_query}")
            
            # Call agent function directly
            result = await accounts_payable_agent_node(agent_state)
            
            print(f"\n📊 Invoice Agent Direct Result:")
            print(f"   Result Type: {type(result)}")
            print(f"   Result Keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
            
            if isinstance(result, dict):
                # Show key information
                for key in ['task_description', 'messages', 'final_result', 'execution_results']:
                    if key in result:
                        value = result[key]
                        if isinstance(value, str) and len(value) > 200:
                            print(f"   {key}: {value[:200]}...")
                        elif isinstance(value, list):
                            print(f"   {key}: {len(value)} items")
                        else:
                            print(f"   {key}: {value}")
            
            print(f"\n📋 Full Invoice Agent Result:")
            print(json.dumps(result, indent=2, default=str))
            
            return result
        
        except Exception as e:
            print(f"❌ Invoice agent direct test error: {e}")
            import traceback
            traceback.print_exc()
            return {"status": "error", "error": str(e)}
    
    async def test_ai_planner_direct(self):
        """Test AI Planner directly."""
        self.print_section("Testing AI Planner Direct")
        
        try:
            from app.services.ai_planner_service import AIPlanner
            from app.services.llm_service import LLMService
            
            print(f"🧠 Initializing AI Planner...")
            
            # Create LLM service first
            llm_service = LLMService()
            planner = AIPlanner(llm_service)
            
            print(f"✅ AI Planner initialized: {type(planner).__name__}")
            
            print(f"🔄 Analyzing task directly...")
            print(f"   Query: {self.test_query}")
            
            # Call planner directly
            result = await planner.analyze_task(self.test_query)
            
            print(f"\n📊 AI Planner Direct Result:")
            print(f"   Result Type: {type(result)}")
            
            if hasattr(result, '__dict__'):
                print(f"   Result Attributes: {list(result.__dict__.keys())}")
                for key, value in result.__dict__.items():
                    if isinstance(value, str) and len(value) > 100:
                        print(f"   {key}: {value[:100]}...")
                    else:
                        print(f"   {key}: {value}")
            
            print(f"\n📋 Full AI Planner Result:")
            print(f"   {result}")
            
            return {"status": "success", "result": str(result)}
        
        except Exception as e:
            print(f"❌ AI Planner direct test error: {e}")
            import traceback
            traceback.print_exc()
            return {"status": "error", "error": str(e)}
    
    def analyze_direct_results(self, results: dict):
        """Analyze results from direct agent tests."""
        self.print_section("Direct Test Results Analysis")
        
        print(f"🔍 Analyzing results from {len(results)} components...")
        
        for component_name, result in results.items():
            print(f"\n📊 {component_name.title()} Analysis:")
            
            if isinstance(result, dict):
                status = result.get('status', 'unknown')
                error = result.get('error')
                
                if error:
                    print(f"   ❌ Status: {status}")
                    print(f"   Error: {error}")
                    
                    # Analyze error type
                    if "import" in error.lower():
                        print(f"   🔧 Issue: Import/dependency problem")
                    elif "mcp" in error.lower():
                        print(f"   🔧 Issue: MCP connection problem")
                    elif "credentials" in error.lower():
                        print(f"   🔧 Issue: Authentication/credentials problem")
                    else:
                        print(f"   🔧 Issue: Other error")
                else:
                    print(f"   ✅ Status: Success (no errors)")
                    
                    # Check for meaningful content
                    has_content = False
                    content_fields = ['final_result', 'messages', 'execution_results']
                    
                    for field in content_fields:
                        if field in result and result[field]:
                            has_content = True
                            if isinstance(result[field], list):
                                print(f"   📋 {field}: {len(result[field])} items")
                            else:
                                content_preview = str(result[field])[:100]
                                print(f"   📋 {field}: {content_preview}...")
                    
                    if not has_content:
                        print(f"   ⚠️  No meaningful content generated")
            else:
                print(f"   ❓ Unexpected result type: {type(result)}")
    
    async def run_all_direct_tests(self):
        """Run all direct agent tests."""
        self.print_header("Direct Agent Testing (No MCP Dependency)")
        
        print(f"🎯 Test Query: {self.test_query}")
        print(f"🔧 Testing Mode: Direct (bypassing MCP servers)")
        print(f"🕒 Test Time: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
        
        results = {}
        
        # Test AI Planner
        print(f"\n🧪 Test 1: AI Planner Direct")
        results["ai_planner"] = await self.test_ai_planner_direct()
        
        # Test Gmail Agent
        print(f"\n🧪 Test 2: Gmail Agent Direct")
        results["gmail_agent"] = await self.test_gmail_agent_direct()
        
        # Test Salesforce Agent
        print(f"\n🧪 Test 3: Salesforce Agent Direct")
        results["salesforce_agent"] = await self.test_salesforce_agent_direct()
        
        # Test Invoice Agent
        print(f"\n🧪 Test 4: Invoice Agent Direct")
        results["invoice_agent"] = await self.test_invoice_agent_direct()
        
        # Analyze results
        self.analyze_direct_results(results)
        
        # Summary
        self.print_section("Test Summary")
        
        successful_tests = 0
        for component_name, result in results.items():
            if isinstance(result, dict) and not result.get('error'):
                successful_tests += 1
                print(f"✅ {component_name}: Success")
            else:
                error = result.get('error', 'Unknown error') if isinstance(result, dict) else 'Invalid result'
                print(f"❌ {component_name}: {error[:100]}...")
        
        print(f"\n📊 Overall Results: {successful_tests}/{len(results)} tests passed")
        
        if successful_tests == len(results):
            print(f"🎉 All direct tests passed! The issue is likely in MCP connection layer.")
        else:
            print(f"⚠️  Some direct tests failed. Issues may be in agent implementation.")
        
        print(f"\n💡 Next Steps:")
        if successful_tests == len(results):
            print(f"   1. The agents work directly - focus on fixing MCP connection")
            print(f"   2. Consider using HTTP transport instead of STDIO for MCP servers")
            print(f"   3. Or implement a connection pooling solution")
        else:
            print(f"   1. Fix the failing agent implementations first")
            print(f"   2. Check import dependencies and service configurations")
            print(f"   3. Then address MCP connection issues")
        
        return results

async def main():
    """Main entry point."""
    print("🧪 Direct Agent Testing")
    print("=" * 30)
    print("Testing agents directly without MCP server dependency")
    print("This helps isolate whether issues are in agents or MCP connection")
    
    tester = DirectAgentTester()
    results = await tester.run_all_direct_tests()
    
    print(f"\n🏁 Direct testing complete!")
    return results

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⚠️ Test interrupted by user.")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()