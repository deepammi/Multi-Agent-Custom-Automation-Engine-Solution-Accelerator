"""Test Salesforce agent with real data."""
import asyncio
import logging
import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv(override=True)

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.agents.salesforce_node import salesforce_agent_node
from app.agents.state import AgentState

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_salesforce_agent():
    """Test Salesforce agent with different queries."""
    logger.info("=" * 60)
    logger.info("Testing Salesforce Agent with Real Data")
    logger.info("=" * 60)
    
    test_cases = [
        {
            "name": "Query Accounts",
            "task": "Show me the 5 most recent accounts from Salesforce"
        },
        {
            "name": "Query Opportunities",
            "task": "List the recent opportunities in my Salesforce pipeline"
        },
        {
            "name": "List Orgs",
            "task": "List my connected Salesforce orgs"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        logger.info(f"\n{'='*60}")
        logger.info(f"Test Case {i}: {test_case['name']}")
        logger.info(f"{'='*60}")
        logger.info(f"Task: {test_case['task']}\n")
        
        # Create test state
        test_state: AgentState = {
            "messages": [],
            "plan_id": f"test-plan-{i}",
            "session_id": "test-session-123",
            "task_description": test_case['task'],
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
        
        # Execute agent
        result = await salesforce_agent_node(test_state)
        
        logger.info(f"\n{'='*60}")
        logger.info(f"Agent Response:")
        logger.info(f"{'='*60}")
        print(result.get('final_result'))
        print()
    
    logger.info("\n" + "=" * 60)
    logger.info("✅ All agent tests complete!")
    logger.info("=" * 60)


if __name__ == "__main__":
    print("\n🚀 Salesforce Agent Real Data Test\n")
    
    try:
        asyncio.run(test_salesforce_agent())
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    except Exception as e:
        logger.error(f"\n❌ Test failed: {e}", exc_info=True)
        sys.exit(1)
