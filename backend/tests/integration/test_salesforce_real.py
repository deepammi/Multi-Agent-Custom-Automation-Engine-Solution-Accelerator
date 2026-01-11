"""Test real Salesforce connection."""
import asyncio
import logging
import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv(override=True)

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.salesforce_mcp_service import get_salesforce_service

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_real_salesforce():
    """Test real Salesforce connection."""
    logger.info("=" * 60)
    logger.info("Testing REAL Salesforce Connection")
    logger.info("=" * 60)
    
    # Check environment variables
    enabled = os.getenv("SALESFORCE_MCP_ENABLED", "false")
    org_alias = os.getenv("SALESFORCE_ORG_ALIAS", "DEFAULT_TARGET_ORG")
    
    logger.info(f"SALESFORCE_MCP_ENABLED: {enabled}")
    logger.info(f"SALESFORCE_ORG_ALIAS: {org_alias}")
    
    sf_service = get_salesforce_service()
    
    if not sf_service.is_enabled():
        logger.error("❌ Salesforce MCP is not enabled!")
        logger.info("Please set SALESFORCE_MCP_ENABLED=true in backend/.env")
        return
    
    # Initialize service
    logger.info("\n1. Initializing Salesforce service...")
    try:
        await sf_service.initialize()
        logger.info("✅ Service initialized successfully")
    except Exception as e:
        logger.error(f"❌ Initialization failed: {e}")
        return
    
    # Test listing orgs
    logger.info("\n2. Listing connected Salesforce orgs...")
    orgs = await sf_service.list_orgs()
    logger.info(f"✅ Found {len(orgs)} org(s)")
    for org in orgs:
        logger.info(f"   - {org.get('username')} (Org ID: {org.get('orgId')})")
    
    # Test account query
    logger.info("\n3. Querying Salesforce accounts...")
    result = await sf_service.get_account_info(limit=5)
    
    if result.get("success"):
        records = result.get("records", [])
        logger.info(f"✅ Query successful - {len(records)} account(s) found")
        for record in records:
            logger.info(f"   - {record.get('Name')}")
            logger.info(f"     ID: {record.get('Id')}")
    else:
        logger.error(f"❌ Query failed: {result.get('error')}")
    
    # Test opportunity query
    logger.info("\n4. Querying Salesforce opportunities...")
    result = await sf_service.get_opportunity_info(limit=5)
    
    if result.get("success"):
        records = result.get("records", [])
        logger.info(f"✅ Query successful - {len(records)} opportunity(ies) found")
        for record in records:
            logger.info(f"   - {record.get('Name')}")
            logger.info(f"     Stage: {record.get('StageName')}")
            logger.info(f"     Amount: ${record.get('Amount', 0):,.2f}")
    else:
        logger.error(f"❌ Query failed: {result.get('error')}")
    
    logger.info("\n" + "=" * 60)
    logger.info("✅ Real Salesforce testing complete!")
    logger.info("=" * 60)


if __name__ == "__main__":
    print("\n🚀 Real Salesforce Connection Test\n")
    
    try:
        asyncio.run(test_real_salesforce())
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    except Exception as e:
        logger.error(f"\n❌ Test failed: {e}", exc_info=True)
        sys.exit(1)
