"""Salesforce agent node for LangGraph."""
import logging
from typing import Dict, Any

from app.agents.state import AgentState
from app.services.salesforce_mcp_service import get_salesforce_service

logger = logging.getLogger(__name__)


async def salesforce_agent_node(state: AgentState) -> Dict[str, Any]:
    """
    Salesforce agent node - handles Salesforce data queries and operations.
    
    This agent can:
    - Query Salesforce accounts, opportunities, contacts
    - Execute custom SOQL queries
    - Search across multiple Salesforce objects
    """
    task = state["task_description"]
    plan_id = state["plan_id"]
    websocket_manager = state.get("websocket_manager")
    
    logger.info(f"Salesforce Agent processing task for plan {plan_id}")
    
    # Send initial processing message
    if websocket_manager:
        try:
            from datetime import datetime
            await websocket_manager.send_message(plan_id, {
                "type": "agent_message",
                "data": {
                    "agent_name": "Salesforce",
                    "content": "🔍 Connecting to Salesforce...",
                    "status": "in_progress",
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }
            })
        except Exception as e:
            logger.error(f"Failed to send WebSocket message: {e}")
    
    try:
        sf_service = get_salesforce_service()
        
        # Check if Salesforce MCP is enabled
        if not sf_service.is_enabled():
            response = (
                "Salesforce Agent: Salesforce integration is currently disabled.\n\n"
                "To enable Salesforce integration:\n"
                "1. Set SALESFORCE_MCP_ENABLED=true in backend/.env\n"
                "2. Configure your Salesforce org alias with SALESFORCE_ORG_ALIAS\n"
                "3. Ensure Salesforce CLI is installed and authorized\n\n"
                "For now, I'm running in mock mode with sample data."
            )
            
            # Still initialize to use mock data
            await sf_service.initialize()
        else:
            await sf_service.initialize()
            response = ""
        
        # Analyze task to determine what Salesforce operation to perform
        task_lower = task.lower()
        
        if "account" in task_lower:
            # Query accounts
            logger.info("Querying Salesforce accounts...")
            result = await sf_service.get_account_info(limit=10)
            
            if result.get("success"):
                records = result.get("records", [])
                if response:
                    response += "\n\n"
                response += f"📊 Found {len(records)} Salesforce accounts:\n\n"
                
                for i, record in enumerate(records, 1):
                    response += f"{i}. **{record.get('Name', 'N/A')}**\n"
                    response += f"   - Phone: {record.get('Phone', 'N/A')}\n"
                    response += f"   - Industry: {record.get('Industry', 'N/A')}\n"
                    
                    revenue = record.get('AnnualRevenue')
                    if revenue:
                        response += f"   - Annual Revenue: ${revenue:,.0f}\n"
                    
                    response += f"   - Salesforce ID: {record.get('Id', 'N/A')}\n\n"
                
                if not records:
                    response += "No accounts found in your Salesforce org.\n"
            else:
                if response:
                    response += "\n\n"
                response += f"❌ Failed to query accounts: {result.get('error', 'Unknown error')}"
        
        elif "opportunity" in task_lower or "deal" in task_lower or "pipeline" in task_lower:
            # Query opportunities
            logger.info("Querying Salesforce opportunities...")
            result = await sf_service.get_opportunity_info(limit=10)
            
            if result.get("success"):
                records = result.get("records", [])
                if response:
                    response += "\n\n"
                response += f"💼 Found {len(records)} Salesforce opportunities:\n\n"
                
                total_amount = 0
                for i, record in enumerate(records, 1):
                    response += f"{i}. **{record.get('Name', 'N/A')}**\n"
                    response += f"   - Stage: {record.get('StageName', 'N/A')}\n"
                    
                    amount = record.get('Amount', 0)
                    if amount:
                        response += f"   - Amount: ${amount:,.2f}\n"
                        total_amount += amount
                    
                    response += f"   - Close Date: {record.get('CloseDate', 'N/A')}\n"
                    
                    account = record.get('Account', {})
                    if account and account.get('Name'):
                        response += f"   - Account: {account.get('Name')}\n"
                    
                    response += f"   - Salesforce ID: {record.get('Id', 'N/A')}\n\n"
                
                if records:
                    response += f"**Total Pipeline Value:** ${total_amount:,.2f}\n"
                else:
                    response += "No opportunities found in your Salesforce org.\n"
            else:
                if response:
                    response += "\n\n"
                response += f"❌ Failed to query opportunities: {result.get('error', 'Unknown error')}"
        
        elif "contact" in task_lower:
            # Query contacts
            logger.info("Querying Salesforce contacts...")
            result = await sf_service.get_contact_info(limit=10)
            
            if result.get("success"):
                records = result.get("records", [])
                if response:
                    response += "\n\n"
                response += f"👥 Found {len(records)} Salesforce contacts:\n\n"
                
                for i, record in enumerate(records, 1):
                    response += f"{i}. **{record.get('Name', 'N/A')}**\n"
                    response += f"   - Email: {record.get('Email', 'N/A')}\n"
                    response += f"   - Phone: {record.get('Phone', 'N/A')}\n"
                    response += f"   - Title: {record.get('Title', 'N/A')}\n"
                    
                    account = record.get('Account', {})
                    if account and account.get('Name'):
                        response += f"   - Account: {account.get('Name')}\n"
                    
                    response += f"   - Salesforce ID: {record.get('Id', 'N/A')}\n\n"
                
                if not records:
                    response += "No contacts found in your Salesforce org.\n"
            else:
                if response:
                    response += "\n\n"
                response += f"❌ Failed to query contacts: {result.get('error', 'Unknown error')}"
        
        elif "org" in task_lower and "list" in task_lower:
            # List connected orgs
            logger.info("Listing Salesforce orgs...")
            orgs = await sf_service.list_orgs()
            
            if response:
                response += "\n\n"
            response += f"🏢 Connected Salesforce Orgs ({len(orgs)}):\n\n"
            
            for i, org in enumerate(orgs, 1):
                response += f"{i}. **{org.get('alias', 'N/A')}**\n"
                response += f"   - Username: {org.get('username', 'N/A')}\n"
                response += f"   - Org ID: {org.get('orgId', 'N/A')}\n"
                response += f"   - Instance: {org.get('instanceUrl', 'N/A')}\n"
                response += f"   - Default: {'Yes' if org.get('isDefaultOrg') else 'No'}\n\n"
            
            if not orgs:
                response += "No Salesforce orgs are currently connected.\n"
        
        else:
            # Generic Salesforce query or help
            if not response:
                response = "Salesforce Agent: I can help you query Salesforce data.\n\n"
            else:
                response += "\n\n"
            
            response += "**Available Operations:**\n"
            response += "- Query accounts (e.g., 'Show me recent accounts')\n"
            response += "- Query opportunities (e.g., 'List open opportunities')\n"
            response += "- Query contacts (e.g., 'Get contact information')\n"
            response += "- List connected orgs (e.g., 'List Salesforce orgs')\n\n"
            response += "Please specify what you'd like to retrieve from Salesforce."
        
        # Send completion message
        if websocket_manager:
            try:
                from datetime import datetime
                await websocket_manager.send_message(plan_id, {
                    "type": "agent_message",
                    "data": {
                        "agent_name": "Salesforce",
                        "content": "✅ Salesforce query complete",
                        "status": "completed",
                        "timestamp": datetime.utcnow().isoformat() + "Z"
                    }
                })
            except Exception as e:
                logger.error(f"Failed to send WebSocket message: {e}")
        
        return {
            "messages": [response],
            "current_agent": "Salesforce",
            "final_result": response
        }
        
    except Exception as e:
        logger.error(f"Salesforce agent error: {e}", exc_info=True)
        error_response = f"Salesforce Agent: ❌ Error processing request\n\n{str(e)}\n\nPlease check your Salesforce configuration and try again."
        
        return {
            "messages": [error_response],
            "current_agent": "Salesforce",
            "final_result": error_response
        }
