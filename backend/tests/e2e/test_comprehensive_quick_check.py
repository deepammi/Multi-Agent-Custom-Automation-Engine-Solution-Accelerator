#!/usr/bin/env python3
"""
Quick check of the updated comprehensive test to verify the changes work correctly.
"""

import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Force disable mock mode for real MCP server testing
os.environ["USE_MOCK_MODE"] = "false"
os.environ["USE_MOCK_LLM"] = "false"

async def quick_test_check():
    """Quick test to verify the comprehensive test changes."""
    
    print("🔍 Quick Check of Updated Comprehensive Test")
    print("=" * 60)
    
    try:
        # Import the test class
        from test_agent_integration_comprehensive import AgentIntegrationTester
        
        # Create tester instance
        tester = AgentIntegrationTester()
        
        print(f"✅ AgentIntegrationTester imported successfully")
        print(f"📊 Test scenarios created: {len(tester.test_scenarios)}")
        
        # Check scenario structure
        for i, scenario in enumerate(tester.test_scenarios[:3], 1):
            print(f"\n{i}. {scenario.agent_name} - {scenario.test_name}")
            print(f"   Parameters: {scenario.test_parameters}")
            print(f"   Expected fields: {scenario.expected_data_fields}")
        
        # Check MCP server availability (without starting them)
        print(f"\n🔧 Checking MCP server availability...")
        await tester._check_mcp_server_availability()
        
        available_servers = [s for s, state in tester.mcp_connection_states.items() 
                           if state.name == "AVAILABLE"]
        
        print(f"Available servers: {available_servers}")
        print(f"Required servers: ['email', 'bill_com', 'salesforce']")
        
        if len(available_servers) >= 3:
            print(f"✅ All required MCP servers are available!")
            print(f"🚀 Comprehensive test should work correctly")
        else:
            print(f"⚠️  Some MCP servers are not available")
            print(f"   This is expected if servers are not running")
        
        print(f"\n✅ Quick check completed successfully")
        
    except Exception as e:
        print(f"❌ Quick check failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(quick_test_check())