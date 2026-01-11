#!/usr/bin/env python3
"""
Real-World Integration Test Script

Simplified test script for testing actual integration with Gmail, Bill.com, and Salesforce
using real queries and data. This script focuses on:

1. Direct agent testing with real MCP connections
2. Manual query input for realistic scenarios
3. Step-by-step execution with real system calls
4. Actual data retrieval and processing

Usage: python3 backend/test_real_world_integration.py
"""

import asyncio
import sys
import os
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import agent modules
try:
    from app.agents.gmail_agent_node import GmailAgentNode
    from app.agents.salesforce_node import SalesforceAgentNode
    from app.agents.nodes import invoice_agent_node
    from app.agents.state import AgentState
    from app.services.gmail_mcp_service import get_gmail_service
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure you're running from the correct directory and all dependencies are installed")
    sys.exit(1)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RealWorldTester:
    """Test real-world integration scenarios."""
    
    def __init__(self):
        """Initialize tester."""
        self.session_id = f"real-test-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}"
        
        # Sample realistic queries
        self.sample_queries = [
            "Find emails about PO-2024-001 payment issues and check invoice status in Bill.com",
            "Look up vendor 'Office Depot' in Salesforce and find related invoices",
            "Search for emails mentioning 'invoice discrepancy' and cross-reference with Bill.com data",
            "Check payment status for recent invoices and find any vendor communications",
            "Investigate overdue payments - find emails and invoice details",
            "Review vendor relationship for 'Acme Corp' and check recent transactions"
        ]
    
    def print_header(self, title: str):
        """Print formatted header."""
        print(f"\n{'=' * 80}")
        print(f"{title.center(80)}")
        print(f"{'=' * 80}")
    
    def print_section(self, title: str):
        """Print section header."""
        print(f"\n🔹 {title}")
        print("-" * (len(title) + 4))
    
    def display_sample_queries(self):
        """Display sample queries."""
        self.print_section("Sample Real-World Queries")
        
        for i, query in enumerate(self.sample_queries, 1):
            print(f"{i:2d}. {query}")
        
        print("\nOr enter your own query...")
    
    def get_user_query(self) -> str:
        """Get user query."""
        self.display_sample_queries()
        
        while True:
            choice = input("\nEnter number (1-6) or custom query: ").strip()
            
            if choice.isdigit():
                choice_num = int(choice)
                if 1 <= choice_num <= len(self.sample_queries):
                    return self.sample_queries[choice_num - 1]
                else:
                    print(f"Please enter 1-{len(self.sample_queries)}")
            elif len(choice) > 10:
                return choice
            else:
                print("Please enter a valid selection")
    
    async def test_gmail_integration(self, query: str) -> Dict[str, Any]:
        """Test Gmail integration with real query."""
        self.print_section("Testing Gmail Integration")
        
        try:
            # Test Gmail service first
            print("📧 Testing Gmail MCP service...")
            gmail_service = get_gmail_service()
            
            # Test basic connectivity
            profile = await gmail_service.get_profile()
            print(f"✅ Gmail connected: {profile[:100]}...")
            
            # Test Gmail agent
            print("🤖 Testing Gmail agent...")
            gmail_agent = GmailAgentNode()
            
            state = {
                "task": query,
                "user_request": query,
                "messages": [],
                "plan_id": f"test-{self.session_id}",
                "session_id": self.session_id
            }
            
            result = await gmail_agent.process(state)
            
            return {
                "status": "success",
                "agent": "gmail",
                "result": result.get("gmail_result", "No result"),
                "message": "Gmail integration successful"
            }
        
        except Exception as e:
            return {
                "status": "error",
                "agent": "gmail",
                "error": str(e),
                "message": f"Gmail integration failed: {e}"
            }
    
    async def test_salesforce_integration(self, query: str) -> Dict[str, Any]:
        """Test Salesforce integration."""
        self.print_section("Testing Salesforce Integration")
        
        try:
            print("🏢 Testing Salesforce agent...")
            
            # Create Salesforce agent
            salesforce_agent = SalesforceAgentNode()
            
            state = AgentState(
                task_description=query,
                plan_id=f"test-{self.session_id}",
                session_id=self.session_id,
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
            
            result = await salesforce_agent.process(state)
            
            return {
                "status": "success",
                "agent": "salesforce",
                "result": result.get("final_result", "No result"),
                "message": "Salesforce integration successful"
            }
        
        except Exception as e:
            return {
                "status": "error",
                "agent": "salesforce",
                "error": str(e),
                "message": f"Salesforce integration failed: {e}"
            }
    
    async def test_invoice_integration(self, query: str) -> Dict[str, Any]:
        """Test Invoice/Bill.com integration."""
        self.print_section("Testing Invoice/Bill.com Integration")
        
        try:
            print("💰 Testing Invoice agent...")
            
            state = AgentState(
                task_description=query,
                plan_id=f"test-{self.session_id}",
                session_id=self.session_id,
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
            
            result = await invoice_agent_node(state)
            
            return {
                "status": "success",
                "agent": "invoice",
                "result": result.get("final_result", "No result"),
                "message": "Invoice integration successful"
            }
        
        except Exception as e:
            return {
                "status": "error",
                "agent": "invoice",
                "error": str(e),
                "message": f"Invoice integration failed: {e}"
            }
    
    async def run_integration_test(self, query: str):
        """Run complete integration test."""
        self.print_header(f"Real-World Integration Test")
        
        print(f"Query: {query}")
        print(f"Session: {self.session_id}")
        
        results = []
        
        # Test each integration
        integrations = [
            ("Gmail", self.test_gmail_integration),
            ("Salesforce", self.test_salesforce_integration),
            ("Invoice/Bill.com", self.test_invoice_integration)
        ]
        
        for name, test_func in integrations:
            try:
                print(f"\n🔄 Testing {name}...")
                result = await test_func(query)
                results.append(result)
                
                if result["status"] == "success":
                    print(f"✅ {name}: {result['message']}")
                    print(f"   Result: {str(result['result'])[:200]}...")
                else:
                    print(f"❌ {name}: {result['message']}")
                    print(f"   Error: {result.get('error', 'Unknown')}")
            
            except Exception as e:
                print(f"❌ {name}: Fatal error - {e}")
                results.append({
                    "status": "fatal_error",
                    "agent": name.lower(),
                    "error": str(e),
                    "message": f"{name} fatal error"
                })
        
        # Summary
        self.print_section("Integration Test Summary")
        
        successful = sum(1 for r in results if r["status"] == "success")
        total = len(results)
        
        print(f"Results: {successful}/{total} integrations successful")
        
        for result in results:
            status_icon = "✅" if result["status"] == "success" else "❌"
            print(f"{status_icon} {result['agent'].title()}: {result['message']}")
        
        if successful == total:
            print("\n🎉 All integrations working correctly!")
        else:
            print(f"\n⚠️  {total - successful} integration(s) need attention")
        
        return results
    
    async def run_interactive_test(self):
        """Run interactive test session."""
        self.print_header("Real-World Integration Testing")
        
        print("This script tests actual integration with:")
        print("• Gmail MCP service for email retrieval")
        print("• Salesforce agent for CRM data")
        print("• Invoice agent for Bill.com integration")
        print("\nUsing real queries and system connections...")
        
        while True:
            try:
                # Get query
                query = self.get_user_query()
                
                # Run test
                results = await self.run_integration_test(query)
                
                # Ask to continue
                print(f"\nTest another query? (y/n): ", end="")
                choice = input().strip().lower()
                
                if choice not in ['y', 'yes']:
                    break
            
            except KeyboardInterrupt:
                print("\n\nTest interrupted. Goodbye!")
                break
            except Exception as e:
                print(f"\nTest error: {e}")
                break
        
        print("\nTesting complete. Thank you!")


async def main():
    """Main entry point."""
    print("🧪 Real-World Integration Test Suite")
    print("====================================")
    
    tester = RealWorldTester()
    await tester.run_interactive_test()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nGoodbye!")
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)