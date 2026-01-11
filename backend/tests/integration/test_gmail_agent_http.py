#!/usr/bin/env python3
"""
Gmail Agent HTTP Test Script

Tests the Gmail agent using HTTP MCP transport.
Assumes MCP servers are already running in HTTP mode.

Usage:
1. Start Gmail MCP server: python3 src/mcp_server/gmail_mcp_server.py --transport http --port 9002
2. Run this test: python3 backend/test_gmail_agent_http.py

Test Query: "What is the status of Payment Invoice number Acme Marketing Invoice number Inv-1001"
"""

import asyncio
import sys
import os
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any
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

class GmailAgentHTTPTester:
    """Test Gmail agent with HTTP MCP transport."""
    
    def __init__(self):
        """Initialize the tester."""
        self.test_query = TEST_QUERY
        self.server_ports = {
            "gmail": 9002,
            "salesforce": 9001,
            "bill_com": 9000
        }
    
    def print_header(self, title: str):
        """Print formatted header."""
        print(f"\n{'=' * 80}")
        print(f"📧 {title}")
        print(f"{'=' * 80}")
    
    def print_section(self, title: str):
        """Print section header."""
        print(f"\n🔹 {title}")
        print("-" * (len(title) + 4))
    
    async def check_server_availability(self) -> Dict[str, bool]:
        """Check which MCP servers are available via HTTP."""
        self.print_section("Checking MCP Server Availability")
        
        from app.services.mcp_http_client import HTTPMCPServiceFactory
        
        print(f"🔍 Checking HTTP MCP servers...")
        
        results = await HTTPMCPServiceFactory.check_all_servers()
        
        for service_name, available in results.items():
            port = self.server_ports[service_name]
            status_icon = "✅" if available else "❌"
            print(f"{status_icon} {service_name.title()} MCP Server: {'Available' if available else 'Not available'} (port {port})")
            
            if not available:
                print(f"   Start with: python3 src/mcp_server/{service_name}_mcp_server.py --transport http --port {port}")
        
        return results
    
    async def test_http_mcp_client_direct(self) -> Dict[str, Any]:
        """Test HTTP MCP client directly."""
        self.print_section("Testing HTTP MCP Client Direct")
        
        try:
            from app.services.mcp_http_client import HTTPMCPServiceFactory
            
            print(f"📧 Creating Gmail HTTP MCP client...")
            
            async with HTTPMCPServiceFactory.create_gmail_client() as client:
                print(f"✅ Gmail HTTP client connected")
                
                # Test profile access
                print(f"\n📋 Testing profile access...")
                try:
                    profile_result = await client.get_profile()
                    print(f"📋 Profile result type: {type(profile_result)}")
                    print(f"📋 Profile result length: {len(str(profile_result))}")
                    print(f"📋 Profile result preview: {str(profile_result)[:200]}...")
                    
                    # Parse JSON to see structure
                    try:
                        parsed_profile = json.loads(profile_result)
                        print(f"📋 Parsed profile keys: {list(parsed_profile.keys())}")
                    except json.JSONDecodeError:
                        print(f"📋 Profile result is not JSON")
                
                except Exception as e:
                    print(f"❌ Profile access failed: {e}")
                
                # Test message listing
                print(f"\n📧 Testing message listing...")
                try:
                    messages_result = await client.list_messages(max_results=5)
                    print(f"📧 Messages result type: {type(messages_result)}")
                    print(f"📧 Messages result length: {len(str(messages_result))}")
                    print(f"📧 Messages result preview: {str(messages_result)[:200]}...")
                    
                    # Parse JSON to see structure
                    try:
                        parsed_messages = json.loads(messages_result)
                        print(f"📧 Parsed messages keys: {list(parsed_messages.keys())}")
                    except json.JSONDecodeError:
                        print(f"📧 Messages result is not JSON")
                
                except Exception as e:
                    print(f"❌ Message listing failed: {e}")
                
                # Test search functionality
                print(f"\n🔍 Testing search functionality...")
                try:
                    search_result = await client.search_messages("Acme Marketing", max_results=3)
                    print(f"🔍 Search result type: {type(search_result)}")
                    print(f"🔍 Search result length: {len(str(search_result))}")
                    print(f"🔍 Search result preview: {str(search_result)[:200]}...")
                    
                    # Parse JSON to see structure
                    try:
                        parsed_search = json.loads(search_result)
                        print(f"🔍 Parsed search keys: {list(parsed_search.keys())}")
                    except json.JSONDecodeError:
                        print(f"🔍 Search result is not JSON")
                
                except Exception as e:
                    print(f"❌ Search failed: {e}")
                
                return {"status": "success", "client_type": "HTTP MCP"}
        
        except Exception as e:
            print(f"❌ HTTP MCP client error: {e}")
            import traceback
            traceback.print_exc()
            return {"status": "error", "error": str(e)}
    
    async def test_gmail_agent_with_http(self) -> Dict[str, Any]:
        """Test Gmail agent using HTTP MCP transport."""
        self.print_section("Testing Gmail Agent with HTTP MCP")
        
        try:
            # First, we need to modify the Gmail agent to use HTTP transport
            # For now, let's test if we can create the agent
            from app.agents.gmail_agent_node import GmailAgentNode
            
            print(f"📧 Initializing Gmail agent...")
            gmail_agent = GmailAgentNode()
            
            print(f"✅ Gmail agent initialized: {type(gmail_agent)}")
            
            # Create test state
            test_state = {
                "task_description": self.test_query,
                "plan_id": f"test-http-gmail-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}",
                "session_id": "test-session-http",
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
            
            print(f"\n📧 Test state created:")
            print(f"   Task: {test_state['task_description']}")
            print(f"   Plan ID: {test_state['plan_id']}")
            
            print(f"\n🔄 Processing with Gmail agent...")
            print(f"⚠️  Note: This may fail if agent is not configured for HTTP transport")
            
            result = await gmail_agent.process(test_state)
            
            print(f"\n📊 Gmail Agent Result:")
            print(f"   Result type: {type(result)}")
            print(f"   Result keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
            
            if isinstance(result, dict):
                for key, value in result.items():
                    if isinstance(value, str) and len(value) > 100:
                        print(f"   {key}: {value[:100]}...")
                    elif isinstance(value, list):
                        print(f"   {key}: {len(value)} items")
                    else:
                        print(f"   {key}: {value}")
            
            print(f"\n📋 Full Gmail Agent Result JSON:")
            print(json.dumps(result, indent=2, default=str))
            
            return result
        
        except Exception as e:
            print(f"❌ Gmail agent HTTP test error: {e}")
            import traceback
            traceback.print_exc()
            return {"status": "error", "error": str(e)}
    
    async def run_all_tests(self):
        """Run all Gmail agent HTTP tests."""
        self.print_header("Gmail Agent HTTP Test Suite")
        
        print(f"🎯 Test Query: {self.test_query}")
        print(f"🔧 Transport: HTTP (assumes servers already running)")
        print(f"🕒 Test Time: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
        
        results = {}
        
        # Test 1: Check server availability
        print(f"\n🧪 Test 1: MCP Server Availability Check")
        server_status = await self.check_server_availability()
        results["server_availability"] = server_status
        
        # Check if Gmail server is available
        if not server_status.get("gmail", False):
            print(f"\n❌ Gmail MCP server is not available via HTTP")
            print(f"   Please start it with:")
            print(f"   python3 src/mcp_server/gmail_mcp_server.py --transport http --port 9002")
            print(f"\n⏭️  Skipping remaining tests")
            return results
        
        # Test 2: Direct HTTP MCP client
        print(f"\n🧪 Test 2: Direct HTTP MCP Client")
        results["http_client"] = await self.test_http_mcp_client_direct()
        
        # Test 3: Gmail agent with HTTP (may fail if not configured)
        print(f"\n🧪 Test 3: Gmail Agent with HTTP MCP")
        results["gmail_agent"] = await self.test_gmail_agent_with_http()
        
        # Summary
        self.print_section("Test Results Summary")
        
        for test_name, result in results.items():
            if test_name == "server_availability":
                available_servers = sum(1 for available in result.values() if available)
                total_servers = len(result)
                print(f"📊 {test_name}: {available_servers}/{total_servers} servers available")
            else:
                status = result.get("status", "unknown") if isinstance(result, dict) else "completed"
                status_icon = "✅" if status == "success" or status == "completed" else "❌"
                print(f"{status_icon} {test_name}: {status}")
                
                if status == "error":
                    print(f"   Error: {result.get('error', 'Unknown error')}")
        
        # Recommendations
        self.print_section("Recommendations")
        
        gmail_available = server_status.get("gmail", False)
        http_client_status = results.get("http_client", {}).get("status", "unknown")
        
        if not gmail_available:
            print("🔧 Gmail MCP Server Not Running:")
            print("   1. Start Gmail server: python3 src/mcp_server/gmail_mcp_server.py --transport http --port 9002")
            print("   2. Verify it's running: curl http://localhost:9002/health")
            print("   3. Re-run this test")
        
        elif http_client_status == "success":
            print("🎉 HTTP MCP Client Working!")
            print("   The HTTP transport is working correctly")
            print("   Next steps:")
            print("   1. Modify Gmail agent to use HTTP transport instead of STDIO")
            print("   2. Update MCP client configuration in agent nodes")
            print("   3. Test full agent workflow")
        
        else:
            print("🔧 HTTP MCP Client Issues:")
            print("   1. Server is running but HTTP client cannot connect properly")
            print("   2. Check server logs for errors")
            print("   3. Verify HTTP endpoints are working")
            print("   4. Test with curl: curl http://localhost:9002/tools")
        
        return results


async def main():
    """Main entry point."""
    print("📧 Gmail Agent HTTP Test")
    print("=" * 30)
    print("This test assumes MCP servers are already running in HTTP mode")
    print("Start servers first with --transport http flag")
    
    tester = GmailAgentHTTPTester()
    results = await tester.run_all_tests()
    
    print(f"\n🏁 HTTP testing complete!")
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