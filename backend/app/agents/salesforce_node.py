"""
Salesforce agent node for LangGraph - UPDATED to use category-based CRM Agent.
Provides CRM functionality using the new CRM Agent with proper MCP protocol.

This file maintains backward compatibility while using the new category-based
CRM Agent internally for proper MCP protocol implementation.
"""
import logging
from typing import Dict, Any

from app.agents.state import AgentState
from app.agents.crm_agent import get_crm_agent

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
    
    # Get message persistence service for direct database saving
    from app.services.message_persistence_service import get_message_persistence_service
    message_persistence = get_message_persistence_service()
    
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
    
    # Save initial processing message to database
    await message_persistence.save_agent_message(
        plan_id=plan_id,
        agent_name="Salesforce",
        content="🔍 Connecting to Salesforce...",
        agent_type="agent",
        metadata={"status": "in_progress"}
    )
    
    try:
        # Get the category-based CRM agent
        crm_agent = get_crm_agent()
        service = 'salesforce'  # Use Salesforce service
        
        response = ""
        
        # Analyze task to determine what Salesforce operation to perform
        task_lower = task.lower()
        
        if "account" in task_lower:
            # Query accounts using category-based CRM agent
            logger.info("Querying Salesforce accounts via CRM Agent...")
            
            try:
                result = await crm_agent.get_accounts(service=service, limit=10)
                
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
            except Exception as e:
                logger.error(f"Error getting accounts via CRM Agent: {e}")
                if response:
                    response += "\n\n"
                response += f"❌ Error retrieving accounts: {str(e)}"
        
        elif "opportunity" in task_lower or "deal" in task_lower or "pipeline" in task_lower:
            # Query opportunities using category-based CRM agent
            logger.info("Querying Salesforce opportunities via CRM Agent...")
            
            try:
                result = await crm_agent.get_opportunities(service=service, limit=10)
                
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
            except Exception as e:
                logger.error(f"Error getting opportunities via CRM Agent: {e}")
                if response:
                    response += "\n\n"
                response += f"❌ Error retrieving opportunities: {str(e)}"
        
        elif "contact" in task_lower:
            # Query contacts using category-based CRM agent
            logger.info("Querying Salesforce contacts via CRM Agent...")
            
            try:
                result = await crm_agent.get_contacts(service=service, limit=10)
                
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
            except Exception as e:
                logger.error(f"Error getting contacts via CRM Agent: {e}")
                if response:
                    response += "\n\n"
                response += f"❌ Error retrieving contacts: {str(e)}"
        
        elif "org" in task_lower and "list" in task_lower:
            # List connected orgs using category-based CRM agent
            logger.info("Listing Salesforce orgs via CRM Agent...")
            
            try:
                orgs = await crm_agent.list_orgs(service=service)
                
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
            except Exception as e:
                logger.error(f"Error listing orgs via CRM Agent: {e}")
                if response:
                    response += "\n\n"
                response += f"❌ Error listing orgs: {str(e)}"
        
        else:
            # Generic Salesforce query or help
            if not response:
                response = "CRM Agent (Salesforce): I can help you query Salesforce data using proper MCP protocol.\n\n"
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
        
        # Save completion message to database
        await message_persistence.save_agent_message(
            plan_id=plan_id,
            agent_name="Salesforce",
            content="✅ Salesforce query complete",
            agent_type="agent",
            metadata={"status": "completed"}
        )
        
        # Save main response to database
        await message_persistence.save_agent_message(
            plan_id=plan_id,
            agent_name="Salesforce",
            content=response,
            agent_type="agent",
            metadata={"status": "completed", "salesforce_integration": True}
        )
        
        # Update state with simplified structure
        from app.agents.state import AgentStateManager
        
        # Add agent result to state
        agent_result = {
            "status": "completed",
            "data": {"salesforce_response": response},
            "message": response
        }
        
        AgentStateManager.add_agent_result(state, "Salesforce", agent_result)
        
        # Send progress update if websocket available
        if websocket_manager:
            try:
                progress = AgentStateManager.get_progress_info(state)
                await websocket_manager.send_message(state["plan_id"], {
                    "type": "step_progress",
                    "data": {
                        "step": progress["current_step"],
                        "total": progress["total_steps"],
                        "agent": "Salesforce",
                        "progress_percentage": progress["progress_percentage"],
                        "timestamp": datetime.utcnow().isoformat() + "Z"
                    }
                })
            except Exception as e:
                logger.error(f"Failed to send progress update: {e}")
        
        result = {
            "messages": [response],
            "current_agent": "Salesforce",
            "salesforce_result": response,
            "collected_data": state.get("collected_data", {}),
            "execution_results": state.get("execution_results", [])
        }
        
        return result
        
    except Exception as e:
        logger.error(f"Salesforce agent error: {e}", exc_info=True)
        error_response = f"Salesforce Agent: ❌ Error processing request\n\n{str(e)}\n\nPlease check your Salesforce configuration and try again."
        
        # Save error message to database
        await message_persistence.save_error_message(
            plan_id=plan_id,
            error_message=f"Salesforce agent error: {str(e)}",
            agent_name="Salesforce",
            metadata={"salesforce_integration": True, "exception": str(e)}
        )
        
        # Save full error response to database
        await message_persistence.save_agent_message(
            plan_id=plan_id,
            agent_name="Salesforce",
            content=error_response,
            agent_type="error",
            metadata={"status": "error", "salesforce_integration": True}
        )
        
        # Update state with error result
        from app.agents.state import AgentStateManager
        
        agent_result = {
            "status": "error",
            "data": {"error_response": error_response},
            "message": error_response
        }
        
        AgentStateManager.add_agent_result(state, "Salesforce", agent_result)
        
        return {
            "messages": [error_response],
            "current_agent": "Salesforce",
            "salesforce_result": error_response,
            "collected_data": state.get("collected_data", {}),
            "execution_results": state.get("execution_results", [])
        }
