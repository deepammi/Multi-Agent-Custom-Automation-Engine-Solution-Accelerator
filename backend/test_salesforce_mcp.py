"""Test Salesforce MCP integration."""
import asyncio
import logging
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.salesforce_mcp_service import get_salesforce_service

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_salesforce_connection():
    """Test Salesforce MCP connection and basic operations."""
    logger.info("=" * 60)
    logger.info("Testing Salesforce MCP Integration")
    logger.info("=" * 60)
    
    sf_service = get_salesforce_service()
    
    # Check if enabled
    if not sf_service.is_enabled():
        logger.warning("⚠️  Salesforce MCP is disabled")
        logger.info("To enable: Set SALESFORCE_MCP_ENABLED=true in backend/.env")
        logger.info("Running tests with mock data...")
    
    # Initialize service
    logger.info("\n1. Initializing Salesforce MCP service...")
    await sf_service.initialize()
    logger.info("✅ Service initialized")
    
    # Test listing orgs
    logger.info("\n2. Testing list_orgs...")
    orgs = await sf_service.list_orgs()
    logger.info(f"✅ Found {len(orgs)} org(s)")
    for org in orgs:
        logger.info(f"   - {org.get('alias')}: {org.get('username')}")
    
    # Test account query
    logger.info("\n3. Testing account query...")
    result = await sf_service.get_account_info(limit=5)
    if result.get("success"):
        records = result.get("records", [])
        logger.info(f"✅ Query successful - {len(records)} account(s) found")
        for record in records:
            logger.info(f"   - {record.get('Name')}: {record.get('Phone')}")
    else:
        logger.error(f"❌ Query failed: {result.get('error')}")
    
    # Test opportunity query
    logger.info("\n4. Testing opportunity query...")
    result = await sf_service.get_opportunity_info(limit=5)
    if result.get("success"):
        records = result.get("records", [])
        logger.info(f"✅ Query successful - {len(records)} opportunity(ies) found")
        for record in records:
            logger.info(f"   - {record.get('Name')}: ${record.get('Amount', 0):,.2f}")
    else:
        logger.error(f"❌ Query failed: {result.get('error')}")
    
    # Test contact query
    logger.info("\n5. Testing contact query...")
    result = await sf_service.get_contact_info(limit=5)
    if result.get("success"):
        records = result.get("records", [])
        logger.info(f"✅ Query successful - {len(records)} contact(s) found")
        for record in records:
            logger.info(f"   - {record.get('Name')}: {record.get('Email')}")
    else:
        logger.error(f"❌ Query failed: {result.get('error')}")
    
    # Test custom SOQL query
    logger.info("\n6. Testing custom SOQL query...")
    custom_query = "SELECT Id, Name FROM Account LIMIT 3"
    result = await sf_service.run_soql_query(custom_query)
    if result.get("success"):
        logger.info(f"✅ Custom query successful - {result.get('totalSize')} record(s)")
    else:
        logger.error(f"❌ Custom query failed: {result.get('error')}")
    
    logger.info("\n" + "=" * 60)
    logger.info("✅ All tests complete!")
    logger.info("=" * 60)
    
    if not sf_service.is_enabled():
        logger.info("\n💡 Next Steps:")
        logger.info("1. Install Salesforce CLI: npm install -g @salesforce/cli")
        logger.info("2. Authorize your org: sf org login web")
        logger.info("3. Enable in .env: SALESFORCE_MCP_ENABLED=true")
        logger.info("4. Configure MCP server in .kiro/settings/mcp.json")


async def test_agent_integration():
    """Test Salesforce agent node integration."""
    logger.info("\n" + "=" * 60)
    logger.info("Testing Salesforce Agent Integration")
    logger.info("=" * 60)
    
    from app.agents.salesforce_node import salesforce_agent_node
    from app.agents.state import AgentState
    
    # Create test state
    test_state: AgentState = {
        "messages": [],
        "plan_id": "test-plan-123",
        "session_id": "test-session-456",
        "task_description": "Show me the 5 most recent accounts from Salesforce",
        "current_agent": "Planner",
        "next_agent": "salesforce",
        "final_result": "",
        "approval_required": False,
        "approved": None,
        "websocket_manager": None,
        "llm_provider": None,
        "llm_temperature": None,
        "extraction_result": None,
        "requires_extraction_approval": None,
        "extraction_approved": None
    }
    
    logger.info("\nExecuting Salesforce agent node...")
    result = await salesforce_agent_node(test_state)
    
    logger.info("\n✅ Agent execution complete")
    logger.info(f"Current Agent: {result.get('current_agent')}")
    logger.info(f"\nAgent Response:\n{result.get('final_result')}")
    
    logger.info("\n" + "=" * 60)


if __name__ == "__main__":
    print("\n🚀 Salesforce MCP Test Suite\n")
    
    try:
        # Run connection tests
        asyncio.run(test_salesforce_connection())
        
        # Run agent integration tests
        asyncio.run(test_agent_integration())
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
    except Exception as e:
        logger.error(f"\n❌ Test failed with error: {e}", exc_info=True)
        sys.exit(1)
