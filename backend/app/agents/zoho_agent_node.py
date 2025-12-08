"""Zoho Invoice agent node for LangGraph."""
import logging
from typing import Dict, Any

from app.agents.state import AgentState
from app.services.zoho_mcp_service import get_zoho_service

logger = logging.getLogger(__name__)


async def zoho_agent_node(state: AgentState) -> Dict[str, Any]:
    """
    Zoho Invoice agent node - handles Zoho Invoice operations.
    
    This agent can:
    - List invoices
    - Get invoice details
    - List customers
    - Search invoices
    """
    task = state["task_description"]
    plan_id = state["plan_id"]
    websocket_manager = state.get("websocket_manager")
    
    logger.info(f"Zoho Agent processing task for plan {plan_id}")
    
    # Send initial processing message
    if websocket_manager:
        try:
            from datetime import datetime
            await websocket_manager.send_message(plan_id, {
                "type": "agent_message",
                "data": {
                    "agent_name": "Zoho Invoice",
                    "content": "📋 Connecting to Zoho Invoice...",
                    "status": "in_progress",
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }
            })
        except Exception as e:
            logger.error(f"Failed to send WebSocket message: {e}")
    
    try:
        zoho_service = get_zoho_service()
        await zoho_service.initialize()
        
        # Analyze task to determine operation
        task_lower = task.lower()
        
        response = ""
        
        # Check if using mock mode
        if not zoho_service.is_enabled():
            response = "**Note:** Running in mock mode (Zoho OAuth not configured)\n\n"
        
        # Route to appropriate operation
        if "customer" in task_lower or "client" in task_lower:
            # List customers
            logger.info("Querying Zoho customers...")
            result = await zoho_service.list_customers(limit=10)
            
            if result.get("success"):
                customers = result.get("contacts", [])
                response += f"👥 **Zoho Customers** ({len(customers)} found)\n\n"
                
                for i, customer in enumerate(customers, 1):
                    response += f"{i}. **{customer.get('contact_name', 'N/A')}**\n"
                    response += f"   - Email: {customer.get('email', 'N/A')}\n"
                    response += f"   - Phone: {customer.get('phone', 'N/A')}\n"
                    response += f"   - Company: {customer.get('company_name', 'N/A')}\n"
                    
                    balance = customer.get('outstanding_receivable_amount', 0)
                    if balance > 0:
                        response += f"   - Outstanding: ${balance:,.2f}\n"
                    
                    response += f"   - Contact ID: {customer.get('contact_id', 'N/A')}\n\n"
                
                if not customers:
                    response += "No customers found.\n"
            else:
                response += f"❌ Failed to retrieve customers: {result.get('error', 'Unknown error')}\n"
        
        else:
            # Check if this is a request for specific invoice details
            import re
            invoice_match = re.search(r'INV-\d{6}', task, re.IGNORECASE)
            
            if invoice_match:
                # Get specific invoice details
                invoice_number = invoice_match.group(0)
                logger.info(f"Getting invoice details for: {invoice_number}")
                result = await zoho_service.get_invoice(invoice_number)
                
                if result.get("success"):
                    invoice = result.get("invoice", {})
                    response += f"📄 **Invoice Details: {invoice.get('invoice_number', 'N/A')}**\n\n"
                    response += f"**Customer:** {invoice.get('customer_name', 'N/A')}\n"
                    response += f"**Date:** {invoice.get('date', 'N/A')}\n"
                    response += f"**Due Date:** {invoice.get('due_date', 'N/A')}\n"
                    response += f"**Status:** {invoice.get('status', 'N/A')}\n"
                    response += f"**Amount:** ${invoice.get('total', 0):,.2f}\n"
                    response += f"**Balance Due:** ${invoice.get('balance', 0):,.2f}\n\n"
                    
                    # Line items
                    line_items = invoice.get('line_items', [])
                    if line_items:
                        response += "**Line Items:**\n"
                        for item in line_items:
                            response += f"  - {item.get('name', 'N/A')}: "
                            response += f"{item.get('quantity', 0)} × ${item.get('rate', 0):,.2f} = "
                            response += f"${item.get('item_total', 0):,.2f}\n"
                else:
                    response += f"❌ Invoice not found: {invoice_number}\n"
            else:
                # Default: List invoices
                logger.info("Listing Zoho invoices...")
                
                # Check for status filter
                status_filter = None
                if "unpaid" in task_lower or "outstanding" in task_lower:
                    status_filter = "unpaid"
                elif "overdue" in task_lower:
                    status_filter = "overdue"
                elif "paid" in task_lower:
                    status_filter = "paid"
                elif "draft" in task_lower:
                    status_filter = "draft"
                
                result = await zoho_service.list_invoices(limit=10, status=status_filter)
                
                if result.get("success"):
                    invoices = result.get("invoices", [])
                    
                    status_text = f" ({status_filter})" if status_filter else ""
                    response += f"📋 **Zoho Invoices{status_text}** ({len(invoices)} found)\n\n"
                    
                    total_amount = 0
                    total_balance = 0
                    
                    for i, invoice in enumerate(invoices, 1):
                        status = invoice.get('status', 'N/A')
                        status_emoji = {
                            'paid': '✅',
                            'sent': '📤',
                            'draft': '📝',
                            'overdue': '⚠️',
                            'void': '❌'
                        }.get(status.lower(), '📄')
                        
                        response += f"{i}. {status_emoji} **{invoice.get('invoice_number', 'N/A')}**\n"
                        response += f"   - Customer: {invoice.get('customer_name', 'N/A')}\n"
                        response += f"   - Date: {invoice.get('date', 'N/A')}\n"
                        response += f"   - Due: {invoice.get('due_date', 'N/A')}\n"
                        response += f"   - Status: {status}\n"
                        response += f"   - Amount: ${invoice.get('total', 0):,.2f}\n"
                        
                        balance = invoice.get('balance', 0)
                        if balance > 0:
                            response += f"   - Balance Due: ${balance:,.2f}\n"
                        
                        response += "\n"
                        
                        total_amount += invoice.get('total', 0)
                        total_balance += balance
                    
                    if invoices:
                        response += f"**Summary:**\n"
                        response += f"  - Total Invoice Amount: ${total_amount:,.2f}\n"
                        if total_balance > 0:
                            response += f"  - Total Outstanding: ${total_balance:,.2f}\n"
                    else:
                        response += "No invoices found.\n"
                else:
                    response += f"❌ Failed to retrieve invoices: {result.get('error', 'Unknown error')}\n"
        
        # Send completion message
        if websocket_manager:
            try:
                from datetime import datetime
                await websocket_manager.send_message(plan_id, {
                    "type": "agent_message",
                    "data": {
                        "agent_name": "Zoho Invoice",
                        "content": "✅ Zoho Invoice query complete",
                        "status": "completed",
                        "timestamp": datetime.utcnow().isoformat() + "Z"
                    }
                })
            except Exception as e:
                logger.error(f"Failed to send WebSocket message: {e}")
        
        return {
            "messages": [response],
            "current_agent": "Zoho Invoice",
            "final_result": response
        }
        
    except Exception as e:
        logger.error(f"Zoho agent error: {e}", exc_info=True)
        error_response = (
            f"Zoho Invoice Agent: ❌ Error processing request\n\n"
            f"{str(e)}\n\n"
            f"Please check your Zoho configuration."
        )
        
        return {
            "messages": [error_response],
            "current_agent": "Zoho Invoice",
            "final_result": error_response
        }
